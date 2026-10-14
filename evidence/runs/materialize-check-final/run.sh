#!/usr/bin/env bash
# materialize-check job: for each package in pkgs.txt, run check_pkg.sh on a copy of the package
# exactly as committed at HEAD 37d30d27 (src/ was made with `git archive`), then remove every image
# and build cache before the next package. Only logs, hashes and image IDs are kept in out/.
set -u; cd /job; O=/job/out; mkdir -p $O
[ -f /job/env.sh ] && . /job/env.sh   # per-job settings (PRUNE_BETWEEN, DELBLOBS, PKG_TIMEOUT)
delblobs() { for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find "$B" -type f -size +50M -delete; done; }
cleanup() {
  docker ps -aq | xargs -r docker rm -f > /dev/null 2>&1
  docker images -q | sort -u | xargs -r docker rmi -f > /dev/null 2>&1
  docker image prune -af > /dev/null 2>&1; docker builder prune -af > /dev/null 2>&1; delblobs
}
{ date -u +%FT%TZ; uname -a; docker version --format 'docker server {{.Server.Version}}'; python3 --version
  echo "--- images at start"; docker images; df -h /; free -g; nproc; cat /job/SOURCE; } > $O/env.txt 2>&1
if ! command -v patch > /dev/null; then
  (apt-get update -qq && apt-get install -y -qq patch) > $O/apt_patch.log 2>&1
  echo "installed GNU patch (was missing)" >> $O/env.txt
fi
patch --version | head -1 >> $O/env.txt 2>&1
command -v flock >> $O/env.txt 2>&1
[ -f /job/prepare.sh ] && bash /job/prepare.sh > $O/prepare.log 2>&1
for P in $(cat /job/pkgs.txt); do
  echo "=== $P $(date -u +%T)"
  MS=materialize.sh; [ -f "/job/hooks/$P.ms" ] && MS=$(cat "/job/hooks/$P.ms")
  [ -f "/job/hooks/$P.pre.sh" ] && bash "/job/hooks/$P.pre.sh" > "$O/$P.pre.log" 2>&1
  timeout "${PKG_TIMEOUT:-1500}" bash /job/check_pkg.sh "$P" "$MS"; echo "check rc=$?"
  rm -rf "/job/src/repairs/$P/files" "/job/src/repairs/$P/orig"
  cleanup; df -h / | tail -1
done
date -u +%FT%TZ > $O/finished
