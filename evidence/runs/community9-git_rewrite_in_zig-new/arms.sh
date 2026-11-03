
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
bj new; IMGNEW=$(tag new); echo "new $IMGNEW $(docker image inspect $IMGNEW --format '{{.Id}}')" >>$O/tags.txt
S=/job/gen; mkdir -p $S /job/w
cp /job/subs/auto39.tar.gz $S/real.tar.gz
# Scaffold archive in the same member style as real archives (./name), from the task's own scaffold.
/job/v/bin/python - <<'PY'
import tarfile, os
root = '/job/base/edgebench/tasks/git_rewrite_in_zig/environment/zig-port'
with tarfile.open('/job/gen/scaf.tar.gz', 'w:gz') as t:
    for d, _, fs in os.walk(root):
        for f in sorted(fs):
            p = os.path.join(d, f); t.add(p, './' + os.path.relpath(p, root), recursive=False)
PY
# Generate main.o the way a solver would, with the judge image's Zig, for both trees; check the oracle test compiles and passes.
for k in scaf real; do mkdir -p /job/w/$k; tar -xzf $S/$k.tar.gz -C /job/w/$k; cp /job/subs/oracle_test.zig /job/w/$k/src/oracle_test.zig; chmod -R a+rwX /job/w/$k
  docker run --rm --network none -v /job/w/$k:/w --entrypoint bash $IMGOLD -c 'cd /w && zig build-obj src/main.zig -lc -lz; echo build-obj rc=$?; ls -la main.o; zig test src/oracle_test.zig; echo zigtest rc=$?; rm -rf .zig-cache' >$O/gen-$k.log 2>&1
  /job/v/bin/python /job/addm.py $S/$k.tar.gz $S/$k-obj.tar.gz ./main.o=/job/w/$k/main.o
  /job/v/bin/python /job/addm.py $S/$k.tar.gz $S/$k-test.tar.gz ./src/oracle_test.zig=/job/w/$k/src/oracle_test.zig
done
sha256sum $S/* >>$O/subs.sha
( grade new-real-p1 $IMGNEW $TD $S/real.tar.gz 420; grade new-real-obj-p1 $IMGNEW $TD $S/real-obj.tar.gz 420; grade new-real-test-p1 $IMGNEW $TD $S/real-test.tar.gz 420; grade new-scaf-p1 $IMGNEW $TD $S/scaf.tar.gz 420; grade new-scaf-obj-p1 $IMGNEW $TD $S/scaf-obj.tar.gz 420; grade new-scaf-test-p1 $IMGNEW $TD $S/scaf-test.tar.gz 420 ) & LA=$!
( grade new-scaf-p2 $IMGNEW $TD $S/scaf.tar.gz 420; grade new-scaf-obj-p2 $IMGNEW $TD $S/scaf-obj.tar.gz 420; grade new-scaf-test-p2 $IMGNEW $TD $S/scaf-test.tar.gz 420; grade new-real-p2 $IMGNEW $TD $S/real.tar.gz 420; grade new-real-obj-p2 $IMGNEW $TD $S/real-obj.tar.gz 420; grade new-real-test-p2 $IMGNEW $TD $S/real-test.tar.gz 420 ) & LB=$!
wait $LA $LB
