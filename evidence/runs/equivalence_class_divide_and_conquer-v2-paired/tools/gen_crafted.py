"""Crafted T3 (P8204) inputs/outputs. Usage: python3 -I gen_crafted.py OUTDIR
Tree: star, n=1_000_000 (f_i = 1), so N(1,2) is the whole vertex set (size n).
Every query is (x=1, y=2). Output strategy 'naive': for each query i:
  "1 1 2"  (empty N(1,0) -> N(1,2), cost n)   "3 i"   "2" (undo, free)
True cost = m*n. 3m operations <= 5m."""
import sys, os
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
n = 1_000_000
def write_in(name, m):
    with open(f"{out}/{name}.in", "w") as f:
        f.write(f"{n} {m}\n"); f.write(" ".join(["1"] * (n - 1)) + "\n")
        f.write("1 2\n" * m)
    open(f"{out}/{name}.ans", "w").close()
def write_out(name, m, trailer=None):
    ops = []
    for i in range(1, m + 1):
        ops += ["1 1 2", f"3 {i}", "2"]
    if trailer: ops += trailer
    with open(f"{out}/{name}.out", "w") as f:
        f.write(f"{len(ops)}\n" + "\n".join(ops) + "\n")
cases = {
  # name: (m, trailer, true cost)
  "A_at_limit":            (2500, None),            # 2.500e9 == W  -> must accept
  "B_over_by_n":           (2501, None),            # 2.501e9 >  W  -> must reject
  "C_over_by_2n":          (2502, None),            # 2.502e9 >  W  -> must reject
  "D_over_by_n_trailer":   (2501, ["1 1 0"]),       # same moves + final zero-cost move to empty N(1,0)
  "E_efficient":           (2501, None),            # same input as B, efficient output (below)
}
for name, (m, tr) in cases.items():
    write_in(name, m)
    if name != "E_efficient":
        write_out(name, m, tr)
# efficient answer for E: move once to N(1,2), mark all, never undo: cost n
with open(f"{out}/E_efficient.out", "w") as f:
    m = 2501
    f.write(f"{m+1}\n1 1 2\n" + "".join(f"3 {i}\n" for i in range(1, m + 1)))
print("written", sorted(os.listdir(out)))
