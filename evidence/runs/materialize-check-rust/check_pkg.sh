#!/usr/bin/env bash
# check_pkg.sh PKG [MATERIALIZE_SCRIPT]
# One repair package, as committed at HEAD (copied by `git archive` into /job/src/repairs/PKG):
#   1. run ./materialize.sh (or the named script) and capture its log;
#   2. recompute the sha256 of every output against source-lock.json (verify.py lock);
#   3. docker build Dockerfile and Dockerfile.work (if present), tagged per task.json.in
#      (seededge/edgebench.<role>.<task>:<image_tag>), and record the image ID;
#   4. smoke: hash the replaced files inside the built image (verify.py smoke).
# Env: PRUNE_BETWEEN=1 removes each built image and its base before the next Dockerfile.
#      /job/hooks/<PKG>.before_work.sh, if present, runs before Dockerfile.work.
# Only logs, hashes and image IDs go to /job/out/PKG.
set -u
P=$1; MS=${2:-materialize.sh}
T=${P%-v2}; S=/job/src/repairs/$P; O=/job/out/$P; mkdir -p "$O"; R=$O/result.env
ts() { date -u +%FT%TZ; }
delblobs() { for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find "$B" -type f -size +50M -delete; done; }
echo "pkg=$P" > "$R"; echo "started=$(ts)" >> "$R"
df -h / | tail -1 > "$O/df.txt"
t0=$(date +%s)
( cd "$S" && "./$MS" ) > "$O/materialize.log" 2>&1; rc=$?
echo "materialize_script=$MS" >> "$R"; echo "materialize_rc=$rc" >> "$R"
echo "materialize_s=$(( $(date +%s) - t0 ))" >> "$R"
if grep -qE 'OK: all [0-9]+ output file\(s\) match source-lock.json' "$O/materialize.log"; then
  echo "materialize_reported_ok=1" >> "$R"
  echo "materialize_ok_line=$(grep -oE 'OK: all [0-9]+ output file\(s\) match source-lock.json' "$O/materialize.log")" >> "$R"
else
  echo "materialize_reported_ok=0" >> "$R"
fi
[ "${DELBLOBS:-0}" = 1 ] && delblobs
df -h / | tail -1 >> "$O/df.txt"
python3 -I /job/verify.py lock "$S" "$O" > "$O/lock.out" 2>&1; echo "lock_rc=$?" >> "$R"
for DF in Dockerfile Dockerfile.work; do
  [ -f "$S/$DF" ] || continue
  K=${DF/./_}
  if [ "$DF" = Dockerfile.work ] && [ -f "/job/hooks/$P.before_work.sh" ]; then
    bash "/job/hooks/$P.before_work.sh" "$S" "$O" > "$O/before_work.log" 2>&1; echo "before_work_rc=$?" >> "$R"
  fi
  ROLE=judge; grep -qE '^FROM .*edgebench\.work\.' "$S/$DF" && ROLE=work
  TAGV=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["image_tag"])' "$S/task.json.in" "$ROLE")
  TAG="seededge/edgebench.$ROLE.$T:$TAGV"
  CTX=.; [ "$P" = arc_compiler_runtime-v2 ] && CTX=files   # README: docker build -f Dockerfile files
  BASEREF=$(grep -E '^FROM ' "$S/$DF" | tail -1 | sed -E 's/--platform=[^ ]+ //' | awk '{print $2}')
  echo "${K}_role=$ROLE" >> "$R"; echo "${K}_tag=$TAG" >> "$R"; echo "${K}_context=$CTX" >> "$R"
  t0=$(date +%s)
  ( cd "$S" && DOCKER_BUILDKIT=1 docker build --progress=plain -f "$DF" -t "$TAG" "$CTX" ) > "$O/build-$DF.log" 2>&1; brc=$?
  echo "${K}_build_rc=$brc" >> "$R"; echo "${K}_build_s=$(( $(date +%s) - t0 ))" >> "$R"
  if [ $brc = 0 ]; then
    echo "${K}_image_id=$(docker image inspect -f '{{.Id}}' "$TAG")" >> "$R"
    echo "${K}_base_image_id=$(docker image inspect -f '{{.Id}}' "$BASEREF" 2>/dev/null)" >> "$R"
    python3 -I /job/verify.py smoke "$S" "$DF" "$CTX" "$TAG" "$O" > "$O/smoke-$DF.out" 2>&1; echo "${K}_smoke_rc=$?" >> "$R"
  fi
  df -h / | tail -1 >> "$O/df.txt"
  if [ "${PRUNE_BETWEEN:-0}" = 1 ]; then
    docker rmi -f "$TAG" "$BASEREF" > /dev/null 2>&1; docker image prune -af > /dev/null 2>&1
    docker builder prune -af > /dev/null 2>&1; delblobs; df -h / | tail -1 >> "$O/df.txt"
  fi
done
echo "finished=$(ts)" >> "$R"
cat "$R"
