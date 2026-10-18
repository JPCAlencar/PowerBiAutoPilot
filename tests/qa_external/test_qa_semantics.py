"""Independent QA probes for semantic mapping (V0.2 hypotheses only)."""
import unittest

import pandas as pd

from powerbi_autopilot.contracts import Table
from powerbi_autopilot.profiling import profile_table
from powerbi_autopilot.semantics import DEFAULT_RULES, SemanticRule, map_columns


def mapped(data, locale='pt-BR', rules=None):
    frame = pd.DataFrame(data, dtype=object)
    t = Table('qa', frame, {'file': 'qa.csv', 'sheet': None, 'sha256': 'qa'},
              list(range(2, len(frame) + 2)))
    return {r['column']: r for r in map_columns(t, profile_table(t, locale), locale, rules)}


def roles(entry):
    return [(s['role'], s['confidence']) for s in entry['suggestions']]


class MappingTests(unittest.TestCase):
    def test_plain_amount_stays_a_capped_hypothesis(self):
        entry = mapped({'Valor': ['10,00', '20,00', '30,00', '40,00', '50,00']})['Valor']
        self.assertEqual(roles(entry), [('amount', 0.6)])
        suggestion = entry['suggestions'][0]
        self.assertEqual(entry['status'], 'hypothesis')
        self.assertEqual(suggestion['confidence_kind'], 'heuristic_strength_not_probability')
        self.assertEqual(suggestion['evidence_kind'], 'inference')
        self.assertTrue(suggestion['requires_business_contract'])
        self.assertEqual(suggestion['evidence']['compatible_count'], 5)

    def test_specific_date_suppresses_the_generic_date_role(self):
        entry = mapped({'Data Pagamento': ['2026-01-05', '2026-01-06', '2026-01-07',
                                           '2026-01-08', '2026-01-09']})['Data Pagamento']
        self.assertEqual([role for role, _ in roles(entry)], ['payment_date'])
        generic = mapped({'Data': ['2026-01-05', '2026-01-06', '2026-01-07',
                                   '2026-01-08', '2026-01-09']})['Data']
        self.assertEqual([role for role, _ in roles(generic)], ['date_unknown'])

    def test_signal_ratio_threshold_is_inclusive_at_eighty_percent(self):
        mixed = mapped({'Status': ['Pago', 'Pago', 'Pago', 'Pago', 'Em análise']})['Status']
        self.assertEqual(roles(mixed), [('payment_status', 0.5)])
        self.assertEqual(mixed['suggestions'][0]['evidence']['plausible_ratio'], 0.8)
        weak = mapped({'Status': ['Pago', 'Pago', 'Pago', 'Em análise', 'A conferir']})['Status']
        self.assertEqual(weak['suggestions'], [])
        self.assertEqual(weak['status'], 'insufficient_evidence')

    def test_currency_and_movement_need_real_vocabulary(self):
        entry = mapped({'Moeda': ['BRL', 'USD', 'BRL', 'EUR', 'BRL']})['Moeda']
        self.assertEqual(roles(entry), [('currency', 0.85)])
        movement = mapped({'Tipo': ['Entrada', 'Saída', 'Entrada', 'Saída', 'Entrada']})['Tipo']
        self.assertEqual([r for r, _ in roles(movement)], ['movement_type'])
        # A non-financial 'Tipo' produces no hypothesis at all.
        neutral = mapped({'Tipo': ['Novo', 'Renovação', 'Novo', 'Novo', 'Renovação']})['Tipo']
        self.assertEqual(neutral['suggestions'], [])

    def test_currency_markers_can_promote_a_non_alias_name(self):
        entry = mapped({'Total': ['R$ 10,00', 'R$ 20,00', 'US$ 5,00', 'R$ 1,00', 'R$ 2,00']})['Total']
        self.assertEqual([r for r, _ in roles(entry)], ['amount'])
        self.assertEqual(entry['suggestions'][0]['evidence']['plausible_ratio'], 1.0)

    def test_identifier_is_never_described_as_a_measure(self):
        entry = mapped({'Cliente_ID': ['1', '2', '3', '4', '5']})['Cliente_ID']
        self.assertEqual(roles(entry), [('entity_id', 0.6)])
        short = mapped({'ID': ['1', '2']})['ID']
        self.assertEqual(roles(short), [('entity_id', 0.6)])

    def test_empty_and_text_columns_are_left_unmapped(self):
        result = mapped({'Valor': [None, None, None], 'Observação': ['a', 'b', 'c']})
        self.assertEqual(result['Valor']['status'], 'insufficient_evidence')
        self.assertEqual(result['Observação']['suggestions'], [])

    def test_custom_semantic_rule_extends_the_defaults_without_code_change(self):
        rule = SemanticRule('document', ('documento',), 'text')
        entry = mapped({'Documento': ['a', 'b', 'c', 'd', 'e']},
                       rules=DEFAULT_RULES + (rule,))['Documento']
        self.assertEqual(roles(entry), [('document', 0.85)])
        self.assertEqual(mapped({'Documento': ['a', 'b']})['Documento']['suggestions'], [])


if __name__ == '__main__':
    unittest.main()
