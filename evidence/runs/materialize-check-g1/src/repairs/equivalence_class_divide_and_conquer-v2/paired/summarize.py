"""Summarize paired logs with the harness parsers. Usage: summ.py <task_json> <log>..."""
import sys, re, json
sys.path.insert(0, __import__('os').environ.get('EBV_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[3]))
from sforge.harness.log_parsers.score_sum import parse_score_sum
from sforge.harness.log_parsers.structured_json import parse_structured_json
from sforge.harness.grading import extract_score
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score
task = json.load(open(sys.argv[1])); spec = parse_rescale_spec(task['judge'].get('rescale'))
for log in sys.argv[2:]:
    s = open(log, errors='replace').read()
    if task['judge']['parser'] == 'score_sum':
        r = parse_score_sum(s)
        raw = extract_score(s)
        ok = sum(x['status'] == 'PASSED' for x in r)
        per = {}
        for m in re.finditer(r'^(T\d_\w+): (\d+)/(\d+)', s, re.M): per[m.group(1).split('_')[0]] = f'{m.group(2)}/{m.group(3)}'
        norm = rescale_score(spec, raw) if spec else min(100, max(0, raw))
        print(f'{log.split("/")[-1]}: raw={raw:g} norm={norm:g} pass_rate={ok}/{len(r)}={ok/len(r):.4f} per_task={per}')
    else:
        o = parse_structured_json(s)
        print(f'{log.split("/")[-1]}: score={o["score"]} valid={o["valid"]} pass_rate={o["pass_rate"]} metrics=' + json.dumps({k: v["raw_score"] for k, v in o["metrics"].items()}))
