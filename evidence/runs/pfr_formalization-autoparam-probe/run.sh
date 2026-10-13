#!/usr/bin/env bash
# pfr_formalization escalation E5: are the five `autoParam (...) sorry` targets reachable?
# (1) baseline probe in the judge repo; (2) exact judge.eval_cmd on the unmodified starter (orig)
# and on a submission (probe) that adds three fully proved lemmas to PFR/WeakPFR.lean, two of them
# using the file's own `variable (μ : Measure Ω := by volume_tac)` binders; then the probe again
# in the submission tree.
set -u
cd /job; OUT=/job/out; mkdir -p $OUT
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
date -u +%FT%TZ > $OUT/started
docker pull -q $JUDGE > $OUT/pull.log 2>&1 || { echo PULL_FAILED; exit 2; }
docker image inspect --format '{{.Id}} {{.RepoDigests}}' $JUDGE > $OUT/image_id.txt
python3 -c "import json;print(json.load(open('/job/task.json'))['judge']['eval_cmd'])" > $OUT/eval_cmd.txt
cp names.txt $OUT/names.txt
echo "=== baseline probe $(date -u +%T)"
docker run --rm --network none --memory 6g --cpus 4 -v /job:/jobin:ro -v $OUT:/out --entrypoint bash $JUDGE -c '
  cd /home/workspace/judge/se-bmk-intern/pfr && cp /jobin/EbvProbe.lean ./EbvProbe.lean && timeout 1800 lake env lean EbvProbe.lean' > $OUT/probe_baseline.out 2>&1
echo "probe rc=$?"; grep EBV $OUT/probe_baseline.out | grep -v '  pp=' | cut -c1-300
echo "=== eval $(date -u +%T)"
docker run --rm --network none --memory 6g --cpus 4 -v /job:/jobin:ro -v $OUT:/out --entrypoint bash $JUDGE -c '
set -u
EVAL=$(cat /out/eval_cmd.txt)
SUB=/home/workspace/se-bmk-intern/pfr; J=/home/workspace/judge/se-bmk-intern/pfr; F=PFR/WeakPFR.lean
mkdir -p $SUB; ( cd $J && tar c --exclude=./.lake . ) | ( cd $SUB && tar x )
for v in orig probe; do
  echo "=== variant $v $(date -u +%T)"
  cp $J/$F $SUB/$F
  if [ $v = probe ]; then
    python3 - $SUB/$F <<PY
import sys
p=sys.argv[1]; s=open(p).read()
a="end Torsion\n"; b="end F2_projection\n"
assert s.count(a)==1 and s.count(b)==1
s=s.replace(a,"/-- ebv probe: fully proved, uses the section variable binder for μ -/\nlemma ebv_probe_torsion : μ = μ := rfl\n\n"+a)
s=s.replace(b,"/-- ebv probe: fully proved, uses the section variable binder for μ\x27 -/\nlemma ebv_probe_f2 : μ\x27 = μ\x27 := rfl\n\n/-- ebv control: auto-param in the lemma signature -/\nlemma ebv_probe_sig {Ω₀ : Type*} [MeasurableSpace Ω₀] (ν : Measure Ω₀ := by volume_tac) : ν = ν := rfl\n\n"+b)
open(p,"w").write(s)
PY
  fi
  diff $J/$F $SUB/$F > /out/weakpfr_$v.diff; sha256sum $SUB/$F
  bash -c "$EVAL" > /out/report_$v.json 2> /out/build_$v.err; echo "eval_cmd rc=$?"
  python3 -c "
import json
s=open(\"/out/report_$v.json\").read(); i=s.find(\">>>>> Start\"); j=s.find(\"{\", i if i>=0 else 0)
try:
  r=json.loads(s[j:s.rfind(\"}\")+1]); print(\"SCORE\", \"$v\", r[\"score\"], r[\"summary\"])
except Exception as e: print(\"no json\", e)"
  ( cd $SUB && lake build ListDeclAxiom 2>/dev/null > /out/listdecl_$v.txt ) || true
  grep -E "^(OK|BAD) (ebv_probe|PFR_projection|torsion_free_doubling|torsion_dist_shrinking|app_ent_PFR)" /out/listdecl_$v.txt | sed -E "s/ : type=.*; unexpected=/ unexpected=/" 
  if [ $v = probe ]; then
    cp /jobin/names_sub.txt /out/names.txt.sub
    cd $SUB && cp /jobin/EbvProbe.lean ./EbvProbe.lean && sed -i "s#/out/names.txt#/out/names.txt.sub#" EbvProbe.lean && timeout 1800 lake env lean EbvProbe.lean > /out/probe_submission.out 2>&1; echo "subprobe rc=$?"; cd /
    grep EBV /out/probe_submission.out | grep -v "  pp=" | cut -c1-300
  fi
  echo "=== done $v $(date -u +%T)"
done'
echo "eval rc=$?"
date -u +%FT%TZ > $OUT/finished
