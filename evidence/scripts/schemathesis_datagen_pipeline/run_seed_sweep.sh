#!/bin/bash
# Repeat the single HTTP-date property under 20 Hypothesis seeds per variant (repaired test only).
cp /ebv/headers_overlay.py /app/src/schemathesis/specs/openapi/headers.py
cd /app
for v in independent_fields off_by_one_clock correct; do
  fails=0
  for s in $(seq 1 20); do
    EBV_DATE_VARIANT=$v python -m pytest -p no:cacheprovider -q --hypothesis-seed=$s \
      "/ebv/tests_repaired/test_01_header_strategies.py::test_http_date_values_grammar" >/dev/null 2>&1 || fails=$((fails+1))
  done
  echo "variant=$v repaired_test_failures=$fails/20 seeds"
done
