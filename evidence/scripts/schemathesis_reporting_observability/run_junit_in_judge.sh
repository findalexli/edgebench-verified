#!/bin/bash
# Inside original reporting judge image; /ebv mounted read-only.
cp -r /ebv/reporting_overlay /app/src/schemathesis/reporting
cd /app
for v in correct drops_error unterminated plaintext; do
  for t in orig repaired; do
    out=$(EBV_JUNIT_VARIANT=$v python -m pytest -p no:cacheprovider -q "/ebv/tests_$t/test_02_reporting.py::test_junitxml_writer_context_manager" 2>&1 | tail -1)
    echo "variant=$v tests=$t :: $out"
  done
done
