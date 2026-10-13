"""Exercise the final native gate against saved receipts and broken copies."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evidence/scripts/validator_followup/check_native_results.py"
RECEIPTS = ROOT / "repairs/ffmpeg_swscale_reimplementation-v2/paired/native-20261013-v2.2"
spec = importlib.util.spec_from_file_location("native_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_saved_receipts_pass():
    assert gate.validate(RECEIPTS) == []


@pytest.mark.parametrize("fault", ["missing_arm", "failed_exit", "missing_reward", "wrong_reward", "wrong_correctness", "missing_workload", "duplicate_exit"])
def test_broken_receipts_fail(tmp_path, fault):
    out = tmp_path / "out"
    shutil.copytree(RECEIPTS, out)
    arm = out / "ffmpeg-skip-candidate"
    if fault == "missing_arm":
        shutil.rmtree(arm)
    elif fault == "failed_exit":
        summary = out / "summary.txt"
        summary.write_text(summary.read_text().replace("ffmpeg-skip-candidate exit=0", "ffmpeg-skip-candidate exit=124"))
    elif fault == "duplicate_exit":
        summary = out / "summary.txt"
        summary.write_text(summary.read_text() + "ffmpeg-skip-candidate exit=0 seconds=25\n")
    elif fault == "missing_reward":
        (arm / "reward.json").unlink()
    else:
        path = arm / "reward.json"
        data = json.loads(path.read_text())
        if fault == "wrong_reward":
            data["reward"] = data["score"] = 1.0
            (arm / "reward.txt").write_text("1.0\n")
        elif fault == "wrong_correctness":
            data["additional_data"]["correctness_passed"] = 0
        else:
            data["additional_data"]["per_workload_speedups"].pop()
        path.write_text(json.dumps(data))
    result = subprocess.run([sys.executable, str(SCRIPT), str(out)], capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "fail"
    assert (out / "ffmpeg-good-original/stdout.log").read_bytes() == (RECEIPTS / "ffmpeg-good-original/stdout.log").read_bytes()
