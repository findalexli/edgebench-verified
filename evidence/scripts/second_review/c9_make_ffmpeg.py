#!/usr/bin/env python3
"""Jobs for the FFmpeg timed-output claim. Arms: real best r1 auto-18 and reviewer-named r1 agent-7, unchanged and with one added line in
swscale_process that returns -1 (or returns 0 without writing) on same-size RGBA->RGB24, the only timed workload no correctness suite covers."""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
from c9_jobs_common import job_dir, real_archive, rewrite, sub_once
T = 'ffmpeg_swscale_reimplementation'
patch = open(sys.argv[1]).read()
A = b"    let c = &mut *(ctx as *mut Context);\n"
COND = b"    if c.sf == Fmt::Rgba && c.df == Fmt::Rgb24 && c.sw == c.dw && c.sh == c.dh { return %d; }\n"
def arms(passes, first):
    r = ' '.join(reversed(first.split()))
    return f'''# judge_local with task.toml limits (cpus=4). Speedups are wall-clock ratios.
for pass in {passes}; do o="{first}"; [ $((pass%2)) = 0 ] && o="{r}"
  for arm in auto18 auto18_err auto18_noop agent7 agent7_err; do for sd in $o; do grade $arm-p$pass $sd $arm.tar.gz 240; done; done
done
'''
# -a and -b were first attempts: the Ubuntu snapshot mirror failed during the base image build on -a, so no arm ran. -a2 replaces -a; -b is regenerated.
for name, passes, first in (('-a2', '1', 'old new'), ('-b', '2 3', 'new old')):
    d = job_dir('community9-' + T + name, T, 'FFmpeg unchecked timed outputs; new = the output PSNR check in the benchmark.', 3000, patch, arms(passes, first))
    s = d + '/subs/'
    a18 = real_archive(T, '', 'auto-18'); a7 = real_archive(T, '', 'agent-7')
    shutil.copy(a18, s + 'auto18.tar.gz'); shutil.copy(a7, s + 'agent7.tar.gz')
    M = './src/lib.rs'
    rewrite(a18, s + 'auto18_err.tar.gz', {M: lambda b: sub_once(b, A, A + COND % -1)})
    rewrite(a18, s + 'auto18_noop.tar.gz', {M: lambda b: sub_once(b, A, A + COND % 0)})
    rewrite(a7, s + 'agent7_err.tar.gz', {M: lambda b: sub_once(b, A, A + COND % -1)})
    print(d)
