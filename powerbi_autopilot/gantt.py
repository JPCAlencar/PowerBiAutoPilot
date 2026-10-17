from __future__ import annotations

import pandas as pd

from .profiler import parse_dates


def validate_gantt(df: pd.DataFrame, task: str, start: str, end: str) -> dict:
    """Valida os intervalos existentes. Não preenche datas ausentes ou cria cronograma planejado."""
    required = [task, start, end]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f'Colunas ausentes: {missing}')
    ds = parse_dates(df[start])
    de = parse_dates(df[end])
    invalid = int(((de < ds) & ds.notna() & de.notna()).sum())
    complete = ds.notna() & de.notna() & df[task].notna()
    return {'total_rows':int(len(df)), 'ready_rows':int((complete & (de >= ds)).sum()), 'missing_or_unparseable_rows':int((~complete).sum()), 'end_before_start_rows':invalid, 'ready': bool(len(df) and complete.all() and invalid == 0)}
