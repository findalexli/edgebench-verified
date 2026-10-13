# EdgeBench Verified schemathesis_reporting_observability v2: replaces only the judge test files listed below.
FROM --platform=linux/amd64 seededge/edgebench.judge.schemathesis_reporting_observability@sha256:b1e16633e75b2a21ef805961bb190c0a71afb75225986997340185eb7d67fc54
COPY files/tests/test.sh /tests/test.sh
COPY files/tests/test_02_reporting.py /tests/test_02_reporting.py
COPY files/tests/test_05_email_coverage.py /tests/test_05_email_coverage.py
