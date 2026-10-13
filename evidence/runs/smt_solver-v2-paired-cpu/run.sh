#!/bin/bash
# smt_solver: paired original/fixed evaluation of the CPU-quota cap on --parallel (E2B worker, root, /job).
# v1 = digest-pinned original judge image; v2 = built from /job/pkg (current fixed version: witness keys + cap).
# Each arm runs the image's own evaluate.py with the grader's exact flags (--timeout 60 --parallel 16 --perturb
# --perturb-salt hidden-sebench, preflight on), --network none --memory 4g --cpus <N>, one container at a time, on
# the same 32-file subset of the hidden set as smt_solver-cpu4v8-a/-b (QF_LIA, hard, all expected unsat: the first 32
# by path). The full eval_cmd (774 files) is too long per arm at 4 workers; its worst case is checked by arithmetic.
# The subset is extracted from the image's own hidden zip at run time and deleted before collection.
# The stand-in solve burns W CPU-seconds (cpuW/spinW) or stops at a W-second wall deadline (wallW), then prints unsat.
# /job/arms.txt lines: "<label> <cpus> <v1|v2> <stand-in solve file in /job/sol>".
set -uo pipefail
V1=seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
V2=ebv/smt_solver:v2
EV=/home/workspace/smt_judge/scripts/evaluate.py
O=/job/out; mkdir -p $O/logs $O/json $O/timing /job/hb
{ nproc; free -m; lscpu | grep -E 'Model name|^CPU\(s\)|Thread'; docker version --format '{{.Server.Version}}'; date -u; } > $O/env.txt 2>&1
docker pull -q $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker image inspect $V1 --format '{{.Id}} {{.RepoDigests}}' >> $O/pull.log
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img bash -c "sha256sum $EV /home/workspace/smt_judge/SMT-hidden_benchmarks.zip; grep -n 'max_workers=parallel\|args.parallel = min' $EV"; done > $O/evaluator_sha.txt 2>&1
for c in 1 2 3 4 8; do echo "cpus=$c $(docker run --rm --network none --cpus $c $V2 python3 -c "import sys; sys.path.insert(0, '/home/workspace/smt_judge/scripts'); import evaluate as e; print(open('/sys/fs/cgroup/cpu.max').read().strip(), 'parallel 16 ->', min(16, e.cpu_quota_workers()))" 2>&1)"; done > $O/v2_workers.txt
sha256sum /job/sol/* > $O/solutions_sha.txt
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
while read -r label cpus ver sol; do
  [ -z "$label" ] && continue
  IMG=$V1; [ $ver = v2 ] && IMG=$V2
  T=$O/timing/$label; D=$O/json/$label; mkdir -p $T $D; chmod 777 $T $D; t0=$(date +%s.%N)
  timeout 1200 docker run --rm --network none --memory 4g --cpus $cpus -v /job/hb:/hb:ro -v /job/sol/$sol:/sol:ro -v $T:/ebvtiming -v $D:/out $IMG bash -c "$EVAL" > $O/logs/$label.log 2>&1
  rc=$?
  s=$(python3 -c "
import json,collections
r=json.load(open('$D/res.json'))
res=[x for v in r.get('results',{}).values() for x in v] if isinstance(r.get('results'),dict) else r.get('results',[])
c=collections.Counter(x.get('verdict') for x in res); t=sorted(x['time'] for x in res)
par=r.get('config',{}).get('parallel', r.get('parallel'))
print('parallel=%s verdicts=%s final_score=%.6f times[min/med/max]=%.1f/%.1f/%.1f' % (par, dict(c), r['final_score'], t[0], t[len(t)//2], t[-1]))
" 2>&1 | tail -1)
  echo "$label cpus=$cpus ver=$ver sol=$sol exit=$rc wall=$(python3 -c "print(round($(date +%s.%N)-$t0,1))")s $(tail -1 $O/logs/$label.log) $s" | tee -a $O/summary.txt
done < /job/arms.txt
python3 /job/timing.py $O/timing > $O/timing_summary.txt 2>&1
rm -rf /job/hb; docker image rm $V2 >/dev/null 2>&1; echo done >> $O/summary.txt
