# materialize-check-g3: input snapshot, superseded

`src/` is the job's input: a snapshot of `tasks/` and `repairs/` as committed at `83181b7f`
(`git archive 83181b7f`; the archive sha256 is in `SOURCE`). It is kept as the exact input of this
clean-machine rebuild check. **Its READMEs, results and status text are superseded**: several packages
were revised after `83181b7f` (for example College English v2.2, Graph Node v2.1, Jagua v2.1 and
Triangulation v2.2), and some claims in those copies were later corrected. Read the current package in
`repairs/<task>-v2/`, not the copy here. The check's results are in `result/` and are summarized in
[`../materialize-check-summary/README.md`](../materialize-check-summary/README.md).
