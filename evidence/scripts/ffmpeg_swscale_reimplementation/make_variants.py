#!/usr/bin/env python3
"""Create honest-but-incomplete variants of the shipped Rust scaffold (src/lib.rs).
usage: make_variants.py <scaffold_dir> <out_dir>"""
import shutil, sys, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
ANCHOR = "    let ctx = unsafe { &*(opaque as *const SwsContext) };\n"
VARIANTS = {
    "v0_scaffold": "",
    # library has not implemented RGBA->RGB24 yet and reports an error code
    "v1_rgba_rgb24_unsupported":
        "    if ctx.src_fmt == PIXFMT_RGBA && ctx.dst_fmt == PIXFMT_RGB24 { return -3; }\n",
    # library not implemented 3:1 downscale yet; reports an error
    "v2_3to1_downscale_unsupported":
        "    if ctx.src_w == 3 * ctx.dst_w { return -3; }\n",
    # bug: for 3:1 downscale the library returns success but writes nothing
    "v3_3to1_downscale_silent_noop":
        "    if ctx.src_w == 3 * ctx.dst_w { return 0; }\n",
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
