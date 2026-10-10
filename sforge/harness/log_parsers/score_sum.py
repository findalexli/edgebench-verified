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

"""Parse complete score-sum records while preserving per-case partial credit.

An evaluator's per-case TLE/RE/WA/CE is an ordinary unsuccessful case. It is
separate from a harness timeout, which means the overall result is incomplete.
"""

from __future__ import annotations

import math
import re

from sforge.harness.constants import PASSED, FAILED

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"


def parse_score_sum(test_output: str) -> list[dict]:
    """Parse CASE records; check declared totals when the evaluator emits them.

    Older emitters without CASES_TOTAL/CASES_OK remain supported; absent totals
    do not establish coverage of an externally expected case set.
    """
    results: list[dict] = []
    seen = set()
    pattern = re.compile(r"CASE\s+(\S+)\s+(OK|TLE|RE|WA|CE)\s+score=(" + NUMBER + r")(?:\s+.*)?")
    for line in test_output.splitlines():
        if not line.startswith("CASE ") and not line.startswith("CASE\t"):
            continue
        match = pattern.fullmatch(line)
        if not match or not math.isfinite(float(match.group(3))):
            raise ValueError("Malformed or nonfinite CASE record")
        case_id, status, _ = match.groups()
        if case_id in seen:
            raise ValueError(f"Duplicate CASE id: {case_id}")
        seen.add(case_id)
        name = f"case_{case_id}" if status == "OK" else f"case_{case_id}_{status}"
        results.append({"name": name, "status": PASSED if status == "OK" else FAILED})
    if not results:
        raise ValueError("No CASE records found")
    for label, actual in (("CASES_TOTAL", len(results)),
                          ("CASES_OK", sum(r["status"] == PASSED for r in results))):
        lines = re.findall(r"^" + label + r"(?:[ \t]+.*)?$", test_output, re.M)
        if lines:
            if len(lines) != 1 or not re.fullmatch(label + r"[ \t]+\d+[ \t]*", lines[0]):
                raise ValueError(f"Malformed or duplicate {label}")
            if int(lines[0].split()[1]) != actual:
                raise ValueError(f"{label} disagrees with CASE records")
    return results
