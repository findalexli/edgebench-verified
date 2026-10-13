#!/usr/bin/env python3
"""Prepare the v2.2 FFmpeg native job after materializing its repair package.
Usage: python3 evidence/scripts/validator_followup/prepare_native.py JOB_DIRECTORY
Then use tools/e2b_run.py with lifetime3000/budget2700. This writes no credentials.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

root=Path(__file__).resolve().parents[3]
job=Path(sys.argv[1]).resolve()
job.mkdir(parents=True,exist_ok=False)
for task,short in [('ffmpeg_swscale_reimplementation','ffmpeg')]:
    src=root/'repairs'/(task+'-v2')
    pkg=job/('pkg-'+short)
    pkg.mkdir()
    lock=json.loads((src/'source-lock.json').read_text())
    for rel,digest in lock['materialize']['outputs'].items():
        data=(src/rel).read_bytes()
        assert hashlib.sha256(data).hexdigest()==digest,rel
        dest=pkg/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
    for name in ['Dockerfile','source-lock.json','repair.patch','materialize.sh']:
        shutil.copyfile(src/name,pkg/name)
shutil.copyfile(root/'repairs/ffmpeg_swscale_reimplementation-v2/paired/followup-ref-shim.c',job/'ref_shim.c')
shutil.copyfile(Path(__file__).with_name('ffmpeg_buffers.py'),job/'ffmpeg_buffers.py')
shutil.copyfile(Path(__file__).with_name('run_ffmpeg_native.sh'),job/'run.sh')
print(job)
