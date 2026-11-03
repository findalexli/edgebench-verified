#!/usr/bin/env python3
"""Run one scenario through the judge's own evaluate() with a chosen per-scenario timeout, keeping every raw engine line with a timestamp.

Usage inside the judge image: long_one.py <plugin.js> <scenario.park> <timeout_s> <raw_out_path>
Nothing in the judge changes; subprocess.Popen is wrapped only to tee the engine's stdout and record its exit code.
"""
import importlib.util, json, os, shutil, subprocess, sys, tempfile, threading, time

plugin, scenario, timeout, raw_path = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
os.environ["OPENRCT2_DIR"] = "/home/workspace/openrct2/release/OpenRCT2"  # as eval_openrct2.py sets it
os.chdir("/home/workspace/openrct2")
spec = importlib.util.spec_from_file_location("e", "/judge/openrct2_original_eval.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
real_popen = subprocess.Popen
raw = open(raw_path, "w", buffering=1)
t0 = time.time()
procs = []


class Tee:
    def __init__(self, cmd, **kw):
        self.p = real_popen(cmd, **kw)
        procs.append(self.p)
        r, w = os.pipe()
        self.stdout = os.fdopen(r, "r", buffering=1)
        self._w = os.fdopen(w, "w", buffering=1)
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.p.stdout:
            raw.write("%.2f %s" % (time.time() - t0, line))
            try:
                self._w.write(line)
            except Exception:
                pass
        raw.write("%.2f __ENGINE_EOF__\n" % (time.time() - t0))
        self._w.close()

    def poll(self):
        return self.p.poll()

    def send_signal(self, s):
        return self.p.send_signal(s)

    def wait(self, timeout=None):
        return self.p.wait(timeout=timeout)

    def kill(self):
        return self.p.kill()


e.subprocess.Popen = Tee
d = tempfile.mkdtemp()
shutil.copy(scenario, d)
score = e.evaluate(plugin, d, timeout)
print("Final score: %.4f" % score)
rc = procs[-1].poll() if procs else None
elapsed = time.time() - t0
raw.write("%.2f __ENGINE_RC__ %s\n" % (elapsed, rc))
print("LONG_ONE " + json.dumps({"scenario": os.path.basename(scenario), "timeout": timeout, "norm": score, "engine_rc": rc, "elapsed": round(elapsed, 1)}))
