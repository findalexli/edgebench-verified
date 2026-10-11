# Supporting evidence

Start with [current status](../AUDIT-STATUS.md) and [the plain-language findings](FINDINGS.md). This page explains where their supporting records live.

## What is included

- [Twelve finding decisions](../evidence/selected/12-finding-decisions.json): exact confirmed claims, how they were checked, limiting evidence and references to the accepted results.
- [51-task evidence table](../evidence/selected/51-task-coverage.md): the tests or observations recorded for each task at the table's original snapshot date.
- [Later Wireless exclusion](../evidence/selected/wireless-original-exclusion.json): the accepted original-version decision and current totals at 02:12 UTC on October 11.
- [Order exclusion binding](../evidence/selected/order-original-exclusion-binding.json): identifies the copied Order decision records and approvals.
- [Evidence manifest](../evidence/selected/EVIDENCE-MANIFEST.json): file identities, sources, selection method and omitted material.

The earlier finding JSON and task table were prepared at **01:22 UTC on October 11**. Their historical counts remain unchanged. The current status page incorporates the later Wireless decision; older snapshots are not live progress counters.

## How to interpret these records

A confirmed finding answers a specific question. It can be concluded without approving the entire task or its proposed repair. Tests on an original component, simulated inputs, mathematical arguments and complete task execution provide different kinds of evidence; the records say which was used.

The selected Order records include its original task card, the disposition registry as it stood then, three actual approvals, the rationale and five immediate decision records. The other task cards and complete native-run archive are not included. These selected files are not a runnable benchmark release.

A separate ANN data check found one repeated numeric test vector and no exact numeric matches between the test and training sets. It did not establish a defect in a uniqueness requirement, an absence of near-duplicates, or dataset rights. Its accepted source is recorded in the manifest.

## What remains local

Full evidence, private task inputs and answers, raw logs, credentials, live worker identities and cloud accounting remain outside Git. JSON archive references identify local source records by path and hash; their bodies are not necessarily available in this repository. Copying a result is not an independent reproduction or permission to redistribute its underlying data.

The recorded reviewers are AI agents. They are not three independent human reviewers or substitutes for specialist review where that is required.
