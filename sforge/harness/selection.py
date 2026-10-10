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

"""Select among valid, finite, completed results.

Verified compatibility change: every policy excludes explicitly invalid and
harness-timed-out entries. A completed evaluation can still award partial credit;
failed cases and per-case time limits do not imply an invalid overall result.
"""

from __future__ import annotations

import math
from typing import Any


def _finite_number(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def select_best(
    entries: list[dict[str, Any]],
    score_direction: str = "maximize",
    policy: str = "pass_rate_first",
) -> dict[str, Any]:
    """Select a rankable result, or return best_valid=False when none exists."""
    fn = _POLICIES.get(policy)
    if fn is None:
        raise ValueError(f"Unknown selection policy: {policy}. Available: {list(_POLICIES)}")
    if score_direction not in ("minimize", "maximize"):
        raise ValueError(f"Unknown score direction: {score_direction}")
    return fn(entries, score_direction)


def _completed_submissions(entries: list[dict]) -> list[dict]:
    results = []
    for entry in entries:
        if entry.get("type", "submission") not in ("submission", "game"):
            continue
        if entry.get("status") not in (None, "completed"):
            continue
        # judge_server can record an infrastructure exception with completed
        # status but no report. Status/validity defaults are not measurements.
        if entry.get("error") is not None:
            continue
        if not any(_finite_number(entry.get(key)) for key in ("pass_rate", "score")):
            continue
        # Missing flags remain compatible with historical/game entries, but
        # explicit false or malformed flags never qualify as valid evidence.
        if entry.get("valid", True) is not True or entry.get("timed_out", False) is not False:
            continue
        rate = entry.get("pass_rate", 0.0)
        if rate is None:
            rate = 0.0
        if not _finite_number(rate) or not 0 <= rate <= 1:
            continue
        if entry.get("score") is not None and not _finite_number(entry["score"]):
            continue
        results.append(entry)
    return results


def _is_better_score(new: float, old: float | None, direction: str) -> bool:
    return old is None or (new < old if direction == "minimize" else new > old)


def _empty_result() -> dict:
    return {"best_score": None, "best_pass_rate": 0.0,
            "best_round": "", "best_valid": False}


def _pass_rate_first(entries: list[dict], score_direction: str) -> dict:
    """Higher pass rate wins; compare scores only when both rates are one."""
    result = _empty_result()
    for entry in _completed_submissions(entries):
        rate = entry.get("pass_rate", 0.0) or 0.0
        score = entry.get("score")
        if score is None:
            score = entry.get("max_score")
        if score is not None and not _finite_number(score):
            continue
        better = not result["best_valid"] or rate > result["best_pass_rate"]
        if rate == result["best_pass_rate"] == 1.0 and score is not None:
            better = _is_better_score(score, result["best_score"], score_direction)
        if better:
            result = {"best_score": score if score is not None else rate,
                      "best_pass_rate": rate, "best_round": entry.get("round", ""),
                      "best_valid": True}
    return result


def _score_first(entries: list[dict], score_direction: str) -> dict:
    """Order finite, valid scores independently of pass rate."""
    result = _empty_result()
    for entry in _completed_submissions(entries):
        score = entry.get("score")
        if score is None:
            continue
        if _is_better_score(score, result["best_score"], score_direction):
            result = {"best_score": score,
                      "best_pass_rate": entry.get("pass_rate", 0.0) or 0.0,
                      "best_round": entry.get("round", ""), "best_valid": True}
    return result


def _valid_then_score(entries: list[dict], score_direction: str) -> dict:
    """Retained policy name; validity now gates all Verified policies."""
    return _score_first(entries, score_direction)


_POLICIES = {"pass_rate_first": _pass_rate_first, "score_first": _score_first,
             "valid_then_score": _valid_then_score}
