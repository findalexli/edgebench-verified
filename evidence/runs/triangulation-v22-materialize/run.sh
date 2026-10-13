#!/bin/bash
# Clean materialize + build check for triangulation_coloring_optimization-v2 package v2.2: run the package's own
# materialize.sh (pull pinned images, docker create/cp, apply repair.patch, verify every output sha256), then build
# both Dockerfiles and list the in-image hashes of the replaced files.
set -uo pipefail
O=/job/out; mkdir -p $O
if ! command -v patch > /dev/null; then (apt-get update -qq && apt-get install -y -qq patch) > $O/apt_patch.log 2>&1; fi
patch --version | head -1 > $O/env.txt 2>&1
cd /job/pkg
rc=1; for k in 1 2 3; do ./materialize.sh > $O/materialize.log 2>&1; rc=$?; [ $rc = 0 ] && break; echo "retry $k rc=$rc" >> $O/materialize.retries; sleep 10; done
echo "materialize exit=$rc" | tee $O/status.txt
sha256sum $(find files -type f | sort) > $O/files.sha256
docker build -q -f Dockerfile -t ebv/tricol-judge:v22m . > $O/build.log 2>&1 && docker build -q -f Dockerfile.work -t ebv/tricol-work:v22m . >> $O/build.log 2>&1
echo "build exit=$?" | tee -a $O/status.txt
WD=/home/workspace/triangulation_coloring
docker run --rm --network none ebv/tricol-judge:v22m bash -c "cd $WD && sha256sum tools/src/*.py cases/* /tmp/eval_triangulation_coloring.py" > $O/hashes_judge.txt 2>&1
docker run --rm --network none ebv/tricol-work:v22m bash -c "cd $WD && sha256sum tools/src/*.py sample_data/*" > $O/hashes_work.txt 2>&1
docker image rm ebv/tricol-judge:v22m ebv/tricol-work:v22m > /dev/null 2>&1
rm -rf /job/pkg/files
echo done > $O/DONE
