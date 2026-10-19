"""Replaceable rules; suggestions are evidence-based hypotheses, never contracts."""
from dataclasses import dataclass

from .parsing import missing, currency_marker
from .profiler import normalize


MOVEMENTS = {'receita', 'despesa', 'entrada', 'saida', 'credito', 'debito',
             'revenue', 'expense', 'income', 'credit', 'debit', 'transferencia',
             'transfer', 'estorno', 'reembolso', 'refund', 'reversal', 'cancelamento'}
PAID = {'pago', 'paid', 'recebido', 'liquidado', 'quitado'}
PENDING = {'pendente', 'pending', 'aberto', 'em_aberto', 'vencido'}
PAID_FLAGS = {'sim', 'true', '1', 's', 'yes', '✓'}
PENDING_FLAGS = {'nao', 'false', '0', 'n', 'no'}
PAYMENT_FLAG_NAMES = ('pago', 'paid', 'quitado', 'liquidado')
CANCELLED = {'cancelado', 'cancelled', 'canceled', 'estornado'}
CURRENCIES = {'brl', 'usd', 'eur', 'gbp', 'ars', 'jpy', 'cad', 'chf', 'aud'}


def token(value):
    return normalize(value) if str(value).strip() != '✓' else '✓'


def header_matches(name, aliases):
    """Match whole names/suffixes with connectors removed, never substrings."""
    def compact(value):
        return '_'.join(p for p in normalize(value).split('_')
                        if p not in {'de', 'da', 'do', 'das', 'dos', 'e'})

    normalized = compact(name)
    return any(normalized == alias or (len(alias) >= 4 and normalized.endswith('_' + alias))
               for alias in map(compact, aliases))


def payment_vocabulary(name):
    """Binary tokens need a payment-specific header; generic Status is unknown."""
    if payment_flag_header(name):
        return PAID | PAID_FLAGS, PENDING | PENDING_FLAGS
    return PAID, PENDING


def payment_flag_header(name):
    # Suffixes such as "Nao Pago" or "Valor Pago" do not establish flag polarity.
    return normalize(name) in PAYMENT_FLAG_NAMES


@dataclass(frozen=True)
class SemanticRule:
    role: str
    aliases: tuple[str, ...]
    kind: str


DEFAULT_RULES = (
    SemanticRule('amount', ('valor', 'valor_total', 'vlr_pgto', 'vlr_pagto', 'amount', 'value', 'receita', 'despesa'), 'number'),
    SemanticRule('balance', ('saldo', 'balance'), 'number'),
    SemanticRule('budget', ('orcamento', 'budget', 'meta'), 'number'),
    SemanticRule('payment_date', ('data_pagamento', 'payment_date', 'data_recebimento', 'dt_pagto', 'dt_pgto'), 'date'),
    SemanticRule('due_date', ('vencimento', 'due_date'), 'date'),
    SemanticRule('posting_date', ('data_lancamento', 'posting_date', 'data_emissao'), 'date'),
    SemanticRule('competence_date', ('competencia', 'accrual_date'), 'date'),
    SemanticRule('start_date', ('data_inicio', 'inicio', 'start_date'), 'date'),
    SemanticRule('end_date', ('data_fim', 'fim', 'end_date', 'conclusao'), 'date'),
    SemanticRule('update_date', ('atualizacao', 'updated_at'), 'date'),
    SemanticRule('date_unknown', ('data', 'date'), 'date'),
    SemanticRule('movement_type', ('tipo', 'natureza', 'movimento', 'movement_type'), 'movement'),
    SemanticRule('payment_status', PAYMENT_FLAG_NAMES + ('status', 'situacao', 'payment_status'), 'status'),
    SemanticRule('currency', ('moeda', 'currency'), 'currency'),
    SemanticRule('category', ('categoria', 'classificacao', 'subgrupo', 'centro_custo'), 'category'),
    SemanticRule('entity_id', ('id', 'codigo', 'cliente_id', 'fornecedor_id', 'projeto_id'), 'identifier'),
    SemanticRule('task', ('atividade', 'tarefa', 'task'), 'text'),
)


def map_columns(table, profile, locale=None, rules=None):
    result = []
    for col in profile['columns']:
        name = col['name']
        values = [v for v in table.frame[name] if not missing(v)]
        tokens = [token(v) for v in values]
        count = len(values)
        suggestions = []
        for rule in (DEFAULT_RULES if rules is None else rules):
            name_match = header_matches(name, rule.aliases)
            currency_markers = sum(currency_marker(v) for v in values)
            if rule.role == 'amount' and currency_markers and count and currency_markers/count >= .8:
                name_match = True
            if not name_match or not count:
                continue
            if rule.kind in ('number', 'date'):
                stats = col[f'{rule.kind}_parse']
                valid = stats['valid']
                # Ambiguity remains evidence of a date/amount shape, but lowers confidence.
                plausible = valid + stats['ambiguous']
                ratio = plausible/count
            elif rule.kind == 'movement':
                valid = sum(v in MOVEMENTS for v in tokens)
                ratio = valid/count
            elif rule.kind == 'status':
                paid, pending = payment_vocabulary(name)
                valid = sum(v in paid | pending | CANCELLED for v in tokens)
                ratio = valid/count
            elif rule.kind == 'currency':
                valid = sum(v in CURRENCIES for v in tokens)
                ratio = valid/count
            elif rule.kind == 'category':
                valid = sum(not isinstance(v, (int, float)) for v in values)
                ratio = valid/count
            else:
                valid, ratio = count, 1
            if ratio < .8:
                continue
            confidence = .85 if valid == count and count >= 5 else .7 if valid == count else .5
            if rule.role in ('amount', 'date_unknown', 'category', 'entity_id'):
                confidence = min(confidence, .6)
            suggestions.append({'role': rule.role, 'confidence': confidence,
                                'confidence_kind': 'heuristic_strength_not_probability',
                                'evidence': {'name_or_currency_pattern': True, 'non_null_count': count,
                                             'compatible_count': valid, 'plausible_ratio': round(ratio, 3)},
                                'evidence_kind': 'inference', 'requires_business_contract': True})
        if any(s['role'].endswith('_date') for s in suggestions):
            suggestions = [s for s in suggestions if s['role'] != 'date_unknown']
        result.append({'column': name, 'status': 'hypothesis' if suggestions else 'insufficient_evidence',
                       'suggestions': sorted(suggestions, key=lambda s: (-s['confidence'], s['role']))})
    return result
