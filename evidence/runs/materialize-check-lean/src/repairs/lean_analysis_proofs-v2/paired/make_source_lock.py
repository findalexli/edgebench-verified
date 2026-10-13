#!/usr/bin/env python3
"""Write source-lock.json (sha256 of original files, replacement files, inputs) for this package."""
import hashlib, json, tarfile
from pathlib import Path
P = Path(__file__).resolve().parent.parent
R = P.parent.parent.parent
h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
tar = P / 'files/judge/v2-build-artifacts.tar'
members = {}
with tarfile.open(tar) as t:
    for m in t.getmembers():
        if m.isfile():
            members['/' + m.name] = hashlib.sha256(t.extractfile(m).read()).hexdigest()
lock = {
  'task_id': 'lean_analysis_proofs',
  'original_task_json': {'path': 'tasks/lean_analysis_proofs.json', 'sha256': h(R / 'tasks/lean_analysis_proofs.json')},
  'original_judge_image': 'seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b',
  'original_work_image': 'seededge/edgebench.work.lean_analysis_proofs@sha256:5b67e0c53a75916896eceb86580a3a1c8e93614f29a7f26418c1f38d445e5d1a',
  'work_image_local': False,
  'original_files_in_judge_image': {
    '/home/workspace/judge/se-bmk-intern/eval_lean.py': h(P / 'orig/eval_lean.py'),
    '/home/workspace/judge/se-bmk-intern/analysis/Analysis/Section_11_2.lean': h(P / 'orig/Section_11_2.lean'),
    '/home/workspace/judge/se-bmk-intern/analysis/Analysis/Section_11_3.lean': h(P / 'orig/Section_11_3.lean'),
  },
  'unchanged_grader_helper': {'/home/workspace/judge/se-bmk-intern/analysis/ListDeclAxiom.lean': 'af482b7af56a231f1b18400ecb7922fa96016bb9b5407f81526c822f677dfdf1'},
  'replacement_files': {str(p.relative_to(P)): h(p) for p in sorted((P / 'files').rglob('*')) if p.is_file()},
  'artifact_tar_members': members,
  'paired_inputs': {str(p.relative_to(P)): h(p) for p in sorted((P / 'paired/variants').glob('*.lean')) + sorted((P / 'paired/lean').glob('*.lean'))},
  'baseline_listings': {k: h(P / 'paired/out' / k) for k in ('v1-listing.txt', 'v2-listing.txt')},
  'other': {'repair.patch': h(P / 'repair.patch'), 'Dockerfile': h(P / 'Dockerfile'), 'Dockerfile.work': h(P / 'Dockerfile.work'), 'task.json.in': h(P / 'task.json.in')},
}
(P / 'source-lock.json').write_text(json.dumps(lock, indent=2) + '\n')
print('ok', len(members))
