#!/usr/bin/env python3
"""Worker-side checks for one repair package (run with python3 -I).

verify.py lock PKG_DIR OUT_DIR
    Recompute sha256 of every materialize output in source-lock.json; write outputs.sha256 and
    lock.json (counts, mismatches, missing). Exit 0 only if all match.
verify.py smoke PKG_DIR DOCKERFILE CONTEXT IMAGE OUT_DIR
    Parse COPY/ADD lines; derive (in-image path, expected sha256) pairs from the local build
    context; hash those paths inside IMAGE (docker run --user 0 --network none); write
    smoke-<dockerfile>.json. Exit 0 only if every pair matches.
Never copies package files into OUT_DIR, only hashes and paths.
"""
import hashlib, json, os, shlex, subprocess, sys, tarfile


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def lock(pkg, out):
    m = json.load(open(os.path.join(pkg, 'source-lock.json')))['materialize']
    rows, bad, missing = [], [], []
    for k, want in sorted(m['outputs'].items()):
        p = os.path.join(pkg, k)
        if not os.path.isfile(p):
            missing.append(k); continue
        got = sha(p)
        rows.append(f'{got}  {k}')
        if got != want:
            bad.append({'path': k, 'got': got, 'want': want})
    open(os.path.join(out, 'outputs.sha256'), 'w').write('\n'.join(rows) + ('\n' if rows else ''))
    extra = []
    for top in ('files', 'orig'):
        d = os.path.join(pkg, top)
        for r, _, fs in os.walk(d):
            for f in fs:
                rel = os.path.relpath(os.path.join(r, f), pkg)
                if rel not in m['outputs'] and rel != (m.get('lean_build') or {}).get('artifact'):
                    extra.append(rel)
    res = {'outputs': len(m['outputs']), 'matched': len(rows) - len(bad), 'mismatched': bad,
           'missing': missing, 'unlocked_extra_files': sorted(extra)}
    json.dump(res, open(os.path.join(out, 'lock.json'), 'w'), indent=1)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()}))
    return 0 if not bad and not missing else 1


def instructions(dockerfile):
    lines, cur = [], ''
    for ln in open(dockerfile):
        s = ln.rstrip('\n')
        if not cur and s.lstrip().startswith('#'):
            continue
        if s.endswith('\\'):
            cur += s[:-1] + ' '; continue
        cur += s
        if cur.strip():
            lines.append(cur.strip())
        cur = ''
    return lines


def smoke(pkg, dockerfile, ctx, image, out):
    lockout = json.load(open(os.path.join(pkg, 'source-lock.json')))['materialize']['outputs']
    ctxdir = os.path.normpath(os.path.join(pkg, ctx))
    pairs, notes = [], []
    for ins in instructions(os.path.join(pkg, dockerfile)):
        w = shlex.split(ins)
        op = w[0].upper()
        if op not in ('COPY', 'ADD'):
            continue
        args = [a for a in w[1:] if not a.startswith('--')]
        srcs, dst = args[:-1], args[-1]
        for s in srcs:
            lp = os.path.join(ctxdir, s)
            if op == 'ADD' and s.endswith('.tar') and os.path.isfile(lp):
                with tarfile.open(lp) as t:
                    for mem in t.getmembers():
                        if mem.isfile():
                            h = hashlib.sha256(t.extractfile(mem).read()).hexdigest()
                            pairs.append(('/' + mem.name.lstrip('/'), h, f'{s}!{mem.name}'))
                notes.append(f'ADD {s}: tar members checked in image')
                continue
            if os.path.isdir(lp):
                for r, _, fs in os.walk(lp):
                    for f in sorted(fs):
                        fp = os.path.join(r, f)
                        rel = os.path.relpath(fp, lp)
                        pairs.append((dst.rstrip('/') + '/' + rel, sha(fp),
                                      os.path.relpath(fp, pkg)))
            elif os.path.isfile(lp):
                d = dst.rstrip('/') + '/' + os.path.basename(s) if (dst.endswith('/') or len(srcs) > 1) else dst
                pairs.append((d, sha(lp), os.path.relpath(lp, pkg)))
            else:
                notes.append(f'source {s} missing in context')
                pairs.append((dst, 'MISSING-SOURCE', s))
    pre = ''
    if os.path.basename(pkg.rstrip('/')).startswith('rust_multicrate') and dockerfile == 'Dockerfile':
        # The judge Dockerfile folds files/ into cas_rust_benchmark.tar.gz and removes /tmp/ebv-v2.
        pairs = []
        for k in sorted(lockout):
            if not k.startswith('files/'):
                continue
            rel = k[len('files/'):]
            if rel.startswith('vendor-deps/'):
                ip = 'workspace/agent-start/' + rel
            else:
                ip = rel
            pairs.append(('cas_rust_benchmark/' + ip, sha(os.path.join(pkg, k)), k))
        pre = ('test ! -e /tmp/ebv-v2 && t=$(mktemp -d) && tar -xzf '
               '/home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz -C "$t" && cd "$t" && ')
        notes.append('rust judge: files checked inside the rewritten cas_rust_benchmark.tar.gz; /tmp/ebv-v2 absent')
    res = {'dockerfile': dockerfile, 'image': image, 'checked': len(pairs), 'ok': 0,
           'bad': [], 'notes': notes, 'in_lock': 0}
    if pairs:
        paths = ' '.join(shlex.quote(p) for p, _, _ in pairs)
        cmd = pre + f'sha256sum {paths}'
        r = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--user', '0',
                            '--entrypoint', 'sh', image, '-c', cmd],
                           capture_output=True, text=True)
        got = {}
        for ln in r.stdout.splitlines():
            h, _, p = ln.partition('  ')
            got[p] = h
        if r.returncode and not got:
            res['docker_run_error'] = r.stderr[-2000:]
        for p, want, src in pairs:
            g = got.get(p)
            inl = lockout.get(src) == want
            res['in_lock'] += inl
            if g == want:
                res['ok'] += 1
            else:
                res['bad'].append({'image_path': p, 'got': g, 'want': want, 'source': src})
        res['pairs'] = [{'image_path': p, 'sha256': w, 'source': s, 'source_in_lock': lockout.get(s) == w}
                        for p, w, s in pairs]
    else:
        notes.append('no COPY/ADD: nothing replaced in this image')
    json.dump(res, open(os.path.join(out, f'smoke-{dockerfile}.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('dockerfile', 'checked', 'ok', 'in_lock')} | {'bad': len(res['bad']), 'notes': notes}))
    return 0 if not res['bad'] and 'docker_run_error' not in res else 1


if __name__ == '__main__':
    if sys.argv[1] == 'lock':
        sys.exit(lock(sys.argv[2], sys.argv[3]))
    sys.exit(smoke(*sys.argv[2:7]))
