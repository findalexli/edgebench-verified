# Reproduce the Rust scorer's misplaced failure credit

The original scorer can mark an unrelated failed test as passed when its named known-failure exemption **passes**. It checks whether the exemption's name appears in the output, without requiring that test's outcome to be `FAILED`.

This replay uses the original Python functions and six explicit simulated Cargo transcripts. It requires no Cargo, Rust compiler, network, benchmark workspace or installed Python packages. The original scorer is supplied separately; no acquired source or private tests are bundled.

## Run

Use Linux with Python 3.8 or newer. Supply the original `cas_rust_benchmark/judge/tools/score.py` and a new output directory:

```bash
python3 -I -B reproduce.py /path/to/original/score.py ./fresh-replay-output
```

The script requires exactly 25,616 source bytes with SHA-256:

```text
d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35
```

A mismatch or existing output directory stops the replay. The script enforces 128 MiB address space, one CPU affinity, 5 CPU seconds and an 18-second alarm. These are declared process limits, not a claim about measured aggregate peak memory.

Successful execution prints a short confirmation and writes `result.json`. Exit zero means the six expected original outcomes were reproduced—including the two mismatches below. It does **not** mean the scorer is correct.

## Expected outcomes

Every fixture discovers and executes eleven tests. Apart from the exemption name read from the scorer's public constant, test names and output are authored examples.

| Fixture | Expected passed/failed | Original passed/failed |
| --- | --- | --- |
| All pass | 11 / 0 | 11 / 0 |
| Only named exemption fails | 11 / 0 | 11 / 0 |
| Named exemption passes; one other test fails | 10 / 1 | **11 / 0** |
| Named exemption passes; two other tests fail | 9 / 2 | **10 / 1** |
| Named exemption and another test fail | 10 / 1 | 10 / 1 |
| Named exemption absent; another test fails | 10 / 1 | 10 / 1 |

The oracle grants credit only when the named exemption actually fails. It preserves that intended exemption policy and the fixed denominator. The finding combines the scorer's named exception with the task's pass-count contract; the public specification does not separately formalize exemption arithmetic.

With all companion crates synthetically passing, the two mismatches produce original scores of **100.0 versus expected 99.9**, and **99.9 versus expected 99.8**. The original layer formula supplies these synthetic totals. For the affected layer, one extra pass contributes `4 / (11 + 29) = 0.1` points. These are not observed model scores or historical benchmark impact.

## What this executes

The replay checks the source hash, selects the unchanged `run_crate_test`, `compute_score`, `CrateResult` and required constants/helpers from its syntax tree, and supplies exactly two simulated Cargo responses per case. Failed transcripts use exit code 101 and internally consistent per-test and summary lines. The original module's CLI and imports are not executed, and its subprocess interface is replaced before any selected function runs.

This is a reproduction of an independently confirmed Python component finding. It does not run real Cargo, compile Rust, execute the pinned judge image, inject hidden tests, or exercise workspace transport or the full scorer CLI. It does not measure whether this combination of outcomes occurs in native tests. It does not extend the result to the separate CLI exemption, whose naming and output routing were not tested. No repair is included or validated.

`validation.json` records a single packaging replay against the retained original and an exact comparison with the accepted six-case result. That replay is packaging validation, not another independent scientific reproduction.
