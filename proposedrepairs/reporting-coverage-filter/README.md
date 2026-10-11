# Reporting coverage-test correction

The original two tests filter generated values using the wrong class. On the tested reporting candidate, that removes every value and makes the absence assertion pass without checking the output.

`repair.patch` changes the native judge tests to use the coverage value type, require a nonempty correctly typed stream, and check both allowed and denied unexpected properties for body and query parameters. It changes phase-five count constants from 10 to 12 while preserving its weight; this is a distinct judge version whose partial scores must not be silently combined with the original.

Twenty paired complete test-function calls in the pinned native environment matched their expected outcomes: twelve returned normally and eight intentionally raised assertions. Twelve calls used the actual candidate generator; eight used explicitly empty or wrong-type doubles. Old tests accepted forced-allow outputs under a deny request; corrected tests rejected them and preserved legitimate allow/deny behavior.

[Accepted result](../../evidence/selected/reporting-coverage-repair-acceptance.json), [case-level observations](../../evidence/selected/reporting-coverage-repair-native.json), and [different review](../../evidence/selected/reporting-coverage-repair-review.json) identify the measured scope. The reviewer checked saved evidence; no independent native replay is claimed.

Apply the patch to the original judge filesystem. The exact private judge and reporting implementation V2 overlay are required to reproduce this run and are not bundled here; their identities and coordinator job are in the evidence. Full pytest collection, all eight unchanged email tests, the patched scoring script, other implementations and task certification remain untested by these controls. The original 55 printed / 53 reported test counts describe an earlier, separate run.
