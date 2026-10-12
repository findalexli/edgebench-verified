# Honest control policy for treant_forest (grid-only; ignores the replay candidate lines).
# At turn 0 only the entrance is revealed, so every other empty cell may receive a treant.
# Greedily add treants (fixed-seed random order) whenever the entrance->flower BFS distance
# stays reachable and does not shrink; then stop placing (-1). Legitimate per README rules.
import sys, random
from collections import deque

def bfs(g, N, s, t):
    d = {s: 0}; q = deque([s])
    while q:
        r, c = q.popleft()
        if (r, c) == t: return d[(r, c)]
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and g[nr][nc] == '.' and (nr, nc) not in d:
                d[(nr, nc)] = d[(r, c)] + 1; q.append((nr, nc))
    return None

def main():
    lines = sys.stdin.read().split('\n')
    N, ti, tj = map(int, lines[0].split())
    g = [list(lines[1+i].strip()) for i in range(N)]   # grid part only
    ent, goal = (0, N//2), (ti, tj)
    cells = [(r, c) for r in range(N) for c in range(N)
             if g[r][c] == '.' and (r, c) not in (ent, goal)]
    random.Random(0).shuffle(cells)
    cur = bfs(g, N, ent, goal)
    placed = []
    for r, c in cells:
        g[r][c] = 'T'
        d = bfs(g, N, ent, goal)
        if d is not None and d >= cur:
            cur = d; placed.append((r, c))
        else:
            g[r][c] = '.'
    print(len(placed), *[v for p in placed for v in p])
    print(-1)

main()
