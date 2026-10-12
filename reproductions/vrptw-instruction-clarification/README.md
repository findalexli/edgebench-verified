# Proposed vehicle-routing instruction clarification

This is an unadopted native-format task proposal. It appends an explicit clarification to the original agent query: the score averages all 56 instances equally, and the installed instances are fixed, not node-scrambled. All executable, image, data and grading fields are unchanged.

The [patch](agent-query.patch) shows the complete text change. [Checks](checks.json) confirm the original query prefix and every other field remain unchanged. All 56 route witnesses subsequently passed the actual original checker/caller; see [accepted result](../../evidence/selected/vrptw-all56-native-acceptance.json).

Before adoption, review the changed wording, bind this distinct prompt version to the task record, and conclude the separately recorded decimal tolerance boundary issue. This clarification does not repair that numerical behavior. The [gate map](gate-map.json) preserves it. References in the saved handoff and gate map locate the canonical local evidence and are not all contained in this selection. No new native run is needed solely for unchanged executable code, but this proposal is not a reviewed release.
