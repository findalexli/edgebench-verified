#!/usr/bin/env python3
"""Refresh the figure block under each case page's outcome line.

English pages (cases/<task>.md) take alt and caption from cases/figures/<task>.json and link
figures/<task>.svg. Chinese pages (cases/zh/<task>.md) take them from tools/i18n/figures.zh.json, for entries
written as {"caption", "alt"}, and link the Chinese figure, ../figures/zh/<task>.svg (the English
../figures/<task>.svg where no Chinese one exists), so the image also shows on GitHub.
The block is the figure line, a blank line, and the italic caption line.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def block(href, alt, caption):
    # square brackets would end the Markdown alt text early; keep their meaning with parentheses
    alt = alt.replace('[', '(').replace(']', ')')
    return f'![{alt}]({href})\n\n*{caption}*'


def refresh(page, stem, alt, caption, href):
    s = page.read_text()
    new = block(href, alt, caption)
    # the alt text runs to the end of its line; older alt text may contain brackets; older Chinese pages
    # linked figures/<task>.svg
    s2, k = re.subn(r'!\[[^\n]*\]\((?:\.\./)?figures/(?:zh/)?' + re.escape(stem) + r'\.svg\)\n\n\*[^\n]*\*',
                    lambda m: new, s)
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
        n += refresh(page, j.stem, cap['alt'], cap['caption'], f'figures/{j.stem}.svg')
zh = json.loads((ROOT / 'tools/i18n/figures.zh.json').read_text())
nz = 0
for stem, v in sorted(zh.items()):
    page = ROOT / 'cases' / 'zh' / f'{stem}.md'
    if isinstance(v, dict) and v.get('alt') and page.exists():
        zfig = ROOT / 'cases/figures/zh' / f'{stem}.svg'
        nz += refresh(page, stem, v['alt'], v['caption'], f'../figures/zh/{stem}.svg' if zfig.exists() else f'../figures/{stem}.svg')
# Chinese pages whose figure has no translated alt text keep their own block; only the link is corrected.
for page in sorted((ROOT / 'cases' / 'zh').glob('*.md')):
    stem = page.stem
    zfig = ROOT / 'cases/figures/zh' / f'{stem}.svg'
    href = f'../figures/zh/{stem}.svg' if zfig.exists() else f'../figures/{stem}.svg'
    t = page.read_text()
    t2 = re.sub(r'(!\[[^\n]*\]\()(?:\.\./)?figures/(?:zh/)?' + re.escape(stem) + r'\.svg\)', lambda m: m.group(1) + href + ')', t)
    if t2 != t:
        page.write_text(t2)
        nz += 1
print(n, 'case pages refreshed;', nz, 'Chinese case pages refreshed')
