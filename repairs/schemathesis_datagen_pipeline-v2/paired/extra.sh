#!/bin/bash
# Seed sweep of the single HTTP-date test: 20 Hypothesis seeds per (variant, image).
for v in correct stdlib_1900 independent_fields off_by_one_clock stdlib_any_year; do for i in v1 v2; do
  docker run --rm --network none --memory 2g --cpus 2 -v /job:/job:ro ebv/$i:latest bash -c '
    . /job/variants/'$v'/apply.sh; cd /app; f=0
    for s in $(seq 1 20); do python -m pytest -p no:cacheprovider -q --hypothesis-seed=$s /tests/test_01_header_strategies.py::test_http_date_values_grammar >/dev/null 2>&1 || f=$((f+1)); done
    echo "sweep variant='$v' image='$i' failing_seeds=$f/20"'
done; done
