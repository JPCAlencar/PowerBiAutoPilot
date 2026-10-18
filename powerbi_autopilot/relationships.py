"""Candidate relationships only; never materializes a join."""
from collections import Counter

from .parsing import missing
from .profiler import normalize
from .profiling import identifier_hint


def candidates(tables, max_candidates=100):
    found, examined = [], 0
    for left in tables:
        for right in tables:
            if left is right:
                continue
            for lc in left.frame.columns:
                for rc in right.frame.columns:
                    ln, rn = normalize(lc), normalize(rc)
                    # Restrict to identifier-like equal names. Unrelated IDs remain hypotheses.
                    if ln != rn or not identifier_hint(lc):
                        continue
                    examined += 1
                    if len(found) >= max_candidates:
                        continue
                    ls = Counter(v for v in left.frame[lc] if not missing(v))
                    rs = Counter(v for v in right.frame[rc] if not missing(v))
                    if not ls or not rs:
                        continue
                    matched = sum(count for v, count in ls.items() if v in rs)
                    orphans = sum(count for v, count in ls.items() if v not in rs)
                    join_rows = sum(count*rs[v] for v, count in ls.items())
                    l_unique, r_unique = max(ls.values()) == 1, max(rs.values()) == 1
                    cardinality = ('one' if l_unique else 'many') + '_to_' + ('one' if r_unique else 'many')
                    left_nulls = len(left.frame)-sum(ls.values())
                    right_nulls = len(right.frame)-sum(rs.values())
                    found.append({'from_table': left.id, 'from_column': lc, 'to_table': right.id,
                                  'to_column': rc, 'cardinality': cardinality,
                                  'coverage_percent': round(100*matched/sum(ls.values()), 2),
                                  'orphan_rows': orphans, 'null_source_rows': left_nulls,
                                  'null_target_rows': right_nulls, 'matched_join_rows': join_rows,
                                  'multiplication_risk': join_rows > matched or (left_nulls > 0 and right_nulls > 1),
                                  'null_join_policy': 'undefined_requires_contract',
                                  'validated': False, 'status': 'candidate_requires_review',
                                  'evidence_kind': 'inference',
                                  'reason': 'Nome de chave e sobreposição observada; significado e granularidade não confirmados.'})
    return {'candidates': found, 'examined_pairs': examined, 'truncated': examined > max_candidates,
            'limit': max_candidates}
