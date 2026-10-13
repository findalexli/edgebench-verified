#!/usr/bin/env python3
"""Build paired-evaluation submissions from the shipped Rust scaffold (src/lib.rs).
Each variant adds at most one line to swscale_process (same anchor as
scripts/ffmpeg_swscale_reimplementation/make_variants.py).
usage: make_variants.py <scaffold_dir> <out_dir>"""
import shutil, sys, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
ANCHOR = "    let ctx = unsafe { &*(opaque as *const SwsContext) };\n"
VARIANTS = {
    # shipped scaffold, unchanged
    "scaffold": "",
    # triggers (review variants v1..v3): honest-incomplete paths that are only timed, never correctness-checked
    "trig_rgba_rgb24_unsupported":
        "    if ctx.src_fmt == PIXFMT_RGBA && ctx.dst_fmt == PIXFMT_RGB24 { return -3; }\n",
    "trig_3to1_unsupported":
        "    if ctx.src_w == 3 * ctx.dst_w { return -3; }\n",
    "trig_3to1_silent_noop":
        "    if ctx.src_w == 3 * ctx.dst_w { return 0; }\n",
    # invalid control: an unsupported path that the 30 correctness workloads DO cover
    "invalid_yuv420p_rgb24_unsupported":
        "    if ctx.src_fmt == PIXFMT_YUV420P && ctx.dst_fmt == PIXFMT_RGB24 { return -3; }\n",
}
for name, patch in VARIANTS.items():
    d = out / name
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(src, d, ignore=shutil.ignore_patterns("target", ".git"))
    lib = d / "src" / "lib.rs"
    text = lib.read_text()
    assert text.count(ANCHOR) == 1
    lib.write_text(text.replace(ANCHOR, ANCHOR + patch))
    print(name, "patched" if patch else "unchanged")
