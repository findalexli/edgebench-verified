This is the source candidate for the Order helper-integrity benchmark version.
The original task stays intact. Its candidate changes one field,
judge.image_tag, to helper-integrity-v1. The separate BENCHMARK.yaml names
edgebench_order_integrity_v1. The task's display name, agent prompt, original
command, submission rules, timeout, parser, score, selection and rescale remain.
The .json.in suffix keeps this proposal out of default task discovery.

The Dockerfile and .dockerignore are the exact previously reviewed recipe.
Build in a private directory containing those files and only the frozen 6265-byte
tests/test_final_result.py candidate. That checker is external and absent from
Git. The FROM image is pinned by acquired OCI digest. The one COPY corrects the
helper's expected hash; helper/binary/baseline bytes stay unchanged. source-lock
binds the original task, candidate, acquired base and accepted V41 observations.
RFC6902 field guards supplement the complete source hash and inverse requirement.

V41 actually built and tested the candidate: legal five passes with printed
0.0000000010, and wrong cost four passes with the named validation failure and
no score. That image and owned VM were removed after collection. This package
does not bind a retained image ID or registry manifest to those past tests.
Docker creation metadata and ownership labels may vary across builds; recipe
and installed-byte reproducibility do not promise identical config/archive bytes.

For the next integrated attempt, the native judge image must exist under its
TaskSpec-derived local key. The pinned fork's judge_submission function already
filters/extracts archives, injects eval.sh, executes the original command, grades
with pytest_v and applies rescale_score. select_best can consume those reports
directly. Two V41 submissions repackaged as bounded regular archives, each with
a harmless excluded tests/ canary, exercise the new transport without another
public oracle call. A model run, HTTP service or 15-phase trace is not required
for this judge integration claim. Full agent/work behavior remains separate.

artifact-policy proposes one private Docker-save archive with a 4GiB hard cap,
streamed and hashed before owned VM closure, then loaded and identity-checked
offline before adoption. Docker-save manifest metadata is not an OCI registry
manifest digest. No public registry, Git image asset or acquired body export is
part of this proposal. Actual archive size and format remain to be measured.

Current native controls have a 1MiB child file limit and 8MiB private-file sweep;
the maintained coordinator closes the VM after JSON collection. A sole owned
artifact exception and bounded private transfer before closure therefore need
focused review and an exact root grant. The archive transport also writes the
owned project and tmp directories, so its bounded backend policy must disclose
that resource regime. No silent change to existing caps or frozen source is
authorized by this source candidate.

All five release gates remain pending, including broader reproduction/corpus,
true query-count accounting, domain/data review, version comparability and
redistribution rights. The work-image fork alias is still uncreated; the
judge-only native entry needs only the judge image. No TaskSpec adoption, image
publication, canonical task/card/count/queue change or new native run occurred.
