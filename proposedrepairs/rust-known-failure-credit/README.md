# Rust known-failure credit: finite prototype

**Status: accepted finite Python-component prototype; not a native Rust repair or certified replacement.** The original task decision remains pending.

For `cas-pty`, a configured known-failure exemption now receives credit only when the parser observed that exact full test name with result `FAILED`. The correction adjusts the same public or hidden bucket. A passing exempt test therefore cannot cancel an unrelated failure. Legitimate failed exemptions retain credit.

V2 preserves the original behavior of other crates, including `cas-cli` substring matching. Independent review found that V1's global exact-name rule assumed an integration-test binary filename was a test-function name. That assumption was unsupported. Preserving CLI behavior establishes compatibility, not its correctness; its policy remains unresolved.

## Apply to the exact acquired source

The patch changes only `judge/tools/score.py` beneath the acquired `cas_rust_benchmark` directory. The original full scorer is not included here; obtain it through authorized access to the pinned task source.

| File identity | Bytes | SHA-256 |
| --- | ---: | --- |
| Original scorer | 25,616 | `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35` |
| Candidate scorer | 26,068 | `a28b312497bae34b8c4730452c57f005c6867bb2f23102ad2bcbf4e5d5444b69` |
| [repair.patch](repair.patch) | 1,550 | `700b66ca7b61dd78870a74d26397e5d81e867fbc96677140c68f0f0286c68b82` |

From the acquired source directory, verify the original checksum, apply the patch using its absolute location, then verify the candidate checksum:

```sh
sha256sum judge/tools/score.py
patch --dry-run -p1 < /absolute/path/to/repair.patch
patch -p1 < /absolute/path/to/repair.patch
sha256sum judge/tools/score.py
```

Stop if either checksum differs from the table. Patch application changes source only; it does not build or test a native judge.

## Accepted evidence and limits

Five paired Python-helper controls used simulated Cargo responses. The regression changed from 11 passed / 0 failed / PASS to 10 passed / 1 failed / TEST_FAIL. Four CLI shapes retained their original results. [Exact author results](../../evidence/selected/rust-known-failure-repair-result.json).

The different V2 review checked the two changed guards, 32 Boolean combinations and reconstructed candidate identity. It reused prior independent mixed public/hidden `cas-pty` controls through unchanged guard behavior; it did not perform a fresh helper replay. [Different review](../../evidence/selected/rust-known-failure-repair-review.json) · [Root acceptance](../../evidence/selected/rust-known-failure-repair-acceptance.json).

No Cargo, Rust compilation, native judge, full scoring CLI, hidden-test injection or benchmark-score comparison was executed for this prototype. Basename-based hidden classification, malformed-output trust and the CLI allowance remain separate limitations. Native-format integration and matched actual-task controls are still needed for a release repair. No new finding, exclusion, certification or task-coverage count follows from packaging it.

The selected records are exact aggregate copies. Their internal archive references may require local auditor access; this package is not a standalone reproduction bundle and grants no redistribution rights to the underlying source. [Machine-readable identities](manifest.json).
