# Shared reporting hooks: tested candidate correction

Parametrized schema clones share hook/configuration objects, but the earlier candidate keyed its reporting caches by each clone's identity. This patch keys them by the shared raw-schema, hook and configuration identities. Independently loaded schemas remain separate.

Apply `candidate.patch` to the frozen reporting implementation V2, not directly to an unmodified upstream image. That full base overlay remains in the coordinator archive; this selection is not a standalone runtime bundle.

With identical controls and resources, changing only the plugin improved four of five integration controls from failure to success. The fifth stopped at our stdout-specific error-message assertion. A separately reviewed control correction now requires the actual injected error event and retains the cleanup assertions. All five corrected controls pass on the same candidate, including parallel execution with an injected writer error. The old candidate was not rerun with those corrected controls: this is not a matched zero-to-five comparison.

The changed plugin also passed a new run of all 55 printed original test items, with original score 1.0 and the script's separate 53/53 summary. Its actual writer passed the separately mounted repaired JUnit test. These are new results on the changed plugin, not inherited baseline passes.

Evidence: [matched four-control improvement](../../evidence/selected/reporting-shared-hook-acceptance.json), [five corrected controls](../../evidence/selected/reporting-writer-error-acceptance.json), and [original-suite regression](../../evidence/selected/reporting-shared-regression-acceptance.json). Different reviewers checked the saved results and source correspondence; no fresh independent native replay is claimed.

The exceptional parallel case checks actual writer failure and completed closing of observed writers, but does not require final report content or both schemas to be fully received. Stateful workflows, arbitrary sessions, full corrected-scorer execution, release packaging and task certification remain separate. Earlier failures and rejected expectations remain in the evidence.
