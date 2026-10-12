# reviewer's minimal Target 1 overlay (headers.py), http_date_values variant off_by_one_clock
export EBV_DATE_VARIANT=off_by_one_clock
cp /job/payload/headers_overlay.py /app/src/schemathesis/specs/openapi/headers.py
