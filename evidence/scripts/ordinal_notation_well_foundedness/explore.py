#!/usr/bin/env python3
"""Bounded exploration of the ChildOf.v relation (direct transcription of ChildOf.v).
Checks (1) the Python transcription against Coq-computed values (see coq_check.v),
(2) bounded search for cycles (a cycle would refute Acc), (3) reachability of each target
from `start` with small N.  Bounded search cannot prove well-foundedness."""
import sys
from collections import deque

def nth0(a, i):          # nth i a 0 ; i is a nat (never negative here)
    return a[i] if 0 <= i < len(a) else 0

def sub(x, y):           # saturated nat subtraction
    return x - y if x > y else 0

def child_flag(a, BR):
    n = len(a)
    return any(nth0(a, sub(i, 1)) == nth0(a, sub(BR, 1)) for i in range(BR + 1, BR + 1 + sub(n, BR + 1)))

def child_block(a, BR, n, i):
    flag = child_flag(a, BR)
    head = nth0(a, sub(BR, 1)) if flag else sub(nth0(a, sub(n, 1)), 1)
    body = []
    for j in range(BR + 1, BR + 1 + sub(n, BR + 1)):
        x = nth0(a, sub(j, 1))
        body.append(x + sub(n, BR) * i if BR <= x else x)
    return [head] + body

def childOf(a, N):
    n = len(a)
    BR = nth0(a, sub(n, 1))
    a0 = a[:-1]
    if BR == 0:
        return a0
    out = list(a0)
    for i in range(1, N + 1):
        out += child_block(a, BR, n, i)
    return out

TARGETS = {
 "task1": [0,1], "task2": [0,1,0,0,3], "task3": [0,1,0,0,3,3], "task4": [0,1,0,0,4],
 "task5": [0,1,0,1], "task6": [0,1,0,2], "task7": [0,1,0,2,0,0,2],
 "task8": [0,1,0,2,0,0,2,0,0,2], "task9": [0,1,0,2,0,3],
}
START = [0,1,0,2,0,3]

def cycle_search(root, maxN, maxlen, budget):
    """DFS; report any node equal to an ancestor on the current path."""
    stack = [(tuple(root), 0)]
    path, onpath = [], set()
    visited = 0
    while stack:
        node, state = stack.pop()
        if state == 1:
            path.pop(); onpath.discard(node); continue
        visited += 1
        if visited > budget:
            return "budget", visited
        if node in onpath:
            return "CYCLE", visited
        path.append(node); onpath.add(node)
        stack.append((node, 1))
        if node:
            for N in range(maxN + 1):
                c = tuple(childOf(list(node), N))
                if len(c) <= maxlen:
                    stack.append((c, 0))
    return "exhausted", visited

def reachable_from_start(maxN, maxlen, budget):
    seen = {tuple(START)}; q = deque([tuple(START)])
    while q and len(seen) < budget:
        a = q.popleft()
        if not a:
            continue
        for N in range(maxN + 1):
            c = tuple(childOf(list(a), N))
            if len(c) <= maxlen and c not in seen:
                seen.add(c); q.append(c)
    return seen

if __name__ == "__main__":
    for N in range(4):
        print("childOf start", N, "=", childOf(START, N))
    for t, a in TARGETS.items():
        print(t, a, "children N=0..2:", [childOf(a, N) for N in range(3)])
    print()
    for t, a in TARGETS.items():
        print(t, "cycle search (N<=2, len<=24, 200k nodes):", cycle_search(a, 2, 24, 200000))
    seen = reachable_from_start(3, 30, 300000)
    print("\nreachable-from-start set size", len(seen))
    for t, a in TARGETS.items():
        print(t, "reached from start (N<=3, len<=30):", tuple(a) in seen)
