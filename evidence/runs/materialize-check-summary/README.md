# Materialize check of all 32 repair packages (2026-10-13)

**Result: 31 of 32 packages pass all four checks. One, `lean_analysis_proofs-v2`, could not be checked: its 33 GB grader image does not fit on the 21 GB E2B worker.**

`pfr_formalization-v2` passes with one documented change in how it was run, explained below.

## What was run

Each package was copied exactly as committed at `83181b7f` (`git archive 83181b7f tasks repairs/<pkg>`; the `SOURCE` file in each job records the archive sha256). Those copies are kept in each job's `src/` as the exact input; their text is superseded by later package revisions (each job's `README.md` says so). The copies went to fresh E2B workers (`harbor-worker-v4`, 21 GB disk, 8 GB RAM, no images at start), six jobs in all, at most three at a time. On each worker:

1. GNU `patch` was missing from the template, so it was installed (`patch 2.7.6`).
2. `./materialize.sh` ran unchanged. It pulled the pinned images by digest, extracted the originals, applied `repair.patch` and checked the result. Its log had to contain `OK: all N output file(s) match source-lock.json`.
3. The sha256 of every output listed in `source-lock.json` → `materialize.outputs` was recomputed by an independent script (`verify.py lock`).
4. `docker build` ran on `Dockerfile`, and on `Dockerfile.work` when there is one. Each image was tagged `seededge/edgebench.<judge|work>.<task>:<image_tag from task.json.in>`, and its image ID was recorded.
5. Smoke test: each file the Dockerfile `COPY`s or `ADD`s was hashed inside the built image (`docker run --user 0 --network none … sha256sum`) and compared with the local file. Where the image takes a tar (`ADD …tar`), every tar member was compared. For the rust judge, the files were checked inside the rewritten `cas_rust_benchmark.tar.gz`, and the script also confirmed that `/tmp/ebv-v2` is gone.
6. All images and the build cache were removed before the next package.

Only logs, hashes and image IDs were kept. No image files were kept; `files/` and `orig/` existed only on the workers. All six workers record `status: exit=0` and `killed: true` in `evidence/runs/ledger.jsonl`, and every job's `result/out/` was collected. `exit=0` means only that the job script finished; whether each package passed is shown in the table.

## Results

| package | materialize ok | outputs match lock | docker build ok | smoke ok | job |
| --- | --- | --- | --- | --- | --- |
| apple_incremental_game-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| arc_compiler_runtime-v2 | yes (4 outputs) | yes (4/4) | Dockerfile: yes | Dockerfile: yes (2/2 files) | `materialize-check-g3` (`exit=0`) |
| borden_source_inversion-v2 | yes (5 outputs) | yes (5/5) | Dockerfile: yes | Dockerfile: yes (2/2 files) | `materialize-check-g3` (`exit=0`) |
| college_english_exam_bank-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g3` (`exit=0`) |
| cta_risk_budget_optimization-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| dabic_gravity_inversion-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (2/2 files) | `materialize-check-g1` (`exit=0`) |
| equivalence_class_divide_and_conquer-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| exchange_core_throughput-v2 | yes (31 outputs) | yes (31/31) | Dockerfile: yes | Dockerfile: yes (31/31 files) | `materialize-check-g1` (`exit=0`) |
| ffmpeg_swscale_reimplementation-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| git_rewrite_in_zig-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| graph_node_classification-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| grid_turing_robot-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| integer_compression_codec-v2 | yes (4 outputs) | yes (4/4) | Dockerfile: yes | Dockerfile: yes (4/4 files) | `materialize-check-g3` (`exit=0`) |
| jagua_nesting_optimization-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| juliet_vulnerability_analyzer-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g1` (`exit=0`) |
| lean_analysis_proofs-v2 | **no** | **no** (0/8) | Dockerfile: **no**; Dockerfile.work: **no** | Dockerfile: not run; Dockerfile.work: not run | `materialize-check-lean` (`exit=0`) |
| molecular_self_assembly-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| openrct2_theme_park_ai-v2 | yes (2 outputs) | yes (2/2) | Dockerfile: yes | Dockerfile: n/a (no COPY) | `materialize-check-g3` (`exit=0`) |
| openttd_transport_ai-v2 | yes (4 outputs) | yes (4/4) | Dockerfile.work: yes | Dockerfile.work: yes (1/1 files) | `materialize-check-g3` (`exit=0`) |
| order_addition_permutation_optimization-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| pfr_formalization-v2 | yes (3 outputs), with work-image CHECK moved to a separate step (disk) | yes (3/3) | Dockerfile: yes; Dockerfile.work: yes | Dockerfile: yes (39/39 files); Dockerfile.work: yes (1/1 files) | `materialize-check-pfr` (`exit=0`) |
| portfolio_risk_calibration-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| rust_multicrate_reconstruction-v2 | yes (9 outputs) | yes (9/9) | Dockerfile: yes; Dockerfile.work: yes | Dockerfile: yes (9/9 files); Dockerfile.work: yes (4/4 files) | `materialize-check-rust` (`exit=0`) |
| schemathesis_config_modernization-v2 | yes (2 outputs) | yes (2/2) | Dockerfile: yes | Dockerfile: yes (2/2 files) | `materialize-check-g2` (`exit=0`) |
| schemathesis_datagen_pipeline-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| schemathesis_reporting_observability-v2 | yes (3 outputs) | yes (3/3) | Dockerfile: yes | Dockerfile: yes (3/3 files) | `materialize-check-g2` (`exit=0`) |
| smt_solver-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| treant_forest-v2 | yes (0 outputs) | yes (0/0) | Dockerfile: yes | Dockerfile: n/a (no COPY) | `materialize-check-g3` (`exit=0`) |
| tree_block_partitioning-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| triangulation_coloring_optimization-v2 | yes (15 outputs) | yes (15/15) | Dockerfile: yes; Dockerfile.work: yes | Dockerfile: yes (12/12 files); Dockerfile.work: yes (4/4 files) | `materialize-check-g3` (`exit=0`) |
| vibrating_path_graph_coloring-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |
| warehouse_forklift_routing-v2 | yes (1 outputs) | yes (1/1) | Dockerfile: yes | Dockerfile: yes (1/1 files) | `materialize-check-g2` (`exit=0`) |

"n/a (no COPY)": `openrct2_theme_park_ai-v2` and `treant_forest-v2` change only the task JSON. Their Dockerfile is a no-op `FROM` the original image, so no file in the image is replaced. `arc_compiler_runtime-v2` was built with context `files/` (`docker build -f Dockerfile files`), as its README says. `dabic_gravity_inversion-v2` (the partial fix) passed. Its one output file is installed at both in-image paths, and both were checked.

## Failure: lean_analysis_proofs-v2 (not checked)

`materialize.sh` failed while pulling the pinned grader image, before any package logic ran:

```
failed to extract layer (application/vnd.oci.image.layer.v1.tar+gzip sha256:0680744c8c4b0a67ec331204ff88618cea1020eb3fb978c69ce3ab74bba4096e) to overlayfs as "extract-186231134-Yn4n sha256:7839705c15c093878b97209d5fd849356963debc4a19182cb0a4961e8cbd406c": write /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/7/fs/home/workspace/baseline/.lake/packages/mathlib/.lake/build/ir/Mathlib/Tactic/CategoryTheory/Monoidal/Basic.c: no space left on device
materialize[lean_analysis_proofs-v2]: ERROR: docker pull failed for seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
```

Both builds then failed because the inputs did not exist (`"/files/judge/v2-build-artifacts.tar": not found` and `"/files/work/Analysis/Section_11_3.lean": not found`). The grader image is 7.65 GB compressed and about 33 GB unpacked. The worker has 18 GB free. This says nothing about the package itself.

**Minimal fix:** run the same job on a machine with about 45 GB of free disk (the earlier 2026-10-12 check ran the judge part on the local host). `tools/e2b_run.py` has no template option; it always uses `harbor-worker-v4`. A `--template` argument would let the job use a bigger-disk template, but the 30 GB template `harbor-worker-v4-s99-25g-v4-20260921-9345d11f` is probably still too small for an image that unpacks to about 33 GB. `Dockerfile.work` (8.25 GB compressed work image) has never been built.

## Deviation: pfr_formalization-v2

The grader image (about 10.5 GB unpacked) and the work image (about 11 GB) do not fit together on a 21 GB worker; this was first seen in `evidence/runs/pfr_formalization-v2-paired-v2/result-attempt1-disk/`. `materialize.sh` pulls both images at the start, but it uses the work image only to check the sha256 of the starter `PFR/WeakPFR.lean`. The job therefore ran a copy of `materialize.sh` with the two `  "work|…"` rows removed (the IMAGES row and the CHECK row; the diff is saved as `pfr_materialize.nowork.diff`). The full Lean rebuild ran inside it, and the regenerated listing matched the saved one (1123 lines, 39 members). The grader image was then removed. The work image was pulled, and the check that was left out ran from the same lock entry: `7b70ca6c…e7b8b`, which matches. Then `Dockerfile.work` was built. This is the first time `Dockerfile.work` has been built for this package; the package README still calls it unverified.

**Minimal fix** (optional): make `materialize.sh` pull and check the work image only after the grader-image steps are done and that image is removed, or allow `MATERIALIZE_SKIP_WORK_CHECK=1`. Either way the unchanged script would run on a 21 GB machine.

**Later change, untested.** Commit `2436424e` reordered the committed `repairs/pfr_formalization-v2/materialize.sh` along the lines of the first option. The check above ran the hand-edited copy (`pfr_materialize.nowork.diff`), not the reordered script, and the reordered script has not been run.

## Jobs

| job | packages | worker | status | elapsed |
| --- | --- | --- | --- | --- |
| `evidence/runs/materialize-check-g1` | 10 | ida5vifhe5ysonlnmf5tk | exit=0, killed | 202 s |
| `evidence/runs/materialize-check-g2` | 11 | icl929gz61vcfgo2wy8j0 | exit=0, killed | 202 s |
| `evidence/runs/materialize-check-g3` | 8 | ivjj7nnkgr6ug39chc914 | exit=0, killed | 161 s |
| `evidence/runs/materialize-check-rust` | 1 (images removed between Dockerfiles) | ibcwoh9oy9w7l0zhz9mio | exit=0, killed | 141 s |
| `evidence/runs/materialize-check-pfr` | 1 (see deviation) | ig4ryl8axo7or6ie0zqoj | exit=0, killed | 202 s |
| `evidence/runs/materialize-check-lean` | 1 (failed: disk) | ihluphjoizjaky9i2ac2n | exit=0, killed | 121 s |

Each package's `result/out/<pkg>/` holds `materialize.log`, `outputs.sha256`, `lock.json`, `build-*.log`, `smoke-*.json` (every in-image path with its hash) and `result.env` (tags and image IDs).

## Image IDs

Image IDs are local to the worker's containerd store. They are recorded here for traceability; they are not reproducible identities.

| package | Dockerfile | tag (per `task.json.in`) | image ID |
| --- | --- | --- | --- |
| apple_incremental_game-v2 | Dockerfile | `seededge/edgebench.judge.apple_incremental_game:16968d8ec7f2-ebv-v2` | `sha256:e9e9209f8f83e60c734176ef59020c4140a1d10a2b174be9c547ee88df14e8c8` |
| arc_compiler_runtime-v2 | Dockerfile | `seededge/edgebench.work.arc_compiler_runtime:v2-analyze-contract-docs` | `sha256:db490848f0948e387f9a3488f0cc8db81fbf3780de36ff5b1c7c2c54e1fb25bc` |
| borden_source_inversion-v2 | Dockerfile | `seededge/edgebench.work.borden_source_inversion:f389fcf94240-ebv-v2.1` | `sha256:0e75d2eb35cc319cb02093553683cb64a9f087e0b0b65b127c7d851927c08bf0` |
| college_english_exam_bank-v2 | Dockerfile | `seededge/edgebench.judge.college_english_exam_bank:6628b6d3f834-ebv-v2.1` | `sha256:1f44d60598fd0ffc1fe2025e7deac12995c8c1da2d7b9a760eda04d1d35d984c` |
| cta_risk_budget_optimization-v2 | Dockerfile | `seededge/edgebench.judge.cta_risk_budget_optimization:a9651058ecef-ebv-v2` | `sha256:4929f304486634613089c1bd33656874dafdb39edfe4e0c25fb5760b2d2d8474` |
| dabic_gravity_inversion-v2 | Dockerfile | `seededge/edgebench.judge.dabic_gravity_inversion:517eb738b87b-ebv-v2` | `sha256:aebd457f7ec62cd780e577003cc8ad479f9973e05f81e35d23f2dcdb2479220b` |
| equivalence_class_divide_and_conquer-v2 | Dockerfile | `seededge/edgebench.judge.equivalence_class_divide_and_conquer:de7206e7e06d-ebv-v2` | `sha256:828b5a6aa5ebbfba97c639e62075b4807d13593aa74c8227ace099261294db74` |
| exchange_core_throughput-v2 | Dockerfile | `seededge/edgebench.judge.exchange_core_throughput:2cbf65650b3c-ebv-v2` | `sha256:67af8fd35c0dfdffdc51c5165284f0f7135684e744aa86cbaa0acd844f26291a` |
| ffmpeg_swscale_reimplementation-v2 | Dockerfile | `seededge/edgebench.judge.ffmpeg_swscale_reimplementation:d3c0aa3fa987-ebv-v2` | `sha256:7aced4674326b7bc74b4037daba16ab337925f2caff5ce53cbf80a320b67e972` |
| git_rewrite_in_zig-v2 | Dockerfile | `seededge/edgebench.judge.git_rewrite_in_zig:0d404251e9c9-ebv-v2` | `sha256:42b7873cddc622e370e3bf58014b47e959bb1961884ff7f4cf69fe16804e95b8` |
| graph_node_classification-v2 | Dockerfile | `seededge/edgebench.judge.graph_node_classification:f2ddd52992ae-ebv-v2` | `sha256:a85965e32ac58e89608cdd0096e0b748dd6b23503cc8c36ac2180b064fea39db` |
| grid_turing_robot-v2 | Dockerfile | `seededge/edgebench.judge.grid_turing_robot:3c6f50ac4fe0-ebv-v2` | `sha256:129c5b193f75b1c8174305e5a727bd4ecc4dda9edc740d1ca284de4b94c42d09` |
| integer_compression_codec-v2 | Dockerfile | `seededge/edgebench.judge.integer_compression_codec:27063396e02a-ebv-v2` | `sha256:8f9e9d1da30dface512a33343570ef1f7041478195df5d6dc029f3be1112bde9` |
| jagua_nesting_optimization-v2 | Dockerfile | `seededge/edgebench.judge.jagua_nesting_optimization:bba393b2dd53-ebv-v2` | `sha256:ea1e92552f0614fb8470cd5124c8d7f52906f07ba67767dcd37a93d671acff13` |
| juliet_vulnerability_analyzer-v2 | Dockerfile | `seededge/edgebench.judge.juliet_vulnerability_analyzer:0c4f2c0057c2-ebv-v2` | `sha256:76a1175683d3d0ae269120b7cc23d66d6097affee5b4698cf0120bcc255c5951` |
| lean_analysis_proofs-v2 | Dockerfile | `seededge/edgebench.judge.lean_analysis_proofs:lean_analysis_proofs-v2-judge` | none (build failed) |
| lean_analysis_proofs-v2 | Dockerfile.work | `seededge/edgebench.work.lean_analysis_proofs:lean_analysis_proofs-v2-work` | none (build failed) |
| molecular_self_assembly-v2 | Dockerfile | `seededge/edgebench.judge.molecular_self_assembly:96df6463f5e6-ebv-v2` | `sha256:762d3238afebf8a7949502a4b3e258f9ebcc2ffcb1052cfb4aa03bfd05bd22a9` |
| openrct2_theme_park_ai-v2 | Dockerfile | `seededge/edgebench.judge.openrct2_theme_park_ai:80316ccd77ae` | `sha256:23f58f03ec5582b9423a8a5f5c0efb133628dc802e93455851091eb2adbc7932` |
| openttd_transport_ai-v2 | Dockerfile.work | `seededge/edgebench.work.openttd_transport_ai:f2e9a9fb0fff-ebv-v2` | `sha256:934d82c7476a00a024dc12fa0f7000e1587ca04a897ac6ea7a1f71b49b8e73f2` |
| order_addition_permutation_optimization-v2 | Dockerfile | `seededge/edgebench.judge.order_addition_permutation_optimization:f6f385925889-ebv-v2` | `sha256:d6107849aa0f2c486b3de891e5337094dee62c87bfadda229b7566e9f2ff3383` |
| pfr_formalization-v2 | Dockerfile | `seededge/edgebench.judge.pfr_formalization:pfr_formalization-v2-judge` | `sha256:17353cd6c1cbdb03da378b5844471be1d7924dab72b8adae800d8749982a5172` |
| pfr_formalization-v2 | Dockerfile.work | `seededge/edgebench.work.pfr_formalization:pfr_formalization-v2-work` | `sha256:63aee091c9bbf03ec1c783f18ffd10498a33c11f1ea4683a4428610ebe177195` |
| portfolio_risk_calibration-v2 | Dockerfile | `seededge/edgebench.judge.portfolio_risk_calibration:08fe0a4bad80-ebv-v2` | `sha256:003421b6eda6604316415062d540ebe278b990823944e6887eb717f0e6c87f7c` |
| rust_multicrate_reconstruction-v2 | Dockerfile | `seededge/edgebench.judge.rust_multicrate_reconstruction:b749374fe7bc-ebv-v2` | `sha256:2715f9e4bc3c9408bd25cbf4beb78e2b95aedee610cd6658e9f4f21462f74733` |
| rust_multicrate_reconstruction-v2 | Dockerfile.work | `seededge/edgebench.work.rust_multicrate_reconstruction:7f639fc9d090-ebv-v2` | `sha256:b845abfef4caf5e107f3a7c5c3ac121b4fcdb3cd90f818a890f5caff5a78a63f` |
| schemathesis_config_modernization-v2 | Dockerfile | `seededge/edgebench.judge.schemathesis_config_modernization:function-identity-v2` | `sha256:3386d83a33931de9ffc027fb9204abd96ac45f8bf046a4d557ef59a07c76119e` |
| schemathesis_datagen_pipeline-v2 | Dockerfile | `seededge/edgebench.judge.schemathesis_datagen_pipeline:http-date-v2` | `sha256:2cd61703c3156ce5df060c56ab8daf9aacb964033081186d0407a7244cf63c67` |
| schemathesis_reporting_observability-v2 | Dockerfile | `seededge/edgebench.judge.schemathesis_reporting_observability:junit-coverage-v2.1` | `sha256:668f8683f17a27aafaf3044f62c98837ad8b416aac6c2f2f7bfa3e5003509d07` |
| smt_solver-v2 | Dockerfile | `seededge/edgebench.judge.smt_solver:fdce54253c61-ebv-v2` | `sha256:002e26a1c99b4060b89efa63afcf994aa31039f30d68d6bf9eed4f922bd36420` |
| treant_forest-v2 | Dockerfile | `seededge/edgebench.judge.treant_forest:d47dc1a7da74` | `sha256:46796dfdfa72bfc77a2b100f57766ecc643cbcb1c9a2da4b75d27d1cae1ce94a` |
| tree_block_partitioning-v2 | Dockerfile | `seededge/edgebench.judge.tree_block_partitioning:f74f0ef897ce-ebv-v2` | `sha256:372b2f231aee98b3c2946e770a1d99265563e8b91b7e30992b58780d6ebf48e1` |
| triangulation_coloring_optimization-v2 | Dockerfile | `seededge/edgebench.judge.triangulation_coloring_optimization:convex-flip-v2.1` | `sha256:de42534c84ba6c20260a2298d14af24a8c1cb8361c4294412082668769b7a33c` |
| triangulation_coloring_optimization-v2 | Dockerfile.work | `seededge/edgebench.work.triangulation_coloring_optimization:convex-flip-v2` | `sha256:b38e2a4c0b3bc0da005f4578d3dd958885e64b800ef2507cb919b88acf6d8575` |
| vibrating_path_graph_coloring-v2 | Dockerfile | `seededge/edgebench.judge.vibrating_path_graph_coloring:eb22343ce84e-ebv-v2` | `sha256:3a865757ab8c909eb8c812699b9c0995a7f9e6ef9151a0949a8fe9885f06a620` |
| warehouse_forklift_routing-v2 | Dockerfile | `seededge/edgebench.judge.warehouse_forklift_routing:d342863c29cc-ebv-v2.1` | `sha256:c59c6799a94a3ac363682e4e73c399643a407842aea9e0c969d047be9f73e652` |
