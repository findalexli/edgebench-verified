# pfr: judge (~12 GB unpacked) and work (~11 GB) images do not fit together on the 21 GB worker,
# and e2b_run.py has no template option, so each image is removed before the next step.
export PRUNE_BETWEEN=1 DELBLOBS=1 PKG_TIMEOUT=3000
