#!/usr/bin/env python3
"""Check candidate buffer helpers against an independent synthetic layout oracle.

Usage: python3 check_buffer_layouts.py MATERIALIZED_CANDIDATE.py
This does not load a task image or verify its allocator/descriptors.
"""
import ast
import ctypes
import hashlib
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace


def check(path):
    source = path.read_bytes()
    nodes = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.FunctionDef)
             and node.name in ('snapshot', 'clear_output')]
    if len(nodes) != 2 or {node.name for node in nodes} != {'snapshot', 'clear_output'}:
        raise AssertionError('Expected exactly one snapshot and one clear_output helper')
    code = compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec')
    rng = random.Random(55)
    layouts = 0
    for count in (1, 2, 3, 4):
        for width, height in ((1, 1), (7, 5), (32, 18), (257, 129)):
            for padding in (0, 1, 17, 64):
                bytes_per_pixel = (1, 2, 3, 4)[:count]
                desc = SimpleNamespace(
                    num_planes=count,
                    planes=[SimpleNamespace(bpp=b) for b in bytes_per_pixel],
                    plane_width=lambda i, w: max(1, (w + 2**i - 1) // 2**i),
                    plane_height=lambda i, h: max(1, (h + 2**i - 1) // 2**i),
                )
                data = (ctypes.POINTER(ctypes.c_uint8) * count)()
                stride = (ctypes.c_int * count)()
                buffers, oracle, sizes = [], [], []
                for i in range(count):
                    row_bytes = desc.plane_width(i, width) * bytes_per_pixel[i]
                    rows = desc.plane_height(i, height)
                    stride[i] = row_bytes + padding
                    size = stride[i] * rows
                    raw = bytes(rng.randrange(256) for _ in range(size))
                    buf = ctypes.create_string_buffer(b'GUARD___' + raw + b'___GUARD')
                    buffers.append(buf)
                    sizes.append(size)
                    data[i] = ctypes.cast(ctypes.addressof(buf) + 8,
                                          ctypes.POINTER(ctypes.c_uint8))
                    # Independent byte-index oracle, not the candidate's ctypes row copy.
                    oracle.append(bytes(raw[y * stride[i] + x]
                                        for y in range(rows) for x in range(row_bytes)))
                namespace = dict(ctypes=ctypes, desc=desc, dst_w=width, dst_h=height,
                                 dst_data=data, dst_stride=stride)
                exec(code, namespace)
                label = (count, width, height, padding)
                assert namespace['snapshot']() == oracle, ('snapshot', label)
                namespace['clear_output']()
                assert namespace['snapshot']() == [bytes(len(p)) for p in oracle], ('reset snapshot', label)
                for buf, size in zip(buffers, sizes):
                    assert buf.raw[:8] == b'GUARD___', ('leading guard', label)
                    assert buf.raw[8 + size:16 + size] == b'___GUARD', ('trailing guard', label)
                    assert buf.raw[8:8 + size] == bytes(size), ('reset pixels and padding', label)
                layouts += 1
    return dict(status='pass', candidate_sha256=hashlib.sha256(source).hexdigest(),
                layouts=layouts,
                scope='Independent synthetic positive-stride layouts; not pinned-image allocator, ABI, or runtime validation')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: check_buffer_layouts.py MATERIALIZED_CANDIDATE.py')
    print(json.dumps(check(Path(sys.argv[1])), indent=2))
