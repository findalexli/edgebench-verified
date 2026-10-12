#!/usr/bin/env python3
"""Refresh the figure block under each case page's outcome line from cases/figures/<task>.json (alt, caption)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
n = 0
for j in sorted((ROOT / 'cases/figures').glob('*.json')):
    page = ROOT / 'cases' / f'{j.stem}.md'
    if not page.exists():
        continue
    cap = json.loads(j.read_text())
    alt = cap['alt'].replace('[', '').replace(']', '')
    s = page.read_text()
    new = f'![{alt}](figures/{j.stem}.svg)\n\n*{cap["caption"]}*'
    s2, k = re.subn(r'!\[[^\]]*\]\(figures/' + re.escape(j.stem) + r'\.svg\)\n\n\*[^\n]*\*', lambda m: new, s)
    assert k == 1, page
    if s2 != s:
        page.write_text(s2); n += 1
print(n, 'case pages refreshed')
