"""The second review of the findings: the status of each task (data/review.json), and a check that every number
written there appears in the saved evidence for that task (evidence/reviews/second-review/)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / 'evidence' / 'reviews' / 'second-review'
KEYS = ['confirmed', 'minor', 'changed-upstream', 'not-confirmed', 'no-problem']
LABELS = {'confirmed': 'Confirmed', 'minor': 'Real, small or unseen', 'changed-upstream': 'Changed upstream',
          'not-confirmed': 'Not confirmed', 'no-problem': 'No problem found'}
EVIDENCE = {'juliet_vulnerability_analyzer': ['pr-evidence/juliet-issue-39.md'],
            'vibrating_path_graph_coloring': ['pr-evidence/vibrating-issue-40.md'],
            'warehouse_forklift_routing': ['pr-evidence/warehouse-pr-38.md'],
            'graph_node_classification': ['pr-evidence/graph-pr-37.md'],
            'dcss_dungeon_ai': ['container/dcss_upstream_notes.json'],
            'pfr_formalization': ['human/pfr_formalization.md'],
            'order_addition_permutation_optimization': ['../../../data/headline.json']}
UPSTREAM_ZH = {
    'Not yet reported.': '尚未向上游报告。',
    "Listed in upstream's known issues.": '已列入上游的已知问题。',
    'Reported: issue #39 and PR #35 (the `infer` part).': '已报告：issue #39 和 PR #35（`infer` 部分）。',
    'Reported: issue #40 and PR #36.': '已报告：issue #40 和 PR #36。',
    'Same mechanism as PR #36; not reported separately.': '与 PR #36 机制相同，未单独报告。',
    "Listed in upstream's known issues. Whether to change the cap, the scale or both is the maintainers' call.": '已列入上游的已知问题。是改上限、改刻度还是两者都改，要由维护者决定。',
    "Not yet reported. Choosing a fix means choosing a new scale, which is the maintainers' call.": '尚未向上游报告。选择修复方案就是选择新的刻度，这要由维护者决定。',
    "The short run is listed in upstream's known issues; issue #12 raises a separate question about this task's scale.": '运行时间过短已列入上游的已知问题；issue #12 就这个任务的刻度提出了另一个问题。',
    'Draft PR #38 and issue #47, closed: no real submission found that loses an input to the limit.': '草稿 PR #38 和 issue #47 已关闭：没有找到因这个时限丢掉输入的真实提交。',
    'Draft PR #37 and issue #46, closed: no real submission found that uses integer keys.': '草稿 PR #37 和 issue #46 已关闭：没有找到使用整数键的真实提交。',
    'Draft PR #41 and issue #44, closed: no solver shown scored wrongly at the official 4 CPUs.': '草稿 PR #41 和 issue #44 已关闭：没有证明有解法在官方的 4 个 CPU 上被评错。',
    'Reported by someone else: issue #31.': '已由他人报告：issue #31。',
}


def relink(doc):
    """Links in a document under first-audit/ that point back to the repository root."""
    return re.sub(r'\]\((?=(?:cases|data|repairs|evidence|tools|tasks|sforge|site)/|FINDINGS\.md|METHOD\.md|README\.md)', '](../', doc)


def load():
    """{task_id: review entry}; tasks not listed in data/review.json had no problem confirmed or claimed."""
    return {r['task_id']: r for r in json.loads((ROOT / 'data/review.json').read_text())}


def status(rev, tid):
    return rev[tid]['status'] if tid in rev else 'no-problem'


def _numbers(text):
    return [float(x) for x in re.findall(r'(?<![\w.])\d+(?:\.\d+)?', text)]


def unsupported(entry):
    """Numbers with a decimal point in an entry's English text that no saved evidence for the task contains."""
    tid = entry['task_id']
    text = ''
    for f in [f'container/{tid}.json', *EVIDENCE.get(tid, [])]:
        if (EV / f).exists():
            text += (EV / f).read_text()
    text += ''.join(json.dumps(c) for c in json.loads((EV / 'astra/claims.json').read_text()) if c['task'] == tid)
    have = _numbers(text)
    out = []
    for field in ('line', 'effect'):
        for m in re.findall(r'(?<![\w.])\d+\.\d+', entry.get(field, '')):
            d = len(m.split('.')[1])
            if not any(abs(round(x, d) - float(m)) < 10 ** -d / 2 or abs(x - float(m)) <= 0.5 * 10 ** -d for x in have):
                out.append(f'{tid}: {m} in {field}')
    return out


def text(entry, field, code):
    """An entry's field in the language `code`, falling back to English."""
    if field == 'upstream':
        v = entry.get('upstream', '')
        return UPSTREAM_ZH[v] if code == 'zh' and v else v
    return entry.get(f'{field}_zh', entry.get(field, '')) if code == 'zh' else entry.get(field, '')


def banner(entry, zh=False):
    """The line placed at the top of a case page."""
    label = {'confirmed': ('Confirmed', '已确认'), 'minor': ('Real, small or unseen', '存在，但影响小或未见'),
             'changed-upstream': ('Changed upstream', '上游已改变'), 'not-confirmed': ('Not confirmed', '未确认')}[entry['status']][zh]
    if zh:
        return f"**第二轮复核（2026 年 11 月）：{label}。** {text(entry, 'line', 'zh')} {text(entry, 'effect', 'zh')} 下文是第一轮审计的原始记录。".replace('  ', ' ')
    return f"**Second review (November 2026): {label}.** {entry['line']} {entry.get('effect', '')} The text below is the first audit's record.".replace('  ', ' ')


MARK = '**Second review (November 2026):', '**第二轮复核（2026 年 11 月）：'


def write_banners():
    """Put each reviewed task's status line right under the title of its case page, in both languages."""
    for tid, e in load().items():
        for f, zh in ((ROOT / 'cases' / f'{tid}.md', False), (ROOT / 'cases' / 'zh' / f'{tid}.md', True)):
            if not f.exists():
                continue
            lines = [x for x in f.read_text().split('\n')]
            if len(lines) > 2 and lines[2].startswith(MARK):
                del lines[2:4]
            lines[2:2] = [banner(e, zh), '']
            f.write_text('\n'.join(lines))


if __name__ == '__main__':
    write_banners()
