#!/usr/bin/env python3
"""A small, careful Markdown renderer for the subset used in cases/*.md and the tasks' agent_query text.

Supported blocks: ATX headings, paragraphs, bullet and ordered lists (nested by indentation, with
continuation paragraphs, code and tables inside items), pipe tables with alignment, fenced code
(``` and ~~~, indented fences included), indented code blocks, block quotes and horizontal rules.
Inline: code spans, **bold**, *italic* / _italic_, [links](url), ![images](src), <autolinks>,
backslash escapes and the one raw HTML element the case pages use, <mark>…</mark>.

All other text is HTML-escaped, so any other tag in the source (for example `<seed>` in a prompt) is
shown literally. Link and image targets pass through a caller-supplied `link(href, is_image)`
function, which may rewrite them (to GitHub URLs, say) or return None to render the link text alone.
No dependency beyond the standard library.
"""
import html
import re

FENCE = re.compile(r'^( {0,3}|\s*)(`{3,}|~{3,})\s*([^`\s]*)[^`]*$')
HEADING = re.compile(r'^ {0,3}(#{1,6})(?:\s+(.*?))?\s*#*\s*$')
HR = re.compile(r'^ {0,3}([-*_])(?:\s*\1){2,}\s*$')
LIST = re.compile(r'^(\s*)([-*+]|\d{1,9}[.)])(\s+|$)(.*)$')
TABLE_SEP = re.compile(r'^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$')
QUOTE = re.compile(r'^ {0,3}> ?(.*)$')


def _indent(s):
    n = 0
    for ch in s:
        if ch == ' ':
            n += 1
        elif ch == '\t':
            n += 4 - n % 4
        else:
            break
    return n


def _dedent(s, k):
    """Remove up to k columns of leading whitespace."""
    s = s.replace('\t', '    ') if s.startswith('\t') else s
    i = 0
    while i < len(s) and i < k and s[i] == ' ':
        i += 1
    return s[i:]


def _is_table_start(lines, i):
    return (i + 1 < len(lines) and '|' in lines[i] and TABLE_SEP.match(lines[i + 1])
            and lines[i + 1].count('-') >= 1 and '|' in lines[i + 1] + lines[i])


class Renderer:
    def __init__(self, link=None, heading_offset=0, slug_prefix=''):
        self.link = link or (lambda href, is_image: href)
        self.heading_offset = heading_offset
        self.slug_prefix = slug_prefix
        self.slugs = set()

    # ---------- inline ----------
    def inline(self, text):
        tokens = []

        def stash(s):
            tokens.append(s)
            return f'\x00{len(tokens) - 1}\x00'

        # code spans: a run of n backticks up to the next run of exactly n backticks
        def code(m):
            body = m.group(2)
            if body.startswith(' ') and body.endswith(' ') and body.strip():
                body = body[1:-1]
            return stash(f'<code>{html.escape(body, quote=False)}</code>')
        text = re.sub(r'(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)', code, text, flags=re.S)
        # backslash escapes
        text = re.sub(r'\\([\\`*_{}\[\]()#+\-.!|<>~"])', lambda m: stash(html.escape(m.group(1))), text)
        # autolinks <https://...>
        def auto(m):
            url = m.group(1)
            href = self.link(url, False)
            return stash(f'<a href="{html.escape(href)}">{html.escape(url)}</a>' if href else html.escape(url))
        text = re.sub(r'<(https?://[^\s<>]+)>', auto, text)
        # <mark> and </mark>: the only raw HTML kept
        text = re.sub(r'<(/?)mark>', lambda m: stash(f'<{m.group(1)}mark>'), text)
        # images and links (the text may hold stashed code; nested brackets one level deep)
        label = r'((?:[^\[\]]|\[[^\[\]]*\])*)'
        target = r'\(\s*<?([^()\s<>]*(?:\([^()\s]*\)[^()\s<>]*)*)>?(?:\s+"([^"]*)")?\s*\)'

        def image(m):
            alt, src, title = m.group(1), m.group(2), m.group(3)
            href = self.link(src, True)
            alt_txt = re.sub(r'\x00(\d+)\x00', lambda k: re.sub('<[^>]+>', '', tokens[int(k.group(1))]), alt)
            if not href:
                return stash(html.escape(alt_txt))
            t = f' title="{html.escape(title)}"' if title else ''
            return stash(f'<img src="{html.escape(href)}" alt="{html.escape(alt_txt)}"{t} loading="lazy">')
        text = re.sub(r'!\[' + label + r'\]' + target, image, text)

        def link(m):
            body, href0 = m.group(1), m.group(2)
            inner = self._emph(html.escape(body, quote=False))
            href = self.link(href0, False)
            if not href:
                return stash(inner)
            return stash(f'<a href="{html.escape(href)}">{inner}</a>')
        text = re.sub(r'\[' + label + r'\]' + target, link, text)
        out = self._emph(html.escape(text, quote=False))
        # restore stashed pieces (they may nest)
        for _ in range(4):
            if '\x00' not in out:
                break
            out = re.sub(r'\x00(\d+)\x00', lambda k: tokens[int(k.group(1))], out)
        return out

    @staticmethod
    def _emph(s):
        s = re.sub(r'\*\*(?=\S)(.+?)(?<=\S)\*\*', r'<strong>\1</strong>', s, flags=re.S)
        s = re.sub(r'(?<![\w_])__(?=\S)(.+?)(?<=\S)__(?![\w_])', r'<strong>\1</strong>', s, flags=re.S)
        s = re.sub(r'(?<![*\w])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![*\w])', r'<em>\1</em>', s, flags=re.S)
        s = re.sub(r'(?<![\w_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w_])', r'<em>\1</em>', s, flags=re.S)
        return s

    # ---------- blocks ----------
    def render(self, src):
        lines = src.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        return '\n'.join(self.blocks(lines))

    def slug(self, text):
        base = self.slug_prefix + (re.sub(r'[^\w\- ]', '', re.sub('<[^>]+>', '', text)).strip().lower().replace(' ', '-') or 'section')
        s, k = base, 2
        while s in self.slugs:
            s, k = f'{base}-{k}', k + 1
        self.slugs.add(s)
        return s

    def blocks(self, lines):
        out, i, n = [], 0, len(lines)
        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            m = FENCE.match(line)
            if m:
                i = self._fence(lines, i, out)
                continue
            m = HEADING.match(line)
            if m:
                level = min(6, len(m.group(1)) + self.heading_offset)
                body = self.inline(m.group(2) or '')
                out.append(f'<h{level} id="{self.slug(body)}">{body}</h{level}>')
                i += 1
                continue
            if HR.match(line):
                out.append('<hr>')
                i += 1
                continue
            if _is_table_start(lines, i):
                i = self._table(lines, i, out)
                continue
            if QUOTE.match(line):
                buf = []
                while i < n and lines[i].strip() and QUOTE.match(lines[i]):
                    buf.append(QUOTE.match(lines[i]).group(1))
                    i += 1
                out.append('<blockquote>' + '\n'.join(self.blocks(buf)) + '</blockquote>')
                continue
            if LIST.match(line) and _indent(line) <= 3:
                i = self._list(lines, i, out)
                continue
            if _indent(line) >= 4:
                buf = []
                while i < n and (_indent(lines[i]) >= 4 or not lines[i].strip()):
                    buf.append(_dedent(lines[i], 4))
                    i += 1
                while buf and not buf[-1].strip():
                    buf.pop()
                out.append('<pre><code>' + html.escape('\n'.join(buf), quote=False) + '</code></pre>')
                continue
            # paragraph
            buf = [line.strip()]
            i += 1
            while i < n and lines[i].strip():
                ln = lines[i]
                if (FENCE.match(ln) or HEADING.match(ln) or HR.match(ln) or QUOTE.match(ln)
                        or _is_table_start(lines, i) or (LIST.match(ln) and LIST.match(ln).group(4).strip())):
                    break
                buf.append(ln.strip())
                i += 1
            out.append('<p>' + self._lines_inline(buf) + '</p>')
        return out

    def _lines_inline(self, buf):
        # a line ending in two spaces or a backslash is a hard break; otherwise lines join with a space
        return self.inline('\n'.join(buf)).replace('\n', ' ')

    def _fence(self, lines, i, out):
        m = FENCE.match(lines[i])
        ind, mark, lang = _indent(lines[i]), m.group(2), m.group(3)
        buf = []
        i += 1
        while i < len(lines):
            ln = lines[i]
            s = ln.strip()
            if s.startswith(mark[0] * len(mark)) and set(s) <= {mark[0]}:
                i += 1
                break
            buf.append(_dedent(ln, ind))
            i += 1
        cls = f' class="language-{html.escape(lang)}"' if lang else ''
        out.append(f'<pre><code{cls}>' + html.escape('\n'.join(buf), quote=False) + '</code></pre>')
        return i

    @staticmethod
    def _cells(row):
        row = row.strip()
        if row.startswith('|'):
            row = row[1:]
        if row.endswith('|') and not row.endswith('\\|'):
            row = row[:-1]
        cells, cur, tick, k = [], '', 0, 0
        while k < len(row):
            ch = row[k]
            if ch == '\\' and k + 1 < len(row) and row[k + 1] == '|':
                cur += '\\|'
                k += 2
                continue
            if ch == '`':
                j = k
                while j < len(row) and row[j] == '`':
                    j += 1
                run = j - k
                tick = 0 if tick == run else (run if tick == 0 else tick)
                cur += row[k:j]
                k = j
                continue
            if ch == '|' and not tick:
                cells.append(cur.strip())
                cur = ''
            else:
                cur += ch
            k += 1
        cells.append(cur.strip())
        return cells

    def _table(self, lines, i, out):
        head = self._cells(lines[i])
        aligns = []
        for c in self._cells(lines[i + 1]):
            c = c.strip()
            aligns.append('right' if c.endswith(':') and not c.startswith(':') else
                          'center' if c.startswith(':') and c.endswith(':') else None)
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip() and '|' in lines[i]:
            rows.append(self._cells(lines[i]))
            i += 1

        def cell(tag, txt, k):
            a = aligns[k] if k < len(aligns) else None
            st = f' style="text-align:{a}"' if a else ''
            return f'<{tag}{st}>{self.inline(txt.replace(chr(92) + "|", "|"))}</{tag}>'
        h = ''.join(cell('th', c, k) for k, c in enumerate(head))
        body = ''.join('<tr>' + ''.join(cell('td', r[k] if k < len(r) else '', k) for k in range(len(head))) + '</tr>'
                       for r in rows)
        out.append(f'<div class="tablewrap"><table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>')
        return i

    def _list(self, lines, i, out):
        m = LIST.match(lines[i])
        base = _indent(lines[i])
        ordered = m.group(2)[0].isdigit()
        start = int(m.group(2)[:-1]) if ordered else 1
        items = []
        n = len(lines)
        while i < n:
            m = LIST.match(lines[i])
            if not m or _indent(lines[i]) != base or m.group(2)[0].isdigit() != ordered:
                # allow a sibling marker indented a little more or less than the first one
                if not (m and abs(_indent(lines[i]) - base) <= 1 and m.group(2)[0].isdigit() == ordered):
                    break
            marker_w = _indent(lines[i]) + len(m.group(2)) + (len(m.group(3)) if m.group(4) else 1)
            content_ind = marker_w if len(m.group(3)) <= 4 else _indent(lines[i]) + len(m.group(2)) + 1
            buf = [m.group(4)]
            i += 1
            blank_seen = False
            in_fence = None
            while i < n:
                ln = lines[i]
                if in_fence:
                    buf.append(_dedent(ln, content_ind))
                    if ln.strip().startswith(in_fence) and set(ln.strip()) <= {in_fence[0]}:
                        in_fence = None
                    i += 1
                    continue
                if not ln.strip():
                    buf.append('')
                    blank_seen = True
                    i += 1
                    continue
                ind = _indent(ln)
                lm = LIST.match(ln)
                if ind >= content_ind or (lm and ind > base + 1) or (not lm and ind > base):
                    fm = FENCE.match(ln)
                    if fm:
                        in_fence = fm.group(2)
                    buf.append(_dedent(ln, min(ind, content_ind)))
                    blank_seen = False
                    i += 1
                    continue
                if lm and ind <= base + 1:
                    break
                if blank_seen:
                    break
                # lazy continuation of the item's paragraph
                if (HEADING.match(ln) or FENCE.match(ln) or HR.match(ln) or _is_table_start(lines, i)):
                    if ind < content_ind:
                        break
                buf.append(ln.strip())
                i += 1
            while buf and not buf[-1].strip():
                buf.pop()
            items.append(buf)
            # stop if the list is followed by a blank line and then a non-list line
        tag = 'ol' if ordered else 'ul'
        st = f' start="{start}"' if ordered and start != 1 else ''
        parts = []
        for buf in items:
            loose_inner = any(not x.strip() for x in buf)
            blocks = self.blocks(buf)
            if len(blocks) >= 1 and blocks[0].startswith('<p>') and not loose_inner:
                blocks[0] = blocks[0][3:-4]
            parts.append('<li>' + '\n'.join(blocks) + '</li>')
        out.append(f'<{tag}{st}>' + ''.join(parts) + f'</{tag}>')
        return i


def render(src, link=None, heading_offset=0, slug_prefix=''):
    return Renderer(link, heading_offset, slug_prefix).render(src)
