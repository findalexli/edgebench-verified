"""Write the patched judge library (swap the c and d assignment lines) next to a copy of lib.h.
Usage: python3 -I patch_overlay.py <original interactive_lib.cpp> <outdir>"""
import hashlib, sys, pathlib, shutil
src = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
raw = src.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '0c57271bd1b05d3cfbb44558fcf2e2770bb020858aa4411eaaa725a89409c982'
B = b'\tc=(c+1)*(x.c+1)-1;\r\n\td=d*(x.c+1)+x.d;\r\n'
A = b'\td=d*(x.c+1)+x.d;\r\n\tc=(c+1)*(x.c+1)-1;\r\n'
assert raw.count(B) == 1
new = raw.replace(B, A, 1)
(out / 'interactive_lib.cpp').write_bytes(new)
shutil.copy(src.parent / 'lib.h', out / 'lib.h')
print('patched sha256', hashlib.sha256(new).hexdigest())
