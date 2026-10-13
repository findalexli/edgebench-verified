#!/usr/bin/env python3
"""Verify candidate benchmark snapshot/clear against original image helpers.
Run in pinned FFmpeg image with PYTHONPATH=/opt/tests. Argument: candidate source.
"""
import ast
import ctypes
import hashlib
import json
from pathlib import Path
import random
import sys
from pixel_formats import PIXFMT_DESCS, allocate_image, image_to_bytes, fill_image_from_bytes

path=Path(sys.argv[1])
nodes=[n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.FunctionDef) and n.name in ('snapshot','clear_output')]
assert len(nodes)==2
code=compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec')
rng=random.Random(20261013)
rows=[]
for fmt,desc in PIXFMT_DESCS.items():
    for w,h in [(2,2),(7,5),(32,18),(257,129)]:
        data,stride,bufs=allocate_image(fmt,w,h)
        for buf in bufs:
            if buf is not None:ctypes.memset(buf,0xa5,ctypes.sizeof(buf))
        planes=[bytes(rng.randrange(256) for _ in range(desc.plane_width(i,w)*desc.planes[i].bpp*desc.plane_height(i,h))) for i in range(desc.num_planes)]
        fill_image_from_bytes(fmt,w,h,data,stride,planes)
        ns=dict(ctypes=ctypes,desc=desc,dst_w=w,dst_h=h,dst_data=data,dst_stride=stride)
        exec(code,ns)
        assert ns['snapshot']()==image_to_bytes(fmt,w,h,data,stride)==planes,(fmt,w,h)
        ns['clear_output']()
        assert ns['snapshot']()==image_to_bytes(fmt,w,h,data,stride)==[bytes(len(p)) for p in planes]
        for i in range(desc.num_planes):
            size=stride[i]*desc.plane_height(i,h)
            assert ctypes.string_at(data[i],size)==bytes(size)
        rows.append(dict(format=fmt,width=w,height=h,strides=list(stride)))
print(json.dumps(dict(status='pass',candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),layouts=rows),indent=2))
