# College English: require every rubric assessment

The final supplied grader could fill an omitted rubric assessment before scoring. This patch checks complete, exactly-once known rule IDs and finite numeric scores before normalization/reconciliation, and passes authoritative rules through the parser. Apply it at the judge filesystem root to the exact `/home/workspace/scoring/grade_with_codex.py` preimage in `manifest.json` (`patch -p1`).

Root-accepted, separately reviewed four-call fixed-response full-main evidence preserves complete output byte-for-byte at valid96 and changes the missing-assessment case from valid96 to invalid0. Duplicate-ID and finite-number guards are explicit versioned policy; this patch does not add maximum-score validation.

The evidence uses supplied final source and a controlled rubric, without live model calls or installed-image/harness parity. No derived image or replacement certification exists; the original exclusion stays unchanged. Only this small patch is selected: no whole grader, hidden rubric, response or answer bodies, private IDs or credentials. Private Git selection grants no public redistribution rights.
