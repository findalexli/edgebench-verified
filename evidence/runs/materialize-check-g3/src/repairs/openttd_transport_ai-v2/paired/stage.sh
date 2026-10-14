#!/bin/bash
# Assemble the E2B job directory for run.sh: ./stage.sh <new-dir>
# Copies only our package files (no image files) plus the original task JSON.
set -eu
here=$(cd "$(dirname "$0")" && pwd); pkg=$(dirname "$here"); repo=$(dirname "$(dirname "$pkg")")
d=$1; mkdir -p "$d/pkg" "$d/root/tasks"
cp "$here/run.sh" "$here/diag_log.py" "$d/"; cp -r "$here/variants" "$d/"
cp "$pkg/materialize.sh" "$pkg/repair.patch" "$pkg/source-lock.json" "$pkg/Dockerfile.work" "$pkg/task.json.in" "$d/pkg/"
cp "$repo/tasks/openttd_transport_ai.json" "$d/root/tasks/"
