set -u
cd /job
URL=https://huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts/resolve/main/opus-5-5-xhigh-16tasks.tar.zst
command -v zstd >/dev/null || (apt-get update -qq && apt-get install -y -qq zstd) >/dev/null 2>&1
curl -sL "$URL" -o /tmp/r.tar.zst; ls -l /tmp/r.tar.zst > out/download.txt; sha256sum /tmp/r.tar.zst >> out/download.txt
mkdir -p /tmp/r && tar -I zstd -xf /tmp/r.tar.zst -C /tmp/r
cd /tmp/r
find . -maxdepth 3 -type d | sort > /job/out/dirs.txt
find . -type f | awk -F/ '{n=split($0,a,"/"); print $0}' | wc -l > /job/out/nfiles.txt
find . -type f -printf '%s %p\n' | sort -k2 > /job/out/files.txt
mkdir -p /job/out/meta
find . \( -name final_result.json -o -name '*.json' -size -200k -path '*result*' -o -name 'README*' -o -name '*.yaml' -size -50k \) -print0 | while IFS= read -r -d '' f; do mkdir -p "/job/out/meta/$(dirname "$f")"; cp "$f" "/job/out/meta/$f"; done
du -sh /tmp/r > /job/out/du.txt
