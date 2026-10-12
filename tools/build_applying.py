#!/usr/bin/env python3
"""Generate APPLYING-FIXES.md: how to apply each repair, with a per-package change table."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
REPAIRS = ROOT / 'repairs'
TASKS = ROOT / 'tasks' if (ROOT / 'tasks').is_dir() else ROOT.parent / 'tasks'


def changes(pkg):
    tid = pkg.name[:-3]
    orig = json.loads((TASKS / f'{tid}.json').read_text())
    new = json.loads((pkg / 'task.json.in').read_text())
    out = []
    if (pkg / 'Dockerfile').exists() and orig['judge'].get('image_tag') != new['judge'].get('image_tag'):
        out.append('grader')
    if orig['work'].get('image_tag') != new['work'].get('image_tag'):
        out.append("agent's starting files")
    if orig['work'].get('agent_query') != new['work'].get('agent_query'):
        out.append('task instructions')
    if orig['judge'].get('rescale') != new['judge'].get('rescale'):
        out.append('score scale')
    other = {k for k in set(orig) | set(new) if k not in ('work', 'judge') and orig.get(k) != new.get(k)}
    other |= {f'judge.{k}' for k in set(orig['judge']) | set(new['judge'])
              if k not in ('image_tag', 'rescale') and orig['judge'].get(k) != new['judge'].get(k)}
    out += sorted(other)
    return tid, out, new['judge'].get('image_tag'), new['work'].get('image_tag')


def main():
    decisions = {r['task_id']: r for r in json.loads((ROOT / 'data/decisions.json').read_text())}
    names = task_names()
    rows = []
    for pkg in sorted(REPAIRS.glob('*-v2')):
        tid, ch, jt, wt = changes(pkg)
        status = 'fixed and tested' if decisions[tid]['proposed'] == 'repair-v2' else 'partial fix; task removed'
        rows.append(f"| [{names[tid]}](repairs/{pkg.name}/README.md) | {', '.join(ch) or '—'} | `{jt}` | {status} |")
    doc = f"""# Applying the fixes

Each fixed task is published as a new version of the original EdgeBench task, in EdgeBench's own
format. Nothing in the original release is modified: the original task definitions stay in `tasks/`,
and the original software images are used unchanged as the base of each fix.

## What a fix contains

Each fix lives in its own folder, `repairs/<task_id>-v2/` ("v2" marks the fixed version).

| File | What it is |
| --- | --- |
| `README.md` | What the fix changes, how it was tested, and its limits |
| `repair.patch` | The change itself, as a standard diff against the original files |
| `materialize.sh` | Rebuilds the changed files: downloads the original public image, extracts the original files, applies the patch, and checks every result against the fingerprints in `source-lock.json` |
| `Dockerfile` (and `Dockerfile.work` when the agent's starting files change) | Builds the fixed image on top of the exact original image, adding only the changed files |
| `task.json.in` | The fixed task definition: a copy of `tasks/<task_id>.json` with only the necessary fields changed |
| `paired/` | The side-by-side test: the same test submissions graded by the original and the fixed grader |

Only the patch is distributed, never copies of the original files, so the fixes can be published
without redistributing EdgeBench's images.

## Build and use one fix

```bash
cd repairs/<task_id>-v2
./materialize.sh                     # regenerate the changed files from the public image
TAG=$(python3 -c "import json;print(json.load(open('task.json.in'))['judge']['image_tag'])")
docker build -t edgebench.judge.<task_id>:$TAG .
# if the package has Dockerfile.work, also build edgebench.work.<task_id>:<work image_tag> from it
cp task.json.in ../../tasks/<task_id>.json   # the harness resolves edgebench.judge.<task_id>:<image_tag>
```

EdgeBench's runner finds images by the names `edgebench.judge.<task_id>:<image_tag>` (the grader)
and `edgebench.work.<task_id>:<image_tag>` (the agent's environment), reading the tags from the task
definition. Replacing the task definition is therefore enough; the runner itself does not change.
Maintainers who build images from source can apply `repair.patch` to their source tree instead.
The paths in the patch are the paths inside the image.

## Test a fix yourself

`paired/run.sh` reruns the side-by-side test. The published runs used machines with 8 virtual CPUs
and 8 GiB of memory. Two fixes differ:
- Lean Analysis uses `paired/run_local.sh`, which was run locally.
- OpenRCT2 has no run script, because only its instructions changed and nothing that runs was
  modified.

The results are in each `paired/results.md` and together in [data/paired-results.csv](data/paired-results.csv).
Every fix was accepted only if three things held:
- the test submission that shows the problem is now graded correctly;
- correct test submissions keep their scores, or the change is explained;
- wrong test submissions are still rejected.

## Scores are not comparable across versions

A score from a fixed version cannot be compared with a score from the original task or the original
leaderboard. Regrade submissions with the fixed version rather than mixing the two. Each fix's
README says exactly which submissions' scores change.

## What each fix changes

| Task | What changes | Fixed grader image tag | Status |
| --- | --- | --- | --- |
{chr(10).join(rows)}

Tasks kept with a note need no change. Their notes are in [FINDINGS.md](FINDINGS.md) and on the
case pages.
"""
    (ROOT / 'APPLYING-FIXES.md').write_text(doc)
    print(len(rows), 'packages')


if __name__ == '__main__':
    main()
