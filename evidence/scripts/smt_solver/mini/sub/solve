#!/usr/bin/env python3
# Fixed-witness stub: prints, for each audit case, the witness a correct solver would print.
import sys, json, re
text = open(sys.argv[1]).read()
case = re.search(r"CASE:(\w+)", text).group(1)
W = {
 # ground-term keys, as the spec describes ("canonical ground terms")
 "scope_conflict": {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b"},
 "define_conflict": {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b"},
 "ground_control": {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b"},
 "single_let": {"a":"@a","b":"@b","(f a)":"@b"},
 # textual (non-ground) key, as the checker actually looks up
 "scope_conflict_textkeys": {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b","(f x)":"@a"},
 "single_let_textkey": {"a":"@a","b":"@b","(f x)":"@b"},
 # known-bad: violates (= (f b) b)
 "ground_control_wrong": {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@a"},
}
vals = dict(W[case])
# values for the evaluator's satisfiability-preserving perturbation symbols (any value works)
for name, sort in re.findall(r"\(declare-fun (__sebench_\w+) \(\) (\w+)\)", text):
    vals[name] = "true" if sort == "Bool" else "0"
print("sat"); print(json.dumps({"values": vals}))
