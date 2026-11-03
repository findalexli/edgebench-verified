# 8 vCPU / 8 GiB worker: official is 16 CPUs, 16g. 16 solver processes stay as in judge/run.sh.
export SEVAL_ARGS="--judge-cpu-limit 8 --judge-mem-limit 7g"
sed -i 's/^cpus = 16/cpus = 8/; s/^memory = "16g"/memory = "7g"/' base/edgebench/tasks/$T/task.toml new/edgebench/tasks/$T/task.toml
/job/v/bin/python /job/stack_fix.py {base,new}/edgebench/tasks/$T/judge/smt_judge/scripts/evaluate.py {base,new}/edgebench/tasks/$T/environment/workspace/scripts/evaluate.py
