# Written by the earlier automated audit of EdgeBench Verified; not ByteDance code.
# It tests the stricter grading patch in verified-harness.patch, NOT EdgeBench's harness:
# against the original sforge/ (6e4e5f4) most tests fail by design. Apply the patch to a
# scratch copy of sforge/ before running it. Licensed under Apache-2.0, like this repository.

"""Grading regressions with authentic pytest subprocesses, not task certification."""

import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from sforge.harness.grading import EvalReport, extract_score, grade_output
from sforge.harness.selection import select_best

POLICIES = ('pass_rate_first', 'score_first', 'valid_then_score')


def grade(output, parser='structured_json', timed_out=False):
    task = SimpleNamespace(task_id='fixture', judge=SimpleNamespace(parser=parser))
    return grade_output(task, output, 'submission', timed_out=timed_out)


def structured(data):
    return '>>>>> Start Structured Result\n' + json.dumps(data) + '\n>>>>> End Structured Result'


def entry(report):
    return {**report.to_dict(), 'type': 'submission', 'status': 'completed', 'round': 'fixture'}


class GradingContractTests(unittest.TestCase):
    def assert_unrankable(self, report):
        self.assertFalse(report.valid)
        self.assertIsNone(report.score)
        self.assertEqual(report.pass_rate, 0)
        for policy in POLICIES:
            self.assertFalse(select_best([entry(report)], policy=policy)['best_valid'])

    def pytest_output(self, source, timeout=10):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'test_fixture.py'
            fixture.write_text(source)
            process = subprocess.Popen(
                [sys.executable, '-m', 'pytest', str(fixture), '-v', '--color=no', '-p', 'no:cacheprovider'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                env={**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'})
            try:
                output, _ = process.communicate(timeout=timeout)
                return output, False, process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                output, _ = process.communicate(timeout=10)
                return output, True, process.returncode

    def test_authentic_pytest_timeout_is_not_complete_pass(self):
        output, timed_out, code = self.pytest_output(
            'import time\ndef test_01_pass():\n    assert True\ndef test_02_wait():\n    time.sleep(30)\n', 3)
        self.assertTrue(timed_out)
        self.assertNotEqual(code, 0)
        self.assertIn('collected 2 items', output)
        self.assertIn('test_01_pass PASSED', output)
        report = grade(output, 'pytest_v', True)
        self.assert_unrankable(report)
        self.assertTrue(report.timed_out)
        self.assertEqual(report.passed, 1)  # Diagnostic count, not suite coverage.
        self.assert_unrankable(grade(output, 'pytest_v'))  # Timeout metadata missing.

    def test_authentic_completed_pytest_partial_credit(self):
        output, timed_out, code = self.pytest_output(
            'def test_01_pass():\n    assert True\ndef test_02_fail():\n    assert False\n')
        self.assertFalse(timed_out)
        self.assertEqual(code, 1)  # Ordinary test failure is a completed evaluation.
        report = grade(output, 'pytest_v')
        self.assertTrue(report.valid, report.summary)
        self.assertEqual((report.passed, report.failed, report.total_tests), (1, 1, 2))
        self.assertEqual(report.pass_rate, .5)
        self.assertEqual(select_best([entry(report)])['best_pass_rate'], .5)

    def test_authentic_completed_pytest_all_pass(self):
        output, timed_out, code = self.pytest_output('def test_ok():\n    assert True\n')
        self.assertEqual(code, 0)
        report = grade(output, 'pytest_v', timed_out)
        self.assertTrue(report.valid, report.summary)
        self.assertEqual(report.pass_rate, 1)

    def test_pytest_summary_cannot_hide_unfinished_collection(self):
        self.assert_unrankable(grade('collected 2 items\ntest_a.py::test_a PASSED\n=== 1 passed in 0.01s ===', 'pytest_v'))

    def test_pytest_deselection_and_existing_xfail_semantics(self):
        output = ('collected 4 items / 1 deselected / 3 selected\n'
                  'test_a.py::test_a PASSED\ntest_a.py::test_b XFAIL\ntest_a.py::test_c SKIPPED\n'
                  '=== 1 passed, 1 xfailed, 1 skipped, 1 deselected in 0.01s ===')
        report = grade(output, 'pytest_v')
        self.assertTrue(report.valid, report.summary)
        self.assertEqual((report.total_tests, report.passed), (2, 2))

    def test_absent_malformed_or_unmeasured_structured_result(self):
        outputs = ['', 'evaluator crashed', '{}', '[]', '{"summary":"starting"}',
                   structured({'valid': True}), structured({'metrics': {'log': 1}}),
                   '>>>>> Start Structured Result\n{bad}\n>>>>> End Structured Result\n{"score":99}',
                   '>>>>> Start Structured Result\n{"score":99}',
                   '>>>>> End Structured Result\n{"score":99}', structured([{'score': 1}]),
                   '{"score":1}\n{"score":99}', '{"score":1,"score":99}']
        for output in outputs:
            with self.subTest(output=output):
                self.assert_unrankable(grade(output))

    def test_structured_types_and_finite_values(self):
        bad = [{'score': v} for v in (True, '99', float('nan'), float('inf'), -float('inf'))]
        bad += [{'score': 1, 'pass_rate': v} for v in (True, '1', -.1, 1.1, float('nan'))]
        bad += [{'score': 1, 'valid': v} for v in ('false', 1, None)]
        bad += [{'score': 1, k: v} for k, v in (
            ('details', {'case': {'status': 'PASSED'}}), ('details', [None]), ('details', [{'status': 'BAD'}]),
            ('metrics', []), ('summary', 1), ('total_tests', -1), ('passed', 1.5))]
        bad += [{'score': 1, 'total_tests': 1, 'passed': 2}]
        for data in bad:
            with self.subTest(data=data):
                self.assert_unrankable(grade(structured(data)))
        self.assert_unrankable(grade('{"score":1e999}'))

    def test_empty_details_object_preserves_measured_partial_result(self):
        data = dict(valid=True, score=12.5, pass_rate=.25, total_tests=4,
                    passed=1, failed=3, errors=0, details={},
                    metrics={'component': 12.5}, summary='Completed partial result')
        report = grade(structured(data))
        self.assertEqual(report.to_dict(), grade(structured({**data, 'details': []})).to_dict())
        self.assertTrue(report.valid, report.summary)
        self.assertEqual((report.score, report.pass_rate, report.total_tests,
                          report.passed, report.failed, report.errors, report.details),
                         (12.5, .25, 4, 1, 3, 0, []))
        self.assertEqual(report.metrics, data['metrics'])
        self.assertEqual(report.summary, data['summary'])
        for policy in POLICIES:
            best = select_best([entry(report)], policy=policy)
            self.assertTrue(best['best_valid'])
            self.assertEqual(best['best_score'], 12.5)

    def test_empty_details_object_does_not_bypass_grade_validation(self):
        bad = [{'valid': True, 'details': {}},
               {'valid': False, 'score': 25, 'details': {}},
               {'score': '25', 'details': {}},
               {'score': float('inf'), 'details': {}},
               {'score': 25, 'total_tests': 1, 'passed': 2, 'details': {}}]
        for data in bad:
            with self.subTest(data=data):
                self.assert_unrankable(grade(structured(data)))
        self.assert_unrankable(grade('{"score":1,"score":2,"details":{}}'))
        self.assert_unrankable(grade(structured({'score': 25, 'details': {}}), timed_out=True))

    def test_explicit_counters_are_not_replaced_by_aggregate_detail(self):
        report = grade(structured({'valid': True, 'score': 65, 'pass_rate': .8,
            'passed': 80, 'failed': 20, 'errors': 0, 'total_tests': 100,
            'details': [{'name': 'hidden_score', 'status': 'PASSED', 'score': 65}]}))
        self.assertTrue(report.valid, report.summary)
        self.assertEqual((report.passed, report.failed, report.total_tests), (80, 20, 100))
        self.assertEqual(report.score, 65)
        self.assertEqual(len(report.details), 1)

    def test_complete_weighted_partial_with_per_case_timeout(self):
        report = grade(structured({'valid': True, 'score': 12.5, 'pass_rate': .25,
            'details': [{'name': 'good', 'status': 'PASSED', 'weight': 1, 'score': 12.5},
                        {'name': 'solver_timeout', 'status': 'ERROR', 'weight': 3, 'score': 0}]}))
        self.assertTrue(report.valid, report.summary)
        self.assertEqual(report.pass_rate, .25)  # Explicit weighting wins over detail count.
        for policy in POLICIES:
            result = select_best([entry(report)], policy=policy)
            self.assertEqual(result['best_score'], 12.5)
            self.assertTrue(result['best_valid'])

    def test_score_only_and_unmarked_output_compatibility(self):
        for output in ('{"score":-4.5}', 'diagnostic log\n{"score":0}\nfinished'):
            report = grade(output)
            self.assertTrue(report.valid, report.summary)
            self.assertTrue(select_best([entry(report)], policy='score_first')['best_valid'])

    def test_structured_score_does_not_fall_back_to_stdout(self):
        report = grade('TOTAL_SCORE 999\n' + structured({'score': None, 'pass_rate': .5}))
        self.assertTrue(report.valid)
        self.assertIsNone(report.score)
        self.assert_unrankable(grade('TOTAL_SCORE 999\n' + structured({'valid': False, 'score': 4})))

    def test_markers_ignore_xtrace_and_unrelated_json(self):
        report = grade("+ echo '>>>>> Start Structured Result'\n{\"score\":999}\n" +
                       structured({'score': 4}) + "\n+ echo '>>>>> End Structured Result'")
        self.assertTrue(report.valid, report.summary)
        self.assertEqual(report.score, 4)

    def test_harness_timeout_invalidates_even_complete_result(self):
        report = grade(structured({'score': 100, 'pass_rate': 1}), timed_out=True)
        self.assert_unrankable(report)
        self.assertEqual(report.metrics['observed_score'], 100)

    def test_score_sum_complete_partial_and_signed_score(self):
        report = grade('CASE 0000 OK score=-1.5\nCASE 0001 TLE score=0\n'
                       'TOTAL_SCORE -1.5\nCASES_OK 1\nCASES_TOTAL 2', 'score_sum')
        self.assertTrue(report.valid, report.summary)
        self.assertEqual((report.pass_rate, report.score), (.5, -1.5))
        for policy in POLICIES:
            self.assertTrue(select_best([entry(report)], policy=policy)['best_valid'])

    def test_score_sum_declared_coverage_and_malformed_records(self):
        outputs = ['CASE 0000 OK score=1\nTOTAL_SCORE 1\nCASES_TOTAL 2',
                   'CASE 0000 OK score=1\nTOTAL_SCORE 1\nCASES_OK 0',
                   'CASE 0000 OK score=1\nCASE 0000 OK score=1\nTOTAL_SCORE 2',
                   'CASE 0000 OK score=inf\nTOTAL_SCORE 1', 'compile error',
                   'CASE 0000 OK score=1', 'CASE 0000 OK score=1oops\nTOTAL_SCORE 1']
        for output in outputs:
            with self.subTest(output=output):
                self.assert_unrankable(grade(output, 'score_sum'))

    def test_total_score_framing(self):
        self.assertEqual(extract_score('diagnostic TOTAL_SCORE 999\nTOTAL_SCORE +1.5e-2'), .015)
        for output in ('TOTAL_SCORE 1\nTOTAL_SCORE 2', 'TOTAL_SCORE NaN', 'TOTAL_SCORE inf',
                       'TOTAL_SCORE 1e999', 'TOTAL_SCORE 12invalid'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                extract_score(output)

    def test_pytest_score_prefix_is_narrow_and_duplicates_rejected(self):
        genuine = "tests/test_result.py::test_cost TOTAL_SCORE 7.0000000000"
        self.assertIsNone(extract_score(genuine))  # Generic extractor stays strict.
        self.assertEqual(extract_score(genuine, allow_pytest_prefix=True), 7.0)
        for prefix in ("diagnostic", "tests/test_result.py", "not_a_python_node::test",
                       "log tests/test_result.py::test_cost"):
            with self.subTest(prefix=prefix):
                self.assertIsNone(extract_score(prefix + " TOTAL_SCORE 999", allow_pytest_prefix=True))
        for output in (genuine + "\nTOTAL_SCORE 8", genuine + "\n" + genuine,
                       genuine.replace("7.0000000000", "NaN"),
                       genuine.replace("7.0000000000", "7junk")):
            with self.subTest(output=output), self.assertRaises(ValueError):
                extract_score(output, allow_pytest_prefix=True)

    def test_uninitialized_report_not_valid(self):
        self.assertFalse(EvalReport('task', 'submission').valid)


class SelectionContractTests(unittest.TestCase):
    def test_invalid_nonfinite_incomplete_never_win(self):
        good = {'score': 5, 'pass_rate': .5, 'round': 'good', 'valid': True}
        bad = [{'score': v} for v in (float('nan'), float('inf'), -float('inf'), True, '99')]
        bad += [{'score': 99, 'valid': False}, {'score': 99, 'timed_out': True},
                {'score': 99, 'valid': 'false'}, {'score': 99, 'status': 'running'}]
        bad += [{'score': 99, 'pass_rate': v} for v in (-1, 2, float('nan'), True, '1')]
        for policy, direction, candidate, reverse in itertools.product(POLICIES, ('maximize', 'minimize'), bad, (False, True)):
            entries = [good, {'pass_rate': 1, 'round': 'bad', **candidate}]
            with self.subTest(policy=policy, direction=direction, candidate=candidate, reverse=reverse):
                result = select_best(list(reversed(entries)) if reverse else entries, direction, policy)
                self.assertEqual(result['best_round'], 'good')

    def test_empty_or_unrankable_best_valid_false(self):
        for policy in POLICIES:
            for entries in ([], [{'valid': False, 'score': 1, 'pass_rate': 1}],
                            [{'valid': True, 'score': float('nan'), 'pass_rate': 1}]):
                self.assertFalse(select_best(entries, policy=policy)['best_valid'])
        for policy in ('score_first', 'valid_then_score'):
            self.assertFalse(select_best([{'valid': True, 'score': None}], policy=policy)['best_valid'])

    def test_server_exception_history_requires_observed_measurement(self):
        # Actual _record_submission(..., report_dict=None, error=str(exc)) shape:
        error_entry = {'type': 'submission', 'status': 'completed', 'round': 'agent-1',
                       'error': 'container failed before report'}
        empty_entries = [error_entry, {'status': 'completed'},
                         {'status': 'completed', 'valid': True},
                         {'status': 'completed', 'score': None, 'pass_rate': None},
                         {'type': 'game', 'max_score': 100},
                         {**error_entry, 'score': 999, 'pass_rate': 1}]
        valid_partial = {'type': 'submission', 'status': 'completed', 'round': 'partial',
                         'valid': True, 'score': 0, 'pass_rate': 0}
        for policy, direction in itertools.product(POLICIES, ('maximize', 'minimize')):
            with self.subTest(policy=policy, direction=direction):
                self.assertFalse(select_best(empty_entries, direction, policy)['best_valid'])
                for entries in (empty_entries + [valid_partial], [valid_partial] + empty_entries):
                    result = select_best(entries, direction, policy)
                    self.assertTrue(result['best_valid'])
                    self.assertEqual(result['best_round'], 'partial')
                    self.assertEqual(result['best_score'], 0)
        # Historical/game entries without flags remain compatible when a real
        # observed measurement is present, including measured zero.
        for policy in POLICIES:
            self.assertTrue(select_best([{'score': 0}], policy=policy)['best_valid'])
        self.assertTrue(select_best([{'pass_rate': 0}])['best_valid'])

    def test_ordering_policies_and_directions(self):
        entries = [{'round': 'partial', 'pass_rate': .5, 'score': 100},
                   {'round': 'full-low', 'pass_rate': 1, 'score': 10},
                   {'round': 'full-high', 'pass_rate': 1, 'score': 20}]
        self.assertEqual(select_best(entries)['best_round'], 'full-high')
        self.assertEqual(select_best(entries, 'minimize')['best_round'], 'full-low')
        for policy in ('score_first', 'valid_then_score'):
            self.assertEqual(select_best(entries, 'maximize', policy)['best_round'], 'partial')
            self.assertEqual(select_best(entries, 'minimize', policy)['best_round'], 'full-low')

    def test_zero_valid_and_ties_stable(self):
        entries = [{'round': 'first', 'score': 0, 'pass_rate': 0},
                   {'round': 'second', 'score': 0, 'pass_rate': 0}]
        for policy in POLICIES:
            result = select_best(entries, policy=policy)
            self.assertTrue(result['best_valid'])
            self.assertEqual(result['best_round'], 'first')
            self.assertEqual(result['best_score'], 0)

    def test_unknown_policy_or_direction_rejected(self):
        with self.assertRaises(ValueError):
            select_best([], score_direction='typo')
        with self.assertRaises(ValueError):
            select_best([], policy='typo')


if __name__ == '__main__':
    unittest.main()
