# Reproduce the ANN flat/empty integration check

This runs the maintained SForge CLI against the **unchanged original ANN judge** with two declared submissions: exact FAISS flat search and an empty-result countercontrol. The accepted run completed archive upload, original evaluation, output collection, grading and normalization: one OK result at raw QPS 19, one WA at zero, and a valid two-case report. QPS 19 normalizes to zero because it is below the task’s 3,108 baseline. It is not a failed run.

Use an authorized, dedicated **Linux x86-64 Docker host** with rootful Docker, Bash, Python 3, `sudo`, `iptables` and GNU `timeout`. Allow at least 4 GiB RAM and sufficient disk for the pinned judge image and runtime build; preserve the audit host’s existing resource guard if running within this project. The judge receives one CPU and 2 GiB memory; the trusted CLI receives one CPU and 512 MiB. This is CPU work, with no model, API key or cloud coordinator required. Do not run these firewall commands on a shared Docker host.

The [task definition](../../tasks/ann_vector_search_qps.json) and [benchmark configuration](../../tasks/BENCHMARK.yaml) already live in this checkout. The [image lock](image-lock.json) pins the original work and judge images; only the judge is needed here. The [source inventory](../../evidence/selected/maintained-core-runtime-inventory.json), [runtime record](../../evidence/selected/maintained-core-runtime.json) and [version lock](../../evidence/selected/maintained-core-runtime-versions.txt) bind the existing 63 core files and 45 installed package versions. The accepted ANN run used CPython 3.12.15 on Debian 12, whereas the earlier CI record used Ubuntu. This recipe uses the same pinned Debian/Python base and version lock, not an identical rebuilt image or wheel-byte lock. Optional E2B is not installed or tested.

## Prepare the exact inputs

Run from the repository root in one Bash shell. This checks local identities without executing the task:

```bash
set -euo pipefail
ANN_REPO=$(pwd -P)
ANN_PACKAGE="$ANN_REPO/reproductions/ann-original-cli"
python3 "$ANN_PACKAGE/check.py"
test -z "$(docker ps -aq)"  # dedicated daemon: no existing containers
ANN_JUDGE='seededge/edgebench.judge.ann_vector_search_qps@sha256:aa2856a379c10b93b0661a0b91b729a80fc2cf9bf119cc1385beea6b93eef288'
ANN_ALIAS='edgebench.judge.ann_vector_search_qps:9171f6b6de41'
ANN_JUDGE_ID='sha256:a285f995eab4dc78c02354ceec593ca936e954eb9e34d67d7524e7ca2bc49de8'
ANN_PYTHON='python@sha256:2ed6491b93cd49272ee6de2b5a38440c3448360322c089fc23e370722d74179d'
timeout 150s docker pull --platform linux/amd64 "$ANN_JUDGE"
test "$(docker image inspect --format '{{.Id}}' "$ANN_JUDGE")" = "$ANN_JUDGE_ID"
if docker image inspect "$ANN_ALIAS" >/dev/null 2>&1; then
  test "$(docker image inspect --format '{{.Id}}' "$ANN_ALIAS")" = "$ANN_JUDGE_ID"
else
  docker tag "$ANN_JUDGE" "$ANN_ALIAS"
fi
timeout 90s docker pull --platform linux/amd64 "$ANN_PYTHON"
test "$(docker image inspect --format '{{.Id}}' "$ANN_PYTHON")" = 'sha256:4f228bc1cbcfc794e4878312cfc241d368eff55a21c08d1e2bb263116c4ef524'
ANN_RUN_ID="ann-reproduction-$(date -u +%Y%m%dT%H%M%S)-$$"
ANN_RUNTIME="edgebench-ann-reproduction:$ANN_RUN_ID"
DOCKER_BUILDKIT=0 timeout 180s docker build --pull=false --network default \
  --memory 512m --cpu-period 100000 --cpu-quota 100000 \
  -f "$ANN_PACKAGE/Dockerfile" -t "$ANN_RUNTIME" "$ANN_REPO"
ANN_RUNTIME_ID=$(docker image inspect --format '{{.Id}}' "$ANN_RUNTIME")
```

The build installs the existing version lock and checks all 45 expected versions. It copies the unchanged maintained core, not the coordinator. Package-index availability and build-isolation tools are external dependencies; a failed pull or build is a setup result, not evidence about ANN correctness. Do not silently substitute a different image or package version.

## Run the unchanged CLI with network isolation

The stock Docker backend does **not** enforce the task’s `internet=false` field. The accepted run used three external DROP rules on an otherwise empty dedicated daemon. The following commands reproduce that isolation on a host with the standard `docker0` bridge and IPv6 disabled. Only the trusted CLI gets the Docker socket; the task container does not.

Continue in the same shell. The cleanup trap removes only this run’s exact container names and tagged rules, including on timeout. It leaves downloaded images and your output directory intact.

```bash
docker network inspect bridge | python3 -c 'import json,sys; n=json.load(sys.stdin); assert len(n)==1 and n[0]["Driver"]=="bridge" and n[0]["EnableIPv6"] is False and n[0].get("Options",{}).get("com.docker.network.bridge.name","docker0")=="docker0"'
ANN_OUTPUT=$(mktemp -d "${TMPDIR:-/tmp}/ann-reproduction.XXXXXX")
ANN_CLI_NAME="ann-cli-$ANN_RUN_ID"
ANN_JUDGE_NAME="edgebench.judge.ann_vector_search_qps.$ANN_RUN_ID"
ANN_RULES_STARTED=0
cleanup_ann() {
  local name expected actual failed=0
  for name in "$ANN_CLI_NAME" "$ANN_JUDGE_NAME"; do
    if actual=$(docker inspect --format '{{.Image}}' "$name" 2>/dev/null); then
      expected="$ANN_RUNTIME_ID"
      if [ "$name" = "$ANN_JUDGE_NAME" ]; then expected="$ANN_JUDGE_ID"; fi
      if [ "$actual" = "$expected" ]; then
        docker rm -f "$name" >/dev/null || failed=1
      else
        echo "Cleanup image identity mismatch: $name" >&2
        failed=1
      fi
    fi
  done
  if [ "$ANN_RULES_STARTED" = 1 ]; then
    for spec in 'INPUT -i' 'FORWARD -o' 'FORWARD -i'; do
      read -r chain direction <<< "$spec"
      if sudo iptables -w 5 -C "$chain" "$direction" docker0 -m comment --comment "$ANN_RUN_ID" -j DROP 2>/dev/null; then
        sudo iptables -w 5 -D "$chain" "$direction" docker0 -m comment --comment "$ANN_RUN_ID" -j DROP || failed=1
      fi
    done
  fi
  return "$failed"
}
trap 'saved_status=$?; trap - EXIT; cleanup_ann || saved_status=1; exit "$saved_status"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
sudo -v
ANN_RULES_STARTED=1
for spec in 'FORWARD -i' 'FORWARD -o' 'INPUT -i'; do
  read -r chain direction <<< "$spec"
  sudo iptables -w 5 -I "$chain" "$direction" docker0 -m comment --comment "$ANN_RUN_ID" -j DROP
  sudo iptables -w 5 -C "$chain" "$direction" docker0 -m comment --comment "$ANN_RUN_ID" -j DROP
done

timeout --signal=TERM --kill-after=10s 880s docker run --rm \
  --name "$ANN_CLI_NAME" --network none --cpus 1 \
  --memory 512m --memory-swap 512m --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
  --mount "type=bind,source=$ANN_REPO,target=/repo,readonly" \
  --mount "type=bind,source=$ANN_OUTPUT,target=/output" \
  "$ANN_RUNTIME" python -B -m sforge \
  --tasks-dir /repo/tasks --log-dir /output/logs eval \
  --backend docker --task ann_vector_search_qps \
  --archive /repo/reproductions/ann-original-cli/controls.tar.gz \
  --run-id "$ANN_RUN_ID" --judge-cpu-limit 1 --judge-mem-limit 2g \
  --timeout 850 --json >"$ANN_OUTPUT/cli.log" 2>&1

cleanup_ann
ANN_RULES_STARTED=0
trap - EXIT INT TERM
ANN_REPORT="$ANN_OUTPUT/logs/runs/$ANN_RUN_ID/ann_vector_search_qps/submissions/manual-1/report.json"
python3 "$ANN_PACKAGE/check.py" --report "$ANN_REPORT"
printf 'Local result directory: %s\n' "$ANN_OUTPUT"
```

The CLI timeout is 850 seconds, with an 880-second outer cap and ten seconds to stop the client. The accepted run took about 545 seconds in the CLI, including about 529 seconds reported for evaluation. A slower host can hit the cap; retain that incomplete outcome rather than treating it as a rejected algorithm or retrying automatically. If the shell or host is killed without running traps, recover the exact saved run ID and remove only its named containers and three tagged rules.

## Read the result

`report.json` and its sibling `test_output.txt` are the actual CLI outputs. `check.py --report` checks two cases, one OK with positive raw QPS and one WA at zero, `valid=true`, `timed_out=false`, pass rate 0.5, and the task’s clipped logarithmic normalization. The intentionally bad control explains the one failed case. Exact QPS and case ordering are not fixed acceptance thresholds.

The [readable control source](controls/ann_benchmarks/algorithms/custom/module.py) and [configuration](controls/ann_benchmarks/algorithms/custom/config.yml) are byte-identical to the three files inside the accepted 811-byte [submission archive](controls.tar.gz). These are disclosed audit controls, not an independent model solution. Flat search uses training vectors and the supplied query only; it does not read ground-truth neighbors or modify timing. The empty control returns no neighbors.

[Observed projection](observed-result.json), [root acceptance](../../evidence/selected/ann-cli-integration-acceptance.json) and [different review](../../evidence/selected/ann-cli-integration-review.json) document the completed native run. The reviewer checked saved projections and hashes; original raw logs were not exported. This simplified checkout recipe has been checked for source/archive identity and command syntax, not executed as an additional native run. The successful underlying path is the accepted CLI run. No historical baseline, hardware-independent throughput, untouched holdout, model competence or whole-task certification is claimed here.

## Data and attribution

The judge image already contains the 525,128,288-byte SIFT HDF5 file identified by [data-manifest.json](data-manifest.json); this Git package contains no vectors or private evaluator source. Martin Aumüller’s [ANN-Benchmarks reproducibility record](https://doi.org/10.5281/zenodo.4607761), published March 16, 2021, declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit the associated work by Aumüller, Bernhardsson and Faithfull, *ANN-Benchmarks: A Benchmarking Tool for Approximate Nearest Neighbor Algorithms*. One fully hashed archive-member occurrence matches the installed file. Archive-wide uniqueness, historical installation lineage and blanket rights to all image contents are not established by that association. This package makes no dataset modifications and requires authorized access to the pinned image.

Task definitions retain the [upstream task license](../../tasks/LICENSE) and ByteDance Seed attribution; maintained harness code retains [Apache-2.0](../../LICENSE). Our declared controls and packaging are audit additions. The unchanged original task, maintained harness version and authored control submission remain distinct.
