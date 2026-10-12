#!/bin/bash
# Inside original reporting judge image (unmodified v4.13.0 starter), /ebv mounted read-only.
cd /app
echo "--- original coverage tests on UNMODIFIED starter (body fix absent) ---"
python -m pytest -p no:cacheprovider -q "/ebv/tests_orig/test_05_email_coverage.py::test_body_unexpected_parameters_control_deny" "/ebv/tests_orig/test_05_email_coverage.py::test_query_unexpected_parameters_control_deny" 2>&1 | tail -3
echo "--- diagnostic: what cover_schema_iter actually yields on the starter ---"
python - <<'PY'
from schemathesis.generation.coverage import cover_schema_iter, CoverageContext, CoverageScenario, GeneratedValue as CovGV
from schemathesis.specs.openapi.negative import GeneratedValue as NegGV
from schemathesis.core.parameters import ParameterLocation
from schemathesis.generation.modes import GenerationMode
from schemathesis.specs.openapi.formats import get_default_format_strategies
import jsonschema_rs
schema = {"type": "object", "properties": {"token": {"type": "string"}}, "required": ["token"], "additionalProperties": False}
for loc in (ParameterLocation.BODY, ParameterLocation.QUERY):
    for allow in (False, True):
        ctx = CoverageContext(root_schema={}, location=loc, media_type=None, generation_modes=[GenerationMode.NEGATIVE],
            is_required=True, custom_formats=get_default_format_strategies(), validator_cls=jsonschema_rs.Draft4Validator,
            allow_extra_parameters=allow)
        vals = list(cover_schema_iter(ctx, schema))
        n_neg = sum(isinstance(v, NegGV) for v in vals); n_cov = sum(isinstance(v, CovGV) for v in vals)
        unexpected = CoverageScenario.OBJECT_UNEXPECTED_PROPERTIES in {v.scenario for v in vals if isinstance(v, CovGV)}
        print(f"loc={loc.name} allow={allow}: yielded={len(vals)} isinstance(negative.GV)={n_neg} isinstance(coverage.GV)={n_cov} OBJECT_UNEXPECTED_PROPERTIES_present={unexpected}")
PY
