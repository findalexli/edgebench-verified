import sys, json, importlib.util
from pathlib import Path
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
E = load(sys.argv[1], "E"); d = Path(sys.argv[2])
for inst in sorted(d.glob("*.instance.json")):
    name = inst.name[:-len(".instance.json")]
    print(name, E.validate_solution(inst, d / f"{name}.solution.json"))
