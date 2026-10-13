#!/bin/bash
# Regrade archived submissions of the third-party Opus 5.5 run with the original grader (digest-pinned
# public judge image) and the fixed grader (built here from the repair package: materialize.sh, then
# docker build). plan.txt lines: "<task> <round> <rep>"; each line grades that submission with v1 then v2,
# one container at a time. Raw captures go to /job/out/raw/ (moved out of the repository after collection;
# only derived scores, verdicts and hashes are kept). The archive is not redistributed.
set -u
START=$(date +%s); DEADLINE=$((START + ${INNER_BUDGET:-3100}))
O=/job/out; mkdir -p $O/raw $O/logs
URL=https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/opus-5-5-xhigh-16tasks.tar.zst
command -v zstd >/dev/null && command -v patch >/dev/null || (apt-get update -qq && apt-get install -y -qq zstd patch) >/dev/null 2>&1
{ nproc; free -m; df -h / | tail -1; lscpu | grep "Model name"; docker version --format '{{.Server.Version}}'; } > $O/env.txt 2>&1
# task -> v1 judge image, cwd, eval_timeout, per-eval time estimate on this worker (s, for the deadline guard)
declare -A V1 CWD TO EST PKG
V1[graph_node_classification]=seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd
V1[tree_block_partitioning]=seededge/edgebench.judge.tree_block_partitioning@sha256:6ebbb44ab188660b15d260143e942ddcf0ba3bceb0bb7d7c78e976b1a36669d2
V1[schemathesis_config_modernization]=seededge/edgebench.judge.schemathesis_config_modernization@sha256:ff71a766c254fc62f6ffd12d877297cb22223a0bb2190e91f95fe6b3231d519e
V1[juliet_vulnerability_analyzer]=seededge/edgebench.judge.juliet_vulnerability_analyzer@sha256:792f6fb1223e2fcff71ca3af025babbebbb2ba4d0b3c02c65c4e9470886e2157
V1[molecular_self_assembly]=seededge/edgebench.judge.molecular_self_assembly@sha256:8afd932de7e54bacee44bcc33ceb4dab1125ad563aa81c1141717f1fc25c6da5
V1[integer_compression_codec]=seededge/edgebench.judge.integer_compression_codec@sha256:15dffad066b4bd1e4844b3d3798a605c80df8e83db547998b560c28e28e989ac
V1[order_addition_permutation_optimization]=seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506f52a5cc7c95680c6df7cd72cb95f81fa236b9794aa507490b947fbd8
CWD[graph_node_classification]=/home/workspace/045_graph_node_classification; TO[graph_node_classification]=1800; EST[graph_node_classification]=45
CWD[tree_block_partitioning]=/home/workspace/p1; TO[tree_block_partitioning]=600; EST[tree_block_partitioning]=330
CWD[schemathesis_config_modernization]=/app; TO[schemathesis_config_modernization]=1800; EST[schemathesis_config_modernization]=60
CWD[juliet_vulnerability_analyzer]=/home/workspace/juliet-static-analyzer/agent-start; TO[juliet_vulnerability_analyzer]=180; EST[juliet_vulnerability_analyzer]=20
CWD[molecular_self_assembly]=/home/workspace/molecules; TO[molecular_self_assembly]=600; EST[molecular_self_assembly]=640
CWD[integer_compression_codec]=/home/workspace/integer-compression-codec; TO[integer_compression_codec]=2400; EST[integer_compression_codec]=120
CWD[order_addition_permutation_optimization]=/home/workspace/complex_job_scheduling; TO[order_addition_permutation_optimization]=600; EST[order_addition_permutation_optimization]=10
TASKS=$(awk 'NF && $1 !~ /^#/ {print $1}' /job/plan.txt | sort -u)
PAT=(); for t in $TASKS; do PAT+=("*/$t/submissions/*/submission.tar.gz" "*/$t/submissions/*/allowed_files.txt" "*/$t/submissions/*/eval.sh"); done
curl -sL "$URL" -o /tmp/r.tar.zst; sha256sum /tmp/r.tar.zst | cut -d' ' -f1 > $O/archive.sha256
mkdir -p /tmp/r && tar -I zstd -xf /tmp/r.tar.zst -C /tmp/r --wildcards "${PAT[@]}" > $O/logs/extract.log 2>&1; echo "rc=$?" >> $O/logs/extract.log
rm -f /tmp/r.tar.zst
for t in $TASKS; do
  docker pull -q ${V1[$t]} > $O/logs/pull-$t.log 2>&1; echo "rc=$?" >> $O/logs/pull-$t.log
  (cd /job/pkg/$t-v2 && bash materialize.sh > $O/logs/materialize-$t.log 2>&1; echo "rc=$?" >> $O/logs/materialize-$t.log)
  docker build -t ebv-rg2/$t:v2 /job/pkg/$t-v2 > $O/logs/build-$t.log 2>&1; echo "rc=$?" >> $O/logs/build-$t.log
  echo "$t v1 $(docker image inspect ${V1[$t]} --format '{{.Id}}') v2 $(docker image inspect ebv-rg2/$t:v2 --format '{{.Id}}')" >> $O/images.txt
done
echo "setup_s=$(( $(date +%s) - START ))" > $O/progress.txt
while read -r t r rep; do
  [ -z "$t" ] && continue; case "$t" in \#*) continue;; esac
  S=$(ls -d /tmp/r/*/$t/submissions/$r 2>/dev/null | head -1)
  L=$t.$r.rep$rep
  if [ -z "$S" ] || [ ! -f "$S/eval.sh" ]; then echo "$L missing" >> $O/progress.txt; continue; fi
  if [ $(( $(date +%s) + 2 * ${EST[$t]} )) -gt $DEADLINE ]; then echo "$L skipped-deadline" >> $O/progress.txt; continue; fi
  [ -f $O/raw/$t.$r.sha256 ] || (cd $S && sha256sum submission.tar.gz eval.sh allowed_files.txt 2>/dev/null) > $O/raw/$t.$r.sha256
  for V in v1 v2; do
    [ $V = v1 ] && I=${V1[$t]} || I=ebv-rg2/$t:v2
    bash /job/judge.sh $I $S ${CWD[$t]} ${TO[$t]} $O/raw/$L.$V 4 6g
  done
  echo "$L done $(( $(date +%s) - START ))" >> $O/progress.txt
done < /job/plan.txt
docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' > $O/logs/images-ls.txt 2>&1
echo done > $O/done
