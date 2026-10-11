"""Local queue fault controls; no provider calls, workers or benchmark runs."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from contextlib import nullcontext
import importlib.util
import json
import math
import os
from pathlib import Path
import tempfile
import sys
from threading import Barrier
from threading import Event, Lock
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tools.cloud_queue import ATTEMPT_RESERVE_USD, QueueStore, digest, validate_job
import tools.cloud_queue as queue_module
import tools.cloud_policy as policy_module
import tools.cloud_dispatch_resources as staging_module


class CloudQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / 'inspect.py'
        self.input.write_bytes(b'# inert source fixture\n')
        self.dbpath = self.root / 'queue.sqlite'
        self.store = QueueStore(self.dbpath)

    def job(self, name='source-fixture-v1'):
        return {
            'schema_version': 1,
            'job_id': name,
            'task_id': 'dcss_dungeon_ai',
            'execution_class': 'native_image_build',
            'operation_id': 'dcss-native-image-build-v1',
            'status': 'ready',
            'certification_effect': 'none',
            'held_probe': False,
            'timeout_seconds': 30,
            'argv': ['python3', 'inspect.py'],
            'network_class': 'none',
            'acceptance': 'A complete aggregate schema with bound source identity.',
            'quality_scope': 'Source inventory only; no task execution.',
            'inputs': [{'path': 'inspect.py', 'target': 'inspect.py',
                        'sha256': digest(self.input.read_bytes())}],
            'exports': ['result.json'],
            'max_export_bytes': 4096,
        }

    def register(self, name='source-fixture-v1'):
        job = self.job(name)
        validate_job(job, self.root)
        self.store.register(job)
        return job

    def complete_result(self):
        return {'exports_verified': True, 'worker_termination_confirmed': True,
                'job_status': 'passed', 'certification_effect': 'none'}

    def events(self):
        with self.store.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM events ORDER BY id')]

    def test_input_bytes_are_fixed_at_validation(self):
        job = self.job()
        payload = validate_job(job, self.root)
        self.input.write_bytes(b'changed after manifest preparation\n')
        self.assertEqual(payload['inspect.py'], b'# inert source fixture\n')
        with self.assertRaises(ValueError):
            validate_job(job, self.root)

    def test_same_job_identity_cannot_change_inputs_or_scope(self):
        job = self.register()
        for field, value in [('argv', ['other']), ('execution_class', 'native_task_control'),
                             ('quality_scope', 'Different claimed scope')]:
            with self.subTest(field=field):
                changed = deepcopy(job)
                changed[field] = value
                with self.assertRaises(ValueError):
                    self.store.register(changed)
        self.assertEqual(len(self.events()), 1)
        self.assertEqual(self.store.snapshot()['jobs'][0]['state'], 'pending')

    def test_changed_input_under_new_path_cannot_reuse_job_identity(self):
        job = self.register()
        other = self.root / 'other.py'
        other.write_bytes(b'# different input\n')
        changed = deepcopy(job)
        changed['inputs'][0].update(path='other.py', sha256=digest(other.read_bytes()))
        validate_job(changed, self.root)
        with self.assertRaises(ValueError):
            self.store.register(changed)

    def test_input_and_export_paths_stay_canonical_and_in_root(self):
        for name in ['../result', '/tmp/result', 'a/../result', 'a//result',
                     'a/./result', 'a\\result', 'result\x00.json', 'a/']:
            for field in ['path', 'target', 'export']:
                with self.subTest(name=name, field=field):
                    job = self.job()
                    if field == 'export':
                        job['exports'] = [name]
                    else:
                        job['inputs'][0][field] = name
                    with self.assertRaises((ValueError, OSError)):
                        validate_job(job, self.root)

    def test_symlink_input_is_not_an_immutable_regular_file(self):
        link = self.root / 'linked.py'
        link.symlink_to(self.input)
        job = self.job()
        job['inputs'][0]['path'] = 'linked.py'
        with self.assertRaises(ValueError):
            validate_job(job, self.root)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO check requires POSIX')
    def test_fifo_is_rejected_before_any_blocking_read(self):
        os.mkfifo(self.root / 'pipe')
        job = self.job()
        job['inputs'][0]['path'] = 'pipe'
        # Never actually read the FIFO even if validation regresses.
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('nonregular input read')):
            with self.assertRaises(ValueError):
                validate_job(job, self.root)

    def test_duplicate_targets_and_exports_fail(self):
        job = self.job()
        job['inputs'].append(deepcopy(job['inputs'][0]))
        with self.assertRaises(ValueError):
            validate_job(job, self.root)

    def test_private_inputs_require_smt_operation_and_explicit_private_root(self):
        private = self.root / 'private'
        private.mkdir()
        data = b'private compressed-input fixture, no real labels'
        (private / 'case.deflate').write_bytes(data)
        job = self.job()
        job['inputs'] = [{'storage': 'private_smt', 'path': 'case.deflate',
                          'target': 'inputs/case.deflate', 'sha256': digest(data)}]
        with self.assertRaises(ValueError):
            validate_job(job, self.root, private_root=private)
        job['operation_id'] = 'smt-cvc5-oracle-shard-v1'
        job['execution_class'] = 'oracle_screen'
        with patch.dict(queue_module.APPROVED_OPERATIONS, {'smt-cvc5-oracle-shard-v1': 'oracle_screen'}):
            with self.assertRaises(ValueError):
                validate_job(job, self.root)
            self.assertEqual(validate_job(job, self.root, private_root=private), {'inputs/case.deflate': data})
            job['inputs'][0]['path'] = '../inspect.py'
            with self.assertRaises(ValueError):
                validate_job(job, self.root, private_root=private)
        job = self.job()
        job['exports'].append(job['exports'][0])
        with self.assertRaises(ValueError):
            validate_job(job, self.root)

    def test_held_jobs_cannot_use_underscore_aliases(self):
        for held in ['ad-overlap', 'coq-output', 'native-codec',
                     'ad_overlap', 'coq_output', 'native_codec']:
            with self.subTest(held=held):
                with self.assertRaises(ValueError):
                    validate_job(self.job(held + '-v1'), self.root)
        job = self.job()
        job['held_probe'] = True
        with self.assertRaises(ValueError):
            validate_job(job, self.root)

    def test_unknown_class_and_certification_are_rejected(self):
        for field, value in [('execution_class', 'all_checks'),
                             ('certification_effect', 'verified'),
                             ('network_class', 'unrestricted'), ('status', 'held')]:
            with self.subTest(field=field):
                job = self.job()
                job[field] = value
                with self.assertRaises(ValueError):
                    validate_job(job, self.root)

    def test_two_coordinators_cannot_claim_same_job(self):
        self.register()
        # Construct both connections before the rendezvous, then contend on claim.
        a, b = QueueStore(self.dbpath), QueueStore(self.dbpath)
        barrier = Barrier(2)

        def contend(store):
            barrier.wait(timeout=5)
            try:
                return ('claimed', store.claim('source-fixture-v1', 0))
            except ValueError:
                return ('rejected', None)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(contend, [a, b]))
        self.assertCountEqual([r[0] for r in results], ['claimed', 'rejected'])
        self.assertEqual(self.store.snapshot()['conservatively_reserved_usd'], ATTEMPT_RESERVE_USD)
        self.assertEqual([e['event'] for e in self.events()], ['registered', 'launch_intent'])

    def test_astra_pilot_has_narrow_resources_and_private_export_scope(self):
        job = self.job('astra-fixture')
        job.update(operation_id='astra-graph-agent-pilot-v1',
                   execution_class='native_task_control',
                   task_id='graph_node_classification', resource_profile='large',
                   network_class='account_authenticated_model',
                   exports=['result.json', 'preparation.json', 'pilot-artifacts.tar.gz'],
                   private_exports=['pilot-artifacts.tar.gz'],
                   max_export_bytes=64 * 1024**2 + 256 * 1024)
        self.assertEqual(validate_job(job, self.root), {'inspect.py': self.input.read_bytes()})
        for field, value in [
            ('resource_profile', 'small'), ('task_id', 'another_task'),
            ('network_class', 'none'), ('private_exports', []),
            ('exports', ['result.json', 'preparation.json', 'auth.json']),
            ('max_export_bytes', 64 * 1024**2 + 256 * 1024 + 1),
        ]:
            with self.subTest(field=field):
                changed = deepcopy(job)
                changed[field] = value
                with self.assertRaises(ValueError):
                    validate_job(changed, self.root)
        ordinary = self.job()
        ordinary['max_export_bytes'] = 2 * 1024**2 + 1
        with self.assertRaises(ValueError):
            validate_job(ordinary, self.root)
        ordinary['max_export_bytes'] = 4096
        ordinary['network_class'] = 'account_authenticated_model'
        with self.assertRaises(ValueError):
            validate_job(ordinary, self.root)
        self.store.register(job)
        self.store.claim(job['job_id'], 0)
        self.assertAlmostEqual(self.store.snapshot()['conservatively_reserved_usd'], .5328)

    def test_durable_launch_intent_blocks_retry_after_coordinator_loss(self):
        self.register()
        attempt = self.store.claim('source-fixture-v1', 0)
        reopened = QueueStore(self.dbpath)
        self.assertEqual(reopened.snapshot()['jobs'][0]['attempt_id'], attempt)
        with self.assertRaises(ValueError):
            reopened.claim('source-fixture-v1', 0)
        self.assertEqual(reopened.snapshot()['conservatively_reserved_usd'], ATTEMPT_RESERVE_USD)

    def test_failed_event_commit_rolls_back_claim_and_budget(self):
        self.register()
        with patch.object(QueueStore, 'event', side_effect=RuntimeError('simulated evidence write failure')):
            with self.assertRaises(RuntimeError):
                self.store.claim('source-fixture-v1', 0)
        self.assertEqual(self.store.snapshot()['jobs'][0]['state'], 'pending')
        self.assertEqual(self.store.snapshot()['conservatively_reserved_usd'], 0)
        self.assertEqual(len(self.events()), 1)

    def test_budget_counts_previous_and_external_attempts_after_restart(self):
        self.register('first')
        self.register('second')
        self.register('third')
        ceiling = 3 * ATTEMPT_RESERVE_USD
        store = QueueStore(self.dbpath, ceiling_usd=ceiling)
        store.claim('first', ATTEMPT_RESERVE_USD)
        reopened = QueueStore(self.dbpath, ceiling_usd=ceiling)
        reopened.claim('second', ATTEMPT_RESERVE_USD)
        with self.assertRaises(ValueError):
            reopened.claim('third', ATTEMPT_RESERVE_USD)
        self.assertAlmostEqual(reopened.snapshot()['conservatively_reserved_usd'], 2 * ATTEMPT_RESERVE_USD)

    def test_nonfinite_or_negative_cost_inputs_do_not_reserve(self):
        self.register()
        for value in [math.nan, math.inf, -math.inf, -0.001, '0']:
            with self.subTest(value=value):
                with self.assertRaises((ValueError, TypeError)):
                    self.store.claim('source-fixture-v1', value)
        self.assertEqual(self.store.snapshot()['conservatively_reserved_usd'], 0)

    def test_large_profile_reserves_its_own_cost_and_respects_total_ceiling(self):
        first = self.job('large-first')
        first.update(resource_profile='large', operation_id='smt-cvc5-high-memory-v1', execution_class='oracle_screen')
        second = deepcopy(first)
        second['job_id'] = 'large-second'
        store = QueueStore(self.dbpath, ceiling_usd=.8)
        store.register(first)
        store.register(second)
        store.claim('large-first', 0)
        self.assertAlmostEqual(store.snapshot()['conservatively_reserved_usd'], .5328)
        with self.assertRaises(ValueError):
            store.claim('large-second', 0)

    def test_large_input_bound_requires_explicit_memory_retry_profile(self):
        data = b'x' * (16 * 1024**2 + 1)
        path = self.root / 'larger.deflate'
        path.write_bytes(data)
        job = self.job('large-input')
        job['inputs'] = [{'path': path.name, 'target': path.name, 'sha256': digest(data)}]
        with self.assertRaises(ValueError):
            validate_job(job, self.root)
        job['resource_profile'] = 'large'
        with self.assertRaises(ValueError):
            validate_job(job, self.root)
        job.update(operation_id='smt-cvc5-high-memory-v1', execution_class='oracle_screen')
        with patch.dict(queue_module.APPROVED_OPERATIONS, {'smt-cvc5-high-memory-v1': 'oracle_screen'}):
            self.assertEqual(validate_job(job, self.root)[path.name], data)
            job.pop('resource_profile')
            with self.assertRaises(ValueError):
                validate_job(job, self.root)

    def test_unknown_and_failure_records_survive_and_cannot_be_overwritten(self):
        for state in ['needs_reconciliation', 'failed']:
            with self.subTest(state=state):
                name = 'fixture-' + state
                self.register(name)
                attempt = self.store.claim(name, 0)
                result = {'job_status': 'unknown', 'exports_verified': False,
                          'worker_termination_confirmed': False, 'error_class': 'ApiOutcomeUnknown'}
                self.store.finish(name, attempt, state, result)
                reopened = QueueStore(self.dbpath)
                with self.assertRaises(ValueError):
                    reopened.claim(name, 0)
                with self.assertRaises(ValueError):
                    reopened.finish(name, attempt, 'completed', self.complete_result())
                with reopened.connect() as db:
                    saved = db.execute('SELECT result FROM attempts WHERE attempt_id=?', (attempt,)).fetchone()[0]
                self.assertEqual(json.loads(saved), result)

    def test_completion_requires_real_execution_and_literal_evidence_flags(self):
        self.register()
        attempt = self.store.claim('source-fixture-v1', 0)
        with self.assertRaises(ValueError):
            self.store.finish('source-fixture-v1', attempt, 'completed', self.complete_result())
        self.store.mark_running('source-fixture-v1', attempt, 'owned-mock-worker')
        for field, value in [('exports_verified', False), ('exports_verified', 'false'),
                             ('worker_termination_confirmed', False),
                             ('worker_termination_confirmed', 'unknown'), ('job_status', 'failed'),
                             ('job_status', 'completed')]:
            with self.subTest(field=field, value=value):
                result = self.complete_result()
                result[field] = value
                with self.assertRaises(ValueError):
                    self.store.finish('source-fixture-v1', attempt, 'completed', result)
        self.store.finish('source-fixture-v1', attempt, 'completed', self.complete_result())
        snapshot = self.store.snapshot()
        self.assertEqual(snapshot['jobs'][0]['state'], 'completed')
        self.assertEqual(snapshot['certified_tasks'], 0)
        self.assertEqual(snapshot['conservatively_reserved_usd'], ATTEMPT_RESERVE_USD)

    def test_foreign_attempt_cannot_take_ownership_or_finish(self):
        self.register()
        attempt = self.store.claim('source-fixture-v1', 0)
        with self.assertRaises(ValueError):
            self.store.mark_running('source-fixture-v1', 'different-attempt', 'mock')
        with self.assertRaises(ValueError):
            self.store.finish('source-fixture-v1', 'different-attempt', 'failed', {})
        self.assertEqual(self.store.snapshot()['jobs'][0]['attempt_id'], attempt)

    def mock_cli(self, *, run_unknown=False, exit_code=0, driver_status='passed'):
        """Inject every cloud boundary; the actual queue and CLI transitions run."""
        module_path = Path(__file__).resolve().parents[1] / 'tools/run_cloud_audit.py'
        spec = importlib.util.spec_from_file_location('cloud_audit_review_fixture', module_path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'cloud_queue': queue_module, 'cloud_policy': policy_module,
                                     'cloud_dispatch_resources': staging_module}):
            spec.loader.exec_module(module)
        module.STAGING_BUDGET = staging_module.StagingBudget()
        module.ROOT = self.root
        module.lifecycle_lock = nullcontext
        module.external_leases = lambda: ()
        module.require_audit_time = lambda seconds: None
        events = []
        job = self.job()
        queue_store = self.store

        class FakeWorker:
            sandbox_id = 'owned-mock-worker'

            def job_root(self, job_id):
                return '/tmp/owned-mock/' + job_id

            def upload(self, *args, **kwargs):
                events.append('upload')
                return {'job_id': args[0], 'file_count': len(args[1]),
                        'input_bytes': sum(map(len, args[1].values())),
                        'input_sha256': args[2], 'remote_input_hashes_verified': True}

            def run(self, *args, **kwargs):
                events.append('run')
                if module.STAGING_BUDGET.snapshot()['active_stages'] != 0:
                    raise AssertionError('Local payload staging retained throughout cloud run')
                if run_unknown:
                    raise queue_unknown('API response lost')
                return {'exit_code': exit_code}

            def download(self, job_id, allowlist, destination, **kwargs):
                events.append('download')
                destination.mkdir(parents=True, exist_ok=True)
                value = {'schema_version': 1, 'job_id': job_id, 'task_id': 'dcss_dungeon_ai',
                         'status': 'running' if run_unknown else driver_status,
                         'scope': 'Mocked transport; no task or image execution.'}
                (destination / 'result.json').write_text(json.dumps(value))
                return {'files': [{'path': 'result.json',
                                  'sha256': 'sha256:' + digest((destination / 'result.json').read_bytes())}]}

            def close(self, *args, **kwargs):
                events.append('close')
                return {'absence_confirmed': True}

        class queue_unknown(RuntimeError):
            pass

        class FakeManager:
            def __init__(self, *args, **kwargs):
                events.append('manager')

            def reserve(self, *args, **kwargs):
                events.append('reserve')
                if queue_store.snapshot()['jobs'][0]['state'] != 'pending':
                    raise AssertionError('Capacity should be reserved before spending intent')
                return 'mock-reservation-token'

            def create_reserved(self, *args, **kwargs):
                if queue_store.snapshot()['jobs'][0]['state'] != 'launch_intent':
                    raise AssertionError('Provider creation before durable spending intent')
                events.append('create')
                return FakeWorker()

            def cancel_reservation(self, *args, **kwargs):
                events.append('cancel')

        class CapacityUnavailable(RuntimeError):
            pass

        provider_module = SimpleNamespace(CloudWorkerManager=FakeManager, SDKProvider=lambda **kwargs: object(),
                                         CapacityUnavailable=CapacityUnavailable)
        return module, provider_module, events, job

    def test_cli_nonzero_process_cannot_complete_from_passed_json(self):
        module, providers, events, job = self.mock_cli(exit_code=1)
        with patch.dict(sys.modules, {'cloud_worker': providers}):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'failed')
        self.assertTrue(outcome['worker_termination_confirmed'])
        self.assertEqual(events, ['manager', 'reserve', 'create', 'upload', 'run', 'download', 'close'])

    def test_driver_terminal_status_is_operation_specific(self):
        module, providers, _, job = self.mock_cli(driver_status='completed')
        with patch.dict(sys.modules, {'cloud_worker': providers}):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'failed')

    def test_cli_publication_failure_is_not_completed(self):
        module, providers, events, job = self.mock_cli()
        normal_save = module.save

        def fail_public_copy(path, value):
            if 'cloud-runs' in path.parts:
                raise OSError('simulated repository export failure')
            return normal_save(path, value)

        with patch.dict(sys.modules, {'cloud_worker': providers}), patch.object(module, 'save', fail_public_copy):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'needs_reconciliation')
        self.assertTrue(outcome['worker_termination_confirmed'])
        saved = self.store.snapshot()['jobs'][0]
        self.assertEqual(saved['state'], 'needs_reconciliation')

    def test_cli_unknown_run_attempts_checkpoint_export_before_cleanup(self):
        module, providers, events, job = self.mock_cli(run_unknown=True)
        with patch.dict(sys.modules, {'cloud_worker': providers}):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'needs_reconciliation')
        self.assertIn('download', events)
        self.assertLess(events.index('download'), events.index('close'))
        self.assertTrue(outcome['worker_termination_confirmed'])

    def test_cli_expired_allowance_does_not_contact_provider(self):
        module, providers, events, job = self.mock_cli()
        module.require_audit_time = lambda seconds: (_ for _ in ()).throw(ValueError('deadline expired'))
        with patch.dict(sys.modules, {'cloud_worker': providers}):
            with self.assertRaises(ValueError):
                module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(events, [])
        self.assertEqual(self.store.snapshot()['conservatively_reserved_usd'], 0)

    def test_cli_slow_preparation_rechecks_deadline_before_execution(self):
        module, providers, events, job = self.mock_cli()

        def deadline_after_preparation(seconds):
            if 'upload' in events:
                raise ValueError('setup consumed remaining job allowance')

        module.require_audit_time = deadline_after_preparation
        with patch.dict(sys.modules, {'cloud_worker': providers}):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'needs_reconciliation')
        self.assertNotIn('run', events)
        self.assertIn('close', events)
        self.assertTrue(outcome['worker_termination_confirmed'])

    def test_capacity_saturation_does_not_claim_or_spend(self):
        module, providers, events, job = self.mock_cli()
        with patch.dict(sys.modules, {'cloud_worker': providers}), patch.object(
                providers.CloudWorkerManager, 'reserve', side_effect=providers.CapacityUnavailable()):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'deferred_capacity')
        self.assertEqual(self.store.snapshot()['conservatively_reserved_usd'], 0)
        self.assertNotIn('create', events)

    def test_budget_exhaustion_releases_uncreated_capacity(self):
        module, providers, events, job = self.mock_cli()
        with patch.dict(sys.modules, {'cloud_worker': providers}), patch.object(self.store, 'claim', side_effect=ValueError('budget')):
            outcome = module.execute_one(job, self.store, self.root / 'state')
        self.assertEqual(outcome['state'], 'deferred_claim_or_budget')
        self.assertEqual(self.store.snapshot()['conservatively_reserved_usd'], 0)
        self.assertEqual(events, ['manager', 'reserve', 'cancel'])

    def test_parallel_dispatch_bounds_threads_and_drains_known_running_jobs(self):
        module, _, _, _ = self.mock_cli()
        rendezvous = Barrier(2)
        counts = {'running': 0, 'peak': 0}
        lock = Lock()
        outcomes = []

        def execute(job):
            with lock:
                counts['running'] += 1
                counts['peak'] = max(counts['peak'], counts['running'])
            rendezvous.wait(timeout=5)
            with lock:
                counts['running'] -= 1
            return {'job_id': job['job_id'], 'state': 'completed'}

        dispatched = module.dispatch_jobs([{'job_id': str(i)} for i in range(4)], execute,
            max_jobs=4, concurrency=2, emit=outcomes.append)
        self.assertEqual(dispatched, 4)
        self.assertEqual(counts, {'running': 0, 'peak': 2})
        self.assertEqual(len(outcomes), 4)

    def test_unknown_outcome_stops_refill_but_drains_other_job(self):
        module, _, _, _ = self.mock_cli()
        rendezvous = Barrier(2)
        release = Event()
        outcomes = []

        def execute(job):
            rendezvous.wait(timeout=5)
            if job['job_id'] == 'first':
                return {'job_id': 'first', 'state': 'needs_reconciliation'}
            self.assertTrue(release.wait(timeout=5))
            return {'job_id': job['job_id'], 'state': 'completed'}

        def emit(outcome):
            outcomes.append(outcome)
            if outcome['state'] == 'needs_reconciliation':
                release.set()

        dispatched = module.dispatch_jobs([{'job_id': name} for name in ('first', 'second', 'never')], execute,
            max_jobs=3, concurrency=2, emit=emit)
        self.assertEqual(dispatched, 2)
        self.assertEqual({item['job_id'] for item in outcomes}, {'first', 'second'})

    def test_report_failure_stops_admission_before_executor_exit(self):
        module, _, _, _ = self.mock_cli()
        stopped = Event()

        def emit(_outcome):
            raise BrokenPipeError('simulated output channel loss')

        with self.assertRaises(BrokenPipeError):
            module.dispatch_jobs([{'job_id': 'first'}, {'job_id': 'never'}],
                lambda job: {'job_id': job['job_id'], 'state': 'completed'},
                max_jobs=2, concurrency=1, emit=emit, stop_admissions=stopped.set)
        self.assertTrue(stopped.is_set())


if __name__ == '__main__':
    unittest.main()
