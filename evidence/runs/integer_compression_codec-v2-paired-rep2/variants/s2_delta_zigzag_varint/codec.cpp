// Honest simple improvement over the starter: delta + zigzag + varint (scalar).
#include "intcompress.h"
#include <cstring>
#include <cstdint>
namespace { constexpr size_t kFail = static_cast<size_t>(-1); }
extern "C" size_t ic_encode(const uint32_t* in, size_t n, uint8_t* out, size_t cap) {
    if (cap < 8) return kFail;
    uint64_t nn = n; std::memcpy(out, &nn, 8); size_t off = 8; uint32_t prev = 0;
    for (size_t i = 0; i < n; ++i) {
        int32_t d = static_cast<int32_t>(in[i] - prev); prev = in[i];
        uint32_t z = (static_cast<uint32_t>(d) << 1) ^ static_cast<uint32_t>(d >> 31);
        if (cap - off < 5) return kFail;
        while (z >= 0x80u) { out[off++] = static_cast<uint8_t>(z) | 0x80u; z >>= 7; }
        out[off++] = static_cast<uint8_t>(z);
    }
    return off;
}
extern "C" size_t ic_decode(const uint8_t* in, size_t in_size, uint32_t* out, size_t cap) {
    if (in_size < 8) return kFail;
    uint64_t nn; std::memcpy(&nn, in, 8); size_t n = nn; if (n > cap) return kFail;
    size_t off = 8; uint32_t prev = 0;
    for (size_t i = 0; i < n; ++i) {
        uint32_t z = 0; int sh = 0;
        for (;;) { if (off >= in_size) return kFail; uint8_t b = in[off++]; z |= static_cast<uint32_t>(b & 0x7f) << sh; if (!(b & 0x80)) break; sh += 7; if (sh > 28) { if (off >= in_size) return kFail; } }
        int32_t d = static_cast<int32_t>((z >> 1) ^ (0u - (z & 1u)));
        prev += static_cast<uint32_t>(d); out[i] = prev;
    }
    return n;
}
extern "C" size_t ic_decode_block(const uint8_t*, size_t, size_t, uint32_t*, size_t) { return kFail; }
