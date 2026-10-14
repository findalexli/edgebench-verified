#!/usr/bin/env python3
"""Refresh the figure block under each case page's outcome line.

English pages (cases/<task>.md) take alt and caption from cases/figures/<task>.json. Chinese pages
(cases/zh/<task>.md) take them from tools/i18n/figures.zh.json, for entries written as {"caption", "alt"}.
The block is the figure line, a blank line, and the italic caption line.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def block(stem, alt, caption):
    alt = alt.replace('[', '').replace(']', '')
    return f'![{alt}](figures/{stem}.svg)\n\n*{caption}*'


def refresh(page, stem, alt, caption):
    s = page.read_text()
    new = block(stem, alt, caption)
    # the alt text runs to the end of its line; older alt text may contain brackets
    s2, k = re.subn(r'!\[[^\n]*\]\(figures/' + re.escape(stem) + r'\.svg\)\n\n\*[^\n]*\*', lambda m: new, s)
    assert k == 1, page
    if s2 != s:
        page.write_text(s2)
        return 1
    return 0


n = 0
for j in sorted((ROOT / 'cases/figures').glob('*.json')):
    page = ROOT / 'cases' / f'{j.stem}.md'
    if page.exists():
        cap = json.loads(j.read_text())
        n += refresh(page, j.stem, cap['alt'], cap['caption'])
zh = json.loads((ROOT / 'tools/i18n/figures.zh.json').read_text())
nz = 0
for stem, v in sorted(zh.items()):
    page = ROOT / 'cases' / 'zh' / f'{stem}.md'
    if isinstance(v, dict) and v.get('alt') and page.exists():
        nz += refresh(page, stem, v['alt'], v['caption'])
print(n, 'case pages refreshed;', nz, 'Chinese case pages refreshed')
