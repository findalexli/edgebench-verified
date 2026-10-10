# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Parser for `pytest -v` output.

Verbose pytest output format:
  tests/test_operators.py::test_add PASSED
  tests/test_operators.py::test_mul FAILED
  tests/test_operators.py::test_neg ERROR

With --forked, crashed tests may appear as:
  FAILED                                     [  5%]
  (no test name — subprocess crashed)

Summary line:
  === 25 passed, 3 failed, 1 error in 12.34s ===
  === 30 passed in 8.21s ===
"""

from __future__ import annotations

import re

from sforge.harness.constants import PASSED, FAILED, ERROR


def _summary_counts(test_output: str) -> dict[str, int] | None:
    # Require a complete terminal-style summary line, not a diagnostic substring.
    matches = list(re.finditer(
        r"^=+\s+([\d\w, ]+)\s+in\s+[\d.]+s(?: \([^\n]*\))?\s+=+[ \t]*$",
        test_output, re.MULTILINE,
    ))
    if not matches:
        return None
    counts = {}
    for match in re.finditer(r"(\d+)\s+(\w+)", matches[-1].group(1)):
        count, label = match.groups()
        counts[label] = counts.get(label, 0) + int(count)
    return counts


def _parse_summary(test_output: str) -> dict[str, int] | None:
    counts = _summary_counts(test_output)
    if counts is None:
        return None
    return {
        "passed": sum(counts.get(s, 0) for s in ("passed", "xfailed", "xpassed")),
        "failed": counts.get("failed", 0),
        "error": counts.get("error", 0) + counts.get("errors", 0),
    }


def validate_pytest_completion(test_output: str, results: list[dict]) -> None:
    """Reject incomplete sessions without treating failed tests as bad framing.

    XFAIL/XPASS and SKIPPED retain upstream's scoring semantics. Collection
    counts are a consistency check when present, not an independent case list.
    """
    summary = _parse_summary(test_output)
    counts = _summary_counts(test_output)
    if summary is None:
        raise ValueError("Missing complete pytest summary")
    if re.search(r"^!+.*(?:Interrupted|KeyboardInterrupt|stopping after).*?!+$", test_output, re.M):
        raise ValueError("Pytest session interrupted or stopped early")
    actual = {"passed": sum(r["status"] == PASSED for r in results),
              "failed": sum(r["status"] == FAILED for r in results),
              "error": sum(r["status"] == ERROR for r in results)}
    if actual != summary:
        raise ValueError("Pytest summary disagrees with named results")
    collection = list(re.finditer(r"collected (\d+) items?([^\n]*)", test_output))
    if collection:
        selected = re.search(r"(\d+) selected", collection[-1].group(2))
        expected = int(selected.group(1) if selected else collection[-1].group(1))
        completed = sum(summary.values()) + counts.get("skipped", 0)
        # Teardown errors can add an ERROR outcome after an already completed
        # test. Therefore only a deficit proves an incomplete collected suite.
        if completed < expected:
            raise ValueError("Pytest summary accounts for fewer than the collected tests")
    if sum(summary.values()) == 0:
        raise ValueError("No graded pytest tests found")


def parse_pytest_v(test_output: str) -> list[dict]:
    """
    Parse pytest -v output.

    Returns list of {"name": str, "status": "PASSED"|"FAILED"|"ERROR"}.

    Uses per-test lines for names, but trusts the summary line for total counts.
    This handles pytest-forked crashes where FAILED appears without a test name.
    """
    results: list[dict] = []

    # Match lines like:
    #   tests/test_ops.py::test_add PASSED
    #   tests/test_ops.py::TestClass::test_method FAILED
    #   tests/test_ops.py::test_neg ERROR
    pattern = re.compile(
        r"^([\w/.\-\[\]]+(?:::[\w.\-\[\]]+)+)\s+(PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED)",
        re.MULTILINE,
    )

    named_passed: list[str] = []
    named_failed: list[str] = []
    named_error: list[str] = []

    for match in pattern.finditer(test_output):
        name = match.group(1)
        raw_status = match.group(2)

        if raw_status in ("PASSED", "XFAIL", "XPASS"):
            named_passed.append(name)
        elif raw_status == "FAILED":
            named_failed.append(name)
        elif raw_status == "SKIPPED":
            continue
        else:
            named_error.append(name)

    # Also match collection errors: "ERROR tests/test_xxx.py" (no :: separator)
    collection_pattern = re.compile(
        r"^ERROR\s+([\w/.\-]+\.py)(?:\s|$)", re.MULTILINE
    )
    for match in collection_pattern.finditer(test_output):
        name = match.group(1)
        if name not in named_error:
            named_error.append(name)

    # Try to get authoritative counts from summary line
    summary = _parse_summary(test_output)

    if summary:
        total_passed = summary["passed"]
        total_failed = summary["failed"]
        total_error = summary["error"]
    elif named_passed or named_failed or named_error:
        total_passed = len(named_passed)
        total_failed = len(named_failed)
        total_error = len(named_error)
    else:
        # No test output at all
        return [{"name": "unknown", "status": ERROR}]

    # Emit named results first
    for name in named_passed:
        results.append({"name": name, "status": PASSED})
    for name in named_failed:
        results.append({"name": name, "status": FAILED})
    for name in named_error:
        results.append({"name": name, "status": ERROR})

    # Fill in unnamed entries from summary (crashed forked tests, etc.)
    unnamed_passed = total_passed - len(named_passed)
    unnamed_failed = total_failed - len(named_failed)
    unnamed_error = total_error - len(named_error)

    for i in range(max(0, unnamed_passed)):
        results.append({"name": f"unnamed_passed_{i + 1}", "status": PASSED})
    for i in range(max(0, unnamed_failed)):
        results.append({"name": f"unnamed_crashed_{i + 1}", "status": FAILED})
    for i in range(max(0, unnamed_error)):
        results.append({"name": f"unnamed_error_{i + 1}", "status": ERROR})

    return results
