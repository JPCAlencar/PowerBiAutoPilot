"""Independent QA probes for the financial diagnosis (V0.2).

Synthetic tables only. No production module, fixture or existing test is changed.
``expectedFailure`` tests encode defects found by this audit (see
docs/QA_INDEPENDENT_V0.2.md, findings QA-F01..QA-F08).
"""
import unittest

import pandas as pd

from powerbi_autopilot import financial
from powerbi_autopilot.contracts import Table
from powerbi_autopilot.profiling import profile_table
from powerbi_autopilot.semantics import map_columns


def table(data, name='qa-table', sha='qa-synthetic-0000000000000000'):
    frame = pd.DataFrame(data, dtype=object)
    source = {'file': 'qa.csv', 'sheet': None, 'sha256': sha}
    return Table(name, frame, source, list(range(2, len(frame) + 2)))


def diagnose(t, locale=None):
    p = profile_table(t, locale)
    return financial.diagnose(t, p, map_columns(t, p, locale), locale)


def codes(result):
    return {i['code'] for i in result['issues']}


def indicator(result, key):
    return next(m for m in result['indicators'] if m['id'] == key)


class CleanFinanceTests(unittest.TestCase):
    def test_complete_schema_reaches_requires_contract_without_blockers(self):
        t = table({'Valor': ['100,00', '50,00'], 'Tipo': ['Receita', 'Despesa'],
                   'Moeda': ['BRL', 'BRL'], 'Status': ['Pago', 'Pendente'],
                   'Data Pagamento': ['2026-01-05', '2026-01-06']})
        r = diagnose(t, 'pt-BR')
        self.assertEqual(codes(r), set())
        self.assertEqual(indicator(r, 'cash_received')['status'], 'requires_contract')
        self.assertEqual(indicator(r, 'cash_paid')['status'], 'requires_contract')
        self.assertEqual(indicator(r, 'incurred_expenses')['status'], 'insufficient_evidence')
        self.assertEqual(r['roles']['amount'], ['Valor'])
        self.assertEqual(r['currencies_observed'], ['BRL'])
        self.assertEqual(r['domain']['name'], 'finance')
        self.assertEqual(r['domain']['status'], 'hypothesis')

    def test_no_metric_value_is_ever_emitted(self):
        t = table({'Valor': ['100,00'], 'Tipo': ['Receita'], 'Moeda': ['BRL'],
                   'Status': ['Pago'], 'Data Pagamento': ['2026-01-05']})
        r = diagnose(t, 'pt-BR')
        for metric in r['indicators']:
            self.assertNotIn('value', metric)
            self.assertNotIn('total', metric)
        available = [m['id'] for m in r['indicators'] if m['status'] == 'available']
        # Only the observed row count is available; every business metric needs a contract.
        self.assertEqual(available, ['record_count'])

    def test_sign_inconsistency_and_special_movements_are_warnings(self):
        t = table({'Tipo': ['Receita', 'Transferência', 'Estorno'], 'Valor': ['-100', '100', '-100'],
                   'Moeda': ['BRL', 'BRL', 'BRL'], 'Status': ['Pago', 'Pago', 'Cancelado'],
                   'Data Pagamento': ['2026-01-01', '2026-01-02', '2026-01-03']})
        r = diagnose(t, 'pt-BR')
        by_code = {i['code']: i for i in r['issues']}
        self.assertEqual(by_code['sign_type_inconsistency']['severity'], 'WARNING')
        self.assertEqual(by_code['special_movements']['severity'], 'WARNING')
        self.assertEqual(by_code['cancelled_records']['severity'], 'WARNING')
        self.assertIn('special_movement_policy',
                      indicator(r, 'cash_received')['missing_requirements'])

    def test_currency_conflict_blocks_monetary_metrics(self):
        t = table({'Valor': ['R$ 10,00', 'US$ 20.00'], 'Tipo': ['Receita', 'Receita'],
                   'Moeda': ['USD', 'USD'], 'Status': ['Pago', 'Pago'],
                   'Data Pagamento': ['2026-01-01', '2026-01-02']})
        r = diagnose(t, 'pt-BR')
        self.assertIn('currency_conflict', codes(r))
        event = next(i for i in r['issues'] if i['code'] == 'currency_conflict')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['scope'], 'monetary_metrics')
        self.assertEqual(event['source_rows'], [2])
        # Only the declared currency survives; the conflict row adds no new currency.
        self.assertEqual(r['currencies_observed'], ['USD'])
        self.assertIn('currency', indicator(r, 'cash_received')['missing_requirements'])

    def test_multiple_declared_currencies_block_cross_currency_metrics(self):
        t = table({'Valor': ['R$ 10,00', 'US$ 20.00'], 'Tipo': ['Receita', 'Receita'],
                   'Moeda': ['BRL', 'USD'], 'Status': ['Pago', 'Pago'],
                   'Data Pagamento': ['2026-01-01', '2026-01-02']})
        r = diagnose(t, 'pt-BR')
        event = next(i for i in r['issues'] if i['code'] == 'mixed_currencies')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['scope'], 'cross_currency_metrics')
        self.assertEqual(event['count'], 2)
        self.assertEqual(r['currencies_observed'], ['BRL', 'USD'])

    def test_value_without_any_currency_is_blocked(self):
        t = table({'Valor': ['10,00', '20,00'], 'Tipo': ['Receita', 'Despesa'],
                   'Status': ['Pago', 'Pendente'],
                   'Data Pagamento': ['2026-01-01', '']})
        r = diagnose(t, 'pt-BR')
        event = next(i for i in r['issues'] if i['code'] == 'unknown_currency')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['source_rows'], [2, 3])
        self.assertEqual(r['currencies_observed'], [])


class StatusVocabularyTests(unittest.TestCase):
    def test_unknown_status_blocks_cash_metrics_with_row_evidence(self):
        # Vocabulary gap recorded as QA-F08: 'Em aberto' is a very common pt-BR
        # status and is not in PENDING, so the row becomes a BLOCKER.
        t = table({'Valor': ['100,00', '50,00'], 'Tipo': ['Receita', 'Receita'],
                   'Moeda': ['BRL', 'BRL'], 'Status': ['Em aberto', 'Pago'],
                   'Data Pagamento': ['2026-01-05', '2026-01-06']})
        r = diagnose(t, 'pt-BR')
        event = next(i for i in r['issues'] if i['code'] == 'unknown_payment_status')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['scope'], 'cash_metrics')
        self.assertEqual(event['source_rows'], [2])
        self.assertIn('payment_status', indicator(r, 'cash_received')['missing_requirements'])

    def test_paid_row_without_any_date_column_is_reported(self):
        t = table({'Valor': ['100,00'], 'Tipo': ['Receita'], 'Moeda': ['BRL'],
                   'Status': ['Pago']})
        r = diagnose(t, 'pt-BR')
        event = next(i for i in r['issues'] if i['code'] == 'paid_without_payment_date')
        self.assertEqual(event['severity'], 'BLOCKER')
        self.assertEqual(event['scope'], 'cash_metrics')
        self.assertEqual(event['count'], 1)

    @unittest.expectedFailure
    def test_qa_f08b_numeric_flag_is_not_a_payment_status(self):
        """QA-F08b: PAID contains '1' and PENDING contains '0', so a boolean-style
        column literally named ``Status`` is accepted as payment_status with
        confidence 0.70 (role hypothesis). Expected: a 1/0-only column is a flag,
        not a paid/pending vocabulary, and must not feed cash metrics.
        """
        t = table({'Valor': ['100,00', '50,00'], 'Tipo': ['Receita', 'Despesa'],
                   'Moeda': ['BRL', 'BRL'], 'Status': ['1', '0']})
        r = diagnose(t, 'pt-BR')
        self.assertEqual(r['roles'].get('payment_status', []), [])
        self.assertNotIn('paid_without_payment_date', codes(r))


class NameOnlyFallbackDefectTests(unittest.TestCase):
    """QA-F01: name-only fallbacks ignore the value evidence used by map_columns."""

    @unittest.expectedFailure
    def test_qa_f01_task_list_status_is_not_a_payment_status(self):
        """A schedule column named ``Status`` (Concluído / Em andamento) is turned
        into a payment status by ``named({'status'})`` even though map_columns
        rejected it (0% of values are paid/pending tokens), and every row is then
        reported as a BLOCKER. Expected: insufficient_evidence and no financial
        BLOCKER; a task table must not inherit cash-metric vocabulary checks.
        """
        t = table({'Tarefa': ['A', 'B'], 'Responsável': ['Ana', 'Bruno'],
                   'Status': ['Concluído', 'Em andamento']})
        p = profile_table(t)
        mapped = {c['column']: c['status'] for c in map_columns(t, p)}
        r = diagnose(t)
        self.assertEqual(mapped['Status'], 'insufficient_evidence')
        self.assertNotIn('unknown_payment_status', codes(r))

    @unittest.expectedFailure
    def test_qa_f01_crm_classification_columns_are_not_movement_types(self):
        """``Tipo`` = PF/PJ (customer type) and ``Status`` = Ativo/Inativo are
        re-interpreted as movement/payment status by name, producing BLOCKERs on a
        table with no financial flow. Expected: both columns stay
        insufficient_evidence and no BLOCKER is raised for them.
        """
        t = table({'Cliente_ID': ['1', '2'], 'Nome': ['Ana', 'Bravo'],
                   'Tipo': ['PF', 'PJ'], 'Status': ['Ativo', 'Inativo']})
        found = codes(diagnose(t))
        self.assertNotIn('unknown_movement_type', found)
        self.assertNotIn('unknown_payment_status', found)


class HeaderMatchingDefectTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_qa_f03_realistic_pt_br_headers_are_mapped(self):
        """QA-F03: aliases must match the whole normalized name or a ``_alias``
        suffix, so the extremely common headers ``Valor Total`` and
        ``Data de Pagamento`` are unmapped and every cash indicator degrades to
        insufficient_evidence. Expected: amount/payment_date recognised.
        """
        t = table({'Valor Total': ['100,00', '50,00'], 'Tipo': ['Receita', 'Despesa'],
                   'Moeda': ['BRL', 'BRL'], 'Status': ['Pago', 'Pendente'],
                   'Data de Pagamento': ['2026-01-05', '2026-01-06']})
        r = diagnose(t, 'pt-BR')
        self.assertEqual(r['roles'].get('amount'), ['Valor Total'])
        self.assertEqual(indicator(r, 'cash_received')['status'], 'requires_contract')
        self.assertNotIn('paid_without_payment_date', codes(r))

    def test_qa_f02_known_alias_with_invalid_value_is_still_blocked(self):
        # Conformance: when the date column IS mapped, a broken value must block.
        t = table({'Valor': ['100,00'], 'Tipo': ['Receita'], 'Moeda': ['BRL'],
                   'Status': ['Pago'], 'Data Pagamento': ['31/02/2026']})
        r = diagnose(t, 'pt-BR')
        self.assertIn('paid_without_payment_date', codes(r))


if __name__ == '__main__':
    unittest.main()

