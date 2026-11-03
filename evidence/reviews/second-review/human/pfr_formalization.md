# Human verification: PFR Formalization

Recorded by a volunteer Lean user on 31 Oct 2026 in the project's verification document. Result: PASS.

> I checked the five theorem statements and the grader. With the workaround, all five completed proofs receive credit (398/423 → 403/423), with no new bad declarations.
>
> The problem matches Lean issue #14708. Lean can replace a private autoParam helper with sorry in a public theorem type. PR #15249 proposes a fix.
>
> Upgrading to a Lean version that includes the fix may eliminate the need for this workaround. However, keeping the current Lean version and using the workaround is also fine.

5/423 is 1.18 points out of 100, as `cases/pfr_formalization.md` records.
