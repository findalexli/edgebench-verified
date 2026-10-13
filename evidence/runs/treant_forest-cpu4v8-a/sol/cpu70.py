# EBV CPU-measurement wrapper (honest control + fixed work). Runs the honest control BASE first (its stdout
# captured), then does fixed extra work: MODE 'cpu' = until this process has used W CPU-seconds in total
# (control + busy loop); MODE 'wall' = until W seconds of wall clock since start (a deadline-driven search).
# Then prints the control's (valid) answer. Start/end wall time and CPU used go to /ebvtiming/<pid>.txt.
import sys, os, io, time, runpy, contextlib
MODE, W, BASE = 'cpu', 70.0, '/ebvsol/base.py'
w0 = time.time(); c0 = time.process_time()
try:
    _log = open(f'/ebvtiming/{os.getpid()}.txt', 'w'); _log.write(f'start {w0:.3f}\n'); _log.flush()
except Exception:
    _log = None
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    try:
        runpy.run_path(BASE, run_name='__main__')
    except SystemExit as e:
        if e.code not in (None, 0):
            raise
cb = time.process_time() - c0
if MODE == 'cpu':
    while time.process_time() - c0 < W:
        pass
else:
    while time.time() - w0 < W:
        pass
sys.stdout.write(buf.getvalue()); sys.stdout.flush()
if _log:
    _log.write(f'end {time.time():.3f} wall {time.time() - w0:.3f} cpu {time.process_time() - c0:.3f} base_cpu {cb:.3f}\n'); _log.close()
