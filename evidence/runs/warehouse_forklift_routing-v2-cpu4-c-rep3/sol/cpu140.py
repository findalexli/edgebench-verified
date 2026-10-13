# EBV control (cpu 140 per input): a fixed 140 s of single-thread CPU work, then the generic valid
# control. 140 s is within the promised 150 s per input (30 s per test case x T=5).
import sys, os, time
_c0 = time.process_time(); _w0 = time.time()
_log = open(f'/ebvtiming/{os.getpid()}.txt', 'w'); _log.write(f'start {_w0:.3f}\n'); _log.flush()
while time.process_time() - _c0 < 140.0:
    pass
exec(compile(open('/opt/ctl/control_solution.py').read(), 'ctl', 'exec'), {'__name__': '__main__'})
sys.stdout.flush()
_log.write(f'end {time.time():.3f} cpu {time.process_time() - _c0:.3f}\n'); _log.close()
