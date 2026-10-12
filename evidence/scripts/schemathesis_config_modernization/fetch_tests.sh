#!/bin/bash
# Re-creates tests_orig/ (from the pinned judge image) and tests_repaired/ (orig + proposed patch).
# Hidden judge tests are not stored in this repository.
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); R=$(cd "$D/../../../proposedrepairs" && pwd)
I=seededge/edgebench.judge.schemathesis_config_modernization@sha256:ff71a766c254fc62f6ffd12d877297cb22223a0bb2190e91f95fe6b3231d519e
rm -rf "$D/tests_orig" "$D/tests_repaired"; mkdir -p "$D/tests_orig"
for f in test_03_metric_system.py test.sh; do docker run --rm --network none --memory 2g "$I" cat /tests/$f > "$D/tests_orig/$f"; done
cp -r "$D/tests_orig" "$D/tests_repaired"
cd "$D/tests_repaired"
for p in schemathesis-config-function-identity/patch.diff; do sed 's#tests/##g' "$R/$p" | patch -p1; done
sha256sum "$D"/tests_orig/* "$D"/tests_repaired/*
