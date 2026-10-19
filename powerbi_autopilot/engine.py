"""Offline orchestration. Domain modules consume contracts, not CLI or Power BI."""
import hashlib
from pathlib import Path

from . import __version__
from .contracts import SCHEMA_VERSION, issue
from .financial import diagnose
from .intake import InputError, read_source
from .planning import plan_transformations
from .profiling import profile_table
from .relationships import candidates
from .semantics import map_columns
from .validation import summarize


def analyze(paths, options=None, locale=None):
    tables, origins = [], []
    for path in paths:
        loaded = read_source(path, options)
        tables.extend(loaded)
        origins.append({'path': Path(path), 'sha256': loaded[0].source['sha256']})
    if len({t.id for t in tables}) != len(tables):
        raise InputError('Fonte/aba repetida: não analisar duas vezes o mesmo conteúdo.')
    reports, issues = [], []
    for table in tables:
        p = profile_table(table, locale)
        mapping = map_columns(table, p, locale)
        finance = diagnose(table, p, mapping, locale)
        local = p['issues'] + finance['issues']
        roles = {s['role'] for c in mapping for s in c['suggestions']}
        if 'task' in roles and not {'start_date', 'end_date'} <= roles:
            local.append(issue('insufficient_schedule_dates', 'BLOCKER', table.id,
                               'Cronograma exige início e fim válidos; atualização/conclusão não comprova início.',
                               scope='project_schedule', count=len(table.frame)))
        reports.append({'id': table.id, 'profile': p, 'semantics': mapping,
                        'financial': finance, 'transformations': plan_transformations(table, p, mapping),
                        'validation': summarize(local)})
        issues.extend(local)
    rels = candidates(tables)
    for rel in rels['candidates']:
        scope = f'join:{rel["from_table"]}.{rel["from_column"]}->{rel["to_table"]}.{rel["to_column"]}'
        if rel['multiplication_risk']:
            issues.append(issue('join_multiplication_risk', 'BLOCKER', rel['from_table'],
                                'Join candidato pode multiplicar registros e valores.', column=rel['from_column'],
                                count=rel['matched_join_rows'], scope=scope))
        if rel['orphan_rows']:
            issues.append(issue('candidate_orphans', 'WARNING', rel['from_table'],
                                'Chaves sem correspondência no relacionamento candidato; validar se as tabelas se relacionam.',
                                column=rel['from_column'], count=rel['orphan_rows'], scope=scope))
    if rels['truncated']:
        issues.append(issue('relationship_search_truncated', 'INFO', 'all',
                            'Limite de candidatos atingido; nem todos foram detalhados.', count=rels['examined_pairs']))
    integrity = []
    for origin in origins:
        same = hashlib.sha256(origin['path'].read_bytes()).hexdigest() == origin['sha256']
        integrity.append({'file': origin['path'].name, 'sha256': origin['sha256'], 'unchanged': same})
        if not same:
            issues.append(issue('source_changed_during_analysis', 'BLOCKER', 'all', 'Fonte mudou durante a leitura; refaça o diagnóstico.', count=1, scope='source_integrity'))
    return {'schema_version': SCHEMA_VERSION, 'engine_version': __version__, 'locale': locale,
            'stages': {'Raw': 'preserved', 'Clean': 'planned_only', 'Analytical': 'not_implemented'},
            'tables': reports, 'relationships': rels, 'issues': issues,
            'validation': summarize(issues), 'source_integrity': integrity,
            'limitations': ['Sem confirmação automática de semântica ou granularidade.',
                            'Sem execução de transformações; reconciliação entre estágios não executada.',
                            'Sem indicadores financeiros calculados, DAX, PBIP ou inspeção visual.',
                            'Análise integral em memória; sem amostragem ou streaming.',
                            'Totais/subtotais detectados somente por heurística; todas as linhas entram no perfil.',
                            'Relações somente entre tabelas e nomes de identificadores iguais; sem chaves compostas.',
                            'Confiança heurística não é probabilidade calibrada.']}
