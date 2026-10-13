# The work-image CHECK that materialize.nowork.sh skipped, using materialize.sh's own lock entry.
set -u; S=$1; O=$2
WORK=seededge/edgebench.work.pfr_formalization@sha256:3be95d28524d9bad61f82306b6448fe3d0fc2dff66fd285d62bfa057bf047c86
P=/home/workspace/se-bmk-intern/pfr/PFR/WeakPFR.lean
docker pull -q --platform linux/amd64 $WORK; df -h / | tail -1
for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find $B -type f -size +50M -delete; done
df -h / | tail -1
want=$(python3 -I -c 'import json,sys; m=json.load(open(sys.argv[1]))["materialize"]; print([i["sha256"] for i in m["inputs"] if i["source"]=="work" and i["path"]==sys.argv[2]][0])' $S/source-lock.json $P)
cid=$(docker create --platform linux/amd64 $WORK true); t=$(mktemp -d)
docker cp -L $cid:$P $t/w; docker rm -f $cid >/dev/null
got=$(sha256sum $t/w | cut -d' ' -f1); rm -rf $t
echo "work $P sha256 $got (lock input $want)"
[ "$got" = "$want" ] && echo "WORK_CHECK_OK" || { echo "WORK_CHECK_MISMATCH"; exit 1; }
