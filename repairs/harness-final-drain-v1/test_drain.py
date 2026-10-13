"""Behavioral tests executing the actual patched harness function with fake I/O."""
import ast
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest

spec = importlib.util.spec_from_file_location('materialize', Path(__file__).with_name('materialize.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.source = module.materialize(Path(cls.temp.name) / 'overlay').read_text()
        cls.tree = ast.parse(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setup_drain(self, finish_times=(), errors=()):
        self.now = 0
        self.calls = 0
        self.finished = False
        def sleep(seconds):
            self.now += seconds
        def get(url, params, timeout):
            self.calls += 1
            if self.calls in errors:
                raise OSError('temporary failure')
            entries = [{'submission_id': str(i), 'status': 'completed' if self.now >= t else ('running' if i == 0 else 'queued')} for i, t in enumerate(finish_times)]
            return types.SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'entries': entries, 'best_score': 42 if all(self.now >= t for t in finish_times) else 0})
        namespace = {'time': types.SimpleNamespace(monotonic=lambda: self.now, time=lambda: self.now, sleep=sleep), 'requests': types.SimpleNamespace(get=get)}
        parts = [n for n in self.tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ('FinalDrainError', '_drain_final_history')]
        exec(compile(ast.Module(body=parts, type_ignores=[]), '<patched harness>', 'exec'), namespace)
        self.namespace = namespace
        self.drain = lambda: namespace['_drain_final_history']('http://judge', 'token', 'secret', 3600, types.SimpleNamespace(info=lambda *_: None, warning=lambda *_: None))

    def test_empty_history(self):
        self.setup_drain()
        self.assertEqual(self.drain()['best_score'], 42)
        self.assertEqual(self.now, 0)

    def test_measured_warehouse_duration(self):
        self.setup_drain((1825.2,))
        self.assertEqual(self.drain()['best_score'], 42)
        self.assertGreaterEqual(self.now, 1825.2)

    def test_serial_queue_longer_than_single_eval_timeout(self):
        self.setup_drain((3500, 7000, 10500))
        self.assertEqual(self.drain()['best_score'], 42)
        self.assertGreaterEqual(self.now, 10500)

    def test_transient_failures(self):
        self.setup_drain((1825.2,), errors=(1, 2, 10))
        self.assertEqual(self.drain()['best_score'], 42)

    def test_persistent_fault_fails(self):
        self.setup_drain(errors=(1, 2, 3))
        with self.assertRaises(self.namespace['FinalDrainError']):
            self.drain()

    def test_stalled_submission_deadline_fails(self):
        self.setup_drain((float('inf'),))
        with self.assertRaises(self.namespace['FinalDrainError']):
            self.drain()
        self.assertEqual(self.now, 4200)

    def test_http_error_fails(self):
        self.setup_drain()
        def bad_status():
            raise OSError('HTTP 503')
        self.namespace['requests'].get = lambda *a, **k: types.SimpleNamespace(raise_for_status=bad_status)
        with self.assertRaises(self.namespace['FinalDrainError']):
            self.drain()

    def test_malformed_history_fails(self):
        self.setup_drain()
        self.namespace['requests'].get = lambda *a, **k: types.SimpleNamespace(raise_for_status=lambda: None, json=lambda: {})
        with self.assertRaises(self.namespace['FinalDrainError']):
            self.drain()

    def test_actual_result_assembly_keeps_late_score(self):
        self.setup_drain((1825.2,))
        branches = [n.orelse for n in ast.walk(self.tree) if isinstance(n, ast.If) and any(isinstance(x, ast.Assign) and isinstance(x.value, ast.Call) and isinstance(x.value.func, ast.Name) and x.value.func.id == '_drain_final_history' for x in n.orelse)]
        self.assertEqual(len(branches), 1)
        branch = branches[0]
        start = next(i for i, x in enumerate(branch) if isinstance(x, ast.Assign) and isinstance(x.value, ast.Call) and isinstance(x.value.func, ast.Name) and x.value.func.id == '_drain_final_history')
        import json
        with tempfile.TemporaryDirectory() as temp:
            ns = dict(self.namespace, host_judge_url='http://judge', session_token='token', admin_secret='secret', task_spec=types.SimpleNamespace(judge=types.SimpleNamespace(eval_timeout=3600)), logger=types.SimpleNamespace(info=lambda *_: None, warning=lambda *_: None), log_dir=Path(temp), json=json, RunResult=lambda **kw: types.SimpleNamespace(**kw), final_archive=b'', agent_output='', agent_timed_out=False, runtime=1, resume_count=0)
            exec(compile(ast.Module(body=branch[start:], type_ignores=[]), '<patched result assembly>', 'exec'), ns)
            self.assertEqual(ns['result'].best_score, 42)
            history = json.loads((Path(temp) / 'run_history.json').read_text())
            self.assertTrue(all(e['status'] == 'completed' for e in history['entries']))

    def test_original_returns_before_same_late_evaluation(self):
        self.setup_drain((1825.2,))
        original = ast.parse((module.ROOT / 'sforge/harness/run_agent.py').read_text())
        branches = [n.orelse for n in ast.walk(original) if isinstance(n, ast.If) and any(isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'drain_deadline' for t in x.targets) for x in n.orelse)]
        self.assertEqual(len(branches), 1)
        branch = branches[0]
        start = next(i for i, x in enumerate(branch) if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'drain_deadline' for t in x.targets))
        import json
        with tempfile.TemporaryDirectory() as temp:
            ns = dict(self.namespace, host_judge_url='http://judge', session_token='token', admin_secret='secret', logger=types.SimpleNamespace(info=lambda *_: None, warning=lambda *_: None), log_dir=Path(temp), json=json, RunResult=lambda **kw: types.SimpleNamespace(**kw), final_archive=b'', agent_output='', agent_timed_out=False, runtime=1, resume_count=0)
            exec(compile(ast.Module(body=branch[start:], type_ignores=[]), '<upstream result assembly>', 'exec'), ns)
            self.assertEqual(self.now, 900)
            self.assertEqual(ns['result'].best_score, 0)
            self.assertEqual(ns['history']['entries'][0]['status'], 'running')

    def test_producer_join_permits_supported_inflight_submission(self):
        self.setup_drain()
        blocks = [n for n in ast.walk(self.tree) if isinstance(n, ast.If) and any(isinstance(x, ast.Expr) and isinstance(x.value, ast.Call) and isinstance(x.value.func, ast.Attribute) and x.value.func.attr == 'join' for x in n.body)]
        self.assertEqual(len(blocks), 1)
        for remaining, succeeds in ((45, True), (420, True), (1000, False)):
            state = {'remaining': remaining}
            def join(timeout):
                state['remaining'] -= timeout
            ns = dict(self.namespace, auto_eval_stop=types.SimpleNamespace(set=lambda: None), auto_eval_thread=types.SimpleNamespace(join=join, is_alive=lambda: state['remaining'] > 0), logger=types.SimpleNamespace(info=lambda *_: None))
            code = compile(ast.Module(body=[blocks[0]], type_ignores=[]), '<actual producer shutdown>', 'exec')
            if succeeds:
                exec(code, ns)
            else:
                with self.assertRaises(self.namespace['FinalDrainError']):
                    exec(code, ns)

    def test_caller_uses_terminal_snapshot_and_propagates_error(self):
        # Execute actual exception-handler guard: all backend kinds must rethrow.
        handlers = [n for n in ast.walk(self.tree) if isinstance(n, ast.ExceptHandler) and n.name == 'e' and any(isinstance(x, ast.If) and 'FinalDrainError' in ast.dump(x.test) for x in n.body)]
        self.assertEqual(len(handlers), 1)
        guard = next(n for n in handlers[0].body if isinstance(n, ast.If))
        self.setup_drain()
        for backend in ('docker', 'k8s', 'e2b'):
            error = self.namespace['FinalDrainError']('incomplete')
            with self.assertRaises(type(error)):
                try:
                    raise error
                except type(error) as e:
                    exec(compile(ast.Module(body=[guard], type_ignores=[]), '<caller guard>', 'exec'), dict(self.namespace, e=e, backend=types.SimpleNamespace(backend_name=backend)))
        self.assertIn('history = _drain_final_history(', self.source)
        self.assertIn('auto_eval_thread.join(timeout=450)', self.source)


if __name__ == '__main__':
    unittest.main()
