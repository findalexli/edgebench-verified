#!/usr/bin/env python3
"""Diagnostic only (not scoring): rebuild the combined workspace exactly as score.py does
(copy_workspace_tree + inject_hidden_tests) and print the first compiler errors of the given crates."""
import os, subprocess, sys, tempfile
RUN = '/tmp/cas_eval/run'; sys.path.insert(0, RUN + '/tools'); import score as S
ws = os.path.join(tempfile.mkdtemp(prefix='diag-'), 'ws')
S.copy_workspace_tree(RUN + '/agent-start', ws, share_vendor=True)
print('injected', S.inject_hidden_tests(ws, RUN + '/hidden-tests/hidden-sources'), flush=True)
for pkg in sys.argv[1:]:
    r = subprocess.run(['cargo', 'test', '--frozen', '-p', pkg, '--no-run'], capture_output=True, text=True, cwd=ws)
    lines = r.stderr.splitlines(); errs = [i for i, l in enumerate(lines) if l.startswith('error')]
    print(f'== {pkg} rc={r.returncode} errors={len(errs)}')
    for i in errs[:12]:
        print('\n'.join(lines[i:i + 8]))
