"""Independent QA probes for candidate relationships (V0.2).

All tables are synthetic and in-memory; nothing is joined or materialized.
"""
import unittest

import pandas as pd

from powerbi_autopilot.contracts import Table
from powerbi_autopilot.relationships import candidates


def table(data, name):
    frame = pd.DataFrame(data, dtype=object)
    source = {'file': 'qa.csv', 'sheet': None, 'sha256': 'qa-' + name}
    return Table(name, frame, source, list(range(2, len(frame) + 2)))


def only(result, from_table, to_table):
    return [c for c in result['candidates']
            if c['from_table'] == from_table and c['to_table'] == to_table]


class CandidateTests(unittest.TestCase):
    def test_many_to_many_multiplication_is_flagged(self):
        result = candidates([table({'Cliente_ID': ['1', '1', '2']}, 'fato'),
                             table({'Cliente_ID': ['1', '1', '2']}, 'dim')])
        rel = only(result, 'fato', 'dim')[0]
        self.assertEqual(rel['cardinality'], 'many_to_many')
        self.assertEqual(rel['matched_join_rows'], 5)
        self.assertEqual(rel['coverage_percent'], 100.0)
        self.assertTrue(rel['multiplication_risk'])
        self.assertEqual(rel['null_join_policy'], 'undefined_requires_contract')
        self.assertFalse(rel['validated'])
        self.assertEqual(rel['evidence_kind'], 'inference')

    def test_candidates_require_identifier_like_equal_names(self):
        result = candidates([table({'Cliente_ID': ['1']}, 'a'),
                             table({'Cliente_ID': ['1'], 'Cliente': ['1']}, 'b')])
        pairs = {(c['from_column'], c['to_column']) for c in result['candidates']}
        # 'Cliente' has no identifier token and a different normalized name.
        self.assertEqual(pairs, {('Cliente_ID', 'Cliente_ID')})
        self.assertEqual(result['candidates'][0]['orphan_rows'], 0)
        self.assertEqual(result['examined_pairs'], 2)

    def test_value_type_mismatch_produces_orphans_without_crashing(self):
        # '001' (text) never equals 1 (number): the key silently looks unrelated.
        result = candidates([table({'Cliente_ID': ['001', '002']}, 'a'),
                             table({'Cliente_ID': [1, 2]}, 'b')])
        rel = only(result, 'a', 'b')[0]
        self.assertEqual(rel['orphan_rows'], 2)
        self.assertEqual(rel['coverage_percent'], 0.0)
        self.assertFalse(rel['multiplication_risk'])

    def test_oriented_pairs_are_reported_independently(self):
        result = candidates([table({'Cliente_ID': ['1', '2', '3']}, 'a'),
                             table({'Cliente_ID': ['1']}, 'b')])
        forward = only(result, 'a', 'b')[0]
        backward = only(result, 'b', 'a')[0]
        # Cardinality describes per-key uniqueness, not row counts.
        self.assertEqual(forward['cardinality'], 'one_to_one')
        self.assertEqual(forward['coverage_percent'], 33.33)
        self.assertEqual(backward['coverage_percent'], 100.0)
        self.assertEqual(forward['matched_join_rows'], 1)

    def test_intra_table_column_pairs_are_never_candidates(self):
        # Documented behaviour (see QA-F15): a self-referencing pair inside one
        # table (Cliente_ID / Vendedor_ID) is out of scope for this module.
        result = candidates([table({'Cliente_ID': ['1'], 'Vendedor_ID': ['1']}, 'vendas')])
        self.assertEqual(result['candidates'], [])
        self.assertEqual(result['examined_pairs'], 0)

    def test_candidate_limit_is_enforced_and_reported(self):
        tables = [table({'ID': [str(i)]}, f't{i}') for i in range(11)]
        result = candidates(tables)
        self.assertEqual(result['limit'], 100)
        self.assertEqual(len(result['candidates']), 100)
        self.assertEqual(result['examined_pairs'], 110)
        self.assertTrue(result['truncated'])


class NullPolicyTests(unittest.TestCase):
    def test_nulls_on_one_side_only_are_counted(self):
        result = candidates([table({'Cliente_ID': ['1', None]}, 'a'),
                             table({'Cliente_ID': ['1']}, 'b')])
        rel = only(result, 'a', 'b')[0]
        self.assertEqual(rel['null_source_rows'], 1)
        self.assertEqual(rel['null_target_rows'], 0)

    @unittest.expectedFailure
    def test_qa_f04_null_multiplication_risk_is_symmetric(self):
        """QA-F04 (CONFIRMED BUG, MEDIUM): ``multiplication_risk`` adds
        ``left_nulls > 0 and right_nulls > 1``. The same key pair is flagged in one
        direction and not in the other, although nulls are excluded from both
        counters and ``matched_join_rows`` equals ``matched`` in both cases (no
        multiplication is actually observed). The engine promotes this flag to a
        BLOCKER, so identical situations receive different severities.
        Expected: neither direction flagged when no multiplication is observed.
        """
        one = table({'Cliente_ID': ['1', None]}, 'one')
        two = table({'Cliente_ID': ['1', None, None]}, 'two')
        first = only(candidates([one, two]), 'one', 'two')[0]
        second = only(candidates([one, two]), 'two', 'one')[0]
        self.assertEqual(first['matched_join_rows'], 1)
        self.assertFalse(first['multiplication_risk'])
        self.assertFalse(second['multiplication_risk'])


if __name__ == '__main__':
    unittest.main()
