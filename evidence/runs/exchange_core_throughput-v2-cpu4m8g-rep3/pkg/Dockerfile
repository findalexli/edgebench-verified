# exchange_core_throughput v2: correctness gate (shipped ITFeesExchangeBasic + ITExchangeCoreIntegrationRejectionBasic
# must pass before the timed test is scored) and the missing surefire JUnit-platform provider pre-seeded in ~/.m2
# so the judge runs with --network none. Only COPY; nothing is installed or fetched.
FROM seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d
COPY files/eval_exchange_core.py /tmp/eval_exchange_core.py
COPY files/m2/repository/ /root/.m2/repository/
