#!/bin/bash
# Inside original reporting judge image; /ebv read-only. Three implementations of TODO Target 5 req. 2:
#   starter       : unmodified v4.13.0 (body NOT suppressed)               -> wrong (no fix)
#   correct_fix   : add ParameterLocation.BODY to the suppression tuple    -> correct
#   always_suppress: drop the allow_extra_parameters condition entirely    -> wrong (over-suppression)
F=/app/src/schemathesis/generation/coverage.py
cp $F /tmp/coverage.orig.py
cd /app
for v in starter correct_fix always_suppress; do
  cp /tmp/coverage.orig.py $F
  case $v in
    correct_fix) python - "$F" <<'PY'
import sys; p=sys.argv[1]; s=open(p).read()
old="                            ParameterLocation.COOKIE,\n                        ):\n                            continue"
assert s.count(old)==1
s=s.replace(old,"                            ParameterLocation.COOKIE,\n                            ParameterLocation.BODY,\n                        ):\n                            continue"); open(p,"w").write(s)
PY
    ;;
    always_suppress) python - "$F" <<'PY'
import sys; p=sys.argv[1]; s=open(p).read()
old="if not ctx.allow_extra_parameters and ctx.location in ("
assert s.count(old)==1
s=s.replace(old,"if ctx.location in (ParameterLocation.BODY, "); open(p,"w").write(s)
PY
    ;;
  esac
  find /app/src -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  for t in orig repaired; do
    res=$(python -m pytest -p no:cacheprovider -q -rA /ebv/tests_$t/test_05_email_coverage.py -k "unexpected_parameters" 2>&1 | grep -E "^(PASSED|FAILED|ERROR) " | sed -E "s#^(PASSED|FAILED|ERROR) .*::(.*)#\2=\1#" | tr '\n' ' ')
    echo "impl=$v tests=$t :: $res"
  done
done
cp /tmp/coverage.orig.py $F
