"""Declarative plans only. No operation here mutates a table."""


def plan_transformations(table, profile, mapping):
    steps = []

    def add(operation, column, reason, risks, preconditions):
        steps.append({'id': f'{table.id}:step_{len(steps)+1}',
                      'source': {'stage': 'Raw', 'table': table.id, 'column': column},
                      'destination': {'stage': 'Clean', 'table': table.id, 'column': column},
                      'operation': operation, 'reason': reason, 'risks': risks,
                      'preconditions': preconditions, 'status': 'proposed_requires_review', 'executed': False})
    for col in profile['columns']:
        name = col['name']
        if col['number_parse']['ambiguous'] or col['date_parse']['ambiguous']:
            add('resolve_locale', name, 'Representações admitem mais de uma interpretação.',
                ['Alterar magnitude ou período.'], ['Confirmar locale na origem.', 'Reexecutar parsers e reconciliar.'])
        if col['type'] in ('number', 'date') and col['storage_type'] == 'object':
            add(f'parse_{col["type"]}', name, 'Padronizar tipo preservando valor e origem.',
                ['Falhas de conversão e perda de precisão.'], ['Zero conversões inválidas/ambíguas.', 'Preservar originais.', 'Comparar linhas e valores após conversão.'])
        if col['missing_count']:
            add('review_missing', name, 'Valores ausentes devem ter tratamento explicitado.',
                ['Imputação pode inventar dados.'], ['Confirmar significado de ausência; não preencher automaticamente.'])
    if profile['duplicate_rows']:
        add('review_duplicates', None, 'Transações iguais podem ser legítimas.',
            ['Remoção pode reduzir totais indevidamente.'], ['Definir granularidade e chave de negócio.', 'Nenhuma exclusão automática.'])
    if any(i['code'] == 'footer_row_suspected' for i in profile['issues']):
        add('review_aggregate_rows', None, 'Possíveis totais/subtotais misturados a registros detalhados.',
            ['Dupla contagem; exclusão pode apagar registros legítimos.'],
            ['Confirmar granularidade e política para linhas agregadas.',
             'Preservar todas as linhas e identidades até revisão.',
             'Reconciliar células e totais por moeda antes de qualquer transformação futura.'])
    for col in mapping:
        if col['suggestions']:
            add('confirm_semantics', col['column'], 'Hipótese semântica precisa de contrato.',
                ['Nome e distribuição não comprovam significado.'], ['Revisar evidências com responsável pela fonte.'])
    return steps
