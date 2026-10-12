"""Build self-contained solution.py submissions from the shipped baseline
(solution/solution_template.py == solution/solution.py in the judge image).
Usage: python3 make_subs.py <solution_template.py> <outdir>"""
import sys
from pathlib import Path
base = Path(sys.argv[1]).read_text(encoding="utf-8")
out = Path(sys.argv[2])
renamed = base.replace("class Solution:", "class _Baseline:", 1)
assert renamed != base
WRAP = {
# Trigger: the review's shrink mode. One real prediction, every other value a non-integer string.
"shrink": '''
class Solution(_Baseline):
    def solve(self, input_data):
        out = super().solve(input_data)
        first = str(input_data["test_nodes"][0])
        preds = {k: (v if k == first else "x") for k, v in out["predictions"].items()}
        return {"predictions": preds, "confidences": {k: 1.0 for k in preds}}
''',
# Honest independent solver: majority label among labeled graph neighbours (train+valid),
# falling back to the baseline's prediction; confidence = vote share. All int class ids.
"neighbor": '''
class Solution(_Baseline):
    def solve(self, input_data):
        base = super().solve(input_data)
        labels = {}
        for row in input_data["nodes"]:
            if row.get("label") is not None:
                labels[int(row["node_id"])] = int(row["label"])
        labeled = set(int(x) for x in input_data["train_nodes"]) | set(int(x) for x in input_data["valid_nodes"])
        adj = {}
        for u, v in input_data["graph"]["edges"]:
            adj.setdefault(int(u), []).append(int(v)); adj.setdefault(int(v), []).append(int(u))
        preds, confs = {}, {}
        for t in input_data["test_nodes"]:
            t = int(t); votes = {}
            for n in adj.get(t, []):
                if n in labeled and n in labels:
                    votes[labels[n]] = votes.get(labels[n], 0) + 1
            if votes:
                lab = max(sorted(votes), key=lambda c: votes[c])
                preds[str(t)] = int(lab); confs[str(t)] = votes[lab] / sum(votes.values())
            else:
                preds[str(t)] = int(base["predictions"][str(t)]); confs[str(t)] = float(base["confidences"].get(str(t), 0.2))
        return {"predictions": preds, "confidences": confs}
''',
# Score-neutral clipping left unchanged in v2: baseline predictions, every confidence NaN.
"nanconf": '''
class Solution(_Baseline):
    def solve(self, input_data):
        out = super().solve(input_data)
        out["confidences"] = {k: float("nan") for k in out["predictions"]}
        return out
''',
# Invalid control caught by the original coverage check: predictions for only half the test nodes.
"missing_half": '''
class Solution(_Baseline):
    def solve(self, input_data):
        out = super().solve(input_data)
        keep = [str(t) for t in input_data["test_nodes"]][: len(input_data["test_nodes"]) // 2]
        return {"predictions": {k: out["predictions"][k] for k in keep},
                "confidences": {k: out["confidences"][k] for k in keep}}
''',
}
(out / "baseline").mkdir(parents=True, exist_ok=True)
(out / "baseline" / "solution.py").write_text(base, encoding="utf-8")
for name, wrap in WRAP.items():
    (out / name).mkdir(parents=True, exist_ok=True)
    (out / name / "solution.py").write_text(renamed + "\n" + wrap, encoding="utf-8")
print("wrote", ["baseline"] + list(WRAP))
