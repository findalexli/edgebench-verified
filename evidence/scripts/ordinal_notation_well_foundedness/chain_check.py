"""Chain check: from each target's list, breadth-first search over children (N <= 3,
length <= 30) and report which other targets are reached. Uses childOf from explore.py
(a transcription of ChildOf.v). A reached target is a true descendant, so Acc of the
searching target implies Acc of every target it reaches.

usage: python3 -I chain_check.py   (run from this directory)
"""
import os
from collections import deque
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "explore.py")).read().split("if __name__")[0]
ns = {}
exec(compile(src, "explore.py", "exec"), ns)
childOf = ns["childOf"]
T = {1: [0, 1], 2: [0, 1, 0, 0, 3], 3: [0, 1, 0, 0, 3, 3], 4: [0, 1, 0, 0, 4], 5: [0, 1, 0, 1],
     6: [0, 1, 0, 2], 7: [0, 1, 0, 2, 0, 0, 2], 8: [0, 1, 0, 2, 0, 0, 2, 0, 0, 2], 9: [0, 1, 0, 2, 0, 3]}

def reach(root, maxN=3, maxlen=30, budget=300000):
    seen = {tuple(root)}; q = deque([tuple(root)])
    while q and len(seen) < budget:
        a = q.popleft()
        for n in range(maxN + 1):
            c = tuple(childOf(list(a), n))
            if len(c) <= maxlen and c not in seen:
                seen.add(c); q.append(c)
    return seen

for i in range(2, 10):
    s = reach(T[i])
    print("task%d reaches:" % i, [j for j in T if j != i and tuple(T[j]) in s])
w = [1, 2, 2, 4, 4, 8, 16, 16, 32]
print("prefix weights:", [sum(w[:k]) for k in range(1, 10)])
