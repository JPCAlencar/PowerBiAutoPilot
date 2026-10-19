"""Small internal contracts; JSON output contains no DataFrames or source values."""
from dataclasses import dataclass, field

import pandas as pd


SCHEMA_VERSION = '0.2.1'


@dataclass
class Table:
    id: str
    frame: pd.DataFrame
    source: dict
    row_numbers: list[int]
    issues: list[dict] = field(default_factory=list)


def issue(code, severity, table, message, *, column=None, rows=(), count=None, scope=None):
    refs = list(rows)
    return {'code': code, 'severity': severity, 'table': table, 'column': column,
            'message': message, 'count': len(refs) if count is None else int(count),
            'source_rows': refs[:20], 'rows_truncated': len(refs) > 20,
            'scope': scope or (f'{table}.{column}' if column else table),
            'evidence_kind': 'observed'}
