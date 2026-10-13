# EBV control (cpu 14). Honest valid control: C=1, one state per step of a BFS shortest route through
# the targets in order. Rule (0,t) -> (0,t+1,d_t). Cost = 1 + (X+1) = X+2.
import sys
from collections import deque
FAIL = None  # set by variants: 'crash' | 'trunc' | 'tle' | 'lower'
FAIL_HEADER = '15 75 1785'  # case 0000

def main():
    import time, os
    w0 = time.time(); c0 = time.process_time()
    lines = sys.stdin.read().split('\n')
    _log = open(f'/ebvtiming/{os.getpid()}.txt', 'w')
    _log.write(f'start {w0:.3f} {lines[0].strip()}\n'); _log.flush()
    while time.process_time() - c0 < 14.0:  # fixed 14 s of single-thread CPU work (< 30 s README limit)
        pass
    N, K, T = map(int, lines[0].split())
    v = [lines[1 + i].strip() for i in range(N)]
    h = [lines[1 + N + i].strip() for i in range(N - 1)]
    tg = [tuple(map(int, lines[2 * N + i].split())) for i in range(K)]
    hit = lines[0].strip() == FAIL_HEADER or FAIL == 'lower'
    D = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    def ok(i, j, d):
        if d == 'U': return i > 0 and h[i - 1][j] == '0'
        if d == 'D': return i < N - 1 and h[i][j] == '0'
        if d == 'L': return j > 0 and v[i][j - 1] == '0'
        return j < N - 1 and v[i][j] == '0'
    moves = []
    for k in range(1, K):
        s, g = tg[k - 1], tg[k]
        prev = {s: None}; q = deque([s])
        while q:
            c = q.popleft()
            if c == g: break
            for d in 'UDLR':
                if ok(c[0], c[1], d):
                    n = (c[0] + D[d][0], c[1] + D[d][1])
                    if n not in prev:
                        prev[n] = (c, d); q.append(n)
        path = []; c = g
        while prev[c] is not None:
            c, d = prev[c]; path.append(d)
        moves += path[::-1]
    if hit and FAIL == 'crash':
        raise RuntimeError('honest bug on this case')
    if hit and FAIL == 'tle':
        import time; time.sleep(40)
    X = len(moves)
    out = [f'1 {X + 1} {X}']
    out += [' '.join(['0'] * N) for _ in range(N)]
    for t, d in enumerate(moves):
        if hit and FAIL == 'lower':
            d = d.lower()
        out.append(f'0 {t} 0 {t + 1} {d}')
    if hit and FAIL == 'trunc':
        out = out[:len(out) // 2]  # e.g. output cut short
    print('\n'.join(out))
    _log.write(f'end {time.time():.3f} cpu {time.process_time() - c0:.3f}\n'); _log.close()

main()
