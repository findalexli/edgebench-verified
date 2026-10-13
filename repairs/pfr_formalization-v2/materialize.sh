#!/usr/bin/env bash
# materialize.sh: regenerate this repair package's image-derived files (files/, orig/) from the
# public, digest-pinned EdgeBench images plus repair.patch, then verify every resulting sha256
# against source-lock.json ("materialize"."outputs"). Afterwards the package Dockerfile builds
# unchanged:   ./materialize.sh && docker build -t <tag> .
#
# Files copied out of the EdgeBench images are deliberately NOT stored in Git; only our diffs are.
# Adapted by hand from tools/materialize.sh.in for pfr_formalization-v2 (the generator's Lean
# rebuild step is specific to lean_analysis_proofs; see the package README).
#
# Steps: pull pinned image(s) by digest if absent -> `docker create` + `docker cp` (no container is
# run) -> apply repair.patch with `patch -p1` -> download public Maven Central artifacts (if any)
# -> verify sha256 of every output. Any mismatch fails loudly.
#
# Disk order (pfr only): the grader image (about 10.5 GB unpacked) and the work image (about 11 GB)
# do not fit together on a 21 GB machine. An image that is used only for a CHECK row (here the work
# image) is therefore pulled after the grader steps and the Lean rebuild are done, and the grader
# image is removed first if this run pulled it. MATERIALIZE_KEEP_IMAGES=1 keeps it (then
# `docker build .` does not pull it again).
#
# Needs: bash, docker, GNU patch, sha256sum, python3 (reads source-lock.json); curl for Maven.
# Env:   EDGEBENCH_ROOT  EdgeBench repo root, for packages whose base text is a public task JSON
#                        (default: three directories above this package).
#        MATERIALIZE_SKIP_LEAN_BUILD=1  skip the Lean rebuild of the judge build artifacts.
set -euo pipefail

PKG_NAME="pfr_formalization-v2"
IMAGES=(
  "judge|seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4"
  "work|seededge/edgebench.work.pfr_formalization@sha256:3be95d28524d9bad61f82306b6448fe3d0fc2dff66fd285d62bfa057bf047c86"
)
BASE=(
  "judge|/home/workspace/judge/se-bmk-intern/pfr/PFR/WeakPFR.lean|files/judge/pfr/PFR/WeakPFR.lean"
)
ORIG=(
  "judge|/home/workspace/judge/se-bmk-intern/pfr/PFR/WeakPFR.lean|orig/WeakPFR.lean"
)
TASKJSON=(
)
CHECK=(
  "work|/home/workspace/se-bmk-intern/pfr/PFR/WeakPFR.lean"
)
COPIES=(
  "files/judge/pfr/PFR/WeakPFR.lean|files/work/PFR/WeakPFR.lean"
)
MAVEN=(
)
LEAN_BUILD=1
cd "$(dirname "${BASH_SOURCE[0]}")"
PKG_DIR=$(pwd)
EDGEBENCH_ROOT="${EDGEBENCH_ROOT:-$PKG_DIR/../..}"
LOCK="$PKG_DIR/source-lock.json"

log() { echo "materialize[$PKG_NAME]: $*" >&2; }
die() { echo "materialize[$PKG_NAME]: ERROR: $*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "missing required tool: $1"; }
need python3; need sha256sum; need patch
[ "${#IMAGES[@]}" -eq 0 ] || need docker
[ "${#MAVEN[@]}" -eq 0 ] || need curl
[ -f "$LOCK" ] || die "source-lock.json not found"

# lockq <outputs|input SOURCE PATH>: read expected values from source-lock.json
lockq() {
  python3 -I - "$LOCK" "$@" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))['materialize']
if sys.argv[2] == 'outputs':
    for k, v in sorted(m['outputs'].items()):
        print(v, k)
elif sys.argv[2] == 'input':
    hits = [i['sha256'] for i in m['inputs'] if i['source'] == sys.argv[3] and i['path'] == sys.argv[4]]
    if not hits:
        sys.exit('no input entry for %s:%s' % (sys.argv[3], sys.argv[4]))
    print(hits[0])
elif sys.argv[2] == 'lean':
    lb = m['lean_build']
    if sys.argv[3] == 'members':
        print('\n'.join(lb['artifact_members']))
    else:
        print(lb[sys.argv[3]])
PY
}

lockq outputs >/dev/null || die "source-lock.json has no usable \"materialize\" block"

sha_of() { sha256sum "$1" | cut -d' ' -f1; }

check_input() {  # check_input SOURCE PATH FILE
  local want got
  want=$(lockq input "$1" "$2") || die "lock has no input entry for $1:$2"
  got=$(sha_of "$3")
  [ "$got" = "$want" ] || die "original $1:$2 has sha256 $got, expected $want (wrong image or file?)"
}

STAGE=$(mktemp -d)
CIDS=()
cleanup() {
  local c
  for c in ${CIDS[@]+"${CIDS[@]}"}; do docker rm -f "$c" >/dev/null 2>&1 || true; done
  rm -rf "$STAGE"
}
trap cleanup EXIT

# The Lean rebuild runs in a 14.7 GB judge image: hold the machine-wide heavy-job lock
# (BRIEF-FOR-REVIEWERS HARD RULE) for the whole run. Set EBV_HEAVY_LOCK_HELD=1 if the caller holds it.
if [ "$LEAN_BUILD" = 1 ] && [ "${EBV_HEAVY_LOCK_HELD:-0}" != 1 ]; then
  need flock
  exec 9>"${EBV_HEAVY_LOCK:-/tmp/ebv-heavy.lock}"
  log "waiting for the heavy-job lock ${EBV_HEAVY_LOCK:-/tmp/ebv-heavy.lock}"
  flock -w 7200 9 || die "could not take the heavy-job lock"
fi

# Roles read by BASE or ORIG rows are needed now; a role used only by CHECK rows is deferred to
# step 5b, after the grader image is no longer needed.
declare -A NEEDED=() CID=() REF=() PULLED=()
for row in ${BASE[@]+"${BASE[@]}"} ${ORIG[@]+"${ORIG[@]}"}; do NEEDED[${row%%|*}]=1; done
open_image() {  # open_image ROLE REF: pull if absent, then `docker create` (no container is run)
  local cid
  if ! docker image inspect "$2" >/dev/null 2>&1; then
    log "pulling $2"
    docker pull --platform linux/amd64 "$2" >/dev/null || die "docker pull failed for $2"
    PULLED[$1]=1
  fi
  cid=$(docker create --platform linux/amd64 "$2" true) || die "docker create failed for $2"
  CIDS+=("$cid"); CID[$1]=$cid
}
for row in ${IMAGES[@]+"${IMAGES[@]}"}; do
  IFS='|' read -r role ref <<<"$row"
  REF[$role]=$ref
  [ -n "${NEEDED[$role]:-}" ] && open_image "$role" "$ref"
done

# 1. Remove previous outputs so nothing stale survives.
while read -r _ path; do rm -f -- "$path"; done < <(lockq outputs)

# 2. Extract originals (base files that repair.patch edits, and orig/ reference copies).
n=0
for row in ${BASE[@]+"${BASE[@]}"} ${ORIG[@]+"${ORIG[@]}"}; do
  IFS='|' read -r role path dst <<<"$row"
  mkdir -p "$(dirname "$dst")"
  docker cp -L "${CID[$role]}:$path" "$STAGE/extract" >/dev/null || die "docker cp $role:$path failed"
  check_input "$role" "$path" "$STAGE/extract"
  mv -f "$STAGE/extract" "$dst"; n=$((n + 1))
done
check_rows() {  # check_rows: run every CHECK row whose image is open now; return 1 if any is left
  local row role path left=0
  for row in ${CHECK[@]+"${CHECK[@]}"}; do
    IFS='|' read -r role path <<<"$row"
    if [ -z "${CID[$role]:-}" ]; then left=1; continue; fi
    docker cp -L "${CID[$role]}:$path" "$STAGE/check" >/dev/null || die "docker cp $role:$path failed"
    check_input "$role" "$path" "$STAGE/check"; rm -f "$STAGE/check"
  done
  return $left
}
check_rows || log "check-only image(s) deferred until after the Lean rebuild (disk)"
for row in ${TASKJSON[@]+"${TASKJSON[@]}"}; do
  IFS='|' read -r rel field dst <<<"$row"
  [ -f "$EDGEBENCH_ROOT/$rel" ] || die "$EDGEBENCH_ROOT/$rel not found (set EDGEBENCH_ROOT to the EdgeBench repo)"
  mkdir -p "$(dirname "$dst")"
  python3 -I - "$EDGEBENCH_ROOT/$rel" "$field" "$dst" <<'PY'
import json, shutil, sys
src, field, dst = sys.argv[1:]
if not field:
    shutil.copyfile(src, dst)
else:
    v = json.load(open(src, encoding='utf-8'))
    for k in field.split('.'):
        v = v[k]
    open(dst, 'wb').write(v.encode('utf-8'))
PY
  check_input taskjson "$rel${field:+#$field}" "$dst"; n=$((n + 1))
done
log "extracted $n original file(s); originals match source-lock.json"

# 3. Apply our diff.
if grep -q '^@@ ' repair.patch; then
  patch -p1 --forward --batch --no-backup-if-mismatch --reject-file="$STAGE/rejects" -s < repair.patch \
    || die "repair.patch did not apply cleanly"
  log "applied repair.patch"
fi
for row in ${COPIES[@]+"${COPIES[@]}"}; do
  IFS='|' read -r src dst <<<"$row"
  mkdir -p "$(dirname "$dst")"; cp -p "$src" "$dst"
done

# 4. Public Maven Central artifacts (not image files): exact URL, sha256 checked in step 6.
for row in ${MAVEN[@]+"${MAVEN[@]}"}; do
  IFS='|' read -r url dst <<<"$row"
  mkdir -p "$(dirname "$dst")"
  curl -fsSL --retry 3 -o "$dst" "$url" || die "download failed: $url"
done
[ "${#MAVEN[@]}" -eq 0 ] || log "downloaded ${#MAVEN[@]} Maven Central file(s)"

# 5. Rebuild the judge build artifacts inside the original image.
lean_build() {
  local ref out art
  art=$(lockq lean artifact)
  if [ "${MATERIALIZE_SKIP_LEAN_BUILD:-0}" = 1 ]; then
    log "MATERIALIZE_SKIP_LEAN_BUILD=1: $art NOT rebuilt; docker build will fail until it is"
    return 0
  fi
  ref=${IMAGES[0]#*|}
  out="$STAGE/lean"; mkdir -p "$out"; chmod 777 "$out"
  lockq lean members > "$out/members.txt"
  log "lake build ListDeclAxiom inside $ref (offline, --memory 6g); takes a few minutes"
  timeout 5400 docker run --rm --network none --memory 6g --cpus 4 \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    -v "$PKG_DIR/files":/v2files:ro -v "$out":/out --entrypoint bash "$ref" -lc '
set -euo pipefail
J=/home/workspace/judge/se-bmk-intern/pfr
touch /tmp/marker; sleep 1
cp /v2files/judge/pfr/PFR/WeakPFR.lean $J/PFR/WeakPFR.lean
( cd $J && lake build ListDeclAxiom ) > /out/v2-listing.raw 2>&1
sed -E "s/^info: ListDeclAxiom\.lean:[0-9]+:[0-9]+: //" /out/v2-listing.raw | grep -E "^(OK|BAD) |^SUMMARY|^HASH" > /out/v2-listing.txt || true
( cd $J && lake build ) > /out/lakebuild-default.raw 2>&1
( cd / && find $J -path $J/.lake/packages -prune -o -type f -newer /tmp/marker -print | sed "s|^/||" | sort > /out/changed.txt )
( cd / && tar --numeric-owner -cf /out/v2-build-artifacts.tar -T /out/members.txt )
chown -R "$HOST_UID:$HOST_GID" /out 2>/dev/null || chmod -R a+rwX /out' || die "lean rebuild failed (see logs above)"
  local want got
  want=$(lockq lean expected_listing_sha256); got=$(sha_of "$out/v2-listing.txt")
  [ "$got" = "$want" ] || die "regenerated ListDeclAxiom listing sha256 $got != saved v2 listing $want"
  diff -q <(sort "$out/members.txt") "$out/changed.txt" >/dev/null \
    || die "the rebuild rewrote a different file set than the saved artifact set: $(diff <(sort "$out/members.txt") "$out/changed.txt" | head -5)"
  diff -q <(tar -tf "$out/v2-build-artifacts.tar" | sort) <(sort "$out/members.txt") >/dev/null \
    || die "artifact tar members differ from source-lock.json"
  mkdir -p "$(dirname "$art")"; mv -f "$out/v2-build-artifacts.tar" "$art"
  log "rebuilt $art: listing identical to saved v2 listing ($(wc -l < "$out/v2-listing.txt") lines), $(wc -l < "$out/members.txt") members"
}
[ "$LEAN_BUILD" = 0 ] || lean_build

# 5b. Check-only images (the work image): free the grader image first, then pull and check.
deferred=0
for role in "${!REF[@]}"; do [ -z "${CID[$role]:-}" ] && deferred=1; done
if [ "$deferred" = 1 ]; then
  for role in "${!CID[@]}"; do
    docker rm -f "${CID[$role]}" >/dev/null 2>&1 || true; unset "CID[$role]"
    if [ -n "${PULLED[$role]:-}" ] && [ "${MATERIALIZE_KEEP_IMAGES:-0}" != 1 ]; then
      log "removing ${REF[$role]} (pulled by this run) to make room; docker build will pull it again"
      docker rmi "${REF[$role]}" >/dev/null || die "docker rmi ${REF[$role]} failed"
    fi
  done
  for role in "${!REF[@]}"; do
    for row in ${CHECK[@]+"${CHECK[@]}"}; do
      [ "${row%%|*}" = "$role" ] && { open_image "$role" "${REF[$role]}"; break; }
    done
  done
  check_rows || die "a CHECK row has no image"
  log "checked the deferred image(s) against source-lock.json"
fi

# 6. Verify every output against source-lock.json.
bad=0; total=0
while read -r want path; do
  total=$((total + 1))
  if [ ! -f "$path" ]; then echo "MISSING  $path" >&2; bad=$((bad + 1)); continue; fi
  got=$(sha_of "$path")
  if [ "$got" != "$want" ]; then echo "MISMATCH $path: got $got want $want" >&2; bad=$((bad + 1)); fi
done < <(lockq outputs)
[ "$bad" -eq 0 ] || die "$bad of $total output file(s) failed sha256 verification"
log "OK: all $total output file(s) match source-lock.json"
