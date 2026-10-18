"""Deterministic JSON and bounded, escaped Markdown rendering."""
import html
import json


def json_text(item):
    return json.dumps(item, indent=2, ensure_ascii=False, allow_nan=False) + '\n'


def safe(value):
    return html.escape(str(value)).replace('|', '\\|').replace('\r', ' ').replace('\n', ' ').replace('`', '&#96;')


def markdown(report):
    val = report['validation']
    lines = ['# Diagnóstico PowerBI Autopilot V0.2', '',
             f'Estado técnico: **{val["status"]}**. Semântica de negócio: **não validada**.', '',
             'Ocorrências: ' + ', '.join(f'{level}: {count}' for level, count in val['counts'].items()) + '.', '',
             'Os arquivos originais são preservados. Clean e Analytical não foram produzidos. Nenhuma correção foi executada.', '']
    for t in report['tables']:
        p = t['profile']
        lines.extend([f'## Fonte: {safe(p["source"]["file"])} / {safe(p["source"]["sheet"] or "CSV")}', '',
                      f'Linhas: {p["rows"]}; duplicatas suspeitas: {p["duplicate_rows"]}. Granularidade: **desconhecida**.', '',
                      f'SHA-256: `{p["source"]["sha256"]}`.', '',
                      '| Coluna | Tipo sugerido | Preenchimento | Distintos | Chave candidata |',
                      '|---|---|---:|---:|---|'])
        for c in p['columns'][:50]:
            lines.append(f'| {safe(c["name"])} | {c["type"]} | {c["fill_percent"]}% | {c["distinct_count"]} | {c["candidate_key"]} |')
        if len(p['columns']) > 50:
            lines.append('Perfil limitado a 50 colunas neste Markdown; JSON contém todas.')
        lines.extend(['', '### Hipóteses semânticas', ''])
        for col in t['semantics'][:50]:
            roles = ', '.join(f'{s["role"]} (força {s["confidence"]})' for s in col['suggestions']) or 'evidência insuficiente'
            lines.append(f'- {safe(col["column"])}: {roles}.')
        lines.extend(['', 'Força heurística combina padrão de nome e valores compatíveis; não representa probabilidade.', '',
                      '### Indicadores e dependências', '',
                      '| Indicador | Estado | Informações adicionais |', '|---|---|---|'])
        for m in t['financial']['indicators']:
            dependencies = ', '.join(m['missing_requirements']) or ('contagem de linhas observada' if m['id'] == 'record_count' else 'revisar contrato de medidas')
            lines.append(f'| {m["id"]} | {m["status"]} | {safe(dependencies)} |')
        lines.extend(['', f'Plano: {len(t["transformations"])} operações propostas, nenhuma executada. Detalhes em plan.json.', ''])
    lines.extend(['## Relacionamentos candidatos', '',
                  'São hipóteses; nenhum join foi executado. Valores nulos exigem política explícita.', ''])
    for rel in report['relationships']['candidates'][:30]:
        lines.append(f'- {safe(rel["from_table"])} → {safe(rel["to_table"])}: {safe(rel["from_column"])}, {rel["cardinality"]}; cobertura {rel["coverage_percent"]}%; órfãos {rel["orphan_rows"]}; risco de multiplicação {rel["multiplication_risk"]}.')
    if len(report['relationships']['candidates']) > 30 or report['relationships']['truncated']:
        lines.append('Lista limitada; consulte relationships no JSON e o indicador truncated.')
    lines.extend(['', '## Ocorrências', '', '| Severidade | Código | Explicação | Escopo | Contagem | Linhas de origem (até 20) |', '|---|---|---|---|---:|---|'])
    for i in report['issues'][:100]:
        lines.append(f'| {i["severity"]} | {i["code"]} | {safe(i["message"])} | {safe(i["scope"])} | {i["count"]} | {safe(i["source_rows"])} |')
    if len(report['issues']) > 100:
        lines.append('Ocorrências limitadas a 100 neste Markdown; JSON contém todas.')
    lines.extend(['', '## Limitações', ''] + [f'- {safe(v)}' for v in report['limitations']])
    return '\n'.join(lines) + '\n'


def artifacts(report):
    profiles = {'schema_version': report['schema_version'], 'tables': [t['profile'] for t in report['tables']]}
    plans = {'schema_version': report['schema_version'], 'executed': False,
             'tables': [{'table': t['id'], 'transformations': t['transformations'],
                         'indicators': t['financial']['indicators']} for t in report['tables']]}
    return {'analysis.json': json_text(report), 'profile.json': json_text(profiles),
            'plan.json': json_text(plans), 'report.md': markdown(report)}
