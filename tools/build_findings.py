#!/usr/bin/env python3
"""Generate FINDINGS.md: every task, grouped by its second-review status (data/review.json)."""
import json
import re
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402
import categories as C  # noqa: E402
import review as RV  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

SECTIONS = {
    'confirmed': ('Confirmed', 'A measured score change on the current judge, large enough to matter. Effects are out of 100 unless stated otherwise.'),
    'minor': ('Real, small or unseen', 'The defect exists, but it moves about a point or less, or it is large only when triggered and no real submission we hold triggers it.'),
    'changed-upstream': ('Changed upstream', 'Real on the original release, no longer applies on the `community` branch.'),
    'not-confirmed': ('Not confirmed', "The first audit's claim did not hold up, or we could not settle it. It may still be a true statement about the code; we could not show it moves a good-faith solver's score on the current judge."),
    'no-problem': ('No problem found', 'Nothing to correct. Each of these tasks carries a short usage note on its case page.'),
}
RULE = 'A task is confirmed when the measured change reaches real work: regrading a real submission shows it, or a repeatability failure affects any submission. A defect that is large only on a trigger no real submission we hold uses stays with the others. Graph Node, for example, drops from 90.52-90.57 to 1.95-2.01 if predictions use integer keys, which the task permits.'
LABEL = {'retain': 'Kept as is', 'retain-with-note': 'Kept, with a note', 'repair-v2': 'Fixed', 'exclude': 'Removed'}


def main():
    decisions = json.loads((ROOT / 'data/decisions.json').read_text())
    d = {r['task_id']: r for r in decisions}
    bad = C.validate(decisions)
    assert not bad, bad
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    names = task_names()
    rev = RV.load()
    ids = lambda k: sorted((t for t in d if RV.status(rev, t) == k), key=lambda t: names[t].lower())  # noqa: E731
    def section(k):
        out = [f"### {SECTIONS[k][0]}", "", SECTIONS[k][1], ""]
        if k == 'no-problem':
            out += ["| Task | What we checked |", "| --- | --- |"]
            out += [f"| [{names[t]}](cases/{t}.md) | {plain[t]['headline']} |" for t in ids(k)]
        else:
            out += ["| Task | Why it is here | First audit |", "| --- | --- | --- |"]
            out += [f"| [{names[t]}](cases/{t}.md) | {rev[t]['line']} | {LABEL[d[t]['proposed']]} |" for t in ids(k)]
        return out + [""]
    others = [k for k in RV.KEYS if k != 'confirmed']
    of32 = Counter(RV.status(rev, t) for t in d if d[t]['proposed'] in ('repair-v2', 'exclude'))
    out = ["# Findings", "",
           f"{len(ids('confirmed'))} of the 51 public EdgeBench tasks have a measured score change on the current judge, "
           "large enough to matter. Effects are out of 100 unless stated otherwise. How the review worked is in "
           "[METHOD.md](METHOD.md); the data is in [data/review.json](data/review.json).", "",
           RULE, "",
           "| Task | What goes wrong | Measured effect | Upstream |", "| --- | --- | --- | --- |"]
    out += [f"| [{names[t]}](cases/{t}.md) | {rev[t]['line']} | {rev[t]['effect']} | {rev[t].get('upstream', '')} |" for t in ids('confirmed')]
    out += ["", "<details>", f"<summary>The other {sum(len(ids(k)) for k in others)} tasks, including first-audit claims we withdrew</summary>", "",
            f"Our first audit reported problems in 32 tasks. Of those 32, {of32['confirmed']} are confirmed, {of32['minor']} are real but small or unseen, "
            f"{of32['changed-upstream']} has changed upstream and {of32['not-confirmed']} are not confirmed.", "",
            "| Status | Tasks |", "| --- | ---: |"]
    out += [f"| {SECTIONS[k][0]} | {len(ids(k))} |" for k in RV.KEYS] + ["| **Total** | **51** |", ""]
    for k in others:
        out += section(k)
    out += ["</details>", ""]
    (ROOT / 'FINDINGS.md').write_text('\n'.join(out))
    # the README's table of confirmed tasks
    rows = ["| Task | What goes wrong | Measured effect | Upstream |", "| --- | --- | --- | --- |"]
    rows += [f"| [{names[t]}](cases/{t}.md) | {rev[t]['line']} | {rev[t]['effect']} | {rev[t].get('upstream', '')} |" for t in ids('confirmed')]
    readme = (ROOT / 'README.md').read_text()
    readme, n = re.subn(r'(<!-- confirmed:start -->\n).*?(\n<!-- confirmed:end -->)', lambda m: m.group(1) + '\n'.join(rows) + m.group(2), readme, flags=re.S)
    assert n == 1, 'README markers missing'
    (ROOT / 'README.md').write_text(readme)
    print({k: len(ids(k)) for k in RV.KEYS})


if __name__ == '__main__':
    main()
