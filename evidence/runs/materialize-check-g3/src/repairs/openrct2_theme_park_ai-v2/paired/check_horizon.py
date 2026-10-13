"""Recompute the per-scenario game horizon from the saved monitor logs and compare it with
(a) first-principles OpenRCT2 timing and (b) the numbers stated in the v2 prompt.
Usage: python3 -I check_horizon.py LOG [LOG...]   (logs written by scripts/openrct2_theme_park_ai/driver.py)"""
import json, sys
from fractions import Fraction as F

# OpenRCT2 timing. Sources: openrct2.d.ts in the work image (GameDate.monthProgress: 0..65536,
# "incremented by 4 each tick, so every month takes ~6.8 minutes"; 8 months per year, March..October)
# and OpenRCT2's fixed 40 Hz game update (25 ms; 16384/40 s = 6.83 min matches the d.ts comment).
TICKS_PER_MONTH = F(65536, 4)            # 16384
DAYS = [31, 30, 31, 30, 31, 31, 30, 31]  # March..October
DAYS_PER_YEAR = sum(DAYS)                # 245
MEAN_TICKS_PER_DAY = TICKS_PER_MONTH * 8 / DAYS_PER_YEAR
BASE_HZ = 40
def mult(speed): return 2 ** (speed - 1)  # speed 1,2,3,4 -> 1,2,4,8 updates per frame

def model_days_per_s(speed): return F(BASE_HZ * mult(speed)) / MEAN_TICKS_PER_DAY

print("month = %d ticks; mean day = %.1f ticks; speed-1 month = %.2f min" %
      (TICKS_PER_MONTH, float(MEAN_TICKS_PER_DAY), float(TICKS_PER_MONTH / BASE_HZ / 60)))
for s in (1, 3, 4):
    print("model speed %d: %.3f game days / wall-s; 120 s -> %.1f days" %
          (s, float(model_days_per_s(s)), float(120 * model_days_per_s(s))))
print("model: 992 target days at speed 4 need %.0f s" % float(992 / model_days_per_s(4)))
print()
print("%-38s %-20s %5s %4s %7s %7s %9s %7s %6s" % ("log", "scenario", "budget", "spd", "t_first", "t_last",
      "days", "d/s", "model"))
for path in sys.argv[1:]:
    speed = 1 if "speed1" in path else 3 if "speed3" in path else 8 if "speed8" in path else 4
    eff = 4 if speed == 8 else speed      # speed 8 is rejected (GameSetSpeedAction: Invalid speed 8)
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.startswith("{"): continue
        d = json.loads(line)
        tr = d["trajectory"]
        print("%-38s %-20s %5d %4s %7.1f %7.1f %4d(%s) %7.3f %6.3f  DONE=%s" % (
            path.split("/")[-1], d["scenario"], d["budget_s"], speed, tr[0][0], tr[-1][0],
            d["game_days_elapsed"], d["samples"], d["game_days_per_wall_s"],
            float(model_days_per_s(eff)), d["done_seen"]))
