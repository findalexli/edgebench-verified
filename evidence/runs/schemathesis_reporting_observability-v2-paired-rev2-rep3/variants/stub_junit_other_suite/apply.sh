# reviewer's minimal schemathesis.reporting stub overlay; JunitXmlWriter variant other_suite
# (correct junit_xml writer, suite named "api-report" instead of "schemathesis")
export EBV_JUNIT_VARIANT=other_suite
cp -r /job/payload/stub_reporting /app/src/schemathesis/reporting
