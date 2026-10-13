# EBV honest control for vibrating_path_graph_coloring (README contract only).
# Greedy K-colouring (fewest conflicts with already-coloured neighbours), then, for every edge that
# still joins two same-coloured vertices, hit its cheaper endpoint until the edge is gone. Hits are
# simulated with the README's vibrating-path rule as implemented by the shipped tools/bin/tester
# (min-weight next edge, no immediate reuse, no unvisited-repeat, no live back edge to earlier path nodes,
# at most 256 path vertices). Every hit starts on a live edge at the hit vertex, so it removes >= 1 edge.
import sys

def main():
    d = sys.stdin.buffer.read().split()
    N, M, K = int(d[0]), int(d[1]), int(d[2])
    cost = [int(x) for x in d[3:3 + N]]
    i = 3 + N
    adj = [[] for _ in range(N)]
    edges = []
    for _ in range(M):
        u = int(d[i]) - 1; v = int(d[i + 1]) - 1; s = int(d[i + 2]); i += 3
        adj[u].append((s, v)); adj[v].append((s, u)); edges.append((u, v))
    for a in adj:
        a.sort()
    pairs = set()
    for u, v in edges:
        pairs.add((u, v) if u < v else (v, u))
    removed = set()

    def hit(node):
        path = [node]; visited = {node}; prev = None
        while len(path) < 256:
            curr = path[-1]; found = False
            for s, v in adj[curr]:
                e = (curr, v) if curr < v else (v, curr)
                if e in removed or e == prev or v in visited:
                    continue
                back = False
                for pn in path[:-1]:
                    e2 = (v, pn) if v < pn else (pn, v)
                    if e2 in pairs and e2 not in removed:
                        back = True; break
                if not back:
                    prev = e; path.append(v); visited.add(v); found = True; break
            if not found:
                break
        got = False
        for a, b in zip(path, path[1:]):
            e = (a, b) if a < b else (b, a)
            if e not in removed:
                removed.add(e); got = True
        assert got

    col = [0] * N
    order = sorted(range(N), key=lambda x: -len(adj[x]))
    for u in order:
        cnt = [0] * (K + 1)
        for s, v in adj[u]:
            if col[v]:
                cnt[col[v]] += 1
        col[u] = min(range(1, K + 1), key=lambda c: cnt[c])
    hits = []
    for u, v in edges:
        if col[u] != col[v]:
            continue
        e = (u, v) if u < v else (v, u)
        x = u if cost[u] <= cost[v] else v
        while e not in removed:
            hit(x); hits.append(x + 1)
    out = [str(len(hits))]
    if hits:
        out.append(' '.join(map(str, hits)))
    out.append(' '.join(map(str, col)))
    sys.stdout.write('\n'.join(out) + '\n')

main()
