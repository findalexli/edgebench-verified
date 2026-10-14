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
    wt = new['work'].get('image_tag') if orig['work'].get('image_tag') != new['work'].get('image_tag') else None
    return tid, out, new['judge'].get('image_tag'), wt


def main():
    decisions = {r['task_id']: r for r in json.loads((ROOT / 'data/decisions.json').read_text())}
    names = task_names()
    rows = []
    for pkg in sorted(REPAIRS.glob('*-v2')):
        tid, ch, jt, wt = changes(pkg)
        status = decisions[tid].get('validation_status', 'Historical paired scope only; see the case page and package limits')
        if decisions[tid]['proposed'] != 'repair-v2':
            status = 'partial fix; task removed; ' + status
        if tid == 'warehouse_forklift_routing':
            ch.append('[host final-drain overlay](repairs/harness-final-drain-v1/README.md)')
        rows.append(f"| [{names[tid]}](repairs/{pkg.name}/README.md) | {', '.join(ch) or '—'} | `{jt}` | {f'`{wt}`' if wt else 'unchanged'} | {status} |")
    doc = f"""# Applying the fixes

Each repair package defines a new version of an original EdgeBench task, in EdgeBench's own
format. The packages are validated to different depths, and the status table and each package's
limits are the authoritative record. The original release is left as it is. Its task definitions stay
in `tasks/`, and each fix uses the original software images, unchanged, as its base.

## What a fix contains

Each fix lives in its own folder, `repairs/<task_id>-v2/` ("v2" marks the fixed version).

| File | What it is |
| --- | --- |
| `README.md` | What the fix changes, how it was tested, and its limits |
| `repair.patch` | The change itself, as a standard diff against the original files |
| `materialize.sh` | Rebuilds the changed files: downloads the original public image, extracts the original files, applies the patch, and checks every result against the fingerprints in `source-lock.json` |
| `Dockerfile` (and `Dockerfile.work` when the agent's starting files change) | Builds the fixed image on top of the exact original image, adding only the changed files |
| `task.json.in` | The fixed task definition: a copy of `tasks/<task_id>.json` with only the necessary fields changed |
| `paired/` | The side-by-side test, in which the original and the fixed grader grade the same test submissions |

The packages contain only the patch and no copies of the original files, so we can publish the fixes
without redistributing EdgeBench's images.

## Build and use one fix

```bash
cd repairs/<task_id>-v2
./materialize.sh                     # regenerate the changed files from the public image
TAG=$(python3 -c "import json;print(json.load(open('task.json.in'))['judge']['image_tag'])")
docker build -t edgebench.judge.<task_id>:$TAG .
# if the package has Dockerfile.work, also build edgebench.work.<task_id>:<work image_tag> from it
# Arc Compiler Runtime and Borden Source Inversion change only the agent's environment: their Dockerfile
# builds edgebench.work.<task_id>:<work image_tag> (Arc: docker build -f Dockerfile files)
cp task.json.in <your EdgeBench checkout>/tasks/<task_id>.json   # not this repository's tasks/, which is locked to the original
```

EdgeBench's runner finds images by the names `edgebench.judge.<task_id>:<image_tag>` (the grader)
and `edgebench.work.<task_id>:<image_tag>` (the agent's environment), reading the tags from the task
definition. These tags name images you build locally; we publish no fixed image to a registry.
Warehouse also needs the host-side final-drain overlay described below. Replacing only its task
definition and grader image leaves the 900-second defect in final-result collection.
Maintainers who build images from source can apply `repair.patch` to their source tree instead.
The paths in the patch are the paths inside the image.

## Warehouse host-side integration

The [final-drain overlay](repairs/harness-final-drain-v1/README.md) is separate from the Warehouse
judge-image patch. It polls until every recorded job is in a terminal state, waits for a bounded
time that takes the queue into account, and reports a failure instead of returning an incomplete
final score. Materialize it into a new source directory and run the harness from that directory;
this repository's locked `sforge/` mirror stays unchanged. Its paired deterministic tests exercise
the real patched drain and result assembly, including a long evaluation and a serial queue (a
conservative model, since the upstream judge server grades submissions concurrently). We have not
verified full Docker/Kubernetes integration. The overlay changes final-result collection for every
task run through the materialized tree. It can wait up to `300 + n·(eval_timeout + 300)` seconds for
`n` pending submissions and keeps the work sandbox allocated meanwhile, so use it for Warehouse runs
or accept that change.

## Test a fix yourself

`paired/run.sh` reruns the side-by-side test. Most published runs used E2B cloud sandboxes with 8
virtual CPUs and 8 GiB of memory, with the grader limited to the CPU count each case page states
(1 to 8). These fixes use other scripts:
- Lean Analysis uses `paired/run_local.sh`, which we ran on a local host with 16 CPUs and 15 GB.
- OpenRCT2 has no run script, because its fix changes only the instructions and nothing that runs.
- Git in Zig uses `paired/run_gates.sh` and `paired/run_oracle.sh`.
- PFR Formalization uses `paired/build_v2.sh` and `paired/grade_variants.sh`.
- Rust Multicrate uses the templates `paired/run-paired.sh.in` and `paired/run-failfast.sh.in`.
- Triangulation and Warehouse Routing also have `paired/run-cpu4.sh` for the 4-CPU tests.
- The separate host overlay uses `python3 repairs/harness-final-drain-v1/test_drain.py` from the repository root (deterministic component tests, no cloud calls).

Each package's results are in its `paired/results.md`, and all of them are in
[data/paired-results.csv](data/paired-results.csv). The status table separates demonstrated controls
from incomplete release validation, component tests and documentation-only changes. The acceptance
criteria are:
- the test submission that shows the problem is now graded correctly;
- correct test submissions keep their scores, or the change is explained;
- wrong test submissions are still rejected.

## Scores are not comparable across versions

A score from a fixed version cannot be compared with a score from the original task or the original
leaderboard. Regrade submissions with the fixed version instead of mixing the two. Each fix's
README says which submissions' scores change.

## What each fix changes

| Task | What changes | Fixed grader image tag | Fixed work image tag | Status |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}

For each task, the tag with the highest suffix (`v2.1` or `v2.2`) replaces every earlier one (`v2`,
and `v2.1` where a `v2.2` exists). The earlier tags' grader or work images differ from the current
fix, so rebuild any image built from an earlier package. Where the fix changes the agent's
environment, the work image column gives its tag; "unchanged" means the fix uses the original work
image and tag.

Tasks kept with a note need no change. Their notes are in [FINDINGS.md](FINDINGS.md) and on the
case pages.
"""
    (ROOT / 'APPLYING-FIXES.md').write_text(doc)
    print(len(rows), 'packages')


if __name__ == '__main__':
    main()
