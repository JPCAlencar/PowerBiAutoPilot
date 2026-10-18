import unittest
from copy import deepcopy

from powerbi_autopilot import financial, planning, validation
from powerbi_autopilot.profiling import profile_table
from powerbi_autopilot.semantics import map_columns
from test_intelligence import table


def diagnose(t, locale=None):
    p = profile_table(t, locale)
    return financial.diagnose(t, p, map_columns(t, p, locale), locale)


class FinancialTests(unittest.TestCase):
    def test_currency_markers_under_generic_name_are_diagnosed(self):
        r = diagnose(table({'x': ['R$ 10,00', 'US$ 20.00']}))
        self.assertEqual(r['currencies_observed'], ['BRL', 'USD'])
        self.assertIn('mixed_currencies', {i['code'] for i in r['issues']})

    def test_clean_finance_proposes_distinct_metrics_but_requires_contract(self):
        t = table({'ID': ['1', '2'], 'Tipo': ['Receita', 'Despesa'], 'Valor': ['100,00', '-30,00'],
                   'Moeda': ['BRL', 'BRL'], 'Pago': ['Sim', 'Sim'],
                   'Data Pagamento': ['2026-01-01', '2026-01-02'],
                   'Competência': ['2026-01-01', '2026-01-01']})
        r = diagnose(t)
        self.assertFalse(any(i['severity'] == 'BLOCKER' for i in r['issues']))
        metrics = {m['id']: m for m in r['indicators']}
        self.assertEqual(metrics['cash_received']['status'], 'requires_contract')
        self.assertEqual(metrics['cash_paid']['status'], 'requires_contract')
        self.assertEqual(metrics['incurred_expenses']['status'], 'requires_contract')
        self.assertEqual(metrics['overdue']['status'], 'insufficient_evidence')
        self.assertNotIn('value', metrics['cash_received'])

    def test_dirty_finance_flags_mixed_currency_sign_missing_payment_and_status(self):
        t = table({'Tipo': ['Receita', 'Receita', 'Despesa'], 'Valor': ['100,00', '-20,00', '-30,00'],
                   'Moeda': ['BRL', 'USD', 'BRL'], 'Pago': ['Sim', '?', 'Sim'],
                   'Data Pagamento': [None, None, '2026-01-03']})
        r = diagnose(t)
        codes = {i['code'] for i in r['issues']}
        self.assertTrue({'mixed_currencies', 'sign_type_inconsistency', 'paid_without_payment_date', 'unknown_payment_status'} <= codes)
        self.assertEqual(next(i for i in r['issues'] if i['code'] == 'paid_without_payment_date')['scope'], 'cash_metrics')
        self.assertEqual(next(m for m in r['indicators'] if m['id'] == 'record_count')['status'], 'available')

    def test_ambiguous_values_and_dates_do_not_become_revenue(self):
        t = table({'Valor': ['1,234', '2,345'], 'Data': ['01/02/2026', '02/03/2026']})
        r = diagnose(t)
        cash = next(m for m in r['indicators'] if m['id'] == 'cash_received')
        self.assertEqual(cash['status'], 'insufficient_evidence')
        self.assertIn('movement_type', cash['missing_requirements'])
        self.assertEqual(r['domain']['status'], 'hypothesis')

    def test_transfer_refund_cancelled_not_ordinary_revenue_and_balance_not_flow(self):
        t = table({'Tipo': ['Transferência', 'Estorno', 'Receita'], 'Valor': ['100', '-100', '100'],
                   'Status': ['Pago', 'Pago', 'Cancelado'], 'Saldo': ['1000', '900', '1000']})
        r = diagnose(t)
        codes = {i['code'] for i in r['issues']}
        self.assertTrue({'special_movements', 'cancelled_records', 'non_additive_balance'} <= codes)
        cash = next(m for m in r['indicators'] if m['id'] == 'cash_received')
        self.assertIn('special_movement_policy', cash['missing_requirements'])

    def test_plan_is_structured_and_never_suggests_automatic_dedup(self):
        t = table({'Valor': ['1,234', '1,234'], 'Data': ['01/02/2026', '01/02/2026']})
        p = profile_table(t)
        plan = planning.plan_transformations(t, p, map_columns(t, p))
        self.assertTrue(plan)
        for step in plan:
            self.assertTrue({'source', 'destination', 'operation', 'reason', 'risks', 'preconditions', 'status'} <= step.keys())
            self.assertFalse(step['executed'])
        self.assertNotIn('drop_duplicates', {s['operation'] for s in plan})
        self.assertEqual(len(t.frame), 2)


class ReconciliationTests(unittest.TestCase):
    def test_reorder_with_lineage_is_exact_even_with_cancelling_large_values(self):
        t = table({'Valor': ['10000000000000000000000000000.00', '0.01', '-10000000000000000000000000000.00'], 'Moeda': ['BRL']*3})
        after = deepcopy(t)
        after.frame = after.frame.iloc[[0, 2, 1]].copy()
        after.row_numbers = [2, 4, 3]
        r = validation.reconcile(t, after, ['Valor'], 'Moeda')
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['totals']['Valor']['BRL']['before'], '0.01')

    def test_reconciliation_requires_matching_provenance_identity(self):
        t = deepcopy(self.raw)
        t.source['sheet'] = 'other_sheet'
        self.assertEqual(validation.reconcile(self.raw, t)['status'], 'failed')
        t = deepcopy(self.raw)
        t.source.pop('sha256')
        self.assertEqual(validation.reconcile(t, deepcopy(t))['status'], 'failed')

    def test_large_decimal_totals_preserve_cents_beyond_context_precision(self):
        t = table({'Valor': ['123456789012345678901234567890.01', '0.02'], 'Moeda': ['BRL', 'BRL']})
        r = validation.reconcile(t, deepcopy(t), ['Valor'], 'Moeda')
        self.assertEqual(r['totals']['Valor']['BRL']['before'], '123456789012345678901234567890.03')

    def test_embedded_currency_conflict_cannot_be_reconciled(self):
        t = table({'Valor': ['USD 10.00'], 'Moeda': ['BRL']})
        r = validation.reconcile(t, deepcopy(t), ['Valor'], 'Moeda')
        self.assertEqual(r['status'], 'failed')
        self.assertIn('unreconciled_currency_conflict', {i['code'] for i in r['issues']})

    def setUp(self):
        self.raw = table({'ID': ['1', '2', '3'], 'Valor': ['0,10', '0,20', '-0,05'], 'Moeda': ['BRL', 'BRL', 'USD']})

    def test_exact_totals_per_currency_and_identity(self):
        result = validation.reconcile(self.raw, deepcopy(self.raw), ['Valor'], 'Moeda')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['totals']['Valor']['BRL']['before'], '0.30')
        self.assertEqual(result['totals']['Valor']['USD']['before'], '-0.05')

    def test_dropped_row_and_duplicate_identity_are_blockers_even_if_total_same(self):
        after = deepcopy(self.raw)
        after.frame = after.frame.iloc[:2].copy()
        after.row_numbers = [2, 3]
        r = validation.reconcile(self.raw, after, ['Valor'], 'Moeda')
        self.assertEqual(r['status'], 'failed')
        self.assertIn('row_loss_or_gain', [i['code'] for i in r['issues']])
        after = deepcopy(self.raw)
        after.row_numbers = [2, 2, 4]
        self.assertEqual(validation.reconcile(self.raw, after, ['Valor'], 'Moeda')['status'], 'failed')

    def test_offsetting_cell_edits_do_not_hide_behind_equal_totals(self):
        after = deepcopy(self.raw)
        after.frame.loc[0, 'Valor'] = '0,20'
        after.frame.loc[1, 'Valor'] = '0,10'
        r = validation.reconcile(self.raw, after, ['Valor'], 'Moeda')
        self.assertEqual(r['status'], 'failed')
        self.assertEqual(r['changed_cells'], 2)
        self.assertEqual(r['changes'][0]['source_row'], 2)

    def test_unparseable_or_unknown_currency_cannot_pass(self):
        bad = deepcopy(self.raw)
        bad.frame.loc[0, 'Valor'] = '1,234'
        self.assertEqual(validation.reconcile(bad, deepcopy(bad), ['Valor'], 'Moeda')['status'], 'failed')
        bad = deepcopy(self.raw)
        bad.frame.loc[0, 'Moeda'] = None
        self.assertEqual(validation.reconcile(bad, deepcopy(bad), ['Valor'], 'Moeda')['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
