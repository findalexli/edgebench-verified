#!/usr/bin/env bash
# pfr_formalization-v2: extract the original files the repair edits (judge + work image), for
# .internal only (image files are never committed). No container runs any task code except `cat`/`find`.
set -u; OUT=/job/out; mkdir -p $OUT/judge $OUT/work
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
WORK=seededge/edgebench.work.pfr_formalization@sha256:3be95d28524d9bad61f82306b6448fe3d0fc2dff66fd285d62bfa057bf047c86
J=/home/workspace/judge/se-bmk-intern
docker pull -q $JUDGE > $OUT/pull_judge.log 2>&1 || { echo PULL_FAILED; exit 2; }
docker image inspect --format '{{.Id}} {{.RepoDigests}}' $JUDGE > $OUT/judge/image_id.txt
docker run --rm --network none --entrypoint bash $JUDGE -c "
cd $J; ls -la; ls -la pfr; cat pfr/lean-toolchain; cat pfr/lakefile* ; 
cd pfr; find PFR -name '*.lean' | sort | xargs sha256sum; sha256sum ListDeclAxiom.lean lake-manifest.json ../eval_lean.py PFR.lean;
grep -rln 'import PFR.WeakPFR\|PFR.WeakPFR' --include=*.lean . | grep -v .lake;
ls -la .lake .lake/build .lake/build/lib/lean/PFR | head -80; id; stat -c '%U %G %a %n' PFR/WeakPFR.lean
" > $OUT/judge/inventory.txt 2>&1
CID=$(docker create $JUDGE true)
for f in pfr/PFR/WeakPFR.lean pfr/ListDeclAxiom.lean eval_lean.py pfr/PFR.lean pfr/lake-manifest.json; do
  docker cp -L $CID:$J/$f $OUT/judge/$(basename $f); done
docker cp -L $CID:$J/pfr/PFR $OUT/judge/PFR_dir
docker rm $CID >/dev/null
docker rmi $JUDGE >/dev/null 2>&1
for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find $B -type f -size +50M -delete; done
df -h / > $OUT/df.txt
docker pull -q $WORK > $OUT/pull_work.log 2>&1 || { echo WORK_PULL_FAILED; exit 3; }
docker image inspect --format '{{.Id}} {{.RepoDigests}} {{.Size}} {{.Config.User}} {{.Config.WorkingDir}}' $WORK > $OUT/work/image_id.txt
docker run --rm --network none --entrypoint bash $WORK -c "
find / -xdev -path '*/PFR/WeakPFR.lean' -not -path '*/.lake/*' 2>/dev/null; ls -la /home/workspace /home/workspace/se-bmk-intern /home/workspace/se-bmk-intern/pfr;
cd /home/workspace/se-bmk-intern/pfr && find PFR -name '*.lean' | sort | xargs sha256sum; sha256sum ListDeclAxiom.lean lake-manifest.json PFR.lean;
stat -c '%U %G %a %n' PFR/WeakPFR.lean PFR; ls -la .lake 2>&1 | head; id
" > $OUT/work/inventory.txt 2>&1
CID=$(docker create $WORK true)
docker cp -L $CID:/home/workspace/se-bmk-intern/pfr/PFR/WeakPFR.lean $OUT/work/WeakPFR.lean
docker rm $CID >/dev/null
echo done
