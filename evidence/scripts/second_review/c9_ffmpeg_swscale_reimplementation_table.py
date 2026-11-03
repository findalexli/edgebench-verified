#!/usr/bin/env python3
"""FFmpeg unchecked timed outputs: judge_local raw and 0-100 scores per arm and judge, the rgba->rgb24 row from the log, and the real-report best."""
import glob, json, os, re, statistics as st, tarfile
J = ['community9-ffmpeg_swscale_reimplementation-a2', 'community9-ffmpeg_swscale_reimplementation-b']
rows = {}
for j in J:
    for f in glob.glob(f'evidence/runs/{j}/result/out/g/*.json'):
        m = re.match(r'(.+)-p(\d)-(old|new)\.json', os.path.basename(f))
        d = json.load(open(f)); t = str(d.get('log_tail'))
        rg = re.findall(r'rgba\\u2192rgb24 4K[^\n]{0,80}|rgba→rgb24 4K[^\n]{0,80}', t)
        cor = re.findall(r'Correctness[^\n]{0,30}', t)
        rows.setdefault((m.group(1), m.group(3)), []).append((m.group(2), d['raw_score'], d['score_0_100'], d['valid'], d.get('runtime_s'), rg[-1:], cor[-1:]))
print('arm judge n mean0_100 min max raw | per-run')
for k in sorted(rows):
    v = sorted(rows[k]); s = [x[2] or 0 for x in v]
    print(k[0], k[1], len(v), round(st.mean(s), 2), round(min(s), 2), round(max(s), 2), [x[1] for x in v])
    print('    ', v[0][4], v[0][5], v[0][6])
print('--- real reports')
rs = []
for f in glob.glob('evidence/runs/claude-opus-ffmpeg_swscale_reimplementation*/result/out/sforge-logs/runs/*/ffmpeg_swscale_reimplementation/submissions/*/report.json'):
    d = json.load(open(f)); rs.append((d.get('score_0_100') or 0, d.get('score'), f.split('runs/')[1].split('/')[0][-3:] + '/' + f.split('/')[-2]))
print('reports', len(rs), 'best', max(rs))
# How many real submissions had a timed workload whose last output failed the check (earlier regrade of all real archives on the same check).
n = 0; errs = {}; hit = []
for tgz in sorted(glob.glob('evidence/runs/claude-opus-ffmpeg_swscale_reimplementation*/result/out.tar.gz')):
    tf = tarfile.open(tgz)
    for m in tf:
        g = re.search(r'raw/ffmpeg_swscale_reimplementation\.((?:auto|agent)-\d+)\.rep1\.v2\.raw\.txt$', m.name)
        if not g: continue
        t = tf.extractfile(m).read().decode('utf8', 'replace'); n += 1
        e = re.findall(r'"label": "([^"]+)",\s*"error": "([^"]+)"', t)
        for l, x in e: errs[(l, re.sub(r'at call \d+', '', x))] = errs.get((l, re.sub(r'at call \d+', '', x)), 0) + 1
        if e:
            g1 = re.search(r'Geometric mean speedup: ([\d.]+)', t)
            hit.append((tgz.split('/')[2][-3:], g.group(1), g1.group(1) if g1 else None))
print('regraded real archives', n, 'timed-output failures', errs)
print('archives with a failure (run, id, speedup on the v2 check):', hit)
v1 = {}
for f in glob.glob('evidence/runs/claude-opus-ffmpeg_swscale_reimplementation*/result/out/sforge-logs/runs/*/ffmpeg_swscale_reimplementation/submissions/*/report.json'):
    d = json.load(open(f)); v1[(f.split('runs/')[1].split('/')[0][-3:], f.split('/')[-2])] = (d.get('score'), d.get('score_0_100'))
print('their reported raw and 0-100 scores:', [v1.get((a, b)) for a, b, _ in hit])
