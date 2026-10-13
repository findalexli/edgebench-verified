"""Bound on the score change from the fix, for the fixed test data (b, N from threshold-v1.log and
the original review run_full.out). 50-digit decimal arithmetic; a sweep, not a proof.
The first part ignores the grader's 4-decimal rounding; the last part models it."""
from decimal import Decimal as D, getcontext
getcontext().prec = 50
def sc(x):
    if x >= D('0.12'): return D(20)
    if x >= 0: return 20*x/D('0.12')
    return max(D(-10), 10*x/D('0.10'))
for N, b in ((243, D('0.24275476264749218')), (242, D('0.24802604023906616'))):
    k = D(252)/D(N)
    eC = lambda a: (1+a)**k - (1+b)**k
    eG = lambda a: (1+a-b)**k - 1
    # peak of excess-score difference: a* where eC = 0.12 (eG just below the cap)
    astar = (D('0.12') + (1+b)**k) ** (1/k) - 1
    peak = 20 - sc(eG(astar))
    # negative side: a where eG = -0.10 (eC already below), and grid
    best = (D(0), None); rmax = D(0)
    a = D('-0.30')
    while a <= D('1.00'):
        d = abs(sc(eC(a)) - sc(eG(a)))
        if d > best[0]: best = (d, a)
        if a > b:
            r = eC(a)/eG(a)
            if r > rmax: rmax = r
        a += D('0.0005')
    # ratio at a -> b limit: (1+b)^(k-1)
    rlim = (1+b)**(k-1)
    print(f'N={N} k=252/{N} b={b}: a*={astar:.8f} eG(a*)={eG(astar):.10f} peak_excess_score_diff={peak:.6f} (4dp-rounded installed: {20 - sc(round(eG(astar),4)):.4f})')
    print(f'   grid max |score diff| over a in [-0.30,1.00] step 0.0005: {best[0]:.6f} at a={best[1]}')
    print(f'   max eC/eG on grid, a in (b, 1.00]: {rmax:.8f}; limit a->b: {rlim:.8f}')
    ir_b = 10*D('2.5')*(max(rmax, rlim)-1)/D('2.0'); so_b = 10*D('4.0')*(max(rmax, rlim)-1)/D('3.5')
    print(f'   IR-score change <= {ir_b:.4f}; Sortino-score change <= {so_b:.4f}; sum with peak: {peak+ir_b+so_b:.4f}')
# Downward side: negative excess, where the information-ratio and Sortino parts are 0 under both
# versions (below their pass lines), so only the excess part can fall.
for N, b in ((243, D('0.24275476264749218')), (242, D('0.24802604023906616'))):
    k = D(252)/D(N); best = (D(0), None); a = D('-0.30')
    while a < b:
        d = sc((1+a-b)**k - 1) - sc((1+a)**k - (1+b)**k)
        if d > best[0]: best = (d, a)
        a += D('0.0001')
    print(f'N={N}: largest fall of the excess part for negative excess, a in [-0.30, b) step 0.0001: {best[0]:.6f} at a={best[1]}')

# ---------------------------------------------------------------------------------------------
# With the grader's 4-decimal rounding. eval_script.py:957-959 rounds excess_return_annual,
# information_ratio and sortino_ratio to 4 decimals before the score functions are applied
# (eval_script.py:1994-1996, 2130-2132). The sweeps above ignore this rounding; these below model it.
from decimal import ROUND_HALF_EVEN
r4 = lambda x: x.quantize(D('0.0001'), rounding=ROUND_HALF_EVEN)
def lin(x, lo, hi): return D(0) if x <= lo else D(10) if x >= hi else 10*(x-lo)/(hi-lo)
IR_LO, IR_HI, SO_LO, SO_HI = D('0.5'), D('2.5'), D('0.5'), D('4.0')
# Rounding a ratio to 4 decimals moves its linear part by at most 10*0.00005/(hi-lo); the rise is a
# difference of two such parts, so the rounding can add at most twice that to the unrounded optimum.
SLACK = 2*10*D('0.00005')/(IR_HI-IR_LO) + 2*10*D('0.00005')/(SO_HI-SO_LO)
for N, b in ((243, D('0.24275476264749218')), (242, D('0.24802604023906616'))):
    k = D(252)/D(N)
    eC = lambda a: (1+a)**k - (1+b)**k
    eG = lambda a: (1+a-b)**k - 1
    # Excess part, exact peak: the smallest a whose fixed excess rounds to 0.1200 is where eC = 0.11995
    # (half-even rounds 0.11995 up to 0.1200); there the original excess is lowest while the fixed part is 20.
    a_lo = (D('0.11995') + (1+b)**k) ** (1/k) - 1
    peak_r = 20 - sc(r4(eG(a_lo)))
    up = (D(0), None); dn = (D(0), None); joint = (D(0), None); joint_r = (D(0), None)
    ir_max = D(0); so_max = D(0)
    a = D('-0.30')
    while a <= D('1.00'):
        c, g = eC(a), eG(a)
        d = sc(r4(c)) - sc(r4(g))
        if d > up[0]: up = (d, a)
        if -d > dn[0]: dn = (-d, a)
        if c > 0:
            rho = g/c
            # Unrounded optimum of each ratio part: choose the risk measure so that the fixed ratio sits
            # exactly at its full-marks line (a larger risk measure lowers both parts' gap; a smaller one caps the fixed part while the original part rises).
            ir_u = lin(IR_HI, IR_LO, IR_HI) - lin(IR_HI*rho, IR_LO, IR_HI)
            so_u = lin(SO_HI, SO_LO, SO_HI) - lin(SO_HI*rho, SO_LO, SO_HI)
            # The same choice evaluated with the grader's rounding.
            TE, DD = c/IR_HI, c/SO_HI
            ir_r = lin(r4(c/TE), IR_LO, IR_HI) - lin(r4(g/TE), IR_LO, IR_HI)
            so_r = lin(r4(c/DD), SO_LO, SO_HI) - lin(r4(g/DD), SO_LO, SO_HI)
            ir_max = max(ir_max, ir_u); so_max = max(so_max, so_u)
            if d + ir_u + so_u > joint[0]: joint = (d + ir_u + so_u, a)
            if d + ir_r + so_r > joint_r[0]: joint_r = (d + ir_r + so_r, a)
        a += D('0.00001')
    print(f'N={N} with 4-dp rounding, a in [-0.30,1.00] step 0.00001:')
    print(f'   excess part: largest rise {up[0]:.4f} at a={up[1]} (exact peak at a={a_lo:.8f}: {peak_r:.4f}); largest fall {dn[0]:.4f} at a={dn[1]}')
    print(f'   per-part maxima (not additive): excess {up[0]:.4f}, IR {ir_max:.4f}, Sortino {so_max:.4f}')
    print(f'   joint rise (all three parts at the same a): {joint_r[0]:.4f} at a={joint_r[1]} with the risk measures at the full-marks lines;'
          f' upper bound with any risk measures {joint[0]:.4f} + rounding slack {SLACK:.4f} = {joint[0]+SLACK:.4f}')
