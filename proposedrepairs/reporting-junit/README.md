# Reporting: check the XML and the recorded error

The original JUnit test accepted plain text and malformed XML because it searched for two text fragments. This proposed patch parses XML and checks that the named testcase contains the supplied error message.

**Status: independently checked local prototype.** Twelve author controls and four fresh reviewer controls passed their expected before/after outcomes (32 selected-function calls in total). Outputs came from controlled writers. The real writer, full suite and a corrected native image still need testing.

The patch changes one test body in `tests/test_02_reporting.py`; all 14 test names and the scoring formula remain unchanged. It accepts both single-suite and multiple-suite roots and messages in error text or the message attribute. It rejects malformed XML, missing or misplaced errors, incorrect messages and incorrect testcase labels.

Apply with `patch -p1` from the acquired judge filesystem root, after verifying the original file identity in [manifest.json](manifest.json). The complete private test source is not distributed here.

This creates a new evaluator version. If exactly this verdict changes from pass to fail among 14 executed phase-two tests, the arithmetic score change is −1/70. No native score effect has been measured.

[Author controls](../../evidence/selected/reporting-junit-repair-author-controls.json) · [fresh reviewer controls](../../evidence/selected/reporting-junit-repair-fresh-controls.json) · [review conclusion](../../evidence/selected/reporting-junit-repair-review.json).
