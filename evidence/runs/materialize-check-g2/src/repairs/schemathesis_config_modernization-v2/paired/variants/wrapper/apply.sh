# reviewer's minimal Target 3 overlay (scripts/schemathesis_config_modernization/metrics_base.py), variant wrapper
export EBV_METRIC_VARIANT=wrapper
cp /job/payload/metrics_base.py /app/src/schemathesis/generation/metrics.py
printf '\nfrom .generation.metrics import MetricContext, MetricFunction, metric  # EBV overlay\n' >> /app/src/schemathesis/__init__.py
