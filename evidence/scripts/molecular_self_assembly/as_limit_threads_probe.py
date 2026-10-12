# Does a modest-RSS threaded Python program survive RLIMIT_AS = 1e9 (the proposed repair)?
import resource, subprocess, sys
CHILD = r'''
import threading, resource, sys
n = int(sys.argv[1]); out = []
def work():
    x = [bytearray(64*1024) for _ in range(50)]  # ~3 MiB per thread, malloc'd in thread arena
    out.append(len(x))
ts = [threading.Thread(target=work) for _ in range(n)]
for t in ts: t.start()
for t in ts: t.join()
print("threads", n, "ok", len(out), "maxrss_kib", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
'''
def lim():
    resource.setrlimit(resource.RLIMIT_AS, (1_000_000_000, 1_000_000_000))
for n in (1, 4, 8, 16, 32, 64):
    p = subprocess.run([sys.executable, "-c", CHILD, str(n)], capture_output=True, text=True, preexec_fn=lim)
    print(n, "rc", p.returncode, (p.stdout.strip() or p.stderr.strip().splitlines()[-1] if (p.stdout or p.stderr) else ""))
