#!/usr/bin/env python3
"""Pre-commit publication check: scan every file Git would commit and fail on anything unpublishable.

Checks (on `git ls-files --cached --others --exclude-standard`, i.e. tracked + untracked-not-ignored):
  1. no verbatim copy of a task-image file (sha256 against .internal/image-file-hashes.txt, if present)
  2. no scorer-tampering counterexample markers (internal-only material)
  3. no credential patterns, and not the local E2B key (from $E2B_API_KEY, or the .env file named by
     $EBV_E2B_ENV or by the one-line file .internal/e2b-env-path)
  4. no file larger than 40 MB
  5. the word "tamper" only in allowlisted scope statements (scorer-isolation notes are internal-only)
  6. no local filesystem paths (/home/, /mnt/c/, /tmp/claude) in *.md files outside evidence/runs/
Usage: python3 tools/check_publish.py   (exit 1 on any finding)
"""
import hashlib
import os
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
# Neutral scope statements that may mention tampering; any other line with the word is flagged.
TAMPER_WORD = re.compile(rb'(?i)tamper')
TAMPER_OK = re.compile(rb'(?i)('
                       rb'scored wrongly or non-repeatably\. Scorer tampering$'   # AGENTS.md scope rule
                       rb'|no tamper material'
                       rb'|tamper material or credentials'
                       rb'|protected from tampering by a deliberately malicious submission is outside'
                       rb'|no tamper(ing)? (analysis|or exploit submissions)'
                       rb'|tampering is out of scope'
                       rb'|tamper with the game, runtime, scoring'   # EdgeBench's own task prompt
                       rb')')
TAMPER_SKIP = ('tasks/', 'sforge/', 'evidence/runs/')   # original task text, harness and raw run records
# /home/workspace and /home/nethack_agent are paths inside the task images, not local paths.
LOCAL_PATH = re.compile(rb'/home/(?!workspace\b|nethack_agent\b)|/mnt/c/|/tmp/claude')


def e2b_env_file():
    p = os.environ.get('EBV_E2B_ENV')
    cfg = ROOT / '.internal' / 'e2b-env-path'
    if not p and cfg.exists():
        p = cfg.read_text().strip()
    return Path(p).expanduser() if p else None
# Lake's project template ships the same boilerplate as the task images' Lean projects.
TEMPLATE_OK = ('evidence/formal/lean/ebv/.github/', 'evidence/formal/lean/ebv/Ebv/Basic.lean')


def main():
    files = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.split('\n')
    files = [f for f in files if f and (ROOT / f).is_file()]
    hashes_path = ROOT / '.internal' / 'image-file-hashes.txt'
    image = set(hashes_path.read_text().split()) - {EMPTY} if hashes_path.exists() else set()
    keys = {os.environ['E2B_API_KEY'].encode()} if os.environ.get('E2B_API_KEY') else set()
    env = e2b_env_file()
    if env and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('E2B_API_KEY='):
                keys.add(line.split('=', 1)[1].strip().strip('"\'').encode())
    keys.discard(b'')
    if not keys:
        print('note: local E2B key not checked (set E2B_API_KEY or EBV_E2B_ENV, or write .internal/e2b-env-path)')
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
        if SECRET.search(data) or any(k in data for k in keys):
            bad.append((f, 'credential pattern'))
        if f not in SELF and not f.startswith(TAMPER_SKIP):
            for ln in data.splitlines():
                if TAMPER_WORD.search(ln) and not TAMPER_OK.search(ln):
                    bad.append((f, 'tamper note outside the scope-statement allowlist'))
                    break
        if f.endswith('.md') and not f.startswith('evidence/runs/') and LOCAL_PATH.search(data):
            bad.append((f, 'local filesystem path in a published .md file'))
    for f, why in bad:
        print(f'{why}: {f}')
    total = sum((ROOT / f).stat().st_size for f in files)
    print(f'{len(files)} files, {total / 1e6:.1f} MB, {len(bad)} problems')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
