# The 69 affected hidden sat files with the judge's own evaluate.py and its flags (timeout 60, parallel 16, perturb, hidden salt).
sub69(){ # label side arm est
  local sd=$2 img; [ $sd = old ] && img=$IMGOLD || img=$IMGNEW
  fits $4 "$1-$sd-sub69" || return 0
  local out=$O/sub/$1-$sd; mkdir -p $out /job/w/$3; [ -f /job/w/$3/build.sh ] || tar xzf /job/subs/$3.tar.gz -C /job/w/$3
  local t0=$(date +%s)
  timeout 900 docker run --rm --network none --cpus 8 --memory 7g -v /job/files69.txt:/files69.txt:ro -v /job/w/$3:/sub:ro -v $out:/out --entrypoint bash $img -c '
python3 - <<PY
import json,os,shutil
H="/home/workspace/smt_judge/hidden_benchmarks"; fs=[l.strip() for l in open("/files69.txt") if l.strip()]
for f in fs:
    os.makedirs(os.path.dirname("/tmp/hb/"+f),exist_ok=True); shutil.copy(H+"/"+f,"/tmp/hb/"+f)
e=json.load(open(H+"/expected_answers.json")); m=json.load(open(H+"/selection_manifest.json"))
json.dump({f:e[f] for f in fs},open("/tmp/hb/expected_answers.json","w")); json.dump([x for x in m if x["selected_path"] in set(fs)],open("/tmp/hb/selection_manifest.json","w"))
PY
cp -r /sub /tmp/sub && cd /tmp/sub && chmod +x build.sh solve && ./build.sh && python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 16 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /tmp/res.json > /out/eval.out 2>&1; echo eval_rc=$?
python3 - <<PY
import json
d=json.load(open("/tmp/res.json")); rows=[{k:r.get(k) for k in ("benchmark","verdict","answer","time","difficulty","model_error")} for v in d["results"].values() for r in v]
for r in rows: r["model_error"]=(r["model_error"] or "")[:70]
json.dump({"final_score":d["final_score"],"rows":rows},open("/out/res.json","w"))
PY
' > $out/run.log 2>&1
  echo "sub69 $1 $sd rc=$? wall=$(( $(date +%s)-t0 )) $(tail -1 $out/run.log | cut -c1-60)" >>$O/summary.txt
}
pub(){ # label side arm: what a solver sees locally: the public QF_UF and QF_UFLRA files with the shipped evaluate.py (timeout 60, parallel 8)
  local sd=$2 img d; [ $sd = old ] && { img=$IMGOLD; d=base; } || { img=$IMGNEW; d=new; }
  fits 300 "$1-$sd-pub" || return 0
  local out=$O/pub/$1-$sd; mkdir -p $out /job/w/$3; [ -f /job/w/$3/build.sh ] || tar xzf /job/subs/$3.tar.gz -C /job/w/$3
  timeout 600 docker run --rm --network none --cpus 8 --memory 7g -v /job/$d/edgebench/tasks/$T/environment/workspace/benchmarks:/b0:ro -v /job/w/$3:/sub:ro -v $out:/out --entrypoint bash $img -c 'cp -r /b0 /tmp/b; cp -r /sub /tmp/sub; cd /tmp/sub; chmod +x build.sh solve; ./build.sh; python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/b --expected /tmp/b/expected_answers.json --manifest /tmp/b/selection_manifest.json --logics QF_UF QF_UFLRA --timeout 60 --parallel 8 --submission-root /tmp/sub --output /out/res.json > /out/eval.out 2>&1; echo eval_rc=$?; python3 -c "
import json
d=json.load(open(\"/out/res.json\")); rows=[{k:r.get(k) for k in (\"benchmark\",\"verdict\",\"model_error\")} for v in d[\"results\"].values() for r in v]
for r in rows: r[\"model_error\"]=(r[\"model_error\"] or \"\")[:70]
json.dump({\"final_score\":d[\"final_score\"],\"rows\":rows},open(\"/out/res.json\",\"w\"))"' > $out/run.log 2>&1
  echo "pub $1 $sd rc=$? $(tail -1 $out/run.log | cut -c1-60)" >>$O/summary.txt
}
mkdir -p $O/sub $O/pub
# Full hidden set via sforge eval, 60 s per case, 16 solver processes on 8 CPUs.
seval real-full2 new real.tar.gz 2900
