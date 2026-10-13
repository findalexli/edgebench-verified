#!/usr/bin/env python3
"""Re-run every published formal result and compare with the saved outputs.

TLA+: each model/config under evidence/formal/tla/ is re-checked with TLC; the outcome class
(exact violated invariant vs no error) must match the saved tlc output.
Lean: each file under evidence/formal/lean/ebv/Ebv/ must have a saved .out and is recompiled (Lean 4 +
Mathlib, project at evidence/formal/lean/ebv; run `lake exe cache get` there first); it must compile
without errors or `sorry` and print the same `#print axioms` lines as the saved output.
Lean compiles run one at a time in a --memory 4g container under /tmp/ebv-heavy.lock.
Usage: python3 tools/check_formal.py [--tla-only|--lean-only]
"""
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / 'evidence' / 'formal'
JAR_URL = 'https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar'
JAR_SHA = '7beec0f04818732a62fa193731711a99aa4f11279499b2360a7d156c519ea78d'
LEAN_IMAGE = 'python:3.11.14-slim'
# Lake template and dependency smoke test, not published axiom-audited results.
LEAN_SETUP_FILES = {'Basic.lean', 'Smoke.lean'}


def jar():
    for p in (ROOT / 'tools' / 'tla2tools.jar', ROOT / '.internal' / 'tools' / 'tla2tools.jar'):
        if p.exists():
            return p
    p = Path(tempfile.gettempdir()) / 'tla2tools.jar'
    if not p.exists():
        urllib.request.urlretrieve(JAR_URL, p)
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != JAR_SHA:
        print(f'note: tla2tools.jar sha256 {got[:12]}… differs from the audited build {JAR_SHA[:12]}…')
    return p


def tlc_class(text):
    # A different broken invariant is not a reproduction of the published finding.
    violated = re.findall(r'Error: Invariant ([\w.]+) is violated', text)
    errors = [line for line in text.splitlines() if line.startswith('Error:')
              and line != 'Error: The behavior up to this point is:']
    if violated and len(errors) == len(violated):
        return 'violated:' + ','.join(sorted(set(violated)))
    if not errors and 'No error has been found' in text:
        return 'no-error'
    return 'unknown'


def check_tla():
    j, bad, n = jar(), 0, 0
    for cfg in sorted(FORMAL.glob('tla/*/*.cfg')):
        d, name = cfg.parent, cfg.stem
        saved = next((p for p in (d / f'tlc-{name}.out', d / f'tlc_{name}.out') if p.exists()), None)
        if saved is None:
            print(f'BAD TLA+ {d.name}/{name}: missing saved output')
            n += 1; bad += 1
            continue
        specs = [p for p in d.glob('*.tla') if '_TTrace_' not in p.name]
        named = [p for p in specs if name.startswith(p.stem)]
        spec = specs[0] if len(specs) == 1 else (max(named, key=lambda p: len(p.stem)) if named else None)
        if spec is None:
            print(f'BAD TLA+ {d.name}/{name}: cannot tell which model it checks (name the .cfg <Model>_<check>.cfg)')
            n += 1; bad += 1
            continue
        with tempfile.TemporaryDirectory() as meta:
            r = subprocess.run(['java', '-XX:+UseParallelGC', '-cp', str(j), 'tlc2.TLC', '-workers', '2',
                                '-deadlock', '-config', cfg.name, '-metadir', meta, spec.name],
                               cwd=d, capture_output=True, text=True, timeout=900)
        got = tlc_class(r.stdout + r.stderr)
        want = tlc_class(saved.read_text()) if saved else 'unknown'
        ok = got == want and got != 'unknown' and (got.startswith('violated:') or r.returncode == 0)
        n += 1; bad += not ok
        print(f"{'OK ' if ok else 'BAD'} TLA+ {d.name}/{name}: {got} (published: {want})")
    return n, bad


def axioms(text):
    return sorted(set(re.findall(r"^'[^']+' (?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)", text, flags=re.M)))


# These two negative controls intentionally apply the installed false statements.
SORRY_CONTROLS = {'EbvRefute.installed_anti_symm_inconsistent',
                  'EbvRefute.installed_div_inconsistent'}


def axiom_names(lines):
    return {line.split("'")[1] for line in lines}


def lean_output_ok(source, saved, output, returncode):
    # Audit the declarations explicitly requested by the source. This does not claim
    # to enumerate every helper declaration; Lean's axiom reports are transitive.
    requested = set(re.findall(r'^#print axioms ([\w.]+)\s*$', source, flags=re.M))
    got, want = axioms(output), axioms(saved)
    # Lean prints fully qualified names even for #print inside a namespace.
    names = axiom_names(want)
    matches = [{n for n in names if n == q or n.endswith('.' + q)} for q in requested]
    covered = set().union(*matches) if matches else set()
    leaks = []
    for line in got:
        allowed = {'propext', 'Classical.choice', 'Quot.sound'}
        if line.split("'")[1] in SORRY_CONTROLS:
            allowed.add('sorryAx')
        reported = re.search(r'depends on axioms: \[([^\]]*)\]', line)
        if reported and set(filter(None, (a.strip() for a in reported[1].split(',')))) - allowed:
            leaks.append(line)
    return (returncode == 0 and not re.search(r'error:', output) and not leaks
            and bool(requested) and all(len(m) == 1 for m in matches)
            and len(covered) == len(requested) and covered == names
            and axiom_names(got) == names and got == want)


def check_lean():
    proj = FORMAL / 'lean' / 'ebv'
    elan = Path.home() / '.elan'
    env = dict(os.environ, PATH=f"{elan / 'bin'}:{os.environ['PATH']}")
    lp = subprocess.run(['lake', 'env', 'printenv', 'LEAN_PATH'], cwd=proj, env=env,
                        capture_output=True, text=True, check=True).stdout.strip()
    lean = subprocess.run(['lake', 'env', 'which', 'lean'], cwd=proj, env=env,
                          capture_output=True, text=True, check=True).stdout.strip()
    n = bad = 0
    with tempfile.TemporaryDirectory() as out:
        Path(out, 'olean', 'Ebv').mkdir(parents=True)
        lp = f'{out}/olean:{lp}'
        for src in sorted((proj / 'Ebv').glob('*.lean')):
            if src.name in LEAN_SETUP_FILES:
                continue
            saved = src.with_suffix('.out')
            if not saved.exists():
                print(f'BAD Lean {src.name}: missing saved output')
                n += 1; bad += 1
                continue
            extra = ['-o', f'{out}/olean/Ebv/{src.stem}.olean']
            cmd = ['docker', 'run', '--rm', '--network', 'none', '--memory', '4g', '--memory-swap', '4g',
                   '--cpus', '2', '-v', f'{elan}:{elan}:ro', '-v', f'{proj}:{proj}:ro', '-v', f'{out}:{out}',
                   '-w', str(proj), '-e', f'LEAN_PATH={lp}', '--user', f'{os.getuid()}:{os.getgid()}',
                   LEAN_IMAGE, lean, *extra, f'Ebv/{src.name}']
            lock = open('/tmp/ebv-heavy.lock', 'w')
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN); lock.close()
            text = r.stdout + r.stderr
            got, want = axioms(text), axioms(saved.read_text())
            ok = lean_output_ok(src.read_text(), saved.read_text(), text, r.returncode)
            n += 1; bad += not ok
            print(f"{'OK ' if ok else 'BAD'} Lean {src.name}: {len(got)} theorems, axioms match published: {got == want}")
    return n, bad


def main():
    n = bad = 0
    if '--lean-only' not in sys.argv:
        a, b = check_tla(); n += a; bad += b
    if '--tla-only' not in sys.argv:
        a, b = check_lean(); n += a; bad += b
    if n == 0:
        print('BAD: no formal checks discovered')
        bad += 1
    print(f'{n} formal checks, {bad} mismatches')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
