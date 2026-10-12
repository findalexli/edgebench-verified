"""Size of the formula difference on the real test horizon (242 aligned NAV points, k=252/242)
with the real benchmark period return 0.248026 (from run_full.out). Pure Python."""
k = 252 / 242; b = 0.24802604023906616
def sc(x):  # score_excess_return copy (eval_script.py lines 1000-1012)
    return 20.0 if x >= 0.12 else (20.0 * x / 0.12 if x >= 0 else max(-10.0, 10.0 * x / 0.10))
worst = (0, None)
for i in range(-300, 1001):
    a = i / 1000
    f = (1 + a - b) ** k - 1; g = (1 + a) ** k - (1 + b) ** k
    d = abs(sc(g) - sc(f))
    if d > worst[0]: worst = (d, (a, f, g, sc(f), sc(g)))
    if i % 100 == 0: print(f'a={a:+.2f} orig={f:+.5f} contract={g:+.5f} diff_pp={100*(g-f):+.3f} score_orig={sc(f):+.3f} score_contract={sc(g):+.3f}')
print('max |excess-score difference| over a in [-0.30,1.00]:', worst)
