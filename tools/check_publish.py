#!/usr/bin/env python3
"""Pre-commit publication check: scan every file Git would commit and fail on anything unpublishable.

Checks (on `git ls-files --cached --others --exclude-standard`, i.e. tracked + untracked-not-ignored):
  1. no verbatim copy of a task-image file (sha256 against .internal/image-file-hashes.txt, if present)
  2. no scorer-tampering counterexample markers (internal-only material)
  3. no credential patterns, and not the local E2B key
  4. no file larger than 40 MB
Usage: python3 tools/check_publish.py   (exit 1 on any finding)
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX = 40 * 1024 * 1024
EMPTY = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
TAMPER = re.compile(rb'AUDIT COUNTEREXAMPLE|_sebench_gt|procinject|labelread|/proc/\$PPID|fake_pass')
SECRET = re.compile(rb'e2b_[a-f0-9]{30,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH) PRIVATE')
SELF = {'tools/check_publish.py'}
# Lake's project template ships the same boilerplate as the task images' Lean projects.
TEMPLATE_OK = ('evidence/formal/lean/ebv/.github/', 'evidence/formal/lean/ebv/Ebv/Basic.lean')


def main():
    files = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.split('\n')
    files = [f for f in files if f and (ROOT / f).is_file()]
    hashes_path = ROOT / '.internal' / 'image-file-hashes.txt'
    image = set(hashes_path.read_text().split()) - {EMPTY} if hashes_path.exists() else set()
    key = None
    env = Path('/home/alex/agentsmd-rl/.env')
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('E2B_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"\'').encode()
    bad = []
    for f in files:
        data = (ROOT / f).read_bytes()
        if len(data) > MAX:
            bad.append((f, 'larger than 40 MB'))
        if image and hashlib.sha256(data).hexdigest() in image and not f.startswith(TEMPLATE_OK) \
                and not f.startswith(('tasks/', 'sforge/')) and Path(f).name not in ('LICENSE', 'LICENSE.md', 'LICENSE.txt'):
            bad.append((f, 'verbatim task-image file'))
        if f not in SELF and TAMPER.search(data):
            bad.append((f, 'internal-only tamper marker'))
        if SECRET.search(data) or (key and key in data):
            bad.append((f, 'credential pattern'))
    for f, why in bad:
        print(f'{why}: {f}')
    total = sum((ROOT / f).stat().st_size for f in files)
    print(f'{len(files)} files, {total / 1e6:.1f} MB, {len(bad)} problems')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
