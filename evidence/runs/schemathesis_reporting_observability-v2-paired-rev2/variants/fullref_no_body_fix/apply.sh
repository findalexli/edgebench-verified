cp -r /job/payload/fullref/. /app/   # earlier accepted 30-file reporting implementation + shared-hook plugin.py (scored 1.0 on v1)
# plausibly-wrong mutation: Target 5 fix 2 omitted (BODY not added to the allow-extra-parameters suppression)
python3 - <<'PY'
p='/app/src/schemathesis/generation/coverage.py'; s=open(p).read()
old='                            ParameterLocation.COOKIE,\n                            ParameterLocation.BODY,\n'; assert s.count(old)==1
open(p,'w').write(s.replace(old,'                            ParameterLocation.COOKIE,\n'))
PY
