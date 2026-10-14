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
static int calls;
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
    calls = 0; init(); return C ? C(sw, sh, sf, dw, dh, df, a) : NULL;
}
int swscale_process(void *c, const uint8_t *const s[4], const int ss[4], uint8_t *const d[4], const int ds[4]) {
    calls++;
#ifdef SKIP_SECOND
    if (calls == 2) return 0;
#endif
#ifdef FAIL_ALWAYS
    return -3;
#endif
    int r = 0;
    for (int i = 0; i < REPEAT; i++) r |= P(c, s, ss, d, ds);
    return r;
}
void swscale_destroy(void *c) { init(); if (D) D(c); }
