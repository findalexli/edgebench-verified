cp -r /job/payload/fullref/. /app/   # earlier accepted 30-file reporting implementation + shared-hook plugin.py (scored 1.0 on v1)
# plausibly-wrong mutation: suppression ignores allow_extra_parameters (always suppresses unexpected properties)
python3 - <<'PY'
p='/app/src/schemathesis/generation/coverage.py'; s=open(p).read()
old='if not ctx.allow_extra_parameters and ctx.location in ('; assert s.count(old)==1
open(p,'w').write(s.replace(old,'if ctx.location in ('))
PY
