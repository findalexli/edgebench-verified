"""Behavioral checks against independently evaluated, rational score scales."""
import importlib.util
import csv
import json
import tempfile
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('impact', Path(__file__).resolve().parents[1] / 'tools/estimate_impact.py')
impact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(impact)


def original(raw):
    if raw <= 5369:
        return F(0)
    if raw <= 88189:
        return F(20) * (raw - 5369) / (88189 - 5369)
    return F(20) + F(60) * (raw - 88189) / (330195 - 88189)


def repaired(raw):
    return max(F(0), min(F(100), F(100) * (raw - 3418) / (92304 - 3418)))


class ImpactIntervals(unittest.TestCase):
    def test_encloses_mixed_segment_and_clipped_run_averages(self):
        points = [0, 3418, 3419, 5368, 5369, 5370, 50000, 88188, 88189, 88190, 92304]
        for count in [1, 2, 3]:
            for runs in product(points, repeat=count):
                old = sum(map(original, runs)) / count
                new = sum(map(repaired, runs)) / count
                published = round(float(old), 1)
                low, high = impact.treant_interval(published)
                self.assertLessEqual(low, float(new) + 1e-10, runs)
                self.assertGreaterEqual(high + 1e-10, float(new), runs)

    def test_chord_and_affine_envelope_exact_at_all_linear_breakpoints(self):
        # All three functions are piecewise affine; checking every breakpoint
        # settles the real-valued raw domain, not merely these finite examples.
        cap = original(92304)
        for raw in [0, 3418, 5369, 88189, 92304]:
            s = original(raw)
            self.assertLessEqual(100*s/cap, repaired(raw))
            self.assertLessEqual(repaired(raw), 100*(1951+4141*s)/88886)

    def test_mean_does_not_determine_repaired_score(self):
        # Both original means are 10; one includes clipping and the other does not.
        first = [0, 88189]
        second = [46779, 46779]
        self.assertEqual(sum(map(original, first)), sum(map(original, second)))
        self.assertNotEqual(sum(map(repaired, first)), sum(map(repaired, second)))

    def test_portfolio_sensitivity_is_not_in_documented_limit_range(self):
        effects = {'portfolio': dict(kind='sensitivity', direction='either', bound=.3921, bound_down=.1)}
        start = {'portfolio': (30., 30.)}
        self.assertEqual(impact.effect_intervals(start, effects, {'bounded'}), start)
        self.assertEqual(impact.effect_intervals(start, effects, {'sensitivity'}), {'portfolio': (29.9, 30.3921)})

    def test_overlapping_intervals_do_not_certify_order(self):
        self.assertFalse(impact.ranking_certified((40, 44), (41, 42)))
        self.assertFalse(impact.ranking_certified((42, 44), (41, 42)))
        self.assertTrue(impact.ranking_certified((42.1, 44), (41, 42)))

    def test_serialized_endpoints_enclose_exact_intervals(self):
        # The CSV must enclose the EXACT rational interval, not a float approximation of it.
        lb = impact.parse_leaderboard()
        effects = json.loads((impact.ROOT / 'evidence/impact/effects.json').read_text())
        exact = impact.interval_rows(lb, effects, impact.exact)
        # Independent exact recomputation of the scale interval (own code, not the module's).
        cap = F(20) + F(60) * F(92304 - 88189, 330195 - 88189)
        for model in impact.MODELS:
            lows, highs = [], []
            for task, row in lb.items():
                v = row[model]
                if v is None or task == 'dabic_gravity_inversion':
                    continue
                v = F(str(v))
                if task == 'treant_forest':
                    lo, hi = max(F(0), v - F(1, 20)), min(cap, v + F(1, 20))
                    lows.append(100 * lo / cap); highs.append(min(F(100), 100 * (1951 + 4141 * hi) / F(88886)))
                elif task == 'borden_source_inversion':
                    lows.append(100 * max(F(0), v - F(1, 20)) / 109); highs.append(100 * min(F(109), v + F(1, 20)) / 109)
                else:
                    lows.append(max(F(0), v - F(1, 20))); highs.append(min(F(100), v + F(1, 20)))
            self.assertEqual(exact[model]['scale_low'], sum(lows) / len(lows))
            self.assertEqual(exact[model]['scale_high'], sum(highs) / len(highs))
        out = {m: dict(model=m, **{k: v for k, v in r.items() if k.endswith(('_low', '_high'))})
               for m, r in exact.items()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'impact.csv'
            impact.write_impact_csv(out, path)
            with path.open() as stream:
                actual = list(csv.DictReader(stream))
        self.assertEqual(len(actual), len(impact.MODELS))
        for row in actual:
            for name, value in exact[row['model']].items():
                if not name.endswith(('_low', '_high')):
                    continue
                written = F(row[name])          # the CSV decimal, read exactly
                if name.endswith('_low'):
                    self.assertLessEqual(written, value, (row['model'], name))
                else:
                    self.assertGreaterEqual(written, value, (row['model'], name))
                self.assertLessEqual(abs(written - value), F(1, 10 ** 9), (row['model'], name))

    def test_published_csv_encloses_exact_intervals(self):
        lb = impact.parse_leaderboard()
        effects = json.loads((impact.ROOT / 'evidence/impact/effects.json').read_text())
        exact = impact.interval_rows(lb, effects, impact.exact)
        with (impact.ROOT / 'data/impact.csv').open() as stream:
            for row in csv.DictReader(stream):
                for name, value in exact[row['model']].items():
                    if name.endswith('_low'):
                        self.assertLessEqual(F(row[name]), value, (row['model'], name))
                    elif name.endswith('_high'):
                        self.assertGreaterEqual(F(row[name]), value, (row['model'], name))

    def test_juliet_bound_encloses_exact_witness(self):
        effects = json.loads((impact.ROOT / 'evidence/impact/effects.json').read_text())
        self.assertGreaterEqual(F(str(effects['juliet_vulnerability_analyzer']['bound'])), F(6380, 241))

    def test_rounding_propagated_on_unchanged_tasks_and_borden(self):
        result = impact.scale_intervals({'unchanged': {'M': 50.}, 'borden_source_inversion': {'M': 50.},
                                        'dabic_gravity_inversion': {'M': 0.}}, 'M')
        self.assertEqual(result['unchanged'], (49.95, 50.05))
        self.assertEqual(result['borden_source_inversion'], (100*49.95/109, 100*50.05/109))
        self.assertNotIn('dabic_gravity_inversion', result)


if __name__ == '__main__':
    unittest.main()
