"""Build a 'faithful reference': upstream file with the hidden test fns (by manifest snippet names) removed,
so the grader's injection has to re-insert them as it does for any solver who leaves tests alone."""
import re,sys
from pathlib import Path
def skip_lit(c,i):
    # returns index after string/char/comment starting at i, or None
    if c.startswith('//',i): return c.find('\n',i)+1 or len(c)
    if c.startswith('/*',i): return c.find('*/',i+2)+2
    m=re.match(r'r(#*)"',c[i:])
    if m and (i==0 or not (c[i-1].isalnum() or c[i-1]=='_')):
        end='"'+m.group(1); return c.find(end,i+len(m.group(0)))+len(end)
    if c[i]=='"' or (c[i]=='b' and c[i+1:i+2]=='"' and not (c[i-1].isalnum() or c[i-1]=='_')):
        j=i+(2 if c[i]=='b' else 1)
        while c[j]!='"':
            j+=2 if c[j]=='\\' else 1
        return j+1
    if c[i]=="'":
        m=re.match(r"'(\\.|\\u\{[0-9a-fA-F]+\}|\\x..|[^\\'])'",c[i:])
        if m: return i+len(m.group(0))
    return None
def match_brace(c,o):
    d=0;i=o
    while i<len(c):
        k=skip_lit(c,i)
        if k is not None: i=k; continue
        if c[i]=='{': d+=1
        elif c[i]=='}':
            d-=1
            if d==0: return i
        i+=1
    raise ValueError('unbalanced')
def remove_fn(c,name):
    m=re.search(r'^([ \t]*)(pub(\([^)]*\))?\s+)?(async\s+)?fn\s+'+re.escape(name)+r'\b',c,re.M)
    if not m: return c,False
    start=m.start()
    # include preceding attribute / doc-comment lines (and multi-line attributes)
    lines_before=c[:start].split('\n')[:-1]
    k=len(lines_before)
    while k>0:
        t=lines_before[k-1].strip()
        if t.startswith('#['):
            k-=1
        else: break
    start=sum(len(l)+1 for l in lines_before[:k])
    # body
    i=m.end(); depth=0
    while True:
        s=skip_lit(c,i)
        if s is not None: i=s; continue
        if c[i]=='(': depth+=1
        elif c[i]==')': depth-=1
        elif c[i]=='{' and depth==0: break
        i+=1
    e=match_brace(c,i)+1
    if c[e:e+1]=='\n': e+=1
    return c[:start]+c[e:],True
if __name__=='__main__':
    src,snip,out=map(Path,sys.argv[1:4])
    c=src.read_text(); names=re.findall(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)", snip.read_text())
    miss=[]
    for n in names:
        c,ok=remove_fn(c,n)
        if not ok: miss.append(n)
    out.write_text(c); print(src, 'missing', miss) if miss else None
