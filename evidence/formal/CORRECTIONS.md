# Corrections prompted by the formal checks

Writing claims precisely enough for Lean 4 or TLA+ exposed one shipped fix that was narrower than
published and eight published statements that said more than the evidence showed. Each was
corrected. None changed a score reported elsewhere in this publication.

| # | Task | What was published | What the formal check showed | Now |
| ---: | --- | --- | --- | --- |
| 1 | College English | The fix rejects any rule marked down with no recorded deduction | Four kinds of contradictory assessment still got full marks: three found by the proof, one by a probe of the real code | Fix revised, re-proved without exclusions, and run side by side three times |
| 2 | SMT Solver | Scores comparable for any solver using only textual keys | Fails when a `let` reuses a declared constant's name; none of the 774 hidden files does | Exception stated |
| 3 | Triangulation | The fixed rule forbids no flip the README allows | Holds on valid triangulations; the existing-edge check can reject a convex flip in an already folded mesh | Qualified to valid triangulations |
| 4 | Jagua Nesting | The fix rejects any positive-area overlap | It rejects overlaps above one millionth of the smaller shape's area | Tolerance stated |
| 5 | FFmpeg | Timed outputs compared at the same 40 dB threshold | 40 dB for scaling, 60 dB for same-size conversions; only the last timed call's output is compared | Thresholds and scope stated |
| 6 | Order Addition | The fix changes only which submission a run keeps | When no submission has a score, the reported fallback rises from 0.6 to 0.8 | Side effect documented |
| 7 | Graph Node | The original scores only the remaining nodes | It pairs the remaining predictions with the first labels in order | Wording corrected |
| 8 | OpenRCT2 | One scenario's 1,667 s exceeds the 1,800 s and 2,400 s caps | One scenario fits under both; only the three together exceed them | Wording corrected |
| 9 | Treant Forest | Published scores convert exactly except between 20 and 21.02 | Runs that scored 0 also convert only approximately (up to 2.19 points divided by the number of runs) | Both exceptions stated |
