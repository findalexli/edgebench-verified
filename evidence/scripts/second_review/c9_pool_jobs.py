#!/usr/bin/env python3
"""Builds evidence/runs/community9-<task>-<suffix>: old (8 cases at once) vs new (min(8, SFORGE_CPUS, cases)) judge, real Opus
archives unchanged, through `sforge eval`, on community @ 1187e2c. Usage: c9_pool_jobs.py <upstream-tree> <spec.json>
spec: {"task":..,"suffix":..,"limit":seconds,"subs":{"alias":"sha10",..},"arms":"<bash>"}"""
import difflib, glob, hashlib, json, os, shutil, sys
tree, spec = sys.argv[1], json.load(open(sys.argv[2]))
T = spec['task']; J = f"evidence/runs/community9-{T}-{spec['suffix']}"
if os.path.exists(J + '/result'): sys.exit('result exists: ' + J)
os.makedirs(J + '/subs', exist_ok=True)
SCRIPT = {'molecular_self_assembly': 'eval_molecules.py', 'apple_incremental_game': 'eval_apple_incremental_game.py', 'grid_turing_robot': 'eval_grid_turing_robot.py', 'triangulation_coloring_optimization': 'eval_triangulation_coloring.py', 'warehouse_forklift_routing': 'eval_warehouse_manager.py'}[T]
rel = f'edgebench/tasks/{T}/judge/{SCRIPT}'; src = open(f'{tree}/{rel}').read()
a = 'max_workers=min(8, len(case_files))'; b = 'max_workers=min(8, int(os.environ.get("SFORGE_CPUS", 4)), len(case_files))'
c = 'max_workers = min(int(os.environ.get("SEBENCH_MOLECULES_WORKERS", "8")), len(case_files))'; d = 'max_workers = min(int(os.environ.get("SEBENCH_MOLECULES_WORKERS", "8")), int(os.environ.get("SFORGE_CPUS", 4)), len(case_files))'
new = src.replace(a, b).replace(c, d); assert new != src
open(J + '/pr.patch', 'w').write(''.join(difflib.unified_diff(src.splitlines(True), new.splitlines(True), 'a/' + rel, 'b/' + rel)))
idx = {}
for f in sorted(glob.glob(f'evidence/runs/claude-opus-{T}*/result/out/sforge-logs/runs/*/{T}/submissions/*/submission.tar.gz')):
    idx.setdefault(hashlib.sha256(open(f, 'rb').read()).hexdigest()[:10], f)
with open(J + '/subs.map', 'w') as m:
    for alias, sha in spec['subs'].items():
        shutil.copy(idx[sha], f'{J}/subs/{alias}.tar.gz'); m.write(f'{alias} {sha} {idx[sha]}\n')
run = open('evidence/scripts/second_review/c9_pool_run.sh').read().replace('@@TASK@@', T).replace('@@LIMIT@@', str(spec['limit'])).replace('@@SCRIPT@@', SCRIPT)
open(J + '/run.sh', 'w').write(run); os.chmod(J + '/run.sh', 0o755)
open(J + '/arms.sh', 'w').write(spec['arms'])
print(J)
