"""Deviation of f32-derived representations of allowed angles from the exact angle (degrees).
Pure Python: f32 rounding via struct (IEEE round-to-nearest-even), products rounded after each op."""
import struct, math
def f(x): return struct.unpack('f', struct.pack('f', x))[0]
PI32 = f(math.pi)
def ulp32(x):
    b = struct.unpack('I', struct.pack('f', abs(x)))[0]
    return struct.unpack('f', struct.pack('I', b + 1))[0] - abs(f(x))
def paths(d):
    r32 = f(f(d) * f(PI32 / f(180.0)))          # Rust f32::to_radians: x * (PI/180) in f32
    r32b = f(math.radians(d))                    # f64 radians stored as f32
    return {
        'f32 rad -> f64 deg': math.degrees(r32),
        'f64 rad -> f32 -> f64 deg': math.degrees(r32b),
        'f32 rad -> f32 deg (to_degrees)': f(r32 * f(180.0 / PI32)),
    }
def dev(v, d): return abs((v - d + 180.0) % 360.0 - 180.0)
worst = {}
for d in [0, 90, 180, 270, 360, -90, -180, -270, 450, 540, 630, 720]:
    for k, v in paths(d).items():
        e = dev(v, d); worst[k] = max(worst.get(k, 0), e)
        if d in (90, 180, 270, -90, -180): print(f'{d:5} {k:34} {v!r:24} dev={e:.3e}')
print('worst over allowed angles (incl. +-360 multiples up to 720):')
for k, v in worst.items(): print(f'  {k:34} {v:.3e}')
m = 0.0
for i in range(0, 720001):
    d = i * 0.001 - 360.0
    for v in paths(d).values(): m = max(m, dev(v, d))
print('max deviation over every 0.001 deg in [-360, 360], all paths: %.3e deg' % m)
print('f32 ulp at 360 deg = %.3e deg; at 720 deg = %.3e; f32 ulp at 2pi rad = %.3e deg'
      % (ulp32(360.0), ulp32(720.0), math.degrees(ulp32(2 * math.pi))))
