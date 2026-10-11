"""Small provider-free controls for the shared cloud budget and creation rate."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.cloud_policy import POLICY_PATH, provider_creation_gate, read_policy


class CloudPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_policy_separates_requested_maximum_from_active_limit(self):
        policy = read_policy()
        self.assertEqual(policy['max_workers'], 50)
        self.assertEqual(policy['max_requested_workers'], 50)
        self.assertIsNone(policy['account_concurrency_limit'])

    def test_changed_budget_shape_and_invalid_limits_fail_closed(self):
        original = json.loads(POLICY_PATH.read_text())
        for key, value in [('max_workers', 51), ('max_workers', True),
                           ('max_workers', 0), ('cpu_per_worker', 8),
                           ('compute_ceiling_usd', 16), ('compute_ceiling_usd', float('nan')),
                           ('queue_per_attempt_reserve_usd', .01), ('create_interval_seconds', 0)]:
            with self.subTest(key=key, value=value):
                policy = dict(original, **{key: value})
                path = self.root / 'policy.json'
                path.write_text(json.dumps(policy))
                with self.assertRaises(ValueError):
                    read_policy(path)

    def test_gate_waits_for_prior_request_even_after_request_failure(self):
        now = [100.0]
        delays = []

        def sleep(delay):
            delays.append(delay)
            now[0] += delay

        with self.assertRaises(RuntimeError):
            with provider_creation_gate(self.root, clock=lambda: now[0], sleep=sleep):
                raise RuntimeError('simulated ambiguous provider request')
        with provider_creation_gate(self.root, clock=lambda: now[0], sleep=sleep):
            self.assertEqual(now[0], 101.0)
        self.assertEqual(delays, [1.0])
        self.assertEqual(json.loads((self.root / 'create-rate.json').read_text())['last_request_started_epoch'], 101)

    def test_corrupt_future_clock_or_symlink_never_enters_request(self):
        path = self.root / 'create-rate.json'
        for value in [106, float('nan'), '100']:
            path.write_text(json.dumps({'schema_version': 1, 'last_request_started_epoch': value}))
            with self.assertRaises(ValueError):
                with provider_creation_gate(self.root, clock=lambda: 100):
                    self.fail('request gate entered with invalid state')
        for state in [{}, {'schema_version': 2, 'last_request_started_epoch': 100}]:
            path.write_text(json.dumps(state))
            with self.assertRaises(ValueError):
                with provider_creation_gate(self.root, clock=lambda: 100):
                    self.fail('request gate entered with missing or unknown schema')
        path.unlink()
        target = self.root / 'other'
        target.write_text('{}')
        path.symlink_to(target)
        with self.assertRaises(ValueError):
            with provider_creation_gate(self.root):
                self.fail('request gate entered through symlink')

    def test_early_returning_sleep_cannot_break_rate_limit(self):
        with provider_creation_gate(self.root, clock=lambda: 100):
            pass
        with self.assertRaises(ValueError):
            with provider_creation_gate(self.root, clock=lambda: 100, sleep=lambda delay: None):
                self.fail('rate interval was not observed')


if __name__ == '__main__':
    unittest.main()
