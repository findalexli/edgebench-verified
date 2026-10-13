set -u
O=/job/out; mkdir -p $O
URL=https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/opus-5-5-xhigh-16tasks.tar.zst
command -v zstd >/dev/null || (apt-get update -qq && apt-get install -y -qq zstd) >/dev/null 2>&1
curl -sL "$URL" -o /tmp/r.tar.zst; sha256sum /tmp/r.tar.zst | cut -d' ' -f1 > $O/archive.sha256
mkdir -p /tmp/r && tar -I zstd -xf /tmp/r.tar.zst -C /tmp/r --wildcards '*/lean_analysis_proofs/submissions/*/test_output.txt' '*/lean_analysis_proofs/submissions/*/report.json'
rm -f /tmp/r.tar.zst
ls /tmp/r/*/lean_analysis_proofs/submissions/ > $O/rounds.txt
python3 -I /job/derive.py
echo done > $O/done
