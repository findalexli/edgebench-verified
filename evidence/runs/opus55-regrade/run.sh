set -u
O=/job/out; mkdir -p $O/logs
URL=https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/opus-5-5-xhigh-16tasks.tar.zst
command -v zstd >/dev/null || (apt-get update -qq && apt-get install -y -qq zstd patch) >/dev/null 2>&1
(nproc; free -m; lscpu | grep "Model name") > $O/env.txt
curl -sL "$URL" -o /tmp/r.tar.zst; sha256sum /tmp/r.tar.zst > $O/archive.sha256
mkdir -p /tmp/r && tar -I zstd -xf /tmp/r.tar.zst -C /tmp/r --wildcards '*/integer_compression_codec/submissions/*' '*/order_addition_permutation_optimization/submissions/*'
rm -f /tmp/r.tar.zst
IC=$(ls -d /tmp/r/*/integer_compression_codec); OA=$(ls -d /tmp/r/*/order_addition_permutation_optimization)
for P in integer_compression_codec-v2 order_addition_permutation_optimization-v2; do
  (cd /job/repairs/$P && bash materialize.sh > $O/logs/materialize-$P.log 2>&1; echo "rc=$?" >> $O/logs/materialize-$P.log)
done
docker build -t ic_v2 /job/repairs/integer_compression_codec-v2 > $O/logs/build-ic.log 2>&1; echo "rc=$?" >> $O/logs/build-ic.log
docker build -t oa_v2 /job/repairs/order_addition_permutation_optimization-v2 > $O/logs/build-oa.log 2>&1; echo "rc=$?" >> $O/logs/build-oa.log
IC1=seededge/edgebench.judge.integer_compression_codec@sha256:15dffad066b4bd1e4844b3d3798a605c80df8e83db547998b560c28e28e989ac
OA1=seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506f52a5cc7c95680c6df7cd72cb95f81fa236b9794aa507490b947fbd8
grade() { # task_dir sub cwd v1img v2img cpus mem timeout tag
  local S=$1/submissions/$2 W=/tmp/sub_$9_$2
  mkdir -p $W && tar -xzf $S/submission.tar.gz -C $W
  (cd $W && find . -type f | sort | head -80) > $O/logs/$9-$2.files.txt
  local b=$(basename $3); if [ -d $W/$b ] && [ "$(ls -A $W | wc -l)" = 1 ]; then W=$W/$b; fi
  case "$(ls -A $W)" in home) W=$W/home/workspace/$b;; esac
  echo "subdir=$W" >> $O/logs/$9-$2.files.txt
  sha256sum $S/submission.tar.gz >> $O/submissions.sha256
  for V in v1 v2; do
    [ $V = v1 ] && I=$4 || I=$5
    EVAL_SH=$S/eval.sh bash /job/judge_one.sh $I $W $3 $8 $O/logs/$9-$2-$V $6 $7
  done
}
for s in agent-20 agent-3; do grade $IC $s /home/workspace/integer-compression-codec $IC1 ic_v2 4 6g 1200 ic; done
for s in agent-1 auto-6 agent-2; do grade $OA $s /home/workspace/complex_job_scheduling $OA1 oa_v2 2 4g 600 oa; done
docker image inspect ic_v2 oa_v2 $IC1 $OA1 --format '{{.Id}} {{index .RepoTags 0}}' > $O/images.txt 2>&1
echo done > $O/done
