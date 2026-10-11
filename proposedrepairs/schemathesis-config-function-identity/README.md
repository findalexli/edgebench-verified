# Schemathesis Config: preserve the decorated function

The original metric decorator checks accept a forwarding wrapper even though C3.3 requires returning the function unchanged. This patch adds the already measured object-identity regression and changes only Phase 3's expected counts from 15 to 16. Apply it at the judge filesystem root to the two exact `/tests/` preimages in `manifest.json` (`patch -p1`).

Accepted original/candidate native runs preserve the reference (16/16) and detect the wrapper (15/16). The wrapper's partial overall score falls by exactly 1/160; other original checks, phase weights and validity behavior remain unchanged. Separate saved-result and contract reviews support this finite repair.

Four fresh source-component controls were separately reviewed and accepted: the reference preserved function identity in both cases, while the wrapper failed it in both. All four preserved values, registration and cleanup. These checks did not rerun the native scorer. This selection is a source overlay, without a derived image or complete modernization/release validation. It does not change the original task disposition or certify a repaired task. The selected patch contains no private answers, raw private IDs or authentication data. Private Git selection grants no public redistribution rights.
