# materialize-check-final: clean-machine rebuild of the three revised packages

`src/` is the job's input: `tasks/` and the three packages exactly as committed at `37d30d27`
(`git archive`; the archive sha256 is in `SOURCE`). `run.sh`, `check_pkg.sh`, `verify.py` and `env.sh`
are the scripts of `materialize-check-g1`, unchanged apart from the commit named in a `run.sh` comment.

One fresh E2B worker (`harbor-worker-v4`, 8 CPUs, 7 GiB, 21 GB disk, no images at start). GNU `patch` was
missing and was installed (2.7.6). For each package: `./materialize.sh` unchanged; independent sha256 of every
output against `source-lock.json` (`verify.py lock`); `docker build` of the `Dockerfile`, tagged from
`task.json.in`; the replaced file hashed inside the built image (`verify.py smoke`); then every image and the
build cache removed. Only logs, hashes and image IDs are kept (`result/out/<pkg>/`).

Worker: `status: exit=0`, `killed: true` (`result/worker.json`, `../ledger.jsonl`).

| package | materialize | outputs match lock | docker build | in-image sha256 of the replaced file |
| --- | --- | --- | --- | --- |
| jagua_nesting_optimization-v2 | OK (1 output) | 1/1 | yes, tag `bba393b2dd53-ebv-v2.1` | `/home/workspace/jagua_task_scorer/evaluate.py` `2c3c189e…3f98` = lock |
| ffmpeg_swscale_reimplementation-v2 | OK (1 output) | 1/1 | yes, tag `d3c0aa3fa987-ebv-v2.2` | `/opt/tests/compute_reward.py` `5d02d680…06c0` = lock |
| juliet_vulnerability_analyzer-v2 | OK (1 output) | 1/1 | yes, tag `0c4f2c0057c2-ebv-v2` | `/root/sebench_private/juliet-static-analyzer-evaluator-v3/scoring/score.py` `d18d481c…b09b` = lock |

Each build's base image ID is the pinned digest of the original judge image (`result.env`).
