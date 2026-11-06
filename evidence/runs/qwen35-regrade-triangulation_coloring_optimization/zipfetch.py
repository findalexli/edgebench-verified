#!/usr/bin/env python3
"""Extract selected members from remote ZIPs using HTTP range requests (no full download).
usage: zipfetch.py OUTDIR REGEX URL [URL ...]   (stdlib only; members written under OUTDIR, paths sanitized)"""
import io, os, re, sys, urllib.request, zipfile, shutil
class RangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url; self.pos = 0
        r = urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=60)
        self.size = int(r.headers['Content-Length']); self.url = r.geturl()
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos
    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0: return 0
        for attempt in range(5):
            try:
                req = urllib.request.Request(self.url, headers={'Range': f'bytes={self.pos}-{self.pos + n - 1}'})
                data = urllib.request.urlopen(req, timeout=300).read(); break
            except Exception:
                if attempt == 4: raise
        b[:len(data)] = data; self.pos += len(data); return len(data)
out, pat = sys.argv[1], re.compile(sys.argv[2]); n = 0
for url in sys.argv[3:]:
    zf = zipfile.ZipFile(io.BufferedReader(RangeFile(url), buffer_size=1 << 20))
    for info in zf.infolist():
        if info.is_dir() or not pat.search(info.filename): continue
        rel = os.path.normpath(info.filename)
        if rel.startswith('..') or os.path.isabs(rel): continue
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        with zf.open(info) as src, open(dst, 'wb') as f: shutil.copyfileobj(src, f, 1 << 20)
        n += 1
print(n, 'members extracted')
