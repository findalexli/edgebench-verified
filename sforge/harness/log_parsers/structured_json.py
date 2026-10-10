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

"""Extract one unambiguous structured result; reject malformed result envelopes.

Fields remain optional, with grading validating their types and whether the result
contains a usable measurement. Explicit markers take precedence over log JSON.
"""

from __future__ import annotations

import json
import re

MARKER_START = ">>>>> Start Structured Result"
MARKER_END = ">>>>> End Structured Result"
_RESULT_KEYS = {"valid", "score", "summary", "details", "metrics", "pass_rate",
                "passed", "failed", "errors", "total_tests"}


def _reject_constant(value: str):
    raise ValueError(f"Nonfinite JSON constant: {value}")


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


_DECODER = json.JSONDecoder(parse_constant=_reject_constant,
                            object_pairs_hook=_unique_object)


def parse_structured_json(output: str) -> dict:
    """Return exactly one result object, or raise ValueError.

    A malformed or incomplete marked result never falls back to unrelated log
    JSON. Unmarked output is supported for compatibility, but multiple result
    objects are ambiguous and rejected. This is framing validation, not proof
    that the producer or its stdout is trusted.
    """
    starts = list(re.finditer(r"^" + re.escape(MARKER_START) + r"[ \t]*$", output, re.M))
    ends = list(re.finditer(r"^" + re.escape(MARKER_END) + r"[ \t]*$", output, re.M))
    if starts or ends:
        if len(starts) != 1 or len(ends) != 1 or starts[0].end() >= ends[0].start():
            raise ValueError("Expected exactly one complete structured-result envelope")
        block = output[starts[0].end():ends[0].start()].strip()
        obj = _DECODER.decode(block)
        if not isinstance(obj, dict):
            raise ValueError("Structured result must be a JSON object")
        return obj

    candidates = []
    consumed_until = 0
    for match in re.finditer(r"^[ \t]*\{", output, re.M):
        start = match.end() - 1
        if start < consumed_until:
            continue
        try:
            obj, end = _DECODER.raw_decode(output, start)
        except ValueError as exc:
            # A malformed JSON-looking record might be the intended result;
            # silently scanning past it could select an unrelated later object.
            raise ValueError("Malformed JSON object in unmarked result output") from exc
        consumed_until = end
        if isinstance(obj, dict) and set(obj) & _RESULT_KEYS:
            candidates.append(obj)
    if len(candidates) != 1:
        raise ValueError("Expected one structured result; found " + str(len(candidates)))
    return candidates[0]
