"""Independent AHC058-style simulator (from the shipped README rules) + one-step-lookahead greedy.
Purpose: order-of-magnitude check of the task's piecewise_max anchors (per-case = anchor/50).
Float64 is used only to rank candidate actions; the final score is recomputed exactly with ints."""
import sys, math, glob
import numpy as np

def parse(path):
    t = open(path).read().split()
    N, L, T, K = map(int, t[:4]); A = list(map(int, t[4:4+N]))
    C = [list(map(int, t[4+N+i*N:4+N+(i+1)*N])) for i in range(L)]
    return N, L, T, K, A, C

def exact_play(N, L, T, K, A, C, actions):
    B = [[1]*N for _ in range(L)]; P = [[0]*N for _ in range(L)]; apples = K
    for a in actions:
        if a is not None:
            i, j = a; cost = C[i][j]*(P[i][j]+1); assert cost <= apples; apples -= cost; P[i][j] += 1
        for j in range(N): apples += A[j]*B[0][j]*P[0][j]
        for i in range(1, L):
            for j in range(N): B[i-1][j] += B[i][j]*P[i][j]
    return apples

def greedy(N, L, T, K, A, C):
    Af = np.array(A, float); Cf = np.array(C, float)
    B = np.ones((L, N)); P = np.zeros((L, N)); apples = float(K); acts = []
    for turn in range(T):
        rem = T - turn
        # candidates: index 0 = nothing, then each (i,j) affordable
        cands = [None] + [(i, j) for i in range(L) for j in range(N) if Cf[i, j]*(P[i, j]+1) <= apples]
        M = len(cands)
        Bs = np.repeat(B[None], M, 0); Ps = np.repeat(P[None], M, 0); ap = np.full(M, apples)
        for k, c in enumerate(cands[1:], 1):
            i, j = c; ap[k] -= Cf[i, j]*(P[i, j]+1); Ps[k, i, j] += 1
        for _ in range(rem):
            ap += (Af*Bs[:, 0]*Ps[:, 0]).sum(1)
            for i in range(1, L): Bs[:, i-1] += Bs[:, i]*Ps[:, i]
        best = cands[int(np.argmax(ap))]
        acts.append(best)
        if best is not None:
            i, j = best; apples -= Cf[i, j]*(P[i, j]+1); P[i, j] += 1
        apples += (Af*B[0]*P[0]).sum()
        for i in range(1, L): B[i-1] += B[i]*P[i]
    return acts

if __name__ == "__main__":
    files = sorted(glob.glob(sys.argv[1] + "/*.txt"))[:int(sys.argv[2])]
    tot = 0
    for f in files:
        N, L, T, K, A, C = parse(f)
        S = exact_play(N, L, T, K, A, C, greedy(N, L, T, K, A, C))
        sc = round(1e5*math.log2(S)) if S > 0 else 0; tot += sc
        print(f.split('/')[-1], sc, flush=True)
    n = len(files)
    print(f"mean_per_case={tot/n:.0f}; anchors per case: baseline={45000000/50:.0f} rank30={262328915.6667/50:.0f} rank1={282791094/50:.0f} super={289952856.4167/50:.0f}")
