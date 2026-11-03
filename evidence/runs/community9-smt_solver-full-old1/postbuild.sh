# Reuse the downloaded blob for the second build.
if [ "$t" = base ]; then mkdir -p new/edgebench/tasks/$T/judge/blobs; cp base/edgebench/tasks/$T/judge/blobs/* new/edgebench/tasks/$T/judge/blobs/; fi
