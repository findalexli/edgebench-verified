# lean: judge image ~7.65 GB compressed (~33 GB unpacked per the package README) on a 21 GB worker;
# e2b_run.py has no template option. Attempted as committed; images removed between Dockerfiles.
export PRUNE_BETWEEN=1 DELBLOBS=1 PKG_TIMEOUT=3100 EBV_HEAVY_LOCK=/tmp/ebv-heavy.lock
