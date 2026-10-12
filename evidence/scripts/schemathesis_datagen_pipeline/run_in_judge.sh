#!/bin/bash
# Run inside the original datagen judge image with this directory mounted at /ebv (read-only).
set -u
cp /ebv/headers_overlay.py /app/src/schemathesis/specs/openapi/headers.py
cd /app
for v in correct independent_fields off_by_one_clock garbage_shape rfc850; do
  for t in orig repaired; do
    out=$(EBV_DATE_VARIANT=$v python -m pytest -p no:cacheprovider /ebv/tests_$t/test_01_header_strategies.py -q 2>&1 | tail -1)
    echo "variant=$v tests=$t :: $out"
  done
done
# Show sample draws per variant, and repaired-predicate verdicts on them.
python - <<'PY'
import os, sys, importlib, re, calendar
sys.path.insert(0, "/ebv/tests_repaired")
for v in ["correct", "independent_fields", "off_by_one_clock", "garbage_shape"]:
    os.environ["EBV_DATE_VARIANT"] = v
    import schemathesis.specs.openapi.headers as h
    importlib.reload(h)
    from hypothesis import given, settings, HealthCheck
    seen = []
    @given(h.http_date_values())
    @settings(max_examples=50, database=None, derandomize=True)
    def f(x): seen.append(x)
    f()
    orig = re.compile(r"^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$")
    import test_01_header_strategies as rep
    o = sum(bool(orig.match(x)) for x in seen); r = sum(bool(rep.is_imf_fixdate(x)) for x in seen)
    bad = [x for x in seen if not rep.is_imf_fixdate(x)][:3]
    print(f"draws variant={v}: n={len(seen)} orig_accepts={o} repaired_accepts={r} rejected_examples={bad}")
PY
