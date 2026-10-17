from __future__ import annotations

import argparse
import json
from pathlib import Path
from .profiler import read_table, profile
from .recipes import make_plan
from .layout import draft_layout
from .gantt import validate_gantt


def dump_json(path: Path, item: dict):
    path.write_text(json.dumps(item, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8')


def run(argv=None):
    parser = argparse.ArgumentParser(description='PowerBI Autopilot starter 0.1')
    sub = parser.add_subparsers(dest='command', required=True)
    analyze = sub.add_parser('analyze', help='Perfil, plano e grid preliminar')
    analyze.add_argument('input')
    analyze.add_argument('--output', default='analysis')
    analyze.add_argument('--sheet')
    analyze.add_argument('--sep')
    args = parser.parse_args(argv)
    df = read_table(args.input, sheet=args.sheet, sep=args.sep)
    p = profile(df)
    plan = make_plan(p)
    for visual in plan['proposed_visuals']:
        if visual['visual'] == 'gantt' and visual['status'] == 'ready_for_date_validation':
            report = validate_gantt(df, visual['fields']['task'], visual['fields']['start'], visual['fields']['end'])
            visual['data_validation'] = report
            visual['status'] = 'dates_valid_pending_semantic_review' if report['ready'] else 'review_data'
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    dump_json(out / 'profile.json', p)
    dump_json(out / 'plan.json', plan)
    dump_json(out / 'layout.json', draft_layout(plan))
    print(f'Análise criada em {out.resolve()} | domínio sugerido: {plan["selected_domain"]} | status: {plan["status"]}')


if __name__ == '__main__':
    run()
