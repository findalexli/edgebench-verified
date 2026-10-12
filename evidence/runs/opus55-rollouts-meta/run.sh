set -u
URL=https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/opus-5-5-xhigh-16tasks.tar.zst
command -v zstd >/dev/null || (apt-get update -qq && apt-get install -y -qq zstd) >/dev/null 2>&1
curl -sL "$URL" -o /tmp/r.tar.zst; sha256sum /tmp/r.tar.zst > /job/out/sha256.txt
mkdir -p /tmp/r && tar -I zstd -xf /tmp/r.tar.zst -C /tmp/r && cd /tmp/r
find . -type f -size -400k ! -name 'agent_output.txt' ! -name '*.tar.gz' ! -name 'allowed_files.txt' -print0 | tar --null -czf /job/out/meta.tar.gz -T -
ls -l /job/out
