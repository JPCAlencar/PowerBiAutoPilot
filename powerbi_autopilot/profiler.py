from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    return re.sub(r"[^a-z0-9]+", "_", "".join(x for x in text if not unicodedata.combining(x)).lower()).strip("_")


def read_table(path: str | Path, sheet: str | None = None, sep: str | None = None) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix in {'.xlsx', '.xlsm'}:
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    if suffix == '.csv':
        return pd.read_csv(path, sep=sep or ',', encoding='utf-8-sig')
    raise ValueError('Formato não suportado neste MVP: use CSV, XLSX ou XLSM')


def parse_dates(series: pd.Series) -> pd.Series:
    raw = series.dropna().astype(str).str.strip()
    if not raw.empty and raw.str.match(r'^\d{4}-\d{2}-\d{2}(?:[T ][0-9:].*)?$').all():
        return pd.to_datetime(series, errors='coerce', format='ISO8601')
    return pd.to_datetime(series, errors='coerce', dayfirst=True)


def is_date_column(series: pd.Series, name: str) -> tuple[bool, pd.Series]:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True, pd.to_datetime(series, errors='coerce')
    normalized = normalize(name)
    # Prevent numeric serials and IDs being parsed as timestamps.
    looks_like_date = any(token in normalized.split('_') for token in ('data','date','inicio','start','fim','end','prazo','deadline'))
    if not looks_like_date or pd.api.types.is_numeric_dtype(series):
        return False, pd.Series(dtype='datetime64[ns]')
    non_null = series.dropna()
    if non_null.empty:
        return False, pd.Series(dtype='datetime64[ns]')
    parsed = parse_dates(non_null)
    if parsed.notna().mean() >= 0.8:
        return True, parse_dates(series)
    return False, pd.Series(dtype='datetime64[ns]')


def profile(df: pd.DataFrame) -> dict:
    if df.columns.duplicated().any():
        raise ValueError('A tabela possui nomes de colunas duplicados; normalizar antes de continuar.')
    n = len(df)
    cols = []
    for name in df.columns:
        s = df[name]
        is_date, parsed = is_date_column(s, str(name))
        if is_date:
            suggested_type = 'date'
        elif pd.api.types.is_bool_dtype(s):
            suggested_type = 'boolean'
        elif pd.api.types.is_numeric_dtype(s):
            suggested_type = 'number'
        else:
            suggested_type = 'text'
        item = {
            'name': str(name), 'type': suggested_type,
            'missing_count': int(s.isna().sum()),
            'missing_percent': round(float(s.isna().mean() * 100), 2) if n else 0.0,
            'distinct_count': int(s.nunique(dropna=True)),
        }
        if is_date and parsed.notna().any():
            item['min_date'] = parsed.min().date().isoformat()
            item['max_date'] = parsed.max().date().isoformat()
            item['invalid_date_count'] = int((s.notna() & parsed.isna()).sum())
        cols.append(item)
    warnings = []
    if n == 0:
        warnings.append('Tabela vazia; não é possível recomendar análises.')
    if n and df.isna().all(axis=1).any():
        warnings.append('Há linhas inteiramente vazias.')
    if n and df.duplicated().any():
        warnings.append(f'Há {int(df.duplicated().sum())} linhas exatamente duplicadas; verificar granularidade antes de removê-las.')
    return {'rows': n, 'columns': cols, 'warnings': warnings}
