# integer_compression_codec v2: score relative to the shipped Varint starter measured in the
# same judge run (instead of the stored baseline_results.json). Only COPY; nothing is installed.
FROM seededge/edgebench.judge.integer_compression_codec@sha256:15dffad066b4bd1e4844b3d3798a605c80df8e83db547998b560c28e28e989ac
COPY files/runner_judge.py /home/workspace/integer-compression-codec/runner_judge.py
COPY files/internal/baseline/starter/ /home/workspace/integer-compression-codec/internal/baseline/starter/
