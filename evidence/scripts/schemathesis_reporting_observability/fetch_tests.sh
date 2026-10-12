#!/bin/bash
# Re-creates tests_orig/ (from the pinned judge image) and tests_repaired/ (orig + proposed patch).
# Hidden judge tests are not stored in this repository.
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); R=$(cd "$D/../../../proposedrepairs" && pwd)
I=seededge/edgebench.judge.schemathesis_reporting_observability@sha256:b1e16633e75b2a21ef805961bb190c0a71afb75225986997340185eb7d67fc54
rm -rf "$D/tests_orig" "$D/tests_repaired"; mkdir -p "$D/tests_orig"
for f in test_02_reporting.py test_05_email_coverage.py test.sh; do docker run --rm --network none --memory 2g "$I" cat /tests/$f > "$D/tests_orig/$f"; done
cp -r "$D/tests_orig" "$D/tests_repaired"
cd "$D/tests_repaired"
for p in reporting-junit/repair.patch reporting-coverage-filter/repair.patch; do sed 's#tests/##g' "$R/$p" | patch -p1; done
sha256sum "$D"/tests_orig/* "$D"/tests_repaired/*
