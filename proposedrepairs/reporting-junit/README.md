# Reporting: check the XML and the recorded error

The original JUnit test accepted plain text and malformed XML because it searched for two text fragments. This proposed patch parses XML and checks that the named testcase contains the supplied error message.

**Status: local before/after controls plus one selected native test against the actual candidate writer.** Twelve author controls and four fresh reviewer controls passed their expected outcomes (32 selected-function calls in total). Those earlier outputs came from controlled writers.

At the October 11, 19:03 UTC acceptance, a 30-file implementation overlay passed all **55 printed test items** under the unchanged original full scorer, earning **1.0**. The script reports **53/53** because phase four uses a nine-test success count despite printing 11 items. Afterward, the actual candidate writer passed the separately mounted patched JUnit test. [Acceptance](../../evidence/selected/reporting-native-reference-acceptance.json) · [native outcomes](../../evidence/selected/reporting-native-reference-result.json) · [saved-result review](../../evidence/selected/reporting-native-reference-review.json).

The full patched scorer and a persisted corrected image remain untested. This overlay is not a certified replacement or proof that every reporting requirement works. The native scorer used a 240-second diagnostic allowance rather than the original 1,800 seconds; the result review reused saved evidence, without another native run. The private implementation and complete test source remain outside this repository.

The patch changes one test body in `tests/test_02_reporting.py`; all 14 test names and the scoring formula remain unchanged. It accepts both single-suite and multiple-suite roots and messages in error text or the message attribute. It rejects malformed XML, missing or misplaced errors, incorrect messages and incorrect testcase labels.

Apply with `patch -p1` from the acquired judge filesystem root, after verifying the original file identity in [manifest.json](manifest.json). The complete private test source is not distributed here.

This creates a new evaluator version. If exactly this verdict changes from pass to fail among 14 executed phase-two tests, the arithmetic score change is −1/70. No native score change caused by this test patch has been measured.

[Author controls](../../evidence/selected/reporting-junit-repair-author-controls.json) · [fresh reviewer controls](../../evidence/selected/reporting-junit-repair-fresh-controls.json) · [review conclusion](../../evidence/selected/reporting-junit-repair-review.json).
