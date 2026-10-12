#!/usr/bin/env python3
"""Differential test: original tester bytes (tools/bin/tester, executed in-process with argv
patched) vs the independent oracle_sim.py, on random biased command strings.
Usage: diff_fuzz.py <tester_path> <n_trials> [seed]"""
import sys, io, os, random, tempfile, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle_sim as O

tester_src = open(sys.argv[1]).read()
code = compile(tester_src.replace('if __name__ == "__main__":\n    main()', ''), 'tester', 'exec')
N = int(sys.argv[2]); rnd = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
tmp = tempfile.mkdtemp()


def run_tester(inp, out):
    fi, fo = os.path.join(tmp, 'i'), os.path.join(tmp, 'o')
    open(fi, 'w').write(inp); open(fo, 'w').write(out)
    ns = {'__name__': 'tester'}; exec(code, ns)
    err = io.StringIO(); sys.argv = ['tester', fi, fo]; rc = 0
    with contextlib.redirect_stderr(err):
        try:
            ns['main']()
        except SystemExit as e:
            rc = e.code or 0
    return rc, err.getvalue().strip()


def biased_string(R, C, arr, illegal_p):
    """Random agent that mostly respects the PROMPT rules; occasionally emits anything."""
    n = R * C - 1; occ = {}; pos = (0, 0); cargo = None; k = 0; nxt = 1; s = []
    for _ in range(rnd.randint(1, 400)):
        if nxt == n + 1:
            break
        if rnd.random() < illegal_p:
            s.append(rnd.choice(['N', 'S', 'E', 'W', 'P', 'D', 'L', 'U', 'LN', 'UE', 'X', 'LS', 'US']))
            break
        opts = []
        for ch, (dr, dc) in O.DIRS.items():
            q = (pos[0] + dr, pos[1] + dc)
            if not (0 <= q[0] < R and 0 <= q[1] < C):
                continue
            if cargo is None or q not in occ:
                opts.append((ch, q, 'm'))
            if cargo is None and q in occ:
                opts.append(('L' + ch, q, 'l'))
            if cargo is not None and q not in occ:
                opts.append(('U' + ch, q, 'u'))
        if pos == (0, 0) and cargo is None and k < n:
            opts += [('P', None, 'p')] * 3
        if pos == (0, 0) and cargo == nxt and k == n:
            opts += [('D', None, 'd')] * 5
        if not opts:
            break
        ch, q, t = rnd.choice(opts)
        s.append(ch)
        if t == 'm': pos = q
        elif t == 'l': cargo = occ.pop(q)
        elif t == 'u': occ[q] = cargo; cargo = None
        elif t == 'p': cargo = arr[k]; k += 1
        elif t == 'd': cargo = None; nxt += 1
    return ''.join(s)


agree = disagree = accepted = 0
for trial in range(N):
    R, C = rnd.choice([(2, 2), (2, 3), (3, 2), (3, 3), (6, 6)])
    n = R * C - 1
    T = rnd.randint(1, 2); cases = []; lines = []
    for _ in range(T):
        a = list(range(1, n + 1))
        while True:
            rnd.shuffle(a)
            if a[-1] != 1: break
        cases.append((R, C, a[:]))
        lines.append(biased_string(R, C, a, rnd.choice([0, 0, 0.002, 0.02])))
    inp = "%d\n" % T + ''.join("%d %d\n%s\n" % (R, C, ' '.join(map(str, a))) for R, C, a in cases)
    out = '\n'.join(lines) + '\n'
    rc, msg = run_tester(inp, out)
    ok, v = O.score_file(inp, out, 'prompt')
    t_ok = (rc == 0 and msg.startswith('Score ='))
    same = (t_ok == ok) and (not ok or msg == "Score = %.1f" % float(v))
    agree += same; disagree += (not same); accepted += t_ok
    if not same and disagree <= 5:
        print("DISAGREE", R, C, repr(out[:120]), rc, msg, ok, v)
print("trials", N, "agree", agree, "disagree", disagree, "tester-accepted", accepted)

# ---- part 2: valid control outputs (generic solver) and single-edit mutations of them
import importlib.util
spec = importlib.util.spec_from_file_location('ctl', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'control_solution.py'))
src = open(spec.origin).read().replace('\nmain()\n', '\n')
ctl = {}; exec(compile(src, 'ctl', 'exec'), ctl)
agree2 = dis2 = acc2 = orig_rej = 0
for trial in range(max(1, N // 10)):
    R, C = rnd.choice([(2, 2), (2, 3), (3, 3), (3, 4), (6, 6), (6, 9)])
    n = R * C - 1
    a = list(range(1, n + 1))
    while True:
        rnd.shuffle(a)
        if a[-1] != 1: break
    s = ctl['solve'](R, C, a)
    if trial % 2:
        j = rnd.randrange(len(s)); op = rnd.choice('dri')
        ch = rnd.choice('NSEWPDLUX')
        s = s[:j] + (ch if op != 'd' else '') + s[j + (op != 'i'):]
    inp = "1\n%d %d\n%s\n" % (R, C, ' '.join(map(str, a)))
    out = s + '\n'
    rc, msg = run_tester(inp, out)
    ok, v = O.score_file(inp, out, 'prompt')
    t_ok = (rc == 0 and msg.startswith('Score ='))
    same = (t_ok == ok) and (not ok or msg == "Score = %.1f" % float(v))
    agree2 += same; dis2 += (not same); acc2 += t_ok
    if t_ok and not O.score_file(inp, out, 'original')[0]:
        orig_rej += 1
    if not same and dis2 <= 5:
        print("DISAGREE2", R, C, rc, msg, ok, v)
print("part2 trials", max(1, N // 10), "agree", agree2, "disagree", dis2, "tester-accepted", acc2,
      "accepted-but-illegal-under-CodeChef-rules", orig_rej)
