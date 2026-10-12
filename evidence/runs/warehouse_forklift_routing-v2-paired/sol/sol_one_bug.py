# Honest-invalid control: generic control, but a bug corrupts one subcase of one input
# (the input whose first subcase is 17x20 -> judge file 0000): final 'D' dropped.
import sys, io
data = sys.stdin.read()
sys.stdin = io.StringIO(data)
buf = io.StringIO(); real = sys.stdout; sys.stdout = buf
exec(compile(open('/opt/ctl/control_solution.py').read(), 'ctl', 'exec'), {'__name__': '__main__'})
sys.stdout = real
lines = buf.getvalue().split('\n')
tok = data.split()
if tok[1:3] == ['17', '20']:
    lines[0] = lines[0][:-1]
sys.stdout.write('\n'.join(lines))
