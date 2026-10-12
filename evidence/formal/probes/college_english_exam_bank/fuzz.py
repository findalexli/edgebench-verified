"""Random differential check of the real grader functions (20,000 assessments, seed 1).
Usage: python3 -I fuzz.py <original b8b2824c...> <earlier fixed 1d941b58...> <revised fixed 87f0e340...> <rubrics.json d05f344e...>
Asserts: every accepted assessment gets the original total; the revised grader never accepts a deductive
row that reports a deduction (numeric score below max, or a positive checkpoint) yet reconciles to full marks.
Prints counts of (earlier accepted?, revised accepted?)."""
import importlib.util, json, sys, random, collections
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
o=load("o",sys.argv[1]); a=load("a",sys.argv[2]); b=load("b",sys.argv[3]); rules=json.load(open(sys.argv[4]))["rules"]
R=random.Random(1)
def tot(m,obj,fixed):
    try: r=m._validate_result(obj,rules) if fixed else m._validate_result(obj)
    except ValueError as e: return "REJ"
    r=m.reconcile_result_with_rubrics(r,rules); return r["raw_total"], [s["score"] for s in r["scores"]]
reasons=["x","poor","poor veto","扣分超过上限，本规则得0","p"*205+"扣分超过上限","触发否决"]
def row(r):
    d={"rule_id":r["rule_id"],"scoring_mode":"deductive","max_score":r["max_score"],"reason":R.choice(reasons)}
    sc=R.choice([None,0,r["max_score"],r["max_score"]-1,0.5,-1,r["max_score"]+2])
    if sc is not None or R.random()<.5: d["score"]=sc if sc is not None else 0
    n=len(r["scoring_details"]); k=R.choice([0,n-1,n,n,n,n+1])
    if k>0: d["checkpoint_scores"]=[{"score":R.choice([0,0,0,0,1,-1,2,0.5])} for _ in range(k)]
    if R.random()<.15: d["rule_veto_triggered"]=True
    if R.random()<.15: d["veto_reason"]=R.choice(["veto: c","x"])
    return d
C=collections.Counter(); bad=[]
for i in range(20000):
    obj={"scores":[row(r) for r in rules]}
    to=tot(o,obj,False); ta=tot(a,obj,True); tb=tot(b,obj,True)
    for t in (ta,tb):
        if t!="REJ": assert t==to
    key=("old",ta!="REJ","new",tb!="REJ"); C[key]+=1
    if ta!="REJ" and tb=="REJ":
        # new rejects: some deductive rule reporting a deduction got full marks in the original reconcile
        ok=False
        for r,s,rw in zip(rules,to[1],[next(x for x in obj["scores"] if x["rule_id"]==r["rule_id"]) for r in rules]):
            rep=(type(rw.get("score")) in (int,float) and rw["score"]<r["max_score"]) or any(c["score"]>0 for c in rw.get("checkpoint_scores",[]))
            if rep and s>=r["max_score"]: ok=True
        assert ok
    if ta=="REJ" and tb!="REJ": C["newly_accepted"]+=1
    if tb!="REJ":
        for r,s,rw in zip(rules,tb[1],[next(x for x in obj["scores"] if x["rule_id"]==r["rule_id"]) for r in rules]):
            rep=(type(rw.get("score")) in (int,float) and rw["score"]<r["max_score"]) or any(c["score"]>0 for c in rw.get("checkpoint_scores",[]))
            assert not (rep and s>=r["max_score"]), "C3 violated"
print(dict(C))
