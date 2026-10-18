"""Independent QA probes for scoped findings and reconciliation (V0.2)."""
import unittest

import pandas as pd

from powerbi_autopilot.contracts import Table, issue
from powerbi_autopilot.validation import reconcile, summarize


def make(data, name='t', sha='sha-a', rows=None, sheet=None):
    frame = pd.DataFrame(data, dtype=object)
    source = {'file': 'qa.csv', 'sheet': sheet, 'sha256': sha}
    return Table(name, frame, source, list(range(2, len(frame) + 2)) if rows is None else rows)


def codes(result):
    return [i['code'] for i in result['issues']]


class SummaryTests(unittest.TestCase):
    def test_status_precedence_and_blocked_scopes(self):
        blocked = summarize([issue('a', 'BLOCKER', 't1', 'm', scope='s2'),
                             issue('b', 'BLOCKER', 't2', 'm', scope='s1'),
                             issue('c', 'WARNING', 't1', 'm', scope='s9')])
        self.assertEqual(blocked['status'], 'blocked_scopes')
        self.assertEqual(blocked['blocked_scopes'], ['s1', 's2'])
        self.assertEqual(blocked['counts'], {'BLOCKER': 2, 'WARNING': 1, 'INFO': 0})
        self.assertEqual(blocked['semantic_validation'], 'not_performed')
        self.assertFalse(blocked['transformations_executed'])
        self.assertEqual(summarize([issue('a', 'WARNING', 't1', 'm', scope='s')])['status'],
                         'review_required')
        self.assertEqual(summarize([])['status'], 'no_findings_in_supported_checks')
        self.assertEqual(summarize([])['blocked_scopes'], [])


class ReconcileTests(unittest.TestCase):
    def base(self):
        return make({'ID': ['1', '2'], 'Valor': ['1.000,00', '500,00'],
                     'Moeda': ['BRL', 'BRL'], 'Obs': ['a', 'b']})

    def test_identical_tables_pass_and_totals_are_decimal_strings(self):
        before = self.base()
        result = reconcile(before, self.base(), amount_columns=('Valor',),
                           currency_column='Moeda', locale='pt-BR')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['changed_cells'], 0)
        self.assertEqual(result['totals'], {'Valor': {'BRL': {'before': '1500.00',
                                                              'after': '1500.00',
                                                              'delta': '0.00'}}})
        self.assertEqual((result['rows_before'], result['rows_after']), (2, 2))

    def test_text_change_is_a_blocker_that_lists_no_values(self):
        after = self.base()
        after.frame.loc[1, 'Obs'] = 'alterado'
        result = reconcile(self.base(), after, amount_columns=('Valor',),
                           currency_column='Moeda', locale='pt-BR')
        self.assertEqual(codes(result), ['unapproved_cell_changes'])
        self.assertEqual(result['changed_cells'], 1)
        self.assertEqual(result['changes'], [{'source_row': 3, 'column': 'Obs'}])
        self.assertNotIn('alterado', repr(result))
        self.assertEqual(result['totals']['Valor']['BRL']['delta'], '0.00')

    def test_amount_change_is_reported_as_unexpected_total_change(self):
        after = self.base()
        after.frame.loc[1, 'Valor'] = '600,00'
        result = reconcile(self.base(), after, amount_columns=('Valor',),
                           currency_column='Moeda', locale='pt-BR')
        self.assertEqual(set(codes(result)), {'unapproved_cell_changes', 'unexpected_total_change'})
        self.assertEqual(result['totals']['Valor']['BRL'],
                         {'before': '1500.00', 'after': '1600.00', 'delta': '100.00'})

    def test_row_loss_and_lineage_are_detected(self):
        after = make({'ID': ['1'], 'Valor': ['1.000,00'], 'Moeda': ['BRL'], 'Obs': ['a']})
        result = reconcile(self.base(), after)
        self.assertEqual(set(codes(result)), {'row_loss_or_gain', 'row_identity_changed'})
        self.assertEqual(result['status'], 'failed')

    def test_schema_rename_requires_an_explicit_contract(self):
        after = self.base().frame.rename(columns={'Obs': 'Observacao'})
        result = reconcile(self.base(), make(after))
        self.assertEqual(codes(result), ['schema_changed'])

    def test_provenance_and_origin_hash_are_enforced(self):
        both_missing = reconcile(make({'ID': ['1']}, sha=None), make({'ID': ['1']}, sha=None))
        self.assertEqual(codes(both_missing), ['missing_source_provenance'])
        # A hash present on one side only adds a second, redundant finding.
        partial = reconcile(self.base(), make(self.base().frame.to_dict('list'), sha=None))
        self.assertEqual(codes(partial), ['missing_source_provenance', 'source_changed'])
        changed = reconcile(self.base(), make(self.base().frame.to_dict('list'), sha='sha-b'))
        self.assertEqual(codes(changed), ['source_changed'])
        other_id = reconcile(self.base(), make(self.base().frame.to_dict('list'), name='other'))
        self.assertEqual(codes(other_id), ['source_identity_changed'])

    def test_unparseable_values_and_ambiguous_currency_block_the_total(self):
        before = make({'Valor': ['abc', '10,00', 'US$ 10,00'], 'Moeda': ['BRL', 'XAU', 'BRL']})
        after = make({'Valor': ['abc', '10,00', 'US$ 10,00'], 'Moeda': ['BRL', 'XAU', 'BRL']})
        result = reconcile(before, after, amount_columns=('Valor',),
                           currency_column='Moeda', locale='pt-BR')
        self.assertEqual(set(codes(result)),
                         {'unreconciled_value', 'unreconciled_currency', 'unreconciled_currency_conflict'})
        for event in result['issues']:
            self.assertEqual(event['severity'], 'BLOCKER')
            self.assertEqual(len(event['source_rows']), 1)
        self.assertEqual(result['totals'], {'Valor': {}})

    def test_missing_reconciliation_column_is_reported_per_side(self):
        before = make({'ID': ['1']})
        result = reconcile(before, make({'ID': ['1']}), amount_columns=('Valor',))
        self.assertEqual(codes(result), ['missing_reconciliation_column'] * 2)
        self.assertEqual(result['totals'], {'Valor': {}})

    def test_changed_cell_evidence_is_capped_but_counted_in_full(self):
        data = {'ID': [str(i) for i in range(120)], 'Obs': ['x'] * 120}
        after_data = {'ID': [str(i) for i in range(120)], 'Obs': ['y'] * 120}
        result = reconcile(make(data), make(after_data))
        self.assertEqual(result['changed_cells'], 120)
        self.assertEqual(len(result['changes']), 100)
        self.assertTrue(result['changes_truncated'])
        event = result['issues'][0]
        self.assertEqual(event['count'], 120)
        self.assertEqual(len(event['source_rows']), 20)
        self.assertTrue(event['rows_truncated'])

    def test_no_amount_columns_means_no_totals(self):
        result = reconcile(self.base(), self.base())
        self.assertEqual(result['totals'], {})
        self.assertEqual(result['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
