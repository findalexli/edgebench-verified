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

"""Grading: parse test output and compute pass rate."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, asdict
from typing import Any

from sforge.harness.constants import (
    START_TEST_OUTPUT,
    END_TEST_OUTPUT,
    PASSED,
    FAILED,
    ERROR,
)
from sforge.harness.log_parsers import get_parser
from sforge.harness.task_spec import TaskSpec

SUMMARY_MAX_LEN = 4096


@dataclass
class EvalDetail:
    name: str
    status: str
    message: str | None = None
    score: float | None = None
    weight: float | None = None


@dataclass
class EvalReport:
    task_id: str
    submission_id: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float = 0.0
    score: float | None = None
    score_0_100: float | None = None
    timed_out: bool = False
    runtime_seconds: float = 0.0
    test_details: list[dict] = field(default_factory=list)
    raw_output: str = ""
    valid: bool = False
    summary: str | None = None
    details: list[EvalDetail] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    submitted_at: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_output", None)
        if d.get("summary") and len(d["summary"]) > SUMMARY_MAX_LEN:
            d["summary"] = d["summary"][:SUMMARY_MAX_LEN]
        return d


def extract_score(test_output: str, *, allow_pytest_prefix: bool = False) -> float | None:
    """Read one finite score record; optionally recognize pytest -s node prefixes.

    With pytest -s -v, a test's first stdout write follows its node ID on the
    same line. Only pytest grading enables this exact form; arbitrary diagnostic
    prefixes remain ineligible. This validates framing, not stdout provenance.
    """
    from sforge.harness.log_parsers.score_sum import NUMBER

    lines = re.findall(r"^TOTAL_SCORE(?:[ \t]+.*)?$", test_output, re.MULTILINE)
    if allow_pytest_prefix:
        lines += re.findall(
            r"^[\w/.\-]+\.py(?:::[\w.\-\[\]]+)+[ \t]+(TOTAL_SCORE(?:[ \t]+.*)?)$",
            test_output, re.MULTILINE,
        )
    if not lines:
        return None
    if len(lines) != 1:
        raise ValueError("Multiple TOTAL_SCORE records")
    match = re.fullmatch(r"TOTAL_SCORE[ \t]+(" + NUMBER + r")[ \t]*", lines[0])
    if match is None or not math.isfinite(float(match.group(1))):
        raise ValueError("Malformed or nonfinite TOTAL_SCORE record")
    return float(match.group(1))


def _invalidate(report: EvalReport, reason: str) -> EvalReport:
    """Retain diagnostic observations, but expose no rankable partial result."""
    report.metrics = dict(report.metrics)
    report.metrics["grading_error"] = reason
    report.metrics["observed_pass_rate"] = report.pass_rate
    if report.score is not None:
        report.metrics["observed_score"] = report.score
    report.valid = False
    report.pass_rate = 0.0
    report.score = None
    report.summary = reason + (". " + report.summary if report.summary else "")
    return report


def extract_test_output(raw_output: str) -> str:
    """Extract content between START/END markers, or return full output.

    Markers are anchored at line start so that `set -x` xtrace lines like
    ``+ echo '>>>>> End Test Output'`` don't match first and accidentally
    truncate the real test output that follows. Uses the FIRST line-start
    START marker and the LAST line-start END marker.
    """
    start_tok = "\n" + START_TEST_OUTPUT
    end_tok = "\n" + END_TEST_OUTPUT
    found_start = False
    start_idx = raw_output.find(start_tok)
    if start_idx != -1:
        start_idx += 1
        found_start = True
    elif raw_output.startswith(START_TEST_OUTPUT):
        start_idx = 0
        found_start = True
    end_idx = raw_output.rfind(end_tok)
    if found_start and end_idx != -1 and end_idx > start_idx:
        return raw_output[start_idx + len(START_TEST_OUTPUT) : end_idx].strip()
    return raw_output


def _grade_legacy(
    task_spec: TaskSpec,
    test_output: str,
    submission_id: str,
    timed_out: bool,
    runtime: float,
    raw_output: str,
) -> EvalReport:
    """Grade using a legacy parser that returns list[dict] of test results."""
    parser = get_parser(task_spec.judge.parser)
    test_results = parser(test_output)

    total = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == PASSED)
    failed = sum(1 for r in test_results if r["status"] == FAILED)
    errors = sum(1 for r in test_results if r["status"] == ERROR)
    pass_rate = passed / total if total > 0 else 0.0

    details = [
        EvalDetail(name=r.get("name", ""), status=r["status"])
        for r in test_results
    ]

    if total > 0:
        summary = f"{passed}/{total} tests passed"
        failed_names = [r.get("name", "") for r in test_results if r["status"] != PASSED]
        if failed_names:
            shown = failed_names[:10]
            summary += f". Failed: {', '.join(shown)}"
            if len(failed_names) > 10:
                summary += f" (+{len(failed_names) - 10} more)"
    else:
        summary = "No tests found"

    report = EvalReport(
        task_id=task_spec.task_id,
        submission_id=submission_id,
        total_tests=total,
        passed=passed,
        failed=failed,
        errors=errors,
        pass_rate=pass_rate,
        score=extract_score(test_output, allow_pytest_prefix=task_spec.judge.parser == "pytest_v"),
        timed_out=timed_out,
        runtime_seconds=runtime,
        test_details=test_results,
        raw_output=raw_output,
        valid=True,
        summary=summary,
        details=details,
    )

    try:
        if task_spec.judge.parser == "pytest_v":
            from sforge.harness.log_parsers.pytest_v import validate_pytest_completion
            validate_pytest_completion(test_output, test_results)
        if task_spec.judge.parser == "score_sum" and report.score is None:
            raise ValueError("Missing TOTAL_SCORE record")
        if total == 0:
            raise ValueError("No graded tests found")
    except ValueError as exc:
        return _invalidate(report, str(exc))
    return report


def _finite_number(value: Any, field_name: str) -> None:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be a finite number")


def _validate_structured(data: dict) -> None:
    if "valid" in data and type(data["valid"]) is not bool:
        raise ValueError("valid must be a boolean")
    for name in ("score", "pass_rate"):
        if data.get(name) is not None:
            _finite_number(data[name], name)
    if data.get("pass_rate") is not None and not 0 <= data["pass_rate"] <= 1:
        raise ValueError("pass_rate must be between zero and one")
    for name in ("passed", "failed", "errors", "total_tests"):
        if name in data and (type(data[name]) is not int or data[name] < 0):
            raise ValueError(f"{name} must be a nonnegative integer")
    if data.get("summary") is not None and not isinstance(data["summary"], str):
        raise ValueError("summary must be a string")
    if not isinstance(data.get("metrics", {}), dict):
        raise ValueError("metrics must be an object")
    details = data.get("details", [])
    if not isinstance(details, list):
        raise ValueError("details must be a list")
    for detail in details:
        if not isinstance(detail, dict):
            raise ValueError("Each detail must be an object")
        if detail.get("status") not in (PASSED, FAILED, ERROR):
            raise ValueError("Each detail requires a PASSED, FAILED, or ERROR status")
        if not isinstance(detail.get("name", ""), str):
            raise ValueError("Detail name must be a string")
        if detail.get("message") is not None and not isinstance(detail["message"], str):
            raise ValueError("Detail message must be a string")
        for name in ("score", "weight"):
            if detail.get(name) is not None:
                _finite_number(detail[name], "Detail " + name)
    if not (data.get("score") is not None or data.get("pass_rate") is not None
            or data.get("total_tests", 0) > 0 or details):
        raise ValueError("Structured result contains no grade-bearing measurement")


def _grade_structured(
    task_spec: TaskSpec,
    test_output: str,
    submission_id: str,
    timed_out: bool,
    runtime: float,
    raw_output: str,
) -> EvalReport:
    """Grade structured output without borrowing a score from unrelated logs."""
    from sforge.harness.log_parsers.structured_json import parse_structured_json

    data = parse_structured_json(test_output)
    # Legacy emitters use an empty object for no per-item results. Preserve
    # that lossless case; nonempty objects still fail the list contract.
    if type(data.get("details")) is dict and not data["details"]:
        data = {**data, "details": []}
    _validate_structured(data)
    raw_details = data.get("details", [])
    details = [EvalDetail(name=d.get("name", ""), status=d["status"],
                          message=d.get("message"), score=d.get("score"),
                          weight=d.get("weight")) for d in raw_details]

    # Explicit counters describe the suite; details may be aggregates, a
    # diagnostic subset, or weighted components (e.g. ARC's hidden_score).
    if any(k in data for k in ("passed", "failed", "errors", "total_tests")):
        passed, failed, errors = (data.get(k, 0) for k in ("passed", "failed", "errors"))
        total = data.get("total_tests", passed + failed + errors)
        if data.get("valid", True) and passed + failed + errors > total:
            raise ValueError("Structured counters exceed total_tests")
    else:
        passed = sum(d.status == PASSED for d in details)
        failed = sum(d.status == FAILED for d in details)
        errors = sum(d.status == ERROR for d in details)
        total = len(details)

    # An explicitly supplied rate may be a task-specific weighted measurement.
    # Do not replace it with an unweighted count of diagnostic details.
    pass_rate = data.get("pass_rate")
    if pass_rate is None:
        pass_rate = passed / total if total > 0 else 0.0

    report = EvalReport(
        task_id=task_spec.task_id, submission_id=submission_id,
        total_tests=total, passed=passed, failed=failed, errors=errors,
        pass_rate=pass_rate, score=data.get("score"), timed_out=timed_out,
        runtime_seconds=runtime, raw_output=raw_output,
        valid=data.get("valid", True), summary=data.get("summary"),
        details=details, metrics=data.get("metrics", {}),
    )
    if not report.valid:
        return _invalidate(report, "Evaluator marked submission invalid")
    return report


def grade_output(
    task_spec: TaskSpec,
    raw_output: str,
    submission_id: str,
    timed_out: bool = False,
    runtime: float = 0.0,
) -> EvalReport:
    """Parse test output and compute pass rate."""
    test_output = extract_test_output(raw_output)

    try:
        grader = _grade_structured if task_spec.judge.parser == "structured_json" else _grade_legacy
        report = grader(task_spec, test_output, submission_id, timed_out, runtime, raw_output)
    except (ValueError, OverflowError) as exc:
        report = EvalReport(task_id=task_spec.task_id, submission_id=submission_id,
                            timed_out=timed_out, runtime_seconds=runtime, raw_output=raw_output)
        return _invalidate(report, "Invalid evaluation output: " + str(exc))
    if timed_out:
        return _invalidate(report, "Harness evaluation timed out; result is incomplete")
    return report
