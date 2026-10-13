# Derived (not executed) fixed-grader score for each archived lean_analysis_proofs submission:
# the v2 grader keeps the v1 per-target verdicts for the 2338 user-facing targets it still scores and
# drops 560 compiler-generated + 3 placeholder targets (checked on the paired controls: v1 PASSED set
# intersected with the v2 target set equals the v2 PASSED set). Outputs counts only.
import json, sys, glob, os
V2 = set(open('/job/v2_targets.txt').read().split())
rows = []
for f in sorted(glob.glob('/tmp/r/*/lean_analysis_proofs/submissions/*/test_output.txt')):
    r = f.split('/')[-2]; s = open(f, errors='replace').read()
    try:
        a = s.index('>>>>> Start Structured Result') + 29; b = s.index('>>>>> End Structured Result')
        d = json.loads(s[a:b])
    except Exception as e:
        rows.append({'round': r, 'error': type(e).__name__}); continue
    det = d.get('details') or []
    p1 = {x['name'] for x in det if x.get('status') == 'PASSED'}
    names = {x['name'] for x in det}
    rows.append({'round': r, 'v1_valid': d.get('valid'), 'v1_score': d.get('score'), 'v1_summary': d.get('summary'),
                 'v1_targets': len(names), 'v1_passed': len(p1), 'v2_targets_present': len(names & V2),
                 'v2_passed_derived': len(p1 & V2), 'v2_score_derived': len(p1 & V2) / len(V2),
                 'v1_passed_dropped_in_v2': len(p1 - V2)})
json.dump(rows, open('/job/out/lean_derived.json', 'w'), indent=1)
