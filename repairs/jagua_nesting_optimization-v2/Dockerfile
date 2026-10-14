# jagua_nesting_optimization v2: the scorer's overlap test becomes an interior-intersection
# area test (area > 1e-6 x smaller item area), and allowed_orientations is enforced
# (within 1e-3 deg, v2.1; the superseded v2 used 1e-6 deg, below f32 angle resolution).
# Only jagua_task_scorer/evaluate.py changes; reference checkout, assets and work image unchanged.
FROM --platform=linux/amd64 seededge/edgebench.judge.jagua_nesting_optimization@sha256:4f029bf7c86d4762ecb7f183b6e1a016fcf8b705ac0efe28aed8f5e9e5208466
COPY files/home/workspace/jagua_task_scorer/evaluate.py /home/workspace/jagua_task_scorer/evaluate.py
