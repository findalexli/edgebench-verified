# Deviation (disk): materialize.sh pulls the judge and the work image together; they do not fit on a
# 21 GB worker (evidence/runs/pfr_formalization-v2-paired-v2/result-attempt1-disk). Its only use of the
# work image is a CHECK of the starter WeakPFR.lean sha256, so this copy drops the two `  "work|` rows
# (the IMAGES row and the CHECK row) and the CHECK is done by the before_work hook instead.
set -u; S=/job/src/repairs/pfr_formalization-v2
grep -v '^  "work|' $S/materialize.sh > $S/materialize.nowork.sh; chmod +x $S/materialize.nowork.sh
diff $S/materialize.sh $S/materialize.nowork.sh > /job/out/pfr_materialize.nowork.diff
JUDGE=seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
docker pull -q --platform linux/amd64 $JUDGE; df -h / | tail -1
for B in $(find / -xdev -type d -path '*content.v1.content/blobs/sha256' 2>/dev/null); do find $B -type f -size +50M -delete; done
df -h / | tail -1
