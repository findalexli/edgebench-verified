#!/usr/bin/env python3
"""Fail closed on incomplete or incorrect six-arm FFmpeg native receipts."""
import json
import math
from pathlib import Path
import re
import sys

ARMS = tuple(f"ffmpeg-{arm}-{revision}" for arm in ("good", "skip", "bad")
             for revision in ("original", "candidate"))


def validate(directory):
    directory = Path(directory)
    errors = []
    try:
        lines = (directory / "summary.txt").read_text().splitlines()
    except OSError as exc:
        lines = []
        errors.append(f"summary.txt: {exc}")
    exits = {}
    for line in lines:
        match = re.fullmatch(r"(ffmpeg-[a-z]+-[a-z]+) exit=(\d+) seconds=(\d+)", line)
        if not match or match[1] not in ARMS or match[1] in exits:
            errors.append(f"invalid or duplicate summary entry: {line!r}")
            continue
        exits[match[1]] = int(match[2])
    for arm in ARMS:
        if exits.get(arm) != 0:
            errors.append(f"{arm}: missing or unsuccessful exit ({exits.get(arm)})")
        folder = directory / arm
        for artifact in ("container.log", "stdout.log", "reward.json", "reward.txt"):
            if not (folder / artifact).is_file():
                errors.append(f"{arm}: missing {artifact}")
        try:
            data = json.loads((folder / "reward.json").read_text())
            reward = data["reward"]
            if isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(reward):
                raise ValueError("reward is not a finite number")
            if data["score"] != reward or float((folder / "reward.txt").read_text()) != reward:
                raise ValueError("score/reward artifacts disagree")
            positive = "-good-" in arm or arm == "ffmpeg-skip-original"
            if not (reward > 0 if positive else reward == 0):
                raise ValueError(f"expected {'positive' if positive else 'zero'} reward, got {reward}")
            details = data["additional_data"]
            passed = 0 if "-bad-" in arm else 30
            if details["correctness_total"] != 30 or details["correctness_passed"] != passed:
                raise ValueError(f"expected {passed}/30 correctness")
            if passed:
                factors = details["per_workload_speedups"]
                results = details["benchmark_results"]
                if details["workloads_benchmarked"] != 10 or len(factors) != 10 or len(results) != 10:
                    raise ValueError("expected all ten timing workloads")
                if positive:
                    if not all(isinstance(s, (int, float)) and math.isfinite(s) and s > 0 for s in factors):
                        raise ValueError("successful control has invalid speedup factors")
                elif any(s != 0 for s in factors) or not all(r.get("error") for r in results):
                    raise ValueError("skipped-call control did not fail all ten timing workloads")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{arm}: {exc}")
    return errors


if __name__ == "__main__":
    failures = validate(sys.argv[1])
    print(json.dumps({"status": "fail" if failures else "pass", "arms": len(ARMS), "errors": failures}, indent=2))
    sys.exit(bool(failures))
