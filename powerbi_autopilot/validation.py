"""Deterministic scoped findings and non-destructive reconciliation."""
from collections import Counter
from decimal import Decimal

from .contracts import issue
from .parsing import number, missing, currency_hint
from .semantics import CURRENCIES
from .exact import add, subtract


def summarize(issues):
    counts = {level: sum(i['severity'] == level for i in issues) for level in ('BLOCKER', 'WARNING', 'INFO')}
    return {'status': 'blocked_scopes' if counts['BLOCKER'] else 'review_required' if counts['WARNING'] else 'no_findings_in_supported_checks',
            'counts': counts, 'blocked_scopes': sorted({i['scope'] for i in issues if i['severity'] == 'BLOCKER'}),
            'semantic_validation': 'not_performed', 'transformations_executed': False}


def reconcile(before, after, amount_columns=(), currency_column=None, locale=None):
    """Strict preservation check; no expected changes are accepted implicitly.

    Source row numbers are lineage IDs, not current DataFrame positions. Reordering
    is permitted only if IDs travel with the rows. Changes list contains no values.
    """
    issues, changes, totals = [], [], {}

    def fail(code, message, rows=(), column=None):
        issues.append(issue(code, 'BLOCKER', before.id, message, rows=rows, column=column, scope='reconciliation'))

    if len(before.frame) != len(after.frame):
        fail('row_loss_or_gain', 'Quantidade de registros mudou.')
    ids_valid = True
    for t in (before, after):
        if len(t.row_numbers) != len(t.frame) or len(set(t.row_numbers)) != len(t.row_numbers):
            fail('invalid_lineage', 'Identidade de linhas ausente ou duplicada.')
            ids_valid = False
    if Counter(before.row_numbers) != Counter(after.row_numbers):
        fail('row_identity_changed', 'Conjunto de linhas de origem mudou.')
    if list(before.frame.columns) != list(after.frame.columns):
        fail('schema_changed', 'Esquema mudou; exige contrato explícito.')
    if not before.source.get('sha256') or not after.source.get('sha256'):
        fail('missing_source_provenance', 'Hash da origem é obrigatório.')
    if before.id != after.id or before.source.get('sheet') != after.source.get('sheet'):
        fail('source_identity_changed', 'Identidade da tabela ou aba diverge.')
    if before.source.get('sha256') != after.source.get('sha256'):
        fail('source_changed', 'Hash da origem diverge.')
    if ids_valid:
        left = dict(zip(before.row_numbers, before.frame.to_dict('records')))
        right = dict(zip(after.row_numbers, after.frame.to_dict('records')))
        for row_id in sorted(left.keys() & right.keys()):
            for col in sorted(left[row_id].keys() & right[row_id].keys()):
                a, b = left[row_id][col], right[row_id][col]
                equal = (missing(a) and missing(b)) or (not missing(a) and not missing(b) and type(a) is type(b) and a == b)
                if not equal:
                    changes.append({'source_row': row_id, 'column': col})
        if changes:
            fail('unapproved_cell_changes', 'Células alteradas sem contrato de transformação.', [c['source_row'] for c in changes])
    for col in amount_columns:
        buckets = []
        for t in (before, after):
            sums = {}
            if col not in t.frame or (currency_column and currency_column not in t.frame):
                fail('missing_reconciliation_column', 'Coluna de reconciliação ausente.', column=col)
                buckets.append(sums)
                continue
            for i, raw in enumerate(t.frame[col]):
                parsed = number(raw, locale)
                if parsed.status != 'valid':
                    fail('unreconciled_value', 'Valor não pode ser reconciliado exatamente.', t.row_numbers[i:i+1], col)
                    continue
                currency = str(t.frame[currency_column].iloc[i]).strip().upper() if currency_column else None
                if not currency or currency.lower() not in CURRENCIES:
                    fail('unreconciled_currency', 'Moeda explícita válida é obrigatória para reconciliar totais.', t.row_numbers[i:i+1], col)
                    continue
                embedded = currency_hint(raw)
                if embedded and embedded != currency:
                    fail('unreconciled_currency_conflict', 'Moeda indicada no valor diverge da coluna.', t.row_numbers[i:i+1], col)
                    continue
                sums[currency] = add(sums.get(currency, Decimal(0)), parsed.value)
            buckets.append(sums)
        totals[col] = {}
        for currency in sorted(buckets[0].keys() | buckets[1].keys()):
            a, b = buckets[0].get(currency, Decimal(0)), buckets[1].get(currency, Decimal(0))
            totals[col][currency] = {'before': str(a), 'after': str(b), 'delta': str(subtract(b, a))}
            if a != b:
                fail('unexpected_total_change', 'Total por moeda mudou inesperadamente.', column=col)
    return {'status': 'failed' if issues else 'passed', 'rows_before': len(before.frame),
            'rows_after': len(after.frame), 'changed_cells': len(changes),
            'changes': changes[:100], 'changes_truncated': len(changes) > 100,
            'totals': totals, 'issues': issues}
