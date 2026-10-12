#!/usr/bin/env python3
"""Run the unchanged original validate_solution() on every <name>.instance.json /
<name>.solution.json pair in a directory. Run inside the pinned judge image."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/workspace/jagua_task_scorer")
import evaluate as E
d = Path(sys.argv[1])
for inst in sorted(d.glob("*.instance.json")):
    name = inst.name[: -len(".instance.json")]
    print(name, E.validate_solution(inst, d / f"{name}.solution.json"))
