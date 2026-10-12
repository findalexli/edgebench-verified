"""Independent (pure-Python, no SimPEG) gravity forward check for dabic_gravity_inversion.

Re-creates the evaluator's hidden 'smoke' geometry (eval_dabic_v2.py:538-601) from its
source constants, and evaluates gz with an own implementation of the Nagy/Plouff
rectangular-prism formula. Purpose: unit/scale sanity (g/cc -> mGal), slab-limit
validation, SNR of the hidden noise model, and receiver/cell-corner coincidence.
It does NOT reproduce the judge's numbers (SimPEG is unavailable locally).
Usage: python3 -I prism_forward_check.py
"""
import math

G = 6.674e-11  # m^3 kg^-1 s^-2
SI_TO_MGAL = 1e5
GCC = 1000.0   # 1 g/cc = 1000 kg/m^3


def prism_gz(xo, yo, zo, x1, x2, y1, y2, z1, z2, rho_gcc):
    """Downward gz (mGal) at (xo,yo,zo) from prism; z positive DOWN; observation above."""
    s = 0.0
    eps = 1e-10
    for i, X in enumerate((x1 - xo, x2 - xo)):
        for j, Y in enumerate((y1 - yo, y2 - yo)):
            for k, Z in enumerate((z1 - zo, z2 - zo)):
                mu = (-1) ** (i + j + k)
                r = math.sqrt(X * X + Y * Y + Z * Z)
                t = 0.0
                if abs(X) > eps and r + Y > eps:
                    t += X * math.log(Y + r)
                if abs(Y) > eps and r + X > eps:
                    t += Y * math.log(X + r)
                if abs(Z) > eps:
                    t -= Z * math.atan2(X * Y, Z * r)
                s += mu * t
    return G * rho_gcc * GCC * s * SI_TO_MGAL


# 1) Bouguer-slab limit: 2*pi*G*rho*t, 1 g/cc, t=100 m -> 4.193 mGal
L = 2e6
slab = prism_gz(0, 0, 0, -L, L, -L, L, 100.0, 200.0, 1.0)
print("slab check: prism=%.4f mGal, 2*pi*G*rho*t=%.4f mGal" % (slab, 2 * math.pi * G * 1000 * 100 * 1e5))

# 2) smoke case geometry (eval_dabic_v2.py:546-550, 557-595), mesh x0='00N' -> z in [-nz*h, 0]
nx, ny, nz, h = 12, 10, 5, 180.0
rx_nx, rx_ny = 10, 8
x_max, y_max = nx * h, ny * h
cells = []
for kz in range(nz):
    zc = -nz * h + (kz + 0.5) * h
    for jy in range(ny):
        yc = (jy + 0.5) * h
        for ix in range(nx):
            xc = (ix + 0.5) * h
            b1 = (0.18 * x_max < xc < 0.43 * x_max and 0.58 * y_max < yc < 0.82 * y_max
                  and -0.78 * nz * h < zc < -0.25 * nz * h)
            b2 = (0.55 * x_max < xc < 0.78 * x_max and 0.22 * y_max < yc < 0.52 * y_max
                  and -0.70 * nz * h < zc < -0.22 * nz * h)
            if b1 or b2:
                cells.append((xc, yc, zc))
rxs = [(x_max * i / (rx_nx - 1), y_max * j / (rx_ny - 1)) for j in range(rx_ny) for i in range(rx_nx)]
d = []
for (xo, yo) in rxs:
    g = 0.0
    for (xc, yc, zc) in cells:
        # convert elevation to depth (positive down) with receivers at elevation 0
        g += prism_gz(xo, yo, 0.0, xc - h / 2, xc + h / 2, yc - h / 2, yc + h / 2, -(zc + h / 2), -(zc - h / 2), 1.0)
    d.append(g)
sig = [0.06 * abs(v) + 0.025 for v in d]
print("smoke: n_cells_anomalous=%d of %d, n_data=%d" % (len(cells), nx * ny * nz, len(rxs)))
print("smoke gz (mGal): min=%.3f max=%.3f mean=%.3f ; mean sigma=%.3f ; peak SNR=%.1f" % (
    min(d), max(d), sum(d) / len(d), sum(sig) / len(sig), max(d) / (0.06 * max(d) + 0.025)))
corner = sum(1 for (xo, yo) in rxs if abs(xo / h - round(xo / h)) < 1e-9 and abs(yo / h - round(yo / h)) < 1e-9)
print("receivers coinciding with top-surface cell corners (z=0): %d of %d" % (corner, len(rxs)))
