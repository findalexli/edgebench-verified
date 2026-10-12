#!/bin/bash
# Re-creates tests_orig/ (from the pinned judge image) and tests_repaired/ (orig + proposed patch).
# Hidden judge tests are not stored in this repository.
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); R=$(cd "$D/../../../proposedrepairs" && pwd)
I=seededge/edgebench.judge.schemathesis_datagen_pipeline@sha256:16b21364d67906d802e24d0b3b4505c42a6ac0f91cd5b382bb4c9d1d20224d37
rm -rf "$D/tests_orig" "$D/tests_repaired"; mkdir -p "$D/tests_orig"
for f in test_01_header_strategies.py; do docker run --rm --network none --memory 2g "$I" cat /tests/$f > "$D/tests_orig/$f"; done
cp -r "$D/tests_orig" "$D/tests_repaired"
cd "$D/tests_repaired"
for p in datagen-http-date/repair.patch; do sed 's#tests/##g' "$R/$p" | patch -p1; done
sha256sum "$D"/tests_orig/* "$D"/tests_repaired/*
