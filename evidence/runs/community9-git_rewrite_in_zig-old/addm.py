import sys, tarfile, io
src, out, *adds = sys.argv[1:]
with tarfile.open(src) as a, tarfile.open(out, 'w:gz') as b:
    for m in a:
        b.addfile(m, a.extractfile(m) if m.isfile() else None)
    for x in adds:
        k, p = x.split('=', 1); d = open(p, 'rb').read(); ti = tarfile.TarInfo(k); ti.size = len(d); ti.mode = 0o644; b.addfile(ti, io.BytesIO(d))
