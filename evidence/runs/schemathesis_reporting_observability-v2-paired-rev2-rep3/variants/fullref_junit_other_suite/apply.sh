cp -r /job/payload/fullref/. /app/   # earlier accepted 30-file reporting implementation + shared-hook plugin.py (scored 1.0 on v1)
# correct variant: the JUnit suite is named "api-report" instead of "schemathesis" (TODO.md names no suite)
python3 - <<'PY'
p='/app/src/schemathesis/reporting/junitxml.py'; s=open(p).read()
old='TestSuite("schemathesis", '; assert s.count(old)==1
open(p,'w').write(s.replace(old,'TestSuite("api-report", '))
PY
