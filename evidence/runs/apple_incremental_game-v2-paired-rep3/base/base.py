# EBV honest control for apple_incremental_game (README rules only): each turn, strengthen the affordable
# level-0 machine whose extra production over the remaining turns per apple spent is largest, if it pays
# back before the end; otherwise do nothing. Exactly T lines.
import sys

def main():
    t = sys.stdin.read().split()
    N, L, T, K = map(int, t[:4]); A = list(map(int, t[4:4 + N]))
    C = [list(map(int, t[4 + N + i * N:4 + N + (i + 1) * N])) for i in range(L)]
    P = [0] * N; apples = K; out = []
    for turn in range(T):
        rem = T - turn
        best = None; br = 0.0
        for j in range(N):
            c = C[0][j] * (P[j] + 1)
            if c <= apples:
                gain = A[j] * rem
                if gain > c and gain / c > br:
                    br = gain / c; best = j
        if best is not None:
            apples -= C[0][best] * (P[best] + 1); P[best] += 1; out.append(f'0 {best}')
        else:
            out.append('-1')
        apples += sum(A[j] * P[j] for j in range(N))
    print('\n'.join(out))

main()
