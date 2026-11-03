#!/usr/bin/env python3
"""Old (8 at once) vs new (min(8, SFORGE_CPUS)) pool: every `sforge eval` of the community9-<task>-* jobs, by submission, condition
and judge. Conditions: hot4 = 4 vCPUs online, one judge; q4 = 8 online, one judge; x2/x3/x5 = 8 online, that many judges at once.
Usage: c9_pool_table.py <task> [--json]"""
import glob, json, os, re, sys
task = sys.argv[1]; out = []; rows = {}
def num(x, nd=2): return None if x is None else round(x, nd)
for job in sorted(glob.glob(f'evidence/runs/community9-{task}-*/')):
    wj = job + 'result/worker.json'
    if not os.path.exists(wj): print(job, 'NOT FINISHED'); continue
    w = json.load(open(wj)); O = job + 'result/out/'
    try: summ = open(O + 'summary.txt').read()
    except OSError: print(job, w.get('status'), 'no summary'); continue
    mem = [int(l.split()[2]) // 1024 for l in open(O + 'sampler.txt', errors='replace') if l.startswith('M ')] if os.path.exists(O + 'sampler.txt') else []
    print(os.path.basename(job[:-1]), 'status', w.get('status'), 'done' if '\ndone' in summ else 'INCOMPLETE', 'skips', re.findall(r'SKIP (\S+)', summ), re.findall(r'oom_lines \d+', summ), 'min_avail_MiB', min(mem) if mem else None)
    H = []; C = {}; I = {}
    if os.path.exists(O + 'sampler.txt'):
        for l in open(O + 'sampler.txt', errors='replace'):
            p = l.split()
            if len(p) < 3: continue
            if p[0] == 'H' and len(p) > 15:
                v = list(map(int, p[7:15])); H.append((int(p[1]), float(p[2]), sum(v), v[3] + v[4], v[7]))
            elif p[0] == 'C':
                d = dict(zip(p[3::2], p[4::2])); C.setdefault(p[2], []).append((int(p[1]), {k: int(x) for k, x in d.items()}))
            elif p[0] == 'I': I[p[2]] = ' '.join(p[3:])
    for m in re.finditer(r'^arm (\S+) side=(\S+) sub=(\S+) rc=(\d+) start=(\d+) end=(\d+) online=(\S+)', summ, re.M):
        lab, side, sub, rc, st, en, on = m.groups(); st, en = int(st), int(en); cond, rd = lab.split('-')[0], re.search(r'-(r\d+)', lab).group(1)
        rp = f'{O}s/{lab}.report.json'
        if not os.path.exists(rp): rows.setdefault((sub, cond, side), []).append({'lab': lab, 'bad': 'no report rc=' + rc}); continue
        r = json.load(open(rp)); tle = []
        tp = f'{O}s/{lab}.judge_output.txt'
        if os.path.exists(tp): tle = re.findall(r'CASE (\S+) TLE', open(tp, errors='replace').read())
        else: tle = [d['name'] for d in r.get('details') or [] if 'TLE' in str(d.get('status')) or 'TLE' in str(d.get('name'))]
        mt = r.get('metrics') or {}
        name = f'sforge.judge.{task}.{lab}'; c = C.get(name, [])
        us = c[-1][1].get('usage_usec') if c else None; thr = c[-1][1].get('nr_throttled') if c else None
        hs = [h for h in H if st <= h[0] <= en]; busy = steal = load = None
        if len(hs) > 1:
            dt = hs[-1][2] - hs[0][2]; busy = 100 * (1 - (hs[-1][3] - hs[0][3]) / dt) if dt else None; steal = 100 * (hs[-1][4] - hs[0][4]) / dt if dt else None; load = sum(h[1] for h in hs) / len(hs)
        rows.setdefault((sub, cond, side), []).append(dict(lab=lab, job=os.path.basename(job[:-1]), rd=rd, ok=mt.get('cases_passed'), tot=mt.get('cases_total'), raw=r.get('score'), s=r.get('score_0_100'), valid=r.get('valid'), to=r.get('timed_out'), sec=r.get('runtime_seconds'), tle=tle, cpu_s=None if us is None else us / 1e6, thr=thr, busy=busy, steal=steal, load=load, online=on, inf=I.get(name), summ=r.get('summary')))
print()
rs = []
for k in sorted(rows):
    v = [x for x in rows[k] if 'bad' not in x]; bad = [x for x in rows[k] if 'bad' in x]
    sc = [x['s'] for x in v if x['s'] is not None]; nul = sum(x['s'] is None for x in v)
    cpu = [x['cpu_s'] for x in v if x['cpu_s'] and x['sec']]
    d = dict(sub=k[0], cond=k[1], side=k[2], n=len(v), ok=[x['ok'] for x in v], tot=(v[0]['tot'] if v else None), scores=[num(x['s']) for x in v], raw=[x['raw'] for x in v], mean=num(sum(sc) / len(sc)) if sc else None, lo=num(min(sc)) if sc else None, hi=num(max(sc)) if sc else None, null=nul,
             tle=[len(x['tle']) for x in v], cpu_per_case=[round(x['cpu_s'] / x['tot'], 1) for x in v if x['cpu_s'] and x['tot']], sec=[round(x['sec']) for x in v], cpu_per_wall=[round(x['cpu_s'] / x['sec'], 2) for x in v if x['cpu_s'] and x['sec']], throttled=[x['thr'] for x in v], host_busy=[num(x['busy'], 0) for x in v], steal=[num(x['steal'], 1) for x in v], load=[num(x['load'], 1) for x in v], online=sorted({x['online'] for x in v}), bad=[x['bad'] for x in bad])
    rs.append(d)
    print(f"{k[0]:7} {k[1]:5} {k[2]:3} n={d['n']} ok={d['ok']} TLE={d['tle']} null={nul} score={d['scores']} mean={d['mean']} sec={d['sec']} cpuS/case={d['cpu_per_case']} cpu/wall={d['cpu_per_wall']} busy%={d['host_busy']} steal%={d['steal']} load={d['load']} online={d['online']}" + (f" BAD={d['bad']}" if bad else ''))
print('\nPer-case timeouts: cases that ever timed out on one pool, count of runs per pool')
for s, c in sorted({(k[0], k[1]) for k in rows}):
    o = [x for x in rows.get((s, c, 'old'), []) if 'bad' not in x]; n = [x for x in rows.get((s, c, 'new'), []) if 'bad' not in x]
    if not (o or n): continue
    co = {}; cn = {}
    for x in o:
        for t in x['tle']: co[t] = co.get(t, 0) + 1
    for x in n:
        for t in x['tle']: cn[t] = cn.get(t, 0) + 1
    if co or cn:
        print(f" {s} {c}: old n={len(o)} new n={len(n)}; cases TLE old only {len([t for t in co if t not in cn])}, new only {len([t for t in cn if t not in co])}, both {len([t for t in co if t in cn])}; old-only {sorted(t for t in co if t not in cn)[:12]}")
print('\nPaired new-old by round (same submission, condition, round, first judge of a batch)')
for s, c in sorted({(k[0], k[1]) for k in rows}):
    o = {(x['job'], x['rd']): x for x in rows.get((s, c, 'old'), []) if 'bad' not in x and not re.search(r'-k[2-9]$', x['lab'])}; n = {(x['job'], x['rd']): x for x in rows.get((s, c, 'new'), []) if 'bad' not in x and not re.search(r'-k[2-9]$', x['lab'])}
    d = [round(n[r]['s'] - o[r]['s'], 2) for r in sorted(o) if r in n and n[r]['s'] is not None and o[r]['s'] is not None]
    if d: print(f" {s} {c}: {d} mean {round(sum(d) / len(d), 2)}")
print('\nBy worker (x3, x5 and repeated conditions): cases OK and score range per job')
for k in sorted(rows):
    J = {}
    for x in rows[k]:
        if 'bad' not in x: J.setdefault(x['job'], []).append(x)
    if len(J) > 1 or k[1] in ('x3', 'x5'):
        for j, v in sorted(J.items()):
            sc = [x['s'] for x in v if x['s'] is not None]
            print(f" {k[0]} {k[1]} {k[2]} {j.split('-')[-1]}: n={len(v)} ok {min(x['ok'] for x in v)}-{max(x['ok'] for x in v)} score {num(min(sc)) if sc else None}-{num(max(sc)) if sc else None}")
print('\nLimit check (first of each condition)')
seen = set()
for k in sorted(rows):
    for x in rows[k]:
        if 'bad' in x: continue
        if (k[1], k[2]) in seen: continue
        seen.add((k[1], k[2])); print(' ', k[1], k[2], x['lab'], x['inf'])
print('\nCalibration (host Python loop, Mloops/s per process, alone and with one process per online CPU)')
for job in sorted(glob.glob(f'evidence/runs/community9-{task}-*/result/out/calib.txt')): print(' ', job.split('/')[2], ' | '.join(l.strip() for l in open(job)))
if '--json' in sys.argv: print(json.dumps(rs))
