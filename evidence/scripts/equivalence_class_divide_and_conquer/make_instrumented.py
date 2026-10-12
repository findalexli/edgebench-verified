"""Create checker_true_cost.cpp from the original checker.cpp: same code, but the
final cost sweep covers state indices 0..tt (the original covers 0..tt-1) and the
total is printed to stderr. Usage: python3 -I make_instrumented.py checker.cpp out.cpp"""
import sys
src = open(sys.argv[1], newline="").read()
reps = [
 ("std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt,", "std::iota(oq, oq+tt+1, 0), std::sort(oq, oq+tt+1,"),
 ("for (int i=0, j=0; i<tt; w+=", "for (int i=0, j=0; i<=tt; w+="),
 ('\touf.ensuref(w <= W, "Operation cost exceeded.")',
  '\t{ long long last = 0; if (tt) for (int v=0; v<n; v++) last += in[v] >= in[t[tt].x] && in[v] < ot[t[tt].x] && d[v] < t[tt].y;\n'
  '\t  fprintf(stderr, "TRUE_COST %lld LAST_INDEX %d CT_LAST %d LAST_SIZE %lld ORIGINAL_COUNTED %lld\\n", w, tt, ct[tt], last, w - (tt ? 1ll*ct[tt]*last : 0)); }\n'
  '\touf.ensuref(w <= W, "Operation cost exceeded.")'),
]
for a, b in reps:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
open(sys.argv[2], "w", newline="").write(src)
