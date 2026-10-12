# Task: implement Arc compiler/runtime modules

Implement the missing JavaScript modules under `compiler/src/` so the Arc language compiler/runtime works. Use `CHEATSHEET.md` as the public language reference.

## Boundaries

- Edit implementation files under `compiler/src/` only during a solver attempt.
- Do not modify tests, scoring scripts, manifests, task metadata, Dockerfile, or package files.
- Work offline. Do not use network search, cloning, GPU, mouse, video, or human interaction.
- Do not add hidden solutions, private provenance, source maps, compiled answer artifacts, answer material.
- Do not attempt to access evaluator-only hidden tests during solving.

## Public smoke scoring

The public package contains smoke/sample tests only. They are intended for local progress checks and interface validation, not as the full official evaluation.

| Item | Value |
| --- | ---: |
| Public raw denominator | 48 |
| Public weighted denominator | 48 |
| Shipped starter (measured) | `SCORE=100.00` (48/48), `SCORE_STATUS=OK` |

Run `bash score.sh` from the package root for public smoke feedback.

## Semantic analysis interface (`compiler/src/semantic.js`)

The evaluator calls `analyze(parse(lex(source)))` from `compiler/src/semantic.js`
(with `lex` from `compiler/src/lexer.js` and `parse` from `compiler/src/parser.js`).
The shipped starter returns `{ ok, errors, warnings, program }`; that shape is **not**
the evaluated interface. The required interface is:

- `analyze(program)` returns an **array** of diagnostic objects (an empty array when
  there are no diagnostics). The evaluator calls `.filter(...)` on the result.
- Each diagnostic has `level` (`"error"` or `"warning"`) and `message` (a string).
- Diagnostic text is checked by substring, case-sensitive:
  - a reference to a name that is not in scope is an error whose `message` contains `Undefined`;
  - assigning to an immutable (`let` without `mut`) binding is an error whose `message`
    contains `Cannot reassign immutable`;
  - calling a user-defined function with the wrong number of arguments is an error whose
    `message` contains `expects N`, where N is the function's declared parameter count
    (for example `expects 2`).

The semantic rules evaluated through this interface (from the language contract):

- Errors are expected for: a name declared inside an `if` block or a `for` loop body and
  used after that block; a name local to one function used from a sibling function;
  reassignment of an immutable binding, including from inside a nested block; a call to a
  user-defined function with too many arguments.
- No errors are expected for: a nested function reading an outer binding; a nested
  function reading a shadowing local binding of its enclosing function; reassignment of a
  `let mut` binding inside a nested block; names introduced by object destructuring
  (`let {a, b} = ...`) and list destructuring with a rest element (`let [a, b, ..rest] = ...`);
  mutually recursive top-level functions (functions are visible before their definition).
- No warnings are expected for a `match` that has a wildcard `_` arm.

## Final evaluation

The final official score is computed by a separate evaluator-only hidden package using SPEC_CONFIRMED tests derived from this public language contract.
