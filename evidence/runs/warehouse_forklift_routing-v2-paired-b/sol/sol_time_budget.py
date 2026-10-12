# Honest time-budget control: generic control, then uses 13 s per test case
# (5 x 13 = 65 s per input), i.e. under half of the promised "30 seconds per test case".
import sys, io, time
t0 = time.time()
exec(compile(open('/opt/ctl/control_solution.py').read(), 'ctl', 'exec'), {'__name__': '__main__'})
sys.stdout.flush()
time.sleep(max(0, 65 - (time.time() - t0)))
