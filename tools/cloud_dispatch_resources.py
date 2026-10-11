# Copyright (c) 2026 EdgeBench Verified contributors
# SPDX-License-Identifier: Apache-2.0
"""Limit coordinator payload staging, independently of running cloud jobs.

Acquire before invoking the existing input validator. Keep the lease through
worker creation and verified upload, then release it BEFORE the long cloud run.
Always close it in the coordinator's existing cleanup/finally path as well.

The lease takes ownership of the loader's dict and clears it on release, so
ordinary dict aliases do not retain its byte values. Callers must not separately
cache those values. This caps admitted payload bytes, not RSS: validator
temporaries, SDK buffers, native thread stacks and Python overhead are additional.
It does not replace process limits, remote ownership or uncertainty accounting.
"""
from __future__ import annotations

from collections import deque
import hashlib
import math
import threading
import time

DEFAULT_PAYLOAD_BYTES = 16 * 1024**2
DEFAULT_STAGED_BYTES = 64 * 1024**2
DEFAULT_STAGES = 4
MAX_FILES = 256


class StagingCapacityTimeout(TimeoutError):
    """No local staging slot became available; no loader was invoked."""


class StagingStopped(RuntimeError):
    """Coordinator stopped admissions; existing leases still require cleanup."""


class StagingBudget:
    def __init__(self, *, max_stages=DEFAULT_STAGES, max_bytes=DEFAULT_STAGED_BYTES):
        if type(max_stages) is not int or max_stages < 1 or type(max_bytes) is not int or max_bytes < 1:
            raise ValueError("Positive integer staging limits required")
        self.max_stages, self.max_bytes = max_stages, max_bytes
        self._condition = threading.Condition()
        self._waiting = deque()
        self._leases = {}
        self._stopped = False
        self._peak_slots = self._peak_reserved = self._peak_loaded = 0

    def _reserve(self, amount, timeout_seconds):
        if type(amount) is not int or not 1 <= amount <= self.max_bytes:
            raise ValueError("Payload reservation exceeds staging byte limit")
        if timeout_seconds is not None and (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds) or timeout_seconds < 0):
            raise ValueError("Staging wait must be nonnegative and finite")
        deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
        ticket = object()
        with self._condition:
            self._waiting.append(ticket)
            try:
                while True:
                    if self._stopped:
                        raise StagingStopped("Staging admissions stopped")
                    reserved = sum(row[0] for row in self._leases.values())
                    if self._waiting[0] is ticket and len(self._leases) < self.max_stages and reserved + amount <= self.max_bytes:
                        self._waiting.popleft()
                        self._leases[ticket] = (amount, 0)
                        self._peak_slots = max(self._peak_slots, len(self._leases))
                        self._peak_reserved = max(self._peak_reserved, reserved + amount)
                        self._condition.notify_all()
                        return ticket
                    remaining = None if deadline is None else deadline - time.monotonic()
                    if remaining is not None and remaining <= 0:
                        raise StagingCapacityTimeout("Local payload staging capacity unavailable")
                    self._condition.wait(remaining)
            except BaseException:
                if ticket in self._waiting:
                    self._waiting.remove(ticket)
                    self._condition.notify_all()
                raise

    def _loaded(self, ticket, amount):
        with self._condition:
            reserved, _ = self._leases[ticket]
            if amount > reserved:
                raise ValueError("Loaded payload exceeds its reserved byte budget")
            self._leases[ticket] = (reserved, amount)
            self._peak_loaded = max(self._peak_loaded, sum(row[1] for row in self._leases.values()))

    def _release(self, ticket):
        with self._condition:
            self._leases.pop(ticket, None)
            self._condition.notify_all()

    def load(self, loader, *, max_payload_bytes=DEFAULT_PAYLOAD_BYTES, timeout_seconds=None):
        """Reserve before loader(); returned lease owns and eventually clears dict."""
        ticket = self._reserve(max_payload_bytes, timeout_seconds)
        payload = None
        try:
            payload = loader()
            if type(payload) is not dict or not 1 <= len(payload) <= MAX_FILES or any(
                    not isinstance(name, str) or not 1 <= len(name) <= 512 or not isinstance(value, bytes)
                    for name, value in payload.items()):
                raise ValueError("Loader must return a bounded dict of named byte payloads")
            total = sum(map(len, payload.values()))
            self._loaded(ticket, total)
            hashes = {name: "sha256:" + hashlib.sha256(value).hexdigest() for name, value in payload.items()}
            return StagedPayload(self, ticket, payload, hashes, total)
        except BaseException:
            if type(payload) is dict:
                payload.clear()
            self._release(ticket)
            raise

    def stop(self):
        """Wake/reject waiting admissions; do not invalidate active leases."""
        with self._condition:
            self._stopped = True
            self._condition.notify_all()

    def snapshot(self):
        with self._condition:
            return {"active_stages": len(self._leases), "waiting_stages": len(self._waiting),
                    "reserved_bytes": sum(row[0] for row in self._leases.values()),
                    "loaded_bytes": sum(row[1] for row in self._leases.values()),
                    "peak_stages": self._peak_slots, "peak_reserved_bytes": self._peak_reserved,
                    "peak_loaded_bytes": self._peak_loaded, "admissions_stopped": self._stopped}


class StagedPayload:
    def __init__(self, budget, ticket, payload, hashes, total):
        self._budget, self._ticket = budget, ticket
        self._payload, self._hashes = payload, hashes
        self.byte_count, self.file_count = total, len(payload)
        self._lock = threading.RLock()
        self._closed = False
        self.remote_upload_verified = False

    @property
    def payload(self):
        with self._lock:
            if self._closed:
                raise RuntimeError("Payload has already been released")
            return self._payload

    @property
    def expected_sha256(self):
        return dict(self._hashes)

    def verified_upload(self, receipt, *, job_id):
        """Drop local bytes only after the existing uploader's exact receipt.

        A rejection raises to the coordinator's existing uncertain-outcome and
        cleanup path. Closing a lease never asserts remote success or retryability.
        """
        with self._lock:
            if self._closed:
                raise RuntimeError("Payload has already been released")
            if not isinstance(receipt, dict) or receipt.get("job_id") != job_id or receipt.get("remote_input_hashes_verified") is not True or type(receipt.get("input_bytes")) is not int or receipt["input_bytes"] != self.byte_count or type(receipt.get("file_count")) is not int or receipt["file_count"] != self.file_count or receipt.get("input_sha256") != self._hashes:
                raise ValueError("Verified upload receipt does not match staged payload")
            self.remote_upload_verified = True
            self.close()

    def close(self):
        with self._lock:
            if not self._closed:
                # Clear while admission is still held: the next loader cannot
                # race ahead of dropping these byte references.
                self._payload.clear()
                self._closed = True
                self._budget._release(self._ticket)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# One process-wide budget shared by coordinator network threads. Separate
# coordinator processes each require their own process memory limit.
STAGING_BUDGET = StagingBudget()
