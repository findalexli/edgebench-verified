#!/usr/bin/env python3
"""Run actual scorer functions with deterministic library/image adapters.
Usage: ffmpeg.py ORIGINAL MATERIALIZED_CANDIDATE
This checks control flow and aggregation, not ABI, native timing or image budgets.
"""
import ast
import ctypes
import __future__
from contextlib import redirect_stdout
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics
import sys
from types import SimpleNamespace


class Lib:
    def __init__(self, mode='good', broken_call=None):
        self.mode,self.broken_call=mode,broken_call
        self.calls=0
        self.destroyed=False
    def swscale_create(self,*args):return 0 if self.mode=='null' else 1
    def swscale_destroy(self,ctx):self.destroyed=True
    def swscale_process(self,ctx,src,ss,dst,ds):
        self.calls+=1
        if self.calls==self.broken_call:
            if self.mode=='error':return -3
            if self.mode=='skip':return 0
            if self.mode=='wrong':ctypes.memset(dst[0],0,4);return 0
        ctypes.memmove(dst[0],b'\x80'*4,4)
        return 0


def load(path):
    nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('benchmark_workloads','compute_psnr','_run_scoring')]
    clock=iter(range(100000))
    def allocate(*args):
        buf=(ctypes.c_uint8*4)()
        return [ctypes.cast(buf,ctypes.POINTER(ctypes.c_uint8))],[2],[buf]
    ns=dict(ctypes=ctypes,math=math,statistics=statistics,random=random,
            time=SimpleNamespace(perf_counter=lambda:next(clock)),
            WARMUP_ITERS=2,BENCH_ITERS=4,PSNR_THRESHOLD_SCALE=40,PSNR_THRESHOLD_CONVERT=60,
            PIXFMT_DESCS={0:SimpleNamespace(num_planes=1,plane_width=lambda i,w:w,plane_height=lambda i,h:h,planes=[SimpleNamespace(bpp=1)])},
            generate_noise_planes=lambda *a:[b'\x80'*4],
            allocate_image=allocate,
            fill_image_from_bytes=lambda f,w,h,d,s,p:ctypes.memmove(d[0],p[0],4),
            image_to_bytes=lambda f,w,h,d,s:[ctypes.string_at(d[0],4)])
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec',flags=__future__.annotations.compiler_flag),ns)
    return ns


def main():
    versions=[load(p) for p in sys.argv[1:]]
    wl=dict(src_fmt=0,dst_fmt=0,src_w=2,src_h=2,dst_w=2,dst_h=2,algo=0,seed=1,label='control')
    rows=[]
    for mode,call in [('good',None),('null',None)]+[(m,c) for m in ('error','skip','wrong') for c in (1,3,4,6)]:
        vals=[]
        for ns in versions:
            lib=Lib(mode,call)
            speedups,results=ns['benchmark_workloads'](lib,Lib(),[wl])
            vals.append(speedups[0])
            if mode!='null':assert lib.destroyed
        assert vals[1]==(1.0 if mode=='good' else 0.0),(mode,call,vals)
        rows.append(dict(mode=mode,call=call,original=vals[0],candidate=vals[1]))
    # Actual _run_scoring final aggregation; huge remaining factors cannot hide a failed workload.
    aggregates=[]
    for factors,expected in [([100.0]*9+[0.0],0.0),([2.0]*10,2.0),([],0.0),([float('nan')],0.0),([float('inf')],0.0)]:
        vals=[]
        for ns in versions:
            observed=[]
            ns.update(sample_correctness_workloads=lambda r:[],check_correctness=lambda *a:(True,[]),
                      sample_benchmark_workloads=lambda r:[],benchmark_workloads=lambda *a:(factors,[]),
                      emit_reward=lambda directory,score,*a,**kw:observed.append(score))
            with redirect_stdout(io.StringIO()):ns['_run_scoring'](SimpleNamespace(output_dir='',total_time_ms=0),None,None,None)
            vals.append(observed[0])
        assert vals[1]==expected,(factors,vals)
        aggregates.append(dict(factors=[str(x) for x in factors],original=str(vals[0]),candidate=vals[1]))
    print(json.dumps({'scope':'actual scorer functions with deterministic adapters; no native timing or full image run','sha256':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sys.argv[1:]},'calls':rows,'aggregation':aggregates,'status':'pass'},indent=2))

if __name__=='__main__':main()
