# Honest near-limit control: generic control, then uses 27 s per test case
# (5 x 27 = 135 s per input), i.e. 90% of the promised "30 seconds per test case".
import sys, time
t0 = time.time()
exec(compile(open('/opt/ctl/control_solution.py').read(), 'ctl', 'exec'), {'__name__': '__main__'})
sys.stdout.flush()
time.sleep(max(0, 135 - (time.time() - t0)))
