# Translating the website

The website in `site/` is built by `tools/build_site.py`. English is the source. Every other language
(today: Chinese, code `zh`) is built under `site/zh/` from its own source files. Any source that does
not exist yet falls back to English, and the page then shows a "translation pending" note (and, when
the page's main text is English, a `noindex` tag). Nothing else needs to change in the builder: add the
files below and rebuild.

```
python3 tools/build_site.py && python3 tools/check_consistency.py
```

The build prints how many pages of each language are still pending. To hide the language switch and
build English only, set `BUILD_ZH = False` in `tools/build_site.py`.

## Files a translator writes

| File | What it is | Start from |
| --- | --- | --- |
| `tools/i18n/zh.json` | Every UI string (header, buttons, labels, the task-page sections, the plain-words grading explanations) and the sentences the builder generates (leaderboard sentences, evidence lines). | `tools/i18n/en.json` |
| `tools/site/zh/overview.html` | Prose of the Overview page. | `tools/site/en/overview.html` |
| `tools/site/zh/method.html` | Prose of the Method page. | `tools/site/en/method.html` |
| `tools/site/zh/leaderboard.html` | Prose of the Leaderboard page. | `tools/site/en/leaderboard.html` |
| `cases/plain.zh.json` | The plain-words summary of each task: `headline`, `about`, `problem`, `effect`, `action` for each of the 51 task ids. | `cases/plain.json` |
| `cases/zh/<task_id>.md` | The full case of each task, 51 files. | `cases/<task_id>.md` |

Optional, for completeness (without them those pieces stay English and the page keeps a short
"translation pending" note):

| File | What it is |
| --- | --- |
| `tools/i18n/figures.zh.json` | `{"<figure name>": "<caption>"}` for the figures in `cases/figures/` (names are the `.json` file names without extension, for example `scoring-pipeline`, `evidence-layers`, `grid_turing_robot`). |
| `cases/figures/zh/<name>.svg` | A figure whose text is translated. Same drawing as `cases/figures/<name>.svg`. |
| `tools/i18n/formal.zh.json` | `{"<task_id>": {"what": "...", "limit": "..."}}` for the rows of `evidence/formal/summary.json` (Table 2 on the Method page and the "Formal check" line of task pages). |
| `category.<English field name>` keys in `zh.json` | The field shown on task cards, for example `"category.Combinatorial Optimization": "..."`. Also `formal.result.<result>` keys for the result column of Table 2. |

## Rules

- **Keys and placeholders.** In `zh.json`, translate values only. Keep every `{name}` exactly; the
  builder fills it in (a number, a task link, a file path). Values may contain HTML (`<b>`, `<code>`,
  `<a href="{task_json}">`); keep the tags. A key you leave out falls back to English.
- **Template tokens.** In `tools/site/zh/*.html`, keep every `{{...}}` token unchanged. They are
  numbers and generated text computed from the data (`{{n_cmp}}`, `{{repair-v2}}`, `{{rank_text}}`),
  figures (`{{fig:smt_solver|smt_solver}}`), evidence lines (`{{verif:smt_solver}}`), and links
  (`{{root}}`, `{{site_root}}`). Never type a number that a token provides. A task link
  `{{task:<task_id>|English text}}` may have its text translated: `{{task:smt_solver|SMT 求解器}}`.
  The builder fails if a token is left unfilled.
- **Case pages.** Keep the Markdown structure (headings, tables, lists, code). Keep code, file paths,
  commands and numbers exactly as in English. Keep links as they are in the English file: the builder
  resolves them relative to `cases/` (or to `cases/zh/`, if that is where the target exists) and turns
  them into GitHub links. Keep the figure line and its italic caption line right after the outcome
  paragraph, as in English (`![...](figures/<id>.svg)` then a blank line and `*...*`); the builder drops
  that pair because the page shows the figure above. The only HTML the renderer keeps is
  `<mark>…</mark>`; anything else between `<` and `>` is shown as text.
- **Facts.** A translation must not change any number, outcome or claim. `tools/check_consistency.py`
  checks the English sources and every built page's outcome; the translator is responsible for the
  rest.
- **What stays English.** The task instructions on each task page are EdgeBench's original text (CC BY
  4.0) and are shown in English in every language; add a sentence saying so in `task.prompt.lang_note`.
  Use `task.found.lang_note` for any note about the case translation. Model names, task ids, file paths
  and the figure drawn by the builder (`evidence-layers`) stay English.
- **The pending note.** Set `pending_note` in `zh.json` to the Chinese text of the note shown on pages
  that still fall back to English.

## How the fallback works

For each page of a language other than English the builder records what came from English:

- the page's own prose (`tools/site/zh/<page>.html`), the case (`cases/zh/<id>.md`) or the plain
  summary (`cases/plain.zh.json`): the main text is English, so the page gets the pending note, its
  `<main>` is marked `lang="en"`, and it is not indexed;
- any string from `en.json`, a caption, a formal-table row or a field name: the page gets the pending
  note only.

The language switch in the header links each page to the same page in the other language
(`site/index.html` and `site/zh/index.html`, `site/tasks/smt_solver.html` and
`site/zh/tasks/smt_solver.html`, and so on).

## Stale translations

`pending-<lang>.json` explicitly withholds older translations after an English
conclusion changes. `sources` lists English source paths relative to the repository;
`plain` and `formal` list task IDs. The builder preserves translated source files,
uses current English for these entries, and shows its existing translation-pending
notice (with noindex when the page's main text falls back). Remove an entry only
after reviewing and updating its translation.
