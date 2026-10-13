"""A stale translated conclusion must not override its corrected source."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_site as site


class TranslationFreshness(unittest.TestCase):
    def test_existing_but_stale_case_falls_back_and_marks_main_text(self):
        lang = site.Lang('zh')
        source = site.ROOT / 'cases/portfolio_risk_calibration.md'
        translated = site.ROOT / 'cases/zh/portfolio_risk_calibration.md'
        self.assertTrue(translated.exists())
        self.assertEqual(lang.source(source, translated), source.read_text())
        self.assertTrue(lang.major)

    def test_stale_plain_and_formal_do_not_override_english(self):
        lang = site.Lang('zh')
        own, en = lang.plain({'portfolio_risk_calibration': {'action': 'current'}})
        self.assertNotIn('portfolio_risk_calibration', own)
        self.assertEqual(lang.formal('treant_forest'), {})
        self.assertIn('formal:treant_forest', lang.t.missing)
        self.assertTrue(lang.formal('integer_compression_codec'))

    def test_english_does_not_get_translation_pending(self):
        lang = site.Lang('en')
        source = site.ROOT / 'cases/portfolio_risk_calibration.md'
        self.assertEqual(lang.source(source, source), source.read_text())
        self.assertFalse(lang.major)
        self.assertEqual(lang.pending, {})

    def test_built_stale_translation_is_noindex_and_contains_current_claim(self):
        page = (site.SITE / 'zh/tasks/portfolio_risk_calibration.html').read_text()
        self.assertIn('<meta name="robots" content="noindex">', page)
        self.assertIn('class="pending"', page)
        self.assertIn('0.3921', page)
        self.assertIn('not a global bound', page)


if __name__ == '__main__':
    unittest.main()
