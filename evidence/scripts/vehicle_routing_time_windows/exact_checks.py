#!/usr/bin/env python3
"""Exact-arithmetic checks for vehicle_routing_time_windows (audit only).
Usage: python3 -I exact_checks.py <internal/cases/raw dir>
1. Distance well-definedness: compare the task's binary64 dist_x10
   (round(sqrt(dx^2+dy^2)*10)/10, round-half-away) with an exact integer oracle.
2. Instance numeric domain: are coordinates/e/l/s integral?
3. Cost-tolerance boundary: binary64 |total-declared|>0.05 vs exact decimal.
4. Rounding-sensitive pairs: 2-customer routes feasible with unrounded Euclidean
   distances but infeasible under task rounding (shows that an edit of
   include/types.h::dist_x10, a submit path, changes verifier verdicts)."""
import math, sys, glob, os
from fractions import Fraction as F
from decimal import Decimal

def parse(p):
    sec=None; nodes={}; dem={}; tw={}; sv={}
    for line in open(p):
        s=line.strip()
        if not s or s.startswith('EOF'): continue
        k=s.split()[0]
        if k in('NODE_COORD_SECTION','DEMAND_SECTION','TIME_WINDOW_SECTION','SERVICE_TIME_SECTION','DEPOT_SECTION'):
            sec=k; continue
        if ':' in s and sec is None: continue
        t=s.split()
        if sec=='NODE_COORD_SECTION': nodes[int(t[0])]=(Decimal(t[1]),Decimal(t[2]))
        elif sec=='DEMAND_SECTION': dem[int(t[0])]=int(t[1])
        elif sec=='TIME_WINDOW_SECTION': tw[int(t[0])]=(Decimal(t[1]),Decimal(t[2]))
        elif sec=='SERVICE_TIME_SECTION': sv[int(t[0])]=Decimal(t[1])
    return nodes,dem,tw,sv

def d64(a,b):
    dx=float(a[0])-float(b[0]); dy=float(a[1])-float(b[1])
    d=math.sqrt(dx*dx+dy*dy); v=d*10.0
    r=math.floor(v+0.5) if v>=0 else -math.floor(-v+0.5)  # std::round half away
    return r/10.0

def dexact_tenths(a,b):
    # integer coordinates -> D integer; exact round(10*sqrt(D)) half-up (never a tie)
    dx=a[0]-b[0]; dy=a[1]-b[1]; D=int(dx*dx+dy*dy)
    if (dx*dx+dy*dy)!=D: return None
    # n = round(sqrt(100 D)): largest n with (n-0.5)^2 <= 100D  <=> (2n-1)^2 <= 400D
    m=math.isqrt(400*D)  # floor(2*sqrt(100D))
    # round(x)= floor(x+0.5) = floor((2x+1)/2)
    n=(m+1)//2
    # tie impossible: (2n-1)^2 == 400D requires odd square == multiple of 4
    return n  # tenths

files=sorted(glob.glob(os.path.join(sys.argv[1],'*.txt')))
nonint=0; mism=0; pairs=0; sens=[]
for f in files:
    nodes,dem,tw,sv=parse(f)
    vals=[x for xy in nodes.values() for x in xy]+[x for el in tw.values() for x in el]+list(sv.values())
    nonint+=sum(1 for v in vals if v!=v.to_integral_value())
    ids=sorted(nodes)
    for i in ids:
        for j in ids:
            if i>=j: continue
            pairs+=1
            ex=dexact_tenths(nodes[i],nodes[j])
            if ex is None or F(ex,10)!=F(d64(nodes[i],nodes[j])).limit_denominator(10):
                mism+=1
    # rounding-sensitive 2-customer routes: exact rational times
    name=os.path.basename(f)[:-4]
    L0=F(tw[0][1])
    def rd(i,j): return F(dexact_tenths(nodes[i],nodes[j]),10)
    def ud(i,j):  # unrounded as float (comparison only)
        dx=float(nodes[i][0]-nodes[j][0]); dy=float(nodes[i][1]-nodes[j][1]); return math.hypot(dx,dy)
    for i in ids[1:]:
        for j in ids[1:]:
            if i==j: continue
            def feas(dist):
                t=0; 
                for prev,c in ((0,i),(i,j)):
                    t+=dist(prev,c); t=max(t,float(tw[c][0]) if dist is ud else F(tw[c][0]))
                    if t>(float(tw[c][1]) if dist is ud else F(tw[c][1])): return False
                    t+=(float(sv[c]) if dist is ud else F(sv[c]))
                t+=dist(j,0)
                return t<=(float(L0) if dist is ud else L0)
            if dem[i]+dem[j]<=10**9 and feas(ud) and not feas(rd):
                sens.append((name,i,j))
print('instances',len(files),'non-integral numeric fields',nonint)
print('pairs',pairs,'binary64 vs exact dist_x10 mismatches',mism)
print('2-customer routes feasible unrounded but infeasible under task rounding:',len(sens),'e.g.',sens[:5])

# 3. cost tolerance boundary
def acc64(total,declared): return not (abs(total-declared)>0.05)
def accexact(total,declared): return abs(F(total)-F(declared))<=F(1,20)
for tot,dec in [('12','12.05'),('12','11.95'),('4','4.05'),('4','3.95'),('1234.5','1234.55'),('1234.5','1234.45'),('1234.5','1234.56')]:
    t=float(tot); dd=float(dec)
    print(f'total={tot} declared={dec}: binary64 accept={acc64(t,dd)} exact-decimal(<=0.05) accept={accexact(tot,dec)}')
# how often is a binary64 sum of tenths off a multiple of 0.1 by >1e-9? (summation drift)
import random
random.seed(0); worst=0
for _ in range(20000):
    xs=[random.randint(1,1500) for _ in range(120)]
    s=0.0
    for x in xs: s+=x/10.0
    worst=max(worst,abs(F(s)-F(sum(xs),10)))
print('max binary64 drift of 120-term sum of tenths over 20000 trials:',float(worst))
