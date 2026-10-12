#!/usr/bin/env python3
"""Generate APPLYING-FIXES.md: how to apply each repair, with a per-package change table."""
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
REPAIRS = ROOT / 'repairs'
TASKS = ROOT / 'tasks' if (ROOT / 'tasks').is_dir() else ROOT.parent / 'tasks'


def changes(pkg):
    tid = pkg.name[:-3]
    orig = json.loads((TASKS / f'{tid}.json').read_text())
    new = json.loads((pkg / 'task.json.in').read_text())
    out = []
    if (pkg / 'Dockerfile').exists() and orig['judge'].get('image_tag') != new['judge'].get('image_tag'):
        out.append('judge image')
    if orig['work'].get('image_tag') != new['work'].get('image_tag'):
        out.append('solver (work) image')
    if orig['work'].get('agent_query') != new['work'].get('agent_query'):
        out.append('task prompt')
    if orig['judge'].get('rescale') != new['judge'].get('rescale'):
        out.append('score scale')
    other = {k for k in set(orig) | set(new) if k not in ('work', 'judge') and orig.get(k) != new.get(k)}
    other |= {f'judge.{k}' for k in set(orig['judge']) | set(new['judge'])
              if k not in ('image_tag', 'rescale') and orig['judge'].get(k) != new['judge'].get(k)}
    out += sorted(other)
    return tid, out, new['judge'].get('image_tag'), new['work'].get('image_tag')


def main():
    decisions = {r['task_id']: r for r in json.loads((ROOT / 'decisions.json').read_text())}
    rows = []
    for pkg in sorted(REPAIRS.glob('*-v2')):
        tid, ch, jt, wt = changes(pkg)
        status = 'accepted' if decisions[tid]['proposed'] == 'repair-v2' else 'partial (task excluded)'
        rows.append(f"| [{tid}](repairs/{pkg.name}/README.md) | {', '.join(ch) or '—'} | `{jt}` | {status} |")
    doc = f"""# Applying the fixes

Every repair is a new version of an EdgeBench task, packaged in EdgeBench's own format. The
original task definitions in `tasks/` and the original images are never modified. Each package in
`repairs/<task_id>-v2/` contains:

| File | Purpose |
| --- | --- |
| `README.md` | The defect, the exact change, score compatibility and limits |
| `repair.patch` | Our change, as a unified diff against the files in the original image |
| `materialize.sh` | Pulls the pinned original image, extracts the original files, applies the patch, and checks every result against `source-lock.json` |
| `Dockerfile` (and `Dockerfile.work` where the solver image changes) | `FROM` the original image digest, then only the changed files |
| `task.json.in` | The task definition for v2: a copy of `tasks/<task_id>.json` with only the necessary fields changed |
| `paired/` | The paired evaluation: the same inputs scored by the original and the repaired evaluator |

## Apply one repair

```bash
cd repairs/<task_id>-v2
./materialize.sh                     # regenerate the changed files from the public image
TAG=$(python3 -c "import json;print(json.load(open('task.json.in'))['judge']['image_tag'])")
docker build -t edgebench.judge.<task_id>:$TAG .
# if the package has Dockerfile.work, also build edgebench.work.<task_id>:<work image_tag> from it
cp task.json.in ../../tasks/<task_id>.json   # the harness resolves edgebench.judge.<task_id>:<image_tag>
```

The harness looks up images as `edgebench.judge.<task_id>:<image_tag>` and
`edgebench.work.<task_id>:<image_tag>`, taking the tags from the task JSON, so no harness change
is needed. Maintainers who build images from source can apply `repair.patch` to their source tree
instead; the patch paths are the in-image paths.

## Check a repair

`paired/run.sh` reruns the paired evaluation (it was run on 8-vCPU / 8 GiB workers). The
accepted results are in `paired/results.md` and in [paired-results.csv](paired-results.csv):
each repair fixes its trigger, keeps valid controls' scores (or explains the change), and still
rejects invalid controls.

## Score compatibility

v2 scores are **not comparable** with v1 leaderboard scores for the same task. Rerun affected
submissions under v2 rather than mixing versions. Each package README states exactly which
submissions' scores change.

## What each repair changes

| Package | Changes | v2 judge image tag | Status |
| --- | --- | --- | --- |
{chr(10).join(rows)}

Tasks retained with a note need no change; their notes are in [FINDINGS.md](FINDINGS.md) and the
case pages.
"""
    (ROOT / 'APPLYING-FIXES.md').write_text(doc)
    print(len(rows), 'packages')


if __name__ == '__main__':
    main()
