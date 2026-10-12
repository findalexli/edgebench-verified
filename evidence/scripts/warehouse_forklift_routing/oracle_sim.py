#!/usr/bin/env python3
"""Independent simulator written from the task prompt / README / CodeChef WAREHOUS statement.

Not derived from tools/bin/tester. Two rule sets:
  mode="prompt":   EdgeBench prompt/README wording: "A forklift carrying a good cannot
                   enter an occupied cell" (an empty forklift may therefore enter one).
  mode="original": CodeChef WAREHOUS statement: N/W/S/E "destination cell must be inside
                   the warehouse and must not contain any shipment" (carrying or not).
Returns (ok, value): value = exact Fraction average score, or an error string.
"""
import sys
from fractions import Fraction

DIRS = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}


def parse_input(text):
    tok = text.split()
    T = int(tok[0]); i = 1; cases = []
    for _ in range(T):
        R, C = int(tok[i]), int(tok[i + 1]); i += 2
        n = R * C - 1
        a = [int(x) for x in tok[i:i + n]]; i += n
        cases.append((R, C, a))
    assert i == len(tok), "trailing tokens"
    return cases


def simulate_case(R, C, arrivals, s, mode="prompt"):
    n = R * C - 1
    if len(s) > 500000:
        return False, "too long"
    occ = {}            # cell -> good
    pos = (0, 0); cargo = None; k = 0; nxt = 1
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in DIRS:
            dr, dc = DIRS[ch]; q = (pos[0] + dr, pos[1] + dc)
            if not (0 <= q[0] < R and 0 <= q[1] < C):
                return False, "move out of bounds"
            if q in occ and (cargo is not None or mode == "original"):
                return False, "move into occupied cell"
            pos = q; i += 1
        elif ch == 'P':
            if pos != (0, 0) or cargo is not None or k >= n:
                return False, "bad P"
            cargo = arrivals[k]; k += 1; i += 1
        elif ch == 'D':
            if pos != (0, 0) or cargo is None or k < n or cargo != nxt:
                return False, "bad D"
            nxt += 1; cargo = None; i += 1
        elif ch in 'LU':
            if i + 1 >= len(s) or s[i + 1] not in DIRS:
                return False, "bad L/U direction"
            dr, dc = DIRS[s[i + 1]]; q = (pos[0] + dr, pos[1] + dc)
            if not (0 <= q[0] < R and 0 <= q[1] < C):
                return False, "L/U out of bounds"
            if ch == 'L':
                if cargo is not None or q not in occ:
                    return False, "bad L"
                cargo = occ.pop(q)
            else:
                if cargo is None or q in occ:
                    return False, "bad U"
                occ[q] = cargo; cargo = None
            i += 2
        else:
            return False, "unknown command"
    if nxt != n + 1:
        return False, "not all dispatched"
    S = len(s)
    return True, Fraction(S + 2, R + C - 1) - 2 * R * C + 20


def score_file(input_text, output_text, mode="prompt"):
    cases = parse_input(input_text)
    lines = output_text.strip().split('\n')
    if len(lines) != len(cases):
        return False, "line count"
    tot = Fraction(0)
    for (R, C, a), line in zip(cases, lines):
        ok, v = simulate_case(R, C, a, line.strip(), mode)
        if not ok:
            return False, v
        tot += v
    return True, tot / len(cases)


if __name__ == "__main__":
    mode = sys.argv[3] if len(sys.argv) > 3 else "prompt"
    ok, v = score_file(open(sys.argv[1]).read(), open(sys.argv[2]).read(), mode)
    print(("OK %s %.6f" % (v, float(v))) if ok else ("FAIL " + v))
