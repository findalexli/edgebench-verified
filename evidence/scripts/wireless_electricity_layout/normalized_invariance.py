"""Check: under score_first/minimize + the task's piecewise_log_min rescale, adding a
compile-failure entry (raw 1e17) to any history never changes the normalized score of
the selected entry, nor the max normalized score over entries.
Usage: python normalized_invariance.py HARNESS_ROOT TASKS_DIR"""
import json, random, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score
from sforge.harness.selection import select_best
judge = json.load(open(Path(sys.argv[2]) / "wireless_electricity_layout.json"))["judge"]
spec = parse_rescale_spec(judge["rescale"]); CE = 1e17
print("rescale", judge["rescale"], "| f(CE) =", rescale_score(spec, CE))
rng = random.Random(1); bad = 0; changed_raw = 0; N = 200000
interesting = [CE, CE * (1 + 1e-12), 6.631007355423963e17, spec.baseline, spec.rank30, spec.rank1, spec.super_anchor, 0.0]
for _ in range(N):
    k = rng.randint(1, 5)
    raws = [rng.choice(interesting) if rng.random() < .3 else 10 ** rng.uniform(13, 19) for _ in range(k)]
    ents = [{"type": "submission", "status": "completed", "round": f"r{i}", "score": r, "pass_rate": 1.0}
            for i, r in enumerate(raws)]
    for pos in range(k + 1):
        withce = ents[:pos] + [{"type": "submission", "status": "completed", "round": "ce", "score": CE, "pass_rate": 0.0}] + ents[pos:]
        a = select_best(ents, "minimize", "score_first"); b = select_best(withce, "minimize", "score_first")
        if rescale_score(spec, a["best_score"]) != rescale_score(spec, b["best_score"]): bad += 1
        if max(rescale_score(spec, r) for r in raws) != max(rescale_score(spec, e["score"]) for e in withce): bad += 1
        changed_raw += a["best_score"] != b["best_score"]
print(f"histories checked={N}; normalized changes={bad}; raw best_score changes={changed_raw}")
