#!/bin/bash
# status.sh: one line per e2e sweep job: state, last controller line, submissions so far, Gemini calls.
cd /home/alex/edgebench-verified/evidence/runs
for l in e2e-gemini-s2h-*.launch.log; do
  j=${l%.launch.log}; st=$(grep -o '"status": "[^"]*"' $l | tail -1 | cut -d'"' -f4); [ -z "$st" ] && st=running
  c=$(ls $j/result/out.tar.gz $j/result/ckpt-* 2>/dev/null | tail -1); n=-; k=-; last=-
  if [ -n "$c" ]; then
    n=$(tar -tzf $c 2>/dev/null | grep -c '/submissions/.*/report.json'); k=$(tar -xzOf $c out/proxy.jsonl 2>/dev/null | wc -l)
    last=$(tar -xzOf $c out/run.log 2>/dev/null | tail -1 | cut -c1-60)
  fi
  printf '%-62s %-10s subs=%-3s calls=%-4s %s\n' ${j#e2e-gemini-s2h-} "$st" $n $k "$last"
done
