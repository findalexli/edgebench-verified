"""Problem categories of the tasks with a problem (fixed or removed), read from data/decisions.json.

Each such task has one primary category (`problem_category`) and optional secondary ones
(`secondary_problem_categories`). Names and plain explanations are UI strings in tools/i18n/<lang>.json
(`pcat.<key>`, `pcat.<key>.short`, `pcat.<key>.blurb`).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = ['engineering', 'grader_logic', 'instruction_mismatch', 'scale_selection']
PROBLEM = ('repair-v2', 'exclude')


def primary(r):
    return r.get('problem_category')


def secondary(r):
    return list(r.get('secondary_problem_categories') or [])


def validate(decisions):
    """Return a list of problems with the category fields (empty when they are consistent)."""
    out = []
    for r in decisions:
        t, p, s = r['task_id'], primary(r), secondary(r)
        if r['proposed'] in PROBLEM:
            if p not in KEYS:
                out.append(f'{t}: primary category {p!r} is not one of {KEYS}')
            if any(k not in KEYS for k in s) or len(set(s)) != len(s) or p in s:
                out.append(f'{t}: secondary categories {s!r} invalid')
        elif 'problem_category' in r or 'secondary_problem_categories' in r:
            out.append(f'{t}: kept task carries a problem category')
    return out


def by_primary(decisions):
    return {k: sorted(r['task_id'] for r in decisions if primary(r) == k) for k in KEYS}


def by_secondary(decisions):
    return {k: sorted(r['task_id'] for r in decisions if k in secondary(r)) for k in KEYS}


def en_strings():
    return json.loads((ROOT / 'tools' / 'i18n' / 'en.json').read_text())
