import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from powerbi_autopilot.engine import analyze


FIXTURES = Path(__file__).parent / 'fixtures'


class BenchmarkTests(unittest.TestCase):
    def test_financial_clean(self):
        r = analyze([FIXTURES/'finance_clean.csv'])
        self.assertEqual(r['validation']['counts']['BLOCKER'], 0)
        self.assertEqual(r['tables'][0]['profile']['rows'], 8)
        self.assertEqual(r['tables'][0]['financial']['domain']['name'], 'finance')
        self.assertTrue(all(s['unchanged'] for s in r['source_integrity']))

    def test_inconsistent_finance_has_real_diagnostics(self):
        r = analyze([FIXTURES/'finance_dirty.csv'])
        codes = {i['code'] for i in r['issues']}
        expected = {'invalid_number', 'invalid_date', 'mixed_currencies', 'unknown_payment_status',
                    'paid_without_payment_date', 'classification_variants', 'suspected_duplicates'}
        self.assertTrue(expected <= codes, expected-codes)

    def test_semantic_ambiguity_declares_insufficient_evidence(self):
        r = analyze([FIXTURES/'finance_ambiguous.csv'])
        cash = next(m for m in r['tables'][0]['financial']['indicators'] if m['id'] == 'cash_received')
        self.assertEqual(cash['status'], 'insufficient_evidence')
        self.assertIn('payment_date', cash['missing_requirements'])
        self.assertFalse(any(c['status'] == 'validated' for c in r['tables'][0]['semantics']))

    def test_excel_relations_include_orphans_and_multiplication(self):
        r = analyze([FIXTURES/'finance_related.xlsx'])
        self.assertEqual(len(r['tables']), 3)
        self.assertIn('join_multiplication_risk', {i['code'] for i in r['issues']})
        self.assertTrue(any(c['orphan_rows'] for c in r['relationships']['candidates']))

    def test_regional_values_require_explicit_locale_when_ambiguous(self):
        p = FIXTURES/'regional_br.csv'
        no_locale = analyze([p])
        with_locale = analyze([p], locale='pt-BR')
        self.assertIn('ambiguous_number', {i['code'] for i in no_locale['issues']})
        self.assertNotIn('ambiguous_number', {i['code'] for i in with_locale['issues']})
        us = analyze([FIXTURES/'regional_us.csv'], locale='en-US')
        self.assertEqual(us['tables'][0]['profile']['columns'][0]['number_distribution']['min'], '-1234.56')

    def test_legitimate_duplicates_preserved_special_movements_and_project_dates(self):
        dup = analyze([FIXTURES/'legitimate_duplicates.csv'])
        self.assertEqual(dup['tables'][0]['profile']['rows'], 3)
        self.assertEqual(dup['tables'][0]['profile']['duplicate_rows'], 1)
        special = analyze([FIXTURES/'transfers_reversals.csv'])
        self.assertIn('special_movements', {i['code'] for i in special['issues']})
        project = analyze([FIXTURES/'projects_missing_dates.csv'])
        self.assertIn('insufficient_schedule_dates', {i['code'] for i in project['issues']})
        self.assertFalse(any(c['name'] == 'Data Início' for c in project['tables'][0]['profile']['columns']))

    def test_fixture_generation_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            for _ in range(2):
                subprocess.run([sys.executable, 'scripts/generate_benchmarks.py', '--output', str(dest)], check=True, capture_output=True)
                current = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()}
                if _ == 0:
                    first = current
                else:
                    self.assertEqual(current, first)


if __name__ == '__main__':
    unittest.main()
