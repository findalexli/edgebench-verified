# borden_source_inversion v2 WORK image: documentation-level repair, labels and judge unchanged.
# Adds a solver-visible copy of the judge's forward model and the README section that
# states its convention exactly. Nothing is installed; no hidden file is copied.
# The JUDGE image is unchanged (v1 digest); v2 differs on the judge side only by the
# `rescale` block in task.json.in.
FROM seededge/edgebench.work.borden_source_inversion@sha256:e1ec4b80816e46760c226c902817751e9a905395828b777ce20c563d1843826a
COPY files/README.md /home/workspace/borden_inverse/README.md
COPY files/forward_model.py /home/workspace/borden_inverse/forward_model.py
