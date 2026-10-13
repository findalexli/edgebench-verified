#!/usr/bin/env python3
"""Check that sforge/ and tasks/ are EdgeBench's original files, byte for byte.

sforge/UPSTREAM.lock records the sha256 of every file from GitHub ByteDance-Seed/EdgeBench (sforge/)
and from the Hugging Face dataset ByteDance-Seed/EdgeBench (tasks/), at the commits it names.
Fails if a locked file is missing or changed, or if an unlocked file sits under sforge/ or tasks/
(Python caches excepted).
Usage: python3 tools/check_upstream.py   (exit 1 on any finding)
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'sforge' / 'UPSTREAM.lock'


def main():
    lock = json.loads(LOCK.read_text())
    problems, n = [], 0
    for part in ('sforge', 'tasks'):
        files = lock[part]['files']
        for rel, want in files.items():
            p = ROOT / rel
            n += 1
            if not p.is_file():
                problems.append(f'missing: {rel}')
            elif hashlib.sha256(p.read_bytes()).hexdigest() != want:
                problems.append(f'changed: {rel}')
        for p in sorted((ROOT / part).rglob('*')):
            rel = p.relative_to(ROOT).as_posix()
            if p.is_file() and '__pycache__' not in p.parts and p != LOCK and rel not in files:
                problems.append(f'not in the lock: {rel}')
    for line in problems:
        print(line)
    print(f'{n} locked files; sforge {lock["sforge"]["commit"][:7]}, tasks {lock["tasks"]["revision"][:7]}: '
          + ('OK' if not problems else f'{len(problems)} problem(s)'))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
