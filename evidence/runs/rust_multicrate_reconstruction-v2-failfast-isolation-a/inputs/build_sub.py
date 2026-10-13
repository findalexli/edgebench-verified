#!/usr/bin/env python3
"""Build one submission (agent-start without vendor-deps/target) for the paired v1/v2 run.
  starter   : the shipped starter, unchanged.
  reference : starter + the 507 todo!() files replaced by upstream CAS v1.0.0 (reference-overlay.tgz,
              github.com/codingagentsystem/cas @ a0a4b5ad), EXCEPT that in the 182 of those files
              that carry hidden-test snippets the hidden test fns are removed again, so the file keeps
              the starter's tests and the grader must inject the hidden tests (as for any solver who
              leaves tests alone). Checked: after removal, each file's test region equals the
              starter's (whitespace-normalised; whole-file test modules: same fn sequence).
  partial   : reference, but crates/cas-search/src/metrics.rs left as the starter (todo!() bodies).
  bad       : reference with PtyConfig::default() returning rows 25 instead of 24 (cas-pty).
Usage: build_sub.py KIND STARTER_DIR OVERLAY_DIR HIDDEN_SOURCES_DIR OUT_DIR"""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import strip
kind, st, up, hs, out = sys.argv[1], *map(Path, sys.argv[2:6])
shutil.copytree(st, out, ignore=shutil.ignore_patterns('vendor-deps', 'target', '.git'), symlinks=True)
def anchor(c):
    a = c.rfind('#[cfg(test)]'); return a if a != -1 else c.rfind('#[cfg(all(')
norm = lambda t: re.sub(r'\s+', '', t)
if kind != 'starter':
    good = 0; files = sorted(str(p.relative_to(up)) for p in up.rglob('*.rs'))
    assert len(files) == 507, len(files)
    for r in files:
        u = (up / r).read_text(); s = (st / r).read_text()
        if (hs / r).exists():
            for n in re.findall(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)", (hs / r).read_text()):
                if re.search(r'\bfn\s+' + n + r'\b', s):
                    continue
                u, _ = strip.remove_fn(u, n)
            au, as_ = anchor(u), anchor(s)
            if au != -1 and as_ != -1 and 'todo!()' not in s[as_:]:
                ok = norm(u[au:]) == norm(s[as_:])
            else:
                ok = re.findall(r'\bfn\s+(\w+)', u) == re.findall(r'\bfn\s+(\w+)', s)
            assert ok, r
            good += 1
        (out / r).write_text(u)
    assert good == 182, good
    print('reference: 507 files, 182 with hidden tests removed and checked')
if kind == 'partial':
    r = 'crates/cas-search/src/metrics.rs'; shutil.copy2(st / r, out / r); print('partial: restored starter', r)
if kind == 'bad':
    p = out / 'crates/cas-pty/src/pty.rs'; c = p.read_text()
    i = c.index('impl Default for PtyConfig'); j = c.index('rows: 24,', i)
    p.write_text(c[:j] + 'rows: 25,' + c[j + 9:]); print('bad: PtyConfig::default rows 24 -> 25')
n = sum(1 for p in out.rglob('*.rs') if 'todo!()' in p.read_text(errors='replace'))
print('files_with_todo', n)
