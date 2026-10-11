# Copyright (c) 2026 EdgeBench Verified contributors
# SPDX-License-Identifier: Apache-2.0
"""Tiny payload/thread controls only; no provider, benchmark or cloud work."""
import threading
import time
import unittest

from tools.cloud_dispatch_resources import (
    DEFAULT_PAYLOAD_BYTES, StagingBudget, StagingCapacityTimeout, StagingStopped,
)


def receipt(lease, job_id="job-1"):
    return {"job_id": job_id, "file_count": lease.file_count, "input_bytes": lease.byte_count,
            "input_sha256": lease.expected_sha256, "remote_input_hashes_verified": True}


def wait_until(predicate):
    deadline = time.monotonic() + 2
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("Thread did not reach the expected test barrier")
        time.sleep(.002)


class DispatchResourceTests(unittest.TestCase):
    def test_default_gate_admits_four_payloads_before_any_fifth_load(self):
        budget = StagingBudget()
        leases = [budget.load(lambda: {"tiny": b"x"}) for _ in range(4)]
        self.addCleanup(lambda: [lease.close() for lease in leases])
        called = []
        with self.assertRaises(StagingCapacityTimeout):
            budget.load(lambda: called.append(True), timeout_seconds=0)
        self.assertEqual(called, [])
        self.assertEqual(budget.snapshot()["active_stages"], 4)
        self.assertEqual(budget.snapshot()["reserved_bytes"], 4 * DEFAULT_PAYLOAD_BYTES)
        self.assertEqual(budget.snapshot()["loaded_bytes"], 4)

    def test_byte_limit_applies_even_with_free_slot(self):
        budget = StagingBudget(max_stages=3, max_bytes=10)
        first = budget.load(lambda: {"first": b"ab"}, max_payload_bytes=6)
        self.addCleanup(first.close)
        with self.assertRaises(StagingCapacityTimeout):
            budget.load(lambda: {"second": b"cd"}, max_payload_bytes=5, timeout_seconds=0)
        second = budget.load(lambda: {"second": b"cd"}, max_payload_bytes=4)
        self.addCleanup(second.close)
        self.assertEqual(budget.snapshot()["reserved_bytes"], 10)
        self.assertEqual(budget.snapshot()["loaded_bytes"], 4)

    def test_verified_upload_clears_alias_and_frees_stage_before_cloud_run(self):
        budget = StagingBudget(max_stages=1, max_bytes=10)
        alias = {"input": b"baseline"}
        lease = budget.load(lambda: alias, max_payload_bytes=10)
        expected = lease.expected_sha256
        lease.verified_upload(receipt(lease), job_id="job-1")
        self.assertEqual(alias, {})
        self.assertTrue(lease.remote_upload_verified)
        self.assertEqual(lease.expected_sha256, expected)
        self.assertEqual(budget.snapshot()["active_stages"], 0)
        # A next upload may proceed while the first remote job is still running.
        with budget.load(lambda: {"next": b"x"}, max_payload_bytes=10, timeout_seconds=0):
            self.assertEqual(budget.snapshot()["active_stages"], 1)
        with self.assertRaises(RuntimeError):
            _ = lease.payload
        lease.close()  # Idempotent finally cleanup must not underflow counters.
        self.assertEqual(budget.snapshot()["reserved_bytes"], 0)

    def test_incomplete_receipt_raises_and_requires_existing_cleanup_path(self):
        budget = StagingBudget(max_stages=1, max_bytes=10)
        lease = budget.load(lambda: {"input": b"x"}, max_payload_bytes=10)
        self.addCleanup(lease.close)
        bad = {**receipt(lease), "remote_input_hashes_verified": False}
        with self.assertRaises(ValueError):
            lease.verified_upload(bad, job_id="job-1")
        self.assertFalse(lease.remote_upload_verified)
        self.assertEqual(budget.snapshot()["active_stages"], 1)
        self.assertEqual(lease.payload, {"input": b"x"})
        lease.close()
        self.assertFalse(lease.remote_upload_verified)
        self.assertEqual(budget.snapshot()["active_stages"], 0)

    def test_job_hash_count_and_size_receipt_mismatches_are_rejected(self):
        for changed in ({"job_id": "other"}, {"file_count": 2}, {"input_bytes": 99},
                        {"input_sha256": {"input": "sha256:" + "0" * 64}}, {"file_count": True}):
            with self.subTest(changed=changed):
                budget = StagingBudget(max_stages=1, max_bytes=10)
                with budget.load(lambda: {"input": b"x"}, max_payload_bytes=10) as lease:
                    with self.assertRaises(ValueError):
                        lease.verified_upload({**receipt(lease), **changed}, job_id="job-1")
                    self.assertEqual(budget.snapshot()["active_stages"], 1)
                self.assertEqual(budget.snapshot()["active_stages"], 0)

    def test_loader_failure_and_oversized_result_release_admission(self):
        budget = StagingBudget(max_stages=1, max_bytes=4)
        def fail():
            raise ValueError("Validator rejected input")
        with self.assertRaises(ValueError):
            budget.load(fail, max_payload_bytes=4)
        alias = {"oversized": b"12345"}
        with self.assertRaises(ValueError):
            budget.load(lambda: alias, max_payload_bytes=4)
        self.assertEqual(alias, {})
        self.assertEqual(budget.snapshot()["active_stages"], 0)
        self.assertEqual(budget.snapshot()["waiting_stages"], 0)

    def test_gate_reserves_before_blocked_loader_allocates(self):
        budget = StagingBudget(max_stages=1, max_bytes=4)
        initial = budget.load(lambda: {"first": b"x"}, max_payload_bytes=4)
        ran = threading.Event()
        errors = []
        def worker():
            try:
                def load():
                    ran.set()
                    return {"second": b"y"}
                with budget.load(load, max_payload_bytes=4, timeout_seconds=2):
                    pass
            except Exception as error:
                errors.append(type(error))
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            wait_until(lambda: budget.snapshot()["waiting_stages"] == 1)
            self.assertFalse(ran.is_set())
            initial.close()
            thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertTrue(ran.is_set())
            self.assertEqual(errors, [])
        finally:
            initial.close()
            budget.stop()
            thread.join(2)

    def test_stop_wakes_waiters_without_invalidating_active_payload(self):
        budget = StagingBudget(max_stages=1, max_bytes=4)
        initial = budget.load(lambda: {"first": b"x"}, max_payload_bytes=4)
        errors, ran = [], []
        def worker():
            try:
                budget.load(lambda: ran.append(True), max_payload_bytes=4)
            except Exception as error:
                errors.append(type(error))
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            wait_until(lambda: budget.snapshot()["waiting_stages"] == 1)
            budget.stop()
            thread.join(2)
            self.assertEqual(errors, [StagingStopped])
            self.assertEqual(ran, [])
            self.assertEqual(initial.payload, {"first": b"x"})
            self.assertEqual(budget.snapshot()["active_stages"], 1)
            self.assertEqual(budget.snapshot()["waiting_stages"], 0)
        finally:
            budget.stop()
            initial.close()
            thread.join(2)

    def test_fifo_waiters_and_timeout_do_not_leak_tickets(self):
        budget = StagingBudget(max_stages=1, max_bytes=4)
        initial = budget.load(lambda: {"first": b"x"}, max_payload_bytes=4)
        with self.assertRaises(StagingCapacityTimeout):
            budget.load(lambda: {"unused": b"x"}, max_payload_bytes=4, timeout_seconds=0)
        self.assertEqual(budget.snapshot()["waiting_stages"], 0)
        order, errors, threads = [], [], []
        def worker(index):
            try:
                def load():
                    order.append(index)
                    return {"file": b"x"}
                with budget.load(load, max_payload_bytes=4, timeout_seconds=2):
                    pass
            except Exception as error:
                errors.append(type(error))
        try:
            for index in range(3):
                thread = threading.Thread(target=worker, args=(index,))
                thread.start()
                threads.append(thread)
                wait_until(lambda: budget.snapshot()["waiting_stages"] == index + 1)
            initial.close()
            for thread in threads:
                thread.join(2)
            self.assertEqual(order, [0, 1, 2])
            self.assertEqual(errors, [])
            self.assertEqual(budget.snapshot()["active_stages"], 0)
        finally:
            initial.close()
            budget.stop()
            for thread in threads:
                thread.join(2)


if __name__ == "__main__":
    unittest.main()
