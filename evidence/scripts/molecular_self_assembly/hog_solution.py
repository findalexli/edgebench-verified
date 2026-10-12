# Baseline molecular output plus a deliberately touched allocation of HOG_MB MiB.
# HOG_MB is substituted by run_memory_probe.sh. Peak RSS is appended to /tmp/rss.log.
import sys, os, resource
HOG_MB = __HOG_MB__
buf = bytearray(HOG_MB * 1024 * 1024)
for i in range(0, len(buf), 4096):
    buf[i] = 1
data = sys.stdin.read().split()
N, T, M, K, L = (int(x) for x in data[:5])
out = []
for comp in range(M):
    base = comp * K
    for off in range(1, K):
        out.append(f"0 {base} {base+off}")
sys.stdout.write("\n".join(out[:N - M]) + "\n")
with open("/tmp/rss.log", "a") as f:
    f.write(f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024}\n")
