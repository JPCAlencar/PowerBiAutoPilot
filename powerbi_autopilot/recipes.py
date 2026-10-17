from __future__ import annotations

from pathlib import Path
import yaml

from .profiler import normalize

RECIPE_DIR = Path(__file__).resolve().parent.parent / 'recipes'


def load_recipes() -> list[dict]:
    recipes = []
    for path in sorted(RECIPE_DIR.glob('*.yaml')):
        with path.open(encoding='utf-8') as handle:
            recipe = yaml.safe_load(handle)
        if recipe:
            recipes.append(recipe)
    return recipes


def detect_domains(columns: list[str]) -> list[dict]:
    names = {normalize(s) for s in columns}
    detected = []
    for r in load_recipes():
        signals = [normalize(x) for x in r['signals']]
        matched = [s for s in signals if any(s == n or s in n.split('_') or (len(s) >= 6 and s in n) for n in names)]
        confidence = round(len(matched) / len(signals), 3) if signals else 0
        if matched:
            detected.append({'domain': r['domain'], 'score': confidence, 'signals': matched})
    return sorted(detected, key=lambda item: (-item['score'], item['domain']))


def make_plan(profile_data: dict) -> dict:
    cols = profile_data['columns']
    names = {normalize(c['name']): c for c in cols}
    classified = detect_domains([c['name'] for c in cols])
    domain = classified[0]['domain'] if classified else 'exploratory'
    proposed = [{'visual': 'table', 'reason': 'Reconhecer granularidade e verificar resultados', 'status': 'proposed'}]
    cautions = list(profile_data['warnings'])
    if domain == 'projects':
        start = next((c for n,c in names.items() if any(k in n for k in ['data_inicio','inicio','start_date','start'] ) and c['type']=='date'), None)
        end = next((c for n,c in names.items() if any(k in n for k in ['data_fim','fim','end_date','end','conclusao']) and c['type']=='date'), None)
        task = next((c for n,c in names.items() if any(k in n for k in ['atividade','tarefa','task'])), None)
        if start and end and task:
            proposed.append({'visual':'gantt','status':'ready_for_date_validation','fields':{'task':task['name'],'start':start['name'],'end':end['name']},'reason':'Atividades com intervalo temporal detectado; validar cronologia e disponibilidade do visual Gantt'})
        else:
            missing = [label for label,value in [('atividade',task),('inicio',start),('fim',end)] if value is None]
            proposed.append({'visual':'gantt','status':'blocked','missing': missing, 'reason':'Não inferir duração sem datas adequadas'})
            cautions.append('Gantt depende de atividade, início e fim válidos.')
        proposed.append({'visual':'status_distribution','status':'proposed','reason':'Distribuição de atividades por estado, caso exista status'})
    elif domain == 'finance':
        proposed.extend([{'visual':'monthly_trend','status':'proposed','reason':'Evolução temporal por tipo de lançamento, condicionada a data válida'}, {'visual':'category_breakdown','status':'proposed','reason':'Categorias apenas se existirem dimensões e regra de sinal'}])
    elif domain == 'logistics':
        proposed.append({'visual':'sla_and_lead_time','status':'proposed','reason':'Exigir datas de início/fim e regra formal de SLA'})
    elif domain == 'revenue':
        proposed.append({'visual':'revenue_trend','status':'proposed','reason':'Validar granularidade monetária, moeda e ocorrência de cancelamentos'})
    else:
        cautions.append('Sem domínio claramente confirmado; revisar objetivo de negócio antes de construir métricas.')
    return {'version':'0.1.0', 'selected_domain':domain,'domain_candidates':classified,'proposed_visuals':proposed,'cautions':cautions,'status':'draft_requires_review'}
