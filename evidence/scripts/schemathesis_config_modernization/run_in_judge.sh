#!/bin/bash
# Usage: run_in_judge.sh  (run inside the original judge image; /ebv mounted read-only)
# Installs the minimal metric overlay into /app and runs the original and the
# proposed-repair Phase 3 test files for each variant.
set -u
cp /ebv/metrics_base.py /app/src/schemathesis/generation/metrics.py
cat >> /app/src/schemathesis/__init__.py <<'PY'

from .generation.metrics import MetricContext, MetricFunction, metric  # EBV overlay
PY
cd /app
for v in identity wrapper no_register; do
  for t in orig repaired; do
    f=/ebv/tests_$t/test_03_metric_system.py
    out=$(EBV_METRIC_VARIANT=$v python -m pytest -p no:cacheprovider "$f" -q 2>&1 | tail -1)
    echo "variant=$v tests=$t :: $out"
  done
done
