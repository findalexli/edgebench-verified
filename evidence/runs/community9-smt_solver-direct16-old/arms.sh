mkdir -p $O/direct
img=$IMGOLD; [ old = new ] && img=$IMGNEW
mkdir -p /job/w/real; tar xzf /job/subs/real.tar.gz -C /job/w/real
t0=$(date +%s)
timeout 3000 docker run --name direct --network none --cpus 8 --memory 7g -v /job/w/real:/sub:ro -v $O/direct:/out --entrypoint bash $img -c '
cp -r /sub /home/workspace/smt_solver_x && cd /home/workspace/smt_solver_x && chmod +x build.sh solve && ./build.sh >/out/build.out 2>&1
python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /home/workspace/smt_judge/hidden_benchmarks --expected /home/workspace/smt_judge/hidden_benchmarks/expected_answers.json --manifest /home/workspace/smt_judge/hidden_benchmarks/selection_manifest.json --timeout 60 --parallel 16 --perturb --perturb-salt hidden-sebench --submission-root /home/workspace/smt_solver_x --output /tmp/res.json > /out/eval.out 2> /out/eval.err; echo eval_rc=$?
cat /sys/fs/cgroup/memory.events; cat /sys/fs/cgroup/memory.peak
python3 - <<PY
import json
d=json.load(open("/tmp/res.json")); rows=[{k:r.get(k) for k in ("benchmark","verdict","answer","time","difficulty","model_error")} for v in d["results"].values() for r in v]
for r in rows: r["model_error"]=(r["model_error"] or "")[:70]
json.dump({"final_score":d["final_score"],"logic_summary":d.get("logic_summary"),"rows":rows},open("/out/res.json","w"))
PY
' > $O/direct/run.log 2>&1
echo "direct direct16-old old par=16 lim= rc=$? wall=$(( $(date +%s)-t0 ))" >>$O/summary.txt
docker inspect direct --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}}' >>$O/summary.txt
