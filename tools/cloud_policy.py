"""Shared audit limits and a durable, cross-controller provider creation gate."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import math
import os
from pathlib import Path
import tempfile
import time

POLICY_PATH = Path(__file__).resolve().parents[1] / "audit/cloud/resource-policy.json"


def read_policy(path=None):
    policy = json.loads(Path(path or POLICY_PATH).read_text())
    if policy.get("schema_version") not in (1, 2):
        raise ValueError("Unknown cloud resource policy")
    for key in ("max_workers", "max_requested_workers"):
        if type(policy.get(key)) is not int or not 1 <= policy[key] <= 50:
            raise ValueError("Cloud worker limit must be between 1 and 50")
    if policy["max_workers"] > policy["max_requested_workers"]:
        raise ValueError("Working limit exceeds the user's requested maximum")
    if (policy.get("cpu_per_worker"), policy.get("memory_mib_per_worker"),
            policy.get("template_id"), policy.get("initial_ttl_seconds")) != (
            2, 4096, "l9vwx8ash6vvnhj9dnx7", 1800):
        raise ValueError("Changing worker shape requires a reviewed cost and task policy")
    cost_keys = ("queue_per_attempt_reserve_usd", "create_interval_seconds")
    if policy["schema_version"] == 1:
        # Preserve the historical 15/5 policy interpretation.
        cost_keys += ("compute_ceiling_usd", "external_work_reserved_usd")
    for key in cost_keys:
        value = policy.get(key)
        if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
            raise ValueError("Missing finite cloud cost or creation interval")
    if policy["schema_version"] == 1:
        if policy["compute_ceiling_usd"] > 15 or policy["external_work_reserved_usd"] != 5:
            raise ValueError("Historical cloud policy exceeds its 15/5 allowance")
    else:
        reserve = policy.get("external_work_reserved_usd")
        if ("compute_ceiling_usd" not in policy or policy["compute_ceiling_usd"] is not None
                or type(reserve) not in (int, float) or not math.isfinite(reserve) or reserve != 0
                or policy.get("budget_policy_authority") != {
                    "path": "audit/evidence/sol-cloud-authorization-v1/budget-user-steering-20261009.json",
                    "sha256": "4c1842fe468d3013d360f726615cfefbec5edaf2451b349758c36735ebbd5aa3",
                    "bytes": 2054}):
            raise ValueError("New budget policy requires exact user steering, null ceiling and zero reserve")
    if (policy["queue_per_attempt_reserve_usd"] != .1656
            or not 1 <= policy["create_interval_seconds"] <= 5):
        raise ValueError("Cloud reservation or creation rate changed")
    if policy.get("audit_deadline_utc") != "2026-10-12T05:52:16+00:00":
        raise ValueError("Audit time allowance changed")
    return policy


@contextmanager
def provider_creation_gate(state_dir, minimum_interval_seconds=1.0, *, clock=time.time, sleep=time.sleep):
    """Hold a shared lock through the request; unknown outcomes retain the slot.

    Callers must still reserve worker capacity and money before entering. This
    gate only limits creation request frequency, including failed requests.
    """
    if type(minimum_interval_seconds) not in (int, float) or not math.isfinite(minimum_interval_seconds) or not 1 <= minimum_interval_seconds <= 5:
        raise ValueError("Creation interval must be between 1 and 5 seconds")
    directory = Path(state_dir)
    directory.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(directory / ".create-rate.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        path = directory / "create-rate.json"
        if path.is_symlink():
            raise ValueError("Creation rate state cannot be a symlink")
        now = clock()
        previous = None
        if path.exists():
            state = json.loads(path.read_text())
            previous = state.get("last_request_started_epoch")
            if state.get("schema_version") != 1 or type(previous) not in (int, float) or not math.isfinite(previous):
                raise ValueError("Creation rate state needs reconciliation")
        if previous is not None:
            if type(previous) not in (int, float) or not math.isfinite(previous) or previous > now + 5:
                raise ValueError("Creation rate clock or state needs reconciliation")
            delay = previous + minimum_interval_seconds - now
            if delay > 0:
                sleep(delay)
                now = clock()
                if now < previous + minimum_interval_seconds:
                    raise ValueError("Creation rate clock did not advance")
        if not math.isfinite(now):
            raise ValueError("Invalid creation clock")
        fd, temporary = tempfile.mkstemp(prefix=".create-rate-", dir=directory)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump({"schema_version": 1, "last_request_started_epoch": now}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        yield
    finally:
        os.close(lock_fd)
