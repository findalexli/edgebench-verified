#!/bin/bash
# Paired v1/v2 evaluation for smt_solver-v2 (E2B worker, root, /job). Judge arms: --network none,
# the judge image's own evaluate.py with the official flags (timeout 60, --perturb, salt
# hidden-sebench); only the image differs. Witness preparation (pip z3) runs in a separate
# python container BEFORE the judge arms and never inside the judge image.
set -uo pipefail
V1=seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6
V2=ebv/smt_solver:v2
O=/job/out; mkdir -p $O/logs $O/json /job/hb /job/subs /job/wit /job/oracle /job/rt
EV=/home/workspace/smt_judge/scripts/evaluate.py
S=$O/summary.txt
nproc > $O/env.txt; free -m >> $O/env.txt; docker version --format '{{.Server.Version}}' >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $S; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $S; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img sha256sum $EV /home/workspace/smt_judge/SMT-hidden_benchmarks.zip; done > $O/evaluator_sha.txt
echo "stage images ok $(date -u +%T)" >> $S
# 1) The 69 scoped expected-sat hidden files, their expected answers and manifest rows (from v1 image).
docker run --rm --network none -v /job:/job $V1 python3 -c "
import zipfile,json
z=zipfile.ZipFile('/home/workspace/smt_judge/SMT-hidden_benchmarks.zip')
fs=[l.strip() for l in open('/job/files69.txt') if l.strip()]
[z.extract(f,'/job/hb') for f in fs]
exp=json.loads(z.read('expected_answers.json')); man=json.loads(z.read('selection_manifest.json'))
if isinstance(man,dict): man=next(v for v in man.values() if isinstance(v,list))
sel=[m for m in man if m.get('selected_path') in set(fs)]
json.dump({f:exp[f] for f in fs},open('/job/hb/expected_answers.json','w'),indent=1)
json.dump(sel,open('/job/hb/selection_manifest.json','w'),indent=1)
print('files',len(fs),'expected_sat',sum(exp[f]=='sat' for f in fs),'manifest_rows',len(sel))
" > $O/extract.log 2>&1
cat $O/extract.log >> $S
# 2) Witness sets with z3 (true formula): A checker-model (textual), B true model textual keys,
#    C true model ground keys, Cw = C with one value changed that z3 proves is NOT a model.
docker pull python:3.11-slim > /dev/null 2>&1
t0=$(date +%s)
timeout 1700 docker run --rm --memory 6g -v /job:/job -e DUMP_DIR=/job/wit python:3.11-slim bash -c '
pip install -q z3-solver==4.13.0.0 > /job/out/pip.log 2>&1 || exit 9
python3 -c "import z3;print(z3.get_version_string())" > /job/out/z3_version.txt
cat /job/files69.txt | xargs -P 7 -I{} sh -c "f={}; n=\$(echo \$f | tr / _); timeout 700 python3 /job/tools/witness_roundtrip.py /job/hb/\$f > /job/rt/\$n.jsonl 2>/job/rt/\$n.err"
cat /job/rt/*.jsonl > /job/out/roundtrip_v1checker.jsonl
cat /job/files69.txt | xargs -P 7 -I{} sh -c "f={}; n=\$(echo \$f | tr / _); echo \$f > /job/oracle/\$n.list; timeout 700 python3 /job/tools/v2_paired/make_witness_sets.py /job/hb /job/wit /job/oracle/\$n.list /job/subs /job/oracle/\$n.jsonl > /dev/null 2>/job/oracle/\$n.err"
cat /job/oracle/*.jsonl > /job/out/oracle.jsonl
' > $O/witness_prep.log 2>&1
echo "stage witnesses rc=$? wall=$(( $(date +%s)-t0 ))s roundtrip_rows=$(wc -l < $O/roundtrip_v1checker.jsonl 2>/dev/null) oracle_rows=$(wc -l < $O/oracle.jsonl 2>/dev/null)" >> $S
for arm in ground textual textual_true ground_wrong; do
  mkdir -p /job/subs/$arm/src/w; cp /job/stub/solve /job/stub/build.sh /job/subs/$arm/
  echo "arm $arm witnesses=$(ls /job/subs/$arm/src/w | wc -l)" >> $S
done
cp -r /job/wit $O/witnesses 2>/dev/null; cp -r /job/subs $O/subs_witness_sets 2>/dev/null
# 3) Judge arms on the 69 files.
EVAL69='cp -r /hb /tmp/hb && cp -r /sub /tmp/sub && cd /tmp/sub && ./build.sh && python3 '$EV' --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 4 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /out/res.json > /out/eval.out 2>&1; echo eval_rc=$?'
run69() { # arm ver img
  local d=$O/json/$1-$2; mkdir -p $d; local t0=$(date +%s)
  timeout 900 docker run --rm --network none --memory 4g --cpus 4 -v /job/hb:/hb:ro -v /job/subs/$1:/sub:ro -v $d:/out $3 bash -c "$EVAL69" > $O/logs/$1-$2.log 2>&1
  echo "c69 $1 $2 exit=$? wall=$(( $(date +%s)-t0 ))s $(tail -1 $O/logs/$1-$2.log)" >> $S
}
for arm in ground textual textual_true ground_wrong; do run69 $arm v1 $V1; run69 $arm v2 $V2; done
# 4) Mini cases (reviewer's fixed-witness stub).
EVALM='cp -r /mini/bench /tmp/hb && cp -r /mini/sub /tmp/sub && cd /tmp/sub && ./build.sh && python3 '$EV' --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 2 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /out/res.json > /out/eval.out 2>&1; echo eval_rc=$?'
for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2; d=$O/json/mini-$v; mkdir -p $d
  timeout 300 docker run --rm --network none --memory 2g --cpus 2 -v /job/mini:/mini:ro -v $d:/out $img bash -c "$EVALM" > $O/logs/mini-$v.log 2>&1
  echo "mini $v exit=$? $(tail -1 $O/logs/mini-$v.log)" >> $S; done
# 5) Full original eval_cmd (all hidden files, parallel 16) for the ground arm, both images.
python3 -c "import json;print(json.load(open('/job/task.json'))['judge']['eval_cmd'])" > /job/eval_cmd.sh
for v in v1 v2; do img=$V1; [ $v = v2 ] && img=$V2; t0=$(date +%s)
  timeout 1200 docker run --rm --network none --memory 4g --cpus 8 -v /job/subs/ground:/sub:ro -v /job/eval_cmd.sh:/eval_cmd.sh:ro $img bash -c 'mkdir -p /home/workspace/smt_solver && cp -r /sub/. /home/workspace/smt_solver/ && bash /eval_cmd.sh' > $O/logs/fulleval-ground-$v.log 2>&1
  echo "fulleval ground $v exit=$? wall=$(( $(date +%s)-t0 ))s $(grep -A1 'Start Structured Result' $O/logs/fulleval-ground-$v.log | tail -1 | cut -c1-200)" >> $S; done
python3 /job/summarize.py > $O/summary_parsed.txt 2>&1
docker image rm $V2 >/dev/null 2>&1; echo done >> $S
