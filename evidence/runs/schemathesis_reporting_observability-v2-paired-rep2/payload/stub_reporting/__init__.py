# Minimal schemathesis.reporting overlay for the v4.13.0 starter (EBV reviewer-authored).
# Only JunitXmlWriter is behaviourally meaningful; other names are import stubs.
# EBV_JUNIT_VARIANT selects the JunitXmlWriter implementation.
from __future__ import annotations

import os
import platform
from io import StringIO
from pathlib import Path

_VARIANT = os.environ.get("EBV_JUNIT_VARIANT", "correct")


class _Base:
    def __init__(self, output, config=None):
        self._own = not hasattr(output, "write")
        self.output = open(output, "w") if self._own else output
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self._own:
            self.output.close()

    def open(self, seed=None, command=""):
        pass

    def write(self, *a, **k):
        pass


class VcrWriter(_Base):
    pass


class HarWriter(_Base):
    pass


class NdjsonWriter(_Base):
    pass


def get_command_representation():
    return "st run"


class JunitXmlWriter(_Base):
    def __init__(self, output):
        super().__init__(output)
        self.errors = {}

    def record_error(self, label, message):
        self.errors.setdefault(label, []).append(message)

    def close(self):
        out = self.output
        if _VARIANT == "correct":
            # Same library the starter's CLI junit handler already uses.
            from junit_xml import TestCase, TestSuite, to_xml_report_file

            cases = []
            for label, msgs in self.errors.items():
                tc = TestCase(label, elapsed_sec=0.0, allow_multiple_subelements=True)
                for m in msgs:
                    tc.add_error_info(message=m)
                cases.append(tc)
            to_xml_report_file(out, [TestSuite("schemathesis", test_cases=cases, hostname=platform.node())], prettyprint=True, encoding="utf-8")
        elif _VARIANT == "drops_error":
            # Plausibly-wrong: well-formed XML, testcase listed, but the error is never written
            # (the case would be reported as PASSING in CI).
            out.write('<?xml version="1.0" ?>\n<testsuites><testsuite name="schemathesis" tests="%d">' % len(self.errors))
            for label in self.errors:
                out.write(f'<testcase name="{label}"/>')
            out.write("</testsuite></testsuites>\n")
        elif _VARIANT == "unterminated":
            # Plausibly-wrong: forgets to close the root elements (malformed XML).
            out.write('<?xml version="1.0" ?>\n<testsuites><testsuite name="schemathesis">')
            for label, msgs in self.errors.items():
                out.write(f'<testcase name="{label}"><error message="{msgs[0]}"/></testcase>')
        elif _VARIANT == "plaintext":
            # Clearly-wrong control: not XML at all.
            for label, msgs in self.errors.items():
                out.write(f"schemathesis {label}: {msgs[0]}\n")
        super().close()
