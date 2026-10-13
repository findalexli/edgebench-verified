#!/usr/bin/env python3
"""Create a separate runnable sforge tree; never modify the upstream mirror."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]


def materialize(destination):
    lock = json.loads((PACKAGE / 'source-lock.json').read_text())
    source = ROOT / lock['source']
    if hashlib.sha256(source.read_bytes()).hexdigest() != lock['original_sha256']:
        raise RuntimeError('Upstream source differs from the pinned repair input')
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT / 'sforge', destination / 'sforge', ignore=shutil.ignore_patterns('__pycache__'))
    subprocess.run(['patch', '--batch', '-p1', '-i', str(PACKAGE / 'repair.patch')], cwd=destination, check=True)
    patched = destination / lock['source']
    if hashlib.sha256(patched.read_bytes()).hexdigest() != lock['patched_sha256']:
        raise RuntimeError('Patched source hash differs from lock')
    return patched


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: materialize.py NEW_OUTPUT_DIRECTORY')
    print(materialize(sys.argv[1]))
