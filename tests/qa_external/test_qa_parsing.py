"""Independent QA probes for scalar parsing (V0.2).

These tests are additive: no production module, fixture or existing test is
modified. Tests marked ``expectedFailure`` encode behaviour the auditor considers
incorrect; they guard the desired contract and fail loudly once it is fixed so
the marker can be removed deliberately.
"""
import unittest
from datetime import date as Date, datetime, timezone
from decimal import Decimal

from powerbi_autopilot.parsing import (
    check_locale, currency_hint, currency_marker, date as parse_date, missing, number)


class NumberParsingTests(unittest.TestCase):
    def test_brazilian_representations_with_explicit_locale(self):
        cases = {
            '1.234,56': Decimal('1234.56'),
            '10,50': Decimal('10.50'),
            'R$ 1.234,56': Decimal('1234.56'),
            'R$ -10,00': Decimal('-10.00'),
            '(1.234,56)': Decimal('-1234.56'),
            '(R$ 1.234,56)': Decimal('-1234.56'),
            '1.234.567': Decimal('1234567'),
            '0,001': Decimal('0.001'),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                parsed = number(raw, 'pt-BR')
                self.assertEqual(parsed.status, 'valid')
                self.assertEqual(parsed.value, expected)

    def test_north_american_representations_with_explicit_locale(self):
        cases = {
            '1,234.56': Decimal('1234.56'),
            '10.50': Decimal('10.50'),
            'US$ 20.00': Decimal('20.00'),
            '-1,234.56': Decimal('-1234.56'),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                parsed = number(raw, 'en-US')
                self.assertEqual(parsed.status, 'valid')
                self.assertEqual(parsed.value, expected)

    def test_mismatched_locale_fails_closed_instead_of_guessing(self):
        # A pt-BR style decimal under en-US is not a legal grouped number, so the
        # engine refuses it (loud BLOCKER downstream) rather than reinterpreting.
        for raw, locale in (('10,50', 'en-US'), ('10.50', 'pt-BR'), ('1 234,56', 'pt-BR')):
            with self.subTest(raw=raw, locale=locale):
                self.assertEqual(number(raw, locale).status, 'invalid')

    def test_without_locale_only_single_digit_groups_are_ambiguous(self):
        self.assertEqual(number('1.234').status, 'ambiguous')
        self.assertEqual(number('1,234').status, 'ambiguous')
        self.assertEqual(number('1.234,56').value, Decimal('1234.56'))
        self.assertEqual(number('1.234.567').value, Decimal('1234567'))
        self.assertEqual(number('1234').value, Decimal('1234'))

    def test_non_numeric_and_empty_inputs(self):
        self.assertEqual(number('').status, 'missing')
        self.assertEqual(number(None).status, 'missing')
        self.assertEqual(number('   ').status, 'missing')
        self.assertEqual(number(True).status, 'invalid')
        self.assertEqual(number('R$').status, 'invalid')
        self.assertEqual(number('abc').status, 'invalid')
        self.assertEqual(number('1e5').status, 'invalid')
        self.assertEqual(number(float('nan')).status, 'missing')
        self.assertEqual(number(Decimal('NaN')).status, 'missing')
        self.assertEqual(number(Decimal('12.50')).value, Decimal('12.50'))

    def test_currency_annotations(self):
        self.assertEqual(currency_hint('R$ 10,00'), 'BRL')
        self.assertEqual(currency_hint('US$ 10.00'), 'USD')
        self.assertEqual(currency_hint('BRL 10'), 'BRL')
        self.assertEqual(currency_hint(u'\u20ac 10'), 'EUR')
        # A bare symbol does not identify a currency.
        self.assertIsNone(currency_hint('$ 10.00'))
        self.assertTrue(currency_marker('R$ 10,00'))
        self.assertFalse(currency_marker('R$'))

    @unittest.expectedFailure
    def test_qa_f09_leading_zero_group_must_not_be_a_thousands_separator(self):
        """QA-F09 (LIKELY BUG, LOW-MEDIUM): silent x1000 magnitude error.

        ``0,500`` / ``0,001`` are written by pt-BR sources to mean fractional
        unit rates. Under an explicit ``en-US`` locale the grouping pattern
        ``\\d{1,3}(?:,\\d{3})+`` accepts a leading ``0`` group and returns 500 /
        1, i.e. a silent 1000x magnification of a value that can only be a
        decimal in practice. A leading zero group never appears in a legitimately
        grouped number, so the safe answer is ``invalid`` (and thus a BLOCKER).
        """
        self.assertEqual(number('0,500', 'en-US').status, 'invalid')
        self.assertEqual(number('0,001', 'en-US').status, 'invalid')


class DateParsingTests(unittest.TestCase):
    def test_iso_forms(self):
        self.assertEqual(parse_date('2026-01-05').value, Date(2026, 1, 5))
        self.assertEqual(parse_date('2026-01-05T10:00:00Z').value, Date(2026, 1, 5))
        self.assertEqual(parse_date('2026-01-05 10:00').value, Date(2026, 1, 5))
        self.assertEqual(parse_date('2026-01-05T10:00:00+03:00').value, Date(2026, 1, 5))

    def test_native_values(self):
        stamp = datetime(2026, 1, 5, 23, 30, tzinfo=timezone.utc)
        self.assertEqual(parse_date(stamp).value, Date(2026, 1, 5))
        self.assertEqual(parse_date(Date(2026, 1, 5)).value, Date(2026, 1, 5))
        self.assertEqual(parse_date(None).status, 'missing')
        self.assertEqual(parse_date(20260105).status, 'invalid')

    def test_day_month_order_depends_on_explicit_locale(self):
        self.assertEqual(parse_date('05/01/2026', 'pt-BR').value, Date(2026, 1, 5))
        self.assertEqual(parse_date('05/01/2026', 'en-US').value, Date(2026, 5, 1))
        self.assertEqual(parse_date('05/01/2026').status, 'ambiguous')
        # Equal components cannot be misread, so no ambiguity is reported.
        self.assertEqual(parse_date('01/01/2026').value, Date(2026, 1, 1))

    def test_unambiguous_without_locale(self):
        self.assertEqual(parse_date('13/05/2026').value, Date(2026, 5, 13))
        self.assertEqual(parse_date('05/13/2026').value, Date(2026, 5, 13))

    def test_invalid_calendar_values_are_refused(self):
        for raw in ('2026-02-30', '2026-13-01', '31/02/2026', '30/02/2026', '2026-00-10',
                    'jan/26', '05/01/26', '2026-1-5', '2026/01/05', '05.01.2026'):
            with self.subTest(raw=raw):
                self.assertEqual(parse_date(raw).status, 'invalid')
        # Fail-closed even when the locale would invert the fields.
        self.assertEqual(parse_date('05/13/2026', 'pt-BR').status, 'invalid')

    def test_locale_validation_and_missing(self):
        self.assertIsNone(check_locale('pt-BR'))
        with self.assertRaises(ValueError):
            check_locale('pt_BR')
        self.assertTrue(missing('   '))
        self.assertFalse(missing('0'))


if __name__ == '__main__':
    unittest.main()
