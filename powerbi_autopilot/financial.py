"""Financial diagnosis; no business metric is computed without a contract."""
from collections import defaultdict

from .contracts import issue
from .parsing import date, number, missing, currency_hint, currency_marker
from .profiling import number_hint
from .semantics import PAID, PENDING, CANCELLED, MOVEMENTS, CURRENCIES, token
from .profiler import normalize


SPECIAL = {'transferencia', 'transfer', 'estorno', 'reembolso', 'refund', 'reversal', 'cancelamento'}


def diagnose(table, profile, mapping, locale=None):
    df = table.frame
    roles = defaultdict(list)
    for col in mapping:
        for suggestion in col['suggestions']:
            roles[suggestion['role']].append(col['column'])
    amounts = list(roles['amount'])
    # Bad conversions must still be diagnosed even if semantic mapping refused a field.
    monetary = [c for c in df.columns if number_hint(c) or c in amounts or any(currency_marker(v) for v in df[c])]
    issues = []

    def add(code, severity, message, indices=(), column=None, scope=None, count=None):
        issues.append(issue(code, severity, table.id, message, column=column,
                            rows=[table.row_numbers[i] for i in indices], scope=scope, count=count))

    def one(role):
        return roles[role][0] if len(roles[role]) == 1 else None

    def named(aliases):
        cols = [c for c in df.columns if normalize(c) in aliases]
        return cols[0] if len(cols) == 1 else None

    movement = one('movement_type') or named({'tipo', 'natureza', 'movement_type'})
    status = one('payment_status') or named({'pago', 'status', 'situacao', 'payment_status'})
    currency = one('currency') or named({'moeda', 'currency'})
    pay_date = one('payment_date') or named({'data_pagamento', 'payment_date', 'data_recebimento'})
    types = [token(v) if not missing(v) else '' for v in df[movement]] if movement else ['']*len(df)
    states = [token(v) if not missing(v) else '' for v in df[status]] if status else ['']*len(df)
    special = [i for i, v in enumerate(types) if v in SPECIAL]
    cancelled = [i for i, v in enumerate(states) if v in CANCELLED]
    if movement:
        unknown = [i for i, v in enumerate(types) if v not in MOVEMENTS]
        if unknown:
            add('unknown_movement_type', 'BLOCKER', 'Tipo de movimento ausente ou fora do vocabulário conhecido.', unknown, movement, 'classified_metrics')
    if special:
        add('special_movements', 'WARNING', 'Transferências, estornos ou reembolsos exigem política própria; não equivalem a receita comum.', special, movement, 'classified_metrics')
    if cancelled:
        add('cancelled_records', 'WARNING', 'Cancelamentos exigem política explícita de exclusão ou reversão.', cancelled, status, 'classified_metrics')
    if status:
        unknown = [i for i, v in enumerate(states) if v not in PAID | PENDING | CANCELLED]
        if unknown:
            add('unknown_payment_status', 'BLOCKER', 'Status ausente ou não reconhecido; não presumir pago/pendente.', unknown, status, 'cash_metrics')
        no_payment = [i for i, v in enumerate(states) if v in PAID and (not pay_date or date(df[pay_date].iloc[i], locale).status != 'valid')]
        if no_payment:
            add('paid_without_payment_date', 'BLOCKER', 'Pagamento declarado sem data de pagamento utilizável.', no_payment, pay_date, 'cash_metrics')
    known_currencies = set()
    unknown_currency_rows, conflict_rows = [], []
    for i in range(len(df)):
        explicit = token(df[currency].iloc[i]).upper() if currency and not missing(df[currency].iloc[i]) else None
        embedded = {currency_hint(df[c].iloc[i]) for c in monetary if currency_hint(df[c].iloc[i])}
        if explicit and explicit.lower() not in CURRENCIES:
            explicit = None
        if explicit and embedded and embedded != {explicit}:
            conflict_rows.append(i)
        if explicit:
            known_currencies.add(explicit)
        elif len(embedded) == 1:
            known_currencies.update(embedded)
        elif monetary:
            unknown_currency_rows.append(i)
    if unknown_currency_rows:
        add('unknown_currency', 'BLOCKER', 'Moeda desconhecida; não assumir BRL nem combinar valores.', unknown_currency_rows, currency, 'monetary_metrics')
    if conflict_rows:
        add('currency_conflict', 'BLOCKER', 'Moeda do campo diverge da indicação textual do valor.', conflict_rows, currency, 'monetary_metrics')
    if len(known_currencies) > 1:
        add('mixed_currencies', 'BLOCKER', 'Múltiplas moedas: agrupar por moeda; conversão exige taxa e data contratadas.', scope='cross_currency_metrics', count=len(known_currencies))
    for col in amounts:
        parsed = [number(v, locale) for v in df[col]]
        conflicting = []
        for kind in set(types) - SPECIAL - {''}:
            indices = [i for i, v in enumerate(types) if v == kind and parsed[i].status == 'valid']
            signs = {parsed[i].value.compare(0) for i in indices if parsed[i].value != 0}
            # Negative receipts or mixed conventions are suspicious; unsigned expenses may be legitimate.
            if len(signs) > 1 or (kind in {'receita', 'entrada', 'income', 'revenue'} and -1 in signs):
                conflicting.extend(indices)
        if conflicting:
            add('sign_type_inconsistency', 'WARNING', 'Sinais possivelmente incompatíveis com o tipo; confirmar convenção assinada/absoluta antes de corrigir.', sorted(set(conflicting)), col, 'classified_metrics')
    for col in roles['balance']:
        add('non_additive_balance', 'INFO', 'Saldo é candidato a snapshot: não somar períodos como fluxos.', column=col, count=len(df), scope='balance_metrics')
    for col in roles['category']:
        variants = defaultdict(set)
        for v in df[col]:
            if not missing(v):
                variants[normalize(v)].add(str(v))
        suspicious = {k for k, values in variants.items() if len(values) > 1}
        refs = [i for i, v in enumerate(df[col]) if not missing(v) and normalize(v) in suspicious]
        if refs:
            add('classification_variants', 'WARNING', 'Categorias diferem apenas em espaços, acentos ou caixa; equivalência precisa de revisão.', refs, col)
    finance_evidence = bool(monetary or amounts or movement or roles['balance'])
    requirements = {
        'amount': len(amounts) == 1 and all(number(v, locale).status == 'valid' for v in df[amounts[0]]) and bool(len(df)),
        'movement_type': bool(one('movement_type')) and not any(i['code'] == 'unknown_movement_type' for i in issues),
        'currency': bool(known_currencies) and not unknown_currency_rows and not conflict_rows,
        'payment_status': bool(one('payment_status')) and not any(i['code'] == 'unknown_payment_status' for i in issues),
        'payment_date': bool(one('payment_date')) and not any(i['code'] == 'paid_without_payment_date' for i in issues),
        'competence_date': bool(one('competence_date')) and all(date(v, locale).status == 'valid' for v in df[one('competence_date')]) if one('competence_date') else False,
        'due_date': bool(one('due_date')),
        'special_movement_policy': not special and not cancelled,
        'opening_balance': False, 'overdue_policy': False, 'reference_date': False,
        'forecast_policy': False,
    }
    indicators = [{'id': 'record_count', 'meaning': 'Contagem observada de linhas, não de transações confirmadas.',
                   'status': 'available', 'missing_requirements': [], 'evidence_kind': 'observed'}]
    definitions = [
        ('cash_received', 'Receitas recebidas por data de pagamento e moeda.', ['amount', 'movement_type', 'currency', 'payment_status', 'payment_date', 'special_movement_policy']),
        ('cash_paid', 'Despesas pagas por data de pagamento e moeda.', ['amount', 'movement_type', 'currency', 'payment_status', 'payment_date', 'special_movement_policy']),
        ('incurred_expenses', 'Despesas incorridas por competência e moeda.', ['amount', 'movement_type', 'currency', 'competence_date', 'special_movement_policy']),
        ('expected_receipts', 'Receitas previstas segundo política de previsão.', ['amount', 'movement_type', 'currency', 'due_date', 'forecast_policy']),
        ('cash_balance', 'Saldo de abertura mais movimentos de caixa contratados.', ['amount', 'currency', 'payment_date', 'opening_balance', 'special_movement_policy']),
        ('overdue', 'Inadimplência segundo vencimento, referência e política.', ['amount', 'currency', 'due_date', 'payment_status', 'overdue_policy', 'reference_date']),
    ]
    for key, meaning, needed in definitions:
        absent = [r for r in needed if not requirements[r]]
        indicators.append({'id': key, 'meaning': meaning, 'status': 'insufficient_evidence' if absent else 'requires_contract',
                           'missing_requirements': absent, 'requires_contract': True,
                           'contract_fields': ['grain', 'nature_mapping', 'sign_convention', 'date_role', 'currency_policy', 'status_policy', 'special_movement_policy', 'aggregation'],
                           'evidence_kind': 'hypothesis'})
    return {'table': table.id, 'domain': {'name': 'finance' if finance_evidence else 'unknown',
                                         'status': 'hypothesis' if finance_evidence else 'insufficient_evidence',
                                         'reason': 'Evidência combinada de campos e valores; domínio não confirmado.'},
            'roles': dict(roles), 'currencies_observed': sorted(known_currencies),
            'indicators': indicators, 'issues': issues,
            'unknowns': ['granularidade de negócio', 'contrato de medidas', 'convenção de sinais']}
