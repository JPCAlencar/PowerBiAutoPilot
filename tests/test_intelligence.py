import unittest
import pandas as pd

from powerbi_autopilot.contracts import Table
from powerbi_autopilot import profiling, relationships, semantics


def table(data, name='movements'):
    df = pd.DataFrame(data, dtype=object)
    return Table(name, df, {'file': 'synthetic.csv', 'sheet': name, 'sha256': 'synthetic'}, list(range(2, len(df)+2)))


class IntelligenceTests(unittest.TestCase):
    def test_native_booleans_are_profiled_as_boolean_not_numeric(self):
        t = table({'Pago': [True, False, None]})
        p = profiling.profile_table(t)
        self.assertEqual(p['columns'][0]['type'], 'boolean')
        self.assertEqual(p['columns'][0]['missing_count'], 1)

    def test_currency_codes_do_not_match_ordinary_word_prefixes(self):
        from powerbi_autopilot.financial import diagnose
        t = table({'Region': ['Europe', 'Eurostar', 'USDollar'], 'City': ['Paris', 'Rome', 'Other']})
        p = profiling.profile_table(t)
        self.assertFalse(any(i['code'] == 'invalid_number' for i in p['issues']))
        r = diagnose(t, p, semantics.map_columns(t, p))
        self.assertEqual(r['domain']['name'], 'unknown')
        self.assertEqual(r['currencies_observed'], [])

    def test_currency_patterns_enable_conversion_diagnostics_under_generic_names(self):
        t = table({'x': ['R$ 1,234', 'R$ banana', 'R$ 20,00']})
        p = profiling.profile_table(t)
        self.assertTrue({'ambiguous_number', 'invalid_number'} <= {i['code'] for i in p['issues']})

    def test_decimal_median_does_not_round_cents(self):
        t = table({'Valor': ['10000000000000000000000000000.01', '10000000000000000000000000000.03']})
        p = profiling.profile_table(t)
        self.assertEqual(p['columns'][0]['number_distribution']['median'], '10000000000000000000000000000.02')

    def test_profile_counts_keys_blank_and_duplicate_rows_no_values(self):
        t = table({'ID': ['001', '002', '003', None], 'Nome': ['PRIVADO', 'PRIVADO', 'PRIVADO', ' '],
                   'Valor': ['10,00', '20,00', 'erro', None]})
        p = profiling.profile_table(t)
        self.assertEqual(p['rows'], 4)
        cols = {c['name']: c for c in p['columns']}
        self.assertEqual(cols['Nome']['missing_count'], 1)
        self.assertEqual(cols['Nome']['fill_percent'], 75)
        self.assertFalse(cols['ID']['candidate_key'])
        self.assertEqual(cols['Valor']['number_parse']['invalid'], 1)
        self.assertEqual(cols['Valor']['number_distribution']['median'], '15.00')
        self.assertNotIn('PRIVADO', str(p))
        self.assertEqual(p['grain']['status'], 'unknown')

    def test_duplicate_transactions_are_only_suspicious_not_removed(self):
        t = table({'Tipo': ['Receita', 'Receita'], 'Valor': ['10,00', '10,00']})
        p = profiling.profile_table(t)
        self.assertEqual(p['duplicate_rows'], 1)
        self.assertEqual(len(t.frame), 2)
        self.assertEqual(next(i for i in p['issues'] if i['code'] == 'suspected_duplicates')['severity'], 'WARNING')

    def test_semantic_mapping_uses_values_and_refuses_bad_named_fields(self):
        t = table({'Valor': ['banana', 'texto'], 'Data Pagamento': ['ontem', 'depois'],
                   'Tipo': ['Entrada', 'Saída'], 'Pago': ['Sim', '?'], 'x': ['R$ 10,00', 'R$ 20,00']})
        m = semantics.map_columns(t, profiling.profile_table(t))
        by = {c['column']: c for c in m}
        self.assertFalse(by['Valor']['suggestions'])
        self.assertFalse(by['Data Pagamento']['suggestions'])
        self.assertEqual(by['Tipo']['suggestions'][0]['role'], 'movement_type')
        self.assertEqual(by['x']['suggestions'][0]['role'], 'amount')
        self.assertEqual(by['Pago']['status'], 'insufficient_evidence')
        self.assertTrue(all(c['status'] != 'validated' for c in m))

    def test_generic_date_amount_and_balance_have_no_confirmed_business_meaning(self):
        t = table({'Valor': ['10', '20'], 'Data': ['2026-01-01', '2026-01-02'], 'Saldo': ['100', '120']})
        m = semantics.map_columns(t, profiling.profile_table(t))
        roles = {c['column']: [s['role'] for s in c['suggestions']] for c in m}
        self.assertEqual(roles['Data'], ['date_unknown'])
        self.assertEqual(roles['Saldo'], ['balance'])
        self.assertEqual(roles['Valor'], ['amount'])
        self.assertTrue(all(s['confidence'] < 1 for c in m for s in c['suggestions']))

    def test_new_domain_rule_requires_no_core_changes(self):
        t = table({'Volume': ['10', '20']})
        rule = semantics.SemanticRule('volume', ('volume',), 'number')
        mapped = semantics.map_columns(t, profiling.profile_table(t), rules=[rule])
        self.assertEqual(mapped[0]['suggestions'][0]['role'], 'volume')

    def test_relationship_cardinality_orphans_and_join_multiplication(self):
        fact = table({'Cliente_ID': ['A', 'A', 'B', 'C', None]}, 'movements')
        dim = table({'Cliente_ID': ['A', 'A', 'B']}, 'clients')
        result = relationships.candidates([fact, dim])
        rel = next(r for r in result['candidates'] if r['from_table'] == 'movements')
        self.assertEqual(rel['cardinality'], 'many_to_many')
        self.assertEqual(rel['orphan_rows'], 1)
        self.assertEqual(rel['null_source_rows'], 1)
        self.assertEqual(rel['matched_join_rows'], 5)
        self.assertTrue(rel['multiplication_risk'])
        self.assertEqual(rel['status'], 'candidate_requires_review')

    def test_valid_relationship_still_requires_business_review(self):
        a = table({'Cliente_ID': ['A', 'B', 'A']}, 'transactions')
        b = table({'Cliente_ID': ['A', 'B']}, 'clients')
        rel = relationships.candidates([a, b])['candidates'][0]
        self.assertEqual(rel['cardinality'], 'many_to_one')
        self.assertEqual(rel['coverage_percent'], 100)
        self.assertFalse(rel['multiplication_risk'])
        self.assertFalse(rel['validated'])

    def test_ambiguous_dates_are_reported_not_parsed_as_fact(self):
        t = table({'Data': ['01/02/2026', '02/03/2026', '31/02/2026']})
        p = profiling.profile_table(t)
        self.assertEqual(p['columns'][0]['date_parse']['ambiguous'], 2)
        codes = {i['code'] for i in p['issues']}
        self.assertTrue({'ambiguous_date', 'invalid_date'} <= codes)


if __name__ == '__main__':
    unittest.main()
