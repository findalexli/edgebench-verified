# Invalid control: places a treant on the entrance cell, which is already revealed.
# The tester must reject this ("cannot place treant at revealed cell") -> WA, 0 per case.
import sys
N, ti, tj = map(int, sys.stdin.readline().split())
print(1, 0, N // 2)
print(-1)
