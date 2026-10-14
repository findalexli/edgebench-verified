"""A stale translated conclusion must not override its corrected source."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_site as site

# The withholding mechanism is tested with an explicit pending list, so the tests do not depend on
# which translations tools/i18n/pending-zh.json currently withholds.
PENDING = {'sources': ['cases/portfolio_risk_calibration.md'],
           'plain': ['portfolio_risk_calibration'], 'formal': ['treant_forest']}


def stale_lang():
    lang = site.Lang('zh')
    lang.pending = PENDING
    return lang


class TranslationFreshness(unittest.TestCase):
    def test_existing_but_stale_case_falls_back_and_marks_main_text(self):
        lang = stale_lang()
        source = site.ROOT / 'cases/portfolio_risk_calibration.md'
        translated = site.ROOT / 'cases/zh/portfolio_risk_calibration.md'
        self.assertTrue(translated.exists())
        self.assertEqual(lang.source(source, translated), source.read_text())
        self.assertTrue(lang.major)

    def test_stale_plain_and_formal_do_not_override_english(self):
        lang = stale_lang()
        own, en = lang.plain({'portfolio_risk_calibration': {'action': 'current'}})
        self.assertNotIn('portfolio_risk_calibration', own)
        self.assertEqual(lang.formal('treant_forest'), {})
        self.assertIn('formal:treant_forest', lang.t.missing)
        self.assertTrue(lang.formal('integer_compression_codec'))

    def test_validation_translation_needs_current_english(self):
        lang = site.Lang('zh')
        tid, entry = next(iter(lang.extra['validation'].items()))
        self.assertEqual(lang.validation(tid, entry['en']), entry['text'])
        self.assertEqual(lang.validation(tid, entry['en'] + ' changed'), entry['en'] + ' changed')
        self.assertIn(f'validation:{tid}', lang.t.missing)

    def test_english_does_not_get_translation_pending(self):
        lang = site.Lang('en')
        source = site.ROOT / 'cases/portfolio_risk_calibration.md'
        self.assertEqual(lang.source(source, source), source.read_text())
        self.assertFalse(lang.major)
        self.assertEqual(lang.pending, {})

    def test_built_translation_contains_current_claim(self):
        page = (site.SITE / 'zh/tasks/portfolio_risk_calibration.html').read_text()
        self.assertIn('0.3921', page)
        self.assertIn('并非全局上限', page)


if __name__ == '__main__':
    unittest.main()
