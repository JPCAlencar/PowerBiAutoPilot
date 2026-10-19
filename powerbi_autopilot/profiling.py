"""Full-table counts and bounded evidence, without row value samples."""

from .contracts import issue
from .parsing import date, number, missing, currency_marker
from .exact import add, subtract, half
from .profiler import normalize


def date_hint(name):
    tokens = set(normalize(name).split('_'))
    return bool(tokens & {'data', 'date', 'inicio', 'fim', 'start', 'end', 'vencimento', 'competencia', 'pagamento', 'atualizacao'} or
                ('dt' in tokens and tokens & {'pgto', 'pagto'}))


def number_hint(name):
    return bool(set(normalize(name).split('_')) & {'valor', 'vlr', 'value', 'amount', 'saldo', 'balance', 'receita', 'despesa', 'orcamento', 'budget', 'total'})


def identifier_hint(name):
    return bool(set(normalize(name).split('_')) & {'id', 'codigo', 'code', 'cpf', 'cnpj'})


def _counts(parsed):
    return {s: sum(v.status == s for v in parsed) for s in ('valid', 'missing', 'invalid', 'ambiguous')}


def _aggregate_rows(table, locale):
    """Bounded-vocabulary layout hypothesis, never a decision to exclude rows."""
    labels = {'total', 'totais', 'subtotal', 'total_geral', 'soma', 'resultado'}
    refs = []
    names = list(table.frame.columns)
    identity_or_date = {i for i, name in enumerate(names) if identifier_hint(name) or date_hint(name)}
    for row_number, values in zip(table.row_numbers, table.frame.itertuples(index=False, name=None)):
        filled = [i for i, value in enumerate(values) if not missing(value)]
        if not filled:
            continue
        label = filled[0]
        if not isinstance(values[label], str) or normalize(values[label]) not in labels:
            continue
        if any(i != label and i in identity_or_date for i in filled):
            continue
        if any(i != label and number(values[i], locale).status in {'valid', 'ambiguous'} for i in filled):
            refs.append(row_number)
    return refs


def profile_table(table, locale=None):
    df, n = table.frame, len(table.frame)
    columns, issues = [], list(table.issues)
    for name in df.columns:
        values = df[name].tolist()
        empty = [missing(v) for v in values]
        nonempty = n - sum(empty)
        distinct = len({v for v, is_empty in zip(values, empty) if not is_empty})
        nums = [number(v, locale) for v in values]
        dates = [date(v, locale) for v in values]
        nc, dc = _counts(nums), _counts(dates)
        date_evidence = date_hint(name) or (nonempty > 0 and dc['valid'] == nonempty)
        numeric_evidence = number_hint(name) or any(currency_marker(v) for v in values) or (nonempty > 0 and nc['valid'] == nonempty and not identifier_hint(name))
        kind = 'date' if date_evidence and dc['valid'] else 'number' if numeric_evidence and nc['valid'] else 'text'
        if nonempty and all(isinstance(v, bool) for v, is_empty in zip(values, empty) if not is_empty):
            kind = 'boolean'
        col = {'name': name, 'storage_type': str(df[name].dtype), 'type': kind,
               'missing_count': sum(empty), 'missing_percent': round(100*sum(empty)/n, 2) if n else 0,
               'fill_percent': round(100*nonempty/n, 2) if n else 0,
               'distinct_count': distinct, 'candidate_key': bool(n and nonempty == n and distinct == n),
               'number_parse': nc, 'date_parse': dc,
               'number_distribution': None, 'date_range': None}
        if numeric_evidence and not identifier_hint(name):
            numbers = sorted(v.value for v in nums if v.status == 'valid')
            if numbers:
                middle = len(numbers)//2
                mid = numbers[middle] if len(numbers) % 2 else half(add(numbers[middle-1], numbers[middle]))
                q1, q3 = numbers[(len(numbers)-1)//4], numbers[3*(len(numbers)-1)//4]
                iqr = subtract(q3, q1)
                spread = add(iqr, half(iqr))
                lower, upper = subtract(q1, spread), add(q3, spread)
                outliers = [table.row_numbers[i] for i, v in enumerate(nums)
                            if iqr > 0 and v.status == 'valid' and (v.value < lower or v.value > upper)]
                col['number_distribution'] = {'min': str(numbers[0]), 'max': str(numbers[-1]),
                                              'median': str(mid), 'negative_count': sum(v < 0 for v in numbers),
                                              'zero_count': sum(v == 0 for v in numbers), 'iqr_outlier_count': len(outliers)}
                if outliers:
                    issues.append(issue('possible_outliers', 'WARNING', table.id, 'Valores fora de 1,5 IQR; não são necessariamente erros.', column=name, rows=outliers))
        if date_evidence and dc['valid']:
            valid = [v.value for v in dates if v.status == 'valid']
            col['date_range'] = {'min': min(valid).isoformat(), 'max': max(valid).isoformat()}
        for label, parsed, enabled in [('number', nums, numeric_evidence), ('date', dates, date_evidence)]:
            if not enabled:
                continue
            for state in ('invalid', 'ambiguous'):
                refs = [table.row_numbers[i] for i, v in enumerate(parsed) if v.status == state]
                if refs:
                    issues.append(issue(f'{state}_{label}', 'BLOCKER', table.id,
                                        'Conversão exige correção na origem ou regra regional explícita.', column=name, rows=refs))
        if any(empty):
            refs = [r for r, flag in zip(table.row_numbers, empty) if flag]
            issues.append(issue('missing_values', 'WARNING', table.id, 'Células ausentes ou em branco.', column=name, rows=refs))
        columns.append(col)
    # Treat whitespace as missing for duplicate diagnostics, never modify the frame.
    duplicate_mask = df.duplicated() if len(df.columns) else [False]*n
    duplicate_rows = [r for r, flag in zip(table.row_numbers, duplicate_mask) if flag]
    if duplicate_rows:
        issues.append(issue('suspected_duplicates', 'WARNING', table.id,
                            'Linhas iguais podem ser transações legítimas; nenhuma removida.', rows=duplicate_rows))
    blank_rows = [r for r, values in zip(table.row_numbers, df.itertuples(index=False, name=None)) if all(missing(v) for v in values)]
    if blank_rows:
        issues.append(issue('empty_rows', 'WARNING', table.id, 'Linhas totalmente vazias preservadas.', rows=blank_rows))
    if not n:
        issues.append(issue('empty_table', 'WARNING', table.id, 'Tabela sem registros.', count=0))
    aggregates = _aggregate_rows(table, locale)
    if aggregates:
        event = issue('footer_row_suspected', 'WARNING', table.id,
                      'Possíveis totais/subtotais entre registros; perfil inclui todas as linhas. Confirmar grão antes de agregar; nenhuma linha removida.',
                      rows=aggregates, scope='aggregation_review')
        event['evidence_kind'] = 'inference'
        issues.append(event)
    return {'table': table.id, 'source': table.source, 'rows': n, 'columns': columns,
            'duplicate_rows': len(duplicate_rows), 'empty_rows': len(blank_rows),
            'grain': {'status': 'unknown', 'candidate_keys': [c['name'] for c in columns if c['candidate_key']],
                      'reason': 'Unicidade observada não comprova entidade nem granularidade de negócio.'},
            'issues': issues}
