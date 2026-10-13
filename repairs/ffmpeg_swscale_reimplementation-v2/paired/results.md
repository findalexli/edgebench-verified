# Paired results: ffmpeg_swscale_reimplementation v1 vs v2

E2B job `evidence/runs/ffmpeg_swscale_reimplementation-v2-paired-b` (exit 0, worker killed; first attempt
lost in a host restart). Original scorer path, `--network none`; v1 = pinned judge image; v2 = image
built from this package's Dockerfile. Scores are raw geometric-mean speedups as reported by the scorer (before the task's rescale).

| Submission | Role | v1 score | v2 score | v2 note |
| --- | --- | --- | --- | --- |
| forwarding shim, each frame once (`ref_r1`) | valid | 0.967353 | 0.980056 | 30/30, no timed errors |
| forwarding shim, each frame twice (`ref_r2`, about 2× slower) | valid | 0.509049 | 0.507032 | 30/30, no timed errors |
| shipped scaffold | baseline | 0.447819 | 0.012416 | its 1080p→360p nearest output is below 40 dB |
| errors on 3:1 downscale | **trigger** | **2.881761** | **0.000464** | two timed workloads return -3 |
| silent no-op on 3:1 downscale | **trigger** | **2.884506** | **0.000463** | two timed outputs below 40 dB |
| errors on RGBA→RGB24 | **trigger** | **1.305860** | **0.000451** | timed error + PSNR failure |
| unsupported yuv420p→rgb24 | invalid | 0.0 (28/30) | 0.0 (28/30) | correctness gate fails in both |

The two shim rows are two different correct controls, not two runs of one: `run.sh` builds `ref_shim.c` with `-DREPEAT=1` and `-DREPEAT=2` and passes each to `/opt/tests/compute_reward.py --candidate` directly, not through `eval_cmd`. The shim forwards every call to the original library (`/verifier-data/libswscale_baseline.so`), so its output is correct by construction; it is a scorer-level control, not a submission. `ref_shim.c` is not otherwise in the repository; its full source:

```c
/* Scorer-level valid control (NOT a submission): forwards the swscale_api.h calls to the
 * FFmpeg baseline library, so every output is correct by construction.  REPEAT=1 gives a
 * correct candidate at baseline speed; REPEAT=2 processes every frame twice (correct, ~2x slower).
 * Built and loaded only by the paired job, passed to compute_reward.py --candidate directly. */
#include <dlfcn.h>
#include <stdint.h>
#include <stddef.h>
#ifndef REPEAT
#define REPEAT 1
#endif
typedef void *(*create_fn)(int, int, int, int, int, int, int);
typedef int (*process_fn)(void *, const uint8_t *const[4], const int[4], uint8_t *const[4], const int[4]);
typedef void (*destroy_fn)(void *);
static void *h; static create_fn C; static process_fn P; static destroy_fn D;
static void init(void) {
    if (h) return;
    h = dlopen(BASELINE_PATH, RTLD_NOW | RTLD_LOCAL);
    if (!h) return;
    C = (create_fn)dlsym(h, "swscale_create");
    P = (process_fn)dlsym(h, "swscale_process");
    D = (destroy_fn)dlsym(h, "swscale_destroy");
}
void *swscale_create(int sw, int sh, int sf, int dw, int dh, int df, int a) {
    init(); return C ? C(sw, sh, sf, dw, dh, df, a) : NULL;
}
int swscale_process(void *c, const uint8_t *const s[4], const int ss[4], uint8_t *const d[4], const int ds[4]) {
    int r = 0;
    for (int i = 0; i < REPEAT; i++) r |= P(c, s, ss, d, ds);
    return r;
}
void swscale_destroy(void *c) { init(); if (D) D(c); }
```

The three trigger variants are one-line edits of the scaffold, which already fails `rgb24 1080p→360p nearest` on v2. The per-workload v2 errors in `result/out/summary_parsed.txt` show each edited workload is caught: `candidate process returned -3` on `rgba→rgb24 4K` (RGBA→RGB24) and on both 3:1 workloads (3:1 errors), and `timed output below PSNR threshold 40.0` on `rgb24→yuv420p 1080p→360p bilinear` (silent no-op).

**Verdict: accepted.** Wrong or missing timed output no longer earns speed credit; correct
implementations keep their scores within timing noise; the invalid control is rejected in both.
The scaffold's drop is correct: its output on one timed workload is genuinely wrong.
