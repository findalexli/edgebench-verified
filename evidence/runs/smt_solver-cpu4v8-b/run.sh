#!/bin/bash
# smt_solver: per-case timeouts at 4 vs 8 CPUs under the official 16 evaluator workers and 60 s timeout.
# Runs the judge image's own evaluate.py with the grader's flags (--timeout 60 --parallel 16 --perturb
# --perturb-salt hidden-sebench, preflight on) on a 32-file subset of the hidden set (QF_LIA, hard, all
# expected unsat; 2 waves of 16), --network none --memory 4g. The full eval_cmd (774 files, ~48 waves at 60 s)
# is too long per arm; the subset is extracted from the image's own hidden zip at run time and never collected.
# /job/arms.txt lines: "<label> <cpus> <stand-in solve file in /job/sol>".
set -uo pipefail
V1=seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
W1=seededge/edgebench.work.smt_solver@sha256:662ee138e84177f9a6fdf3393c028a655491a61e10b1e64e77dd254987af18fe
EV=/home/workspace/smt_judge/scripts/evaluate.py
O=/job/out; mkdir -p $O/logs $O/json $O/timing $O/docs /job/hb
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' >> $O/pull.log
docker run --rm --network none $V1 bash -c "sha256sum $EV /home/workspace/smt_judge/SMT-hidden_benchmarks.zip; grep -n 'max_workers=parallel\|communicate(timeout=timeout)\|UNSAT_STATUS_ONLY_CREDIT =\|WEIGHTS =' $EV; ls /home/workspace/smt_judge; grep -rniE 'second|timeout|cpu|core|thread|parallel|worker|wall' --include='*.md' /home/workspace 2>/dev/null | head -40" > $O/docs/judge.txt 2>&1
docker pull -q $W1 >> $O/pull.log 2>&1 && docker run --rm --network none $W1 bash -c 'cd /home/workspace/smt_solver; ls; grep -rniE "second|timeout|cpu|core|thread|parallel|worker|wall" --include="*.md" . | head -40; grep -n "parallel\|timeout" scripts/evaluate.py | grep add_argument' > $O/docs/work.txt 2>&1; docker image rm $W1 >/dev/null 2>&1
docker run --rm --network none -v /job:/job $V1 python3 -c "
import zipfile,json
z=zipfile.ZipFile('/home/workspace/smt_judge/SMT-hidden_benchmarks.zip')
exp=json.loads(z.read('expected_answers.json')); man=json.loads(z.read('selection_manifest.json'))
sel=[m for m in man if m['selected_path'].startswith('QF_LIA/') and m['difficulty']=='hard' and exp[m['selected_path']]=='unsat']
sel=sorted(sel,key=lambda m:m['selected_path'])[:32]
fs=[m['selected_path'] for m in sel]
[z.extract(f,'/job/hb') for f in fs]
json.dump({f:exp[f] for f in fs},open('/job/hb/expected_answers.json','w'),indent=1)
json.dump(sel,open('/job/hb/selection_manifest.json','w'),indent=1)
print('subset files',len(fs),'all_unsat',all(exp[f]=='unsat' for f in fs))
" > $O/extract.log 2>&1
cat $O/extract.log | tee -a $O/summary.txt
EVAL='cp -r /hb /tmp/hb && mkdir -p /tmp/sub/src && cp /sol /tmp/sub/solve && printf "#!/bin/sh\nexit 0\n" > /tmp/sub/build.sh && chmod +x /tmp/sub/solve /tmp/sub/build.sh && cd /tmp/sub && ./build.sh && python3 '$EV' --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 16 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /out/res.json > /out/eval.out 2>&1; echo eval_rc=$?'
while read -r label cpus sol; do
  [ -z "$label" ] && continue
  T=$O/timing/$label; D=$O/json/$label; mkdir -p $T $D; chmod 777 $T $D; t0=$(date +%s.%N)
  timeout 900 docker run --rm --network none --memory 4g --cpus $cpus -v /job/hb:/hb:ro -v /job/sol/$sol:/sol:ro -v $T:/ebvtiming -v $D:/out $V1 bash -c "$EVAL" > $O/logs/$label.log 2>&1
  rc=$?
  s=$(python3 -c "
import json,collections
r=json.load(open('$D/res.json'))
res=[x for v in r.get('results',{}).values() for x in v] if isinstance(r.get('results'),dict) else r.get('results',[])
c=collections.Counter(x.get('verdict') for x in res); t=sorted(x['time'] for x in res)
print('verdicts=%s final_score=%.6f times[min/med/max]=%.1f/%.1f/%.1f' % (dict(c), r['final_score'], t[0], t[len(t)//2], t[-1]))
" 2>&1 | tail -1)
  echo "$label cpus=$cpus sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))")s $(tail -1 $O/logs/$label.log) $s" | tee -a $O/summary.txt
done < /job/arms.txt
rm -rf /job/hb; echo done >> $O/summary.txt
