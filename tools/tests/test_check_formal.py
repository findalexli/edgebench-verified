"""Regression checks for formal-result admission; no Lean/Docker/Java execution."""
import importlib.util
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('check_formal', Path(__file__).resolve().parents[1] / 'check_formal.py')
formal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formal)


class ResultAdmissionTests(unittest.TestCase):
    def test_wrong_invariant_does_not_reproduce_saved_failure(self):
        self.assertNotEqual(formal.tlc_class('Error: Invariant Sound is violated.'),
                            formal.tlc_class('Error: Invariant Complete is violated by the initial state:'))

    def test_tlc_diagnostics_do_not_count_as_success(self):
        for output in ('Error: Invariant Sound could not be evaluated.',
                       'No error has been found\nError: Model checking failed.'):
            self.assertEqual(formal.tlc_class(output), 'unknown')
        self.assertEqual(formal.tlc_class('No error has been found'), 'no-error')
        self.assertEqual(formal.tlc_class('Error: Invariant Sound is violated.\nError: The behavior up to this point is:'), 'violated:Sound')

    def test_tlc_requires_exit_status_for_the_observed_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / 'tla' / 'example'
            model.mkdir(parents=True)
            (model / 'Example.cfg').write_text('INVARIANT Sound\n')
            (model / 'Example.tla').write_text('---- MODULE Example ----\n====\n')
            saved = model / 'tlc-Example.out'
            for output, valid_exit in (
                ('Error: Invariant Sound is violated.\n', 12),
                ('No error has been found\n', 0),
            ):
                saved.write_text(output)
                for exit_code in (-9, 1, 0, 12):
                    with self.subTest(output=output, exit_code=exit_code):
                        result = subprocess.CompletedProcess([], exit_code, output, '')
                        with patch.object(formal, 'FORMAL', root), patch.object(formal, 'jar', return_value='unused'), patch.object(formal.subprocess, 'run', return_value=result):
                            self.assertEqual(formal.check_tla(), (1, int(exit_code != valid_exit)))

    def test_lean_reports_must_cover_requested_declarations(self):
        source = '#print axioms Example.first\n#print axioms Example.second\n'
        partial = "'Example.first' depends on axioms: [propext]\n"
        self.assertFalse(formal.lean_output_ok(source, partial, partial, 0))
        full = partial + "'Example.second' does not depend on any axioms\n"
        self.assertTrue(formal.lean_output_ok(source, full, full, 0))
        self.assertFalse(formal.lean_output_ok(source, full, full, 1))
        self.assertFalse(formal.lean_output_ok(source, full, full + 'error: broken', 0))

    def test_namespace_qualified_output_matches_unqualified_print(self):
        output = "'Example.first' does not depend on any axioms\n"
        self.assertTrue(formal.lean_output_ok('#print axioms first\n', output, output, 0))
        ambiguous = output + "'Other.first' does not depend on any axioms\n"
        self.assertFalse(formal.lean_output_ok('#print axioms first\n', ambiguous, ambiguous, 0))

    def test_inconsistent_name_is_not_a_sorry_exemption(self):
        source = '#print axioms Example.fake_inconsistent\n'
        output = "'Example.fake_inconsistent' depends on axioms: [sorryAx]\n"
        self.assertFalse(formal.lean_output_ok(source, output, output, 0))
        name = 'EbvRefute.installed_div_inconsistent'
        output = f"'{name}' depends on axioms: [sorryAx]\n"
        self.assertTrue(formal.lean_output_ok(f'#print axioms {name}\n', output, output, 0))

    def test_custom_axiom_does_not_pass_by_matching_saved_output(self):
        output = "'Example.proof' depends on axioms: [Example.assumption]\n"
        self.assertFalse(formal.lean_output_ok('#print axioms Example.proof\n', output, output, 0))

    def test_sorry_warning_outside_allowlist_fails(self):
        source = '#print axioms Example.proof\n'
        output = "'Example.proof' depends on axioms: [propext]\n"
        self.assertTrue(formal.lean_output_ok(source, output, output, 0))
        unprinted = "Ebv/Example.lean:12:8: warning: declaration uses `sorry`\n" + output
        self.assertFalse(formal.lean_output_ok(source, unprinted, unprinted, 0))
        allowed = "Ebv/LeanAnalysisLocal.lean:54:8: warning: declaration uses `sorry`\n" + output
        self.assertTrue(formal.lean_output_ok(source, allowed, allowed, 0))

    def test_every_saved_lean_output_passes_its_own_replay(self):
        lean_dir = Path(__file__).resolve().parents[2] / 'evidence/formal/lean/ebv/Ebv'
        checked = 0
        for src in sorted(lean_dir.glob('*.lean')):
            if src.name in formal.LEAN_SETUP_FILES:
                continue
            saved = src.with_suffix('.out').read_text()
            self.assertTrue(formal.lean_output_ok(src.read_text(), saved, saved, 0), src.name)
            checked += 1
        self.assertGreater(checked, 20)

    def test_missing_lean_saved_output_is_a_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'lean' / 'ebv' / 'Ebv'
            source.mkdir(parents=True)
            (source / 'Lost.lean').write_text('#print axioms Example.proof\n')
            with patch.object(formal, 'FORMAL', root), patch.object(formal.subprocess, 'run') as run:
                run.return_value.stdout = '/unused'
                self.assertEqual(formal.check_lean(), (1, 1))
                self.assertEqual(run.call_count, 2)  # path discovery only; no Docker

    def test_missing_tla_saved_output_fails_before_model_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / 'tla' / 'example'
            model.mkdir(parents=True)
            (model / 'Example.cfg').write_text('INVARIANT Sound\n')
            (model / 'Example.tla').write_text('---- MODULE Example ----\n====\n')
            with patch.object(formal, 'FORMAL', root), patch.object(formal, 'jar', return_value='unused'), patch.object(formal.subprocess, 'run') as run:
                self.assertEqual(formal.check_tla(), (1, 1))
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
