cp -r /job/payload/fullref/. /app/   # earlier accepted 30-file reporting implementation + shared-hook plugin.py (scored 1.0 on v1)
# plausibly-wrong mutation: record_error creates the testcase but never attaches the <error> element
python3 - <<'PY'
p='/app/src/schemathesis/reporting/junitxml.py'; s=open(p).read()
old='self._get_or_create(label).add_error_info(output=message)'; assert s.count(old)==1
open(p,'w').write(s.replace(old,'self._get_or_create(label)'))
PY
