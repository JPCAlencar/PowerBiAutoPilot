"""Conservative scalar parsers. No locale guesses for ambiguous representations."""
from dataclasses import dataclass
from datetime import date as Date, datetime
from decimal import Decimal, InvalidOperation
import numbers
import re

import pandas as pd


@dataclass(frozen=True)
class Parsed:
    value: object = None
    status: str = 'invalid'


def missing(value):
    return value is None or (isinstance(value, str) and not value.strip()) or bool(pd.isna(value))


def check_locale(locale):
    if locale not in (None, 'pt-BR', 'en-US'):
        raise ValueError('Locale suportado: pt-BR ou en-US')


CURRENCY_PREFIX = r'(?:R\$|US\$|(?:BRL|USD|EUR)(?=$|[\s\d(+-])|\$|€)'


def currency_marker(value):
    text = str(value).strip()
    match = re.match(r'^\(?[+-]?\s*' + CURRENCY_PREFIX, text, re.I)
    return bool(match and text[match.end():].strip())


def currency_hint(value):
    text = re.sub(r'^[\s(+-]+', '', str(value)).upper()
    match = re.match(CURRENCY_PREFIX, text)
    if match:
        return {'R$': 'BRL', 'BRL': 'BRL', 'US$': 'USD', 'USD': 'USD', '€': 'EUR', 'EUR': 'EUR'}.get(match.group())
    return None  # A bare $ does not identify a currency.


def number(value, locale=None):
    check_locale(locale)
    if missing(value):
        return Parsed(status='missing')
    if isinstance(value, bool):
        return Parsed()
    if isinstance(value, (numbers.Real, Decimal)):
        try:
            d = Decimal(str(value))
            return Parsed(d, 'valid') if d.is_finite() else Parsed()
        except InvalidOperation:
            return Parsed()
    text = str(value).strip().replace('\u00a0', ' ')
    # Only recognized currency annotations may be removed.
    text, outer_currency = re.subn(r'^' + CURRENCY_PREFIX + r'\s*', '', text, count=1, flags=re.I)
    neg = text.startswith('(') and text.endswith(')')
    if neg:
        text = text[1:-1].strip()
        if not outer_currency:
            text = re.sub(r'^' + CURRENCY_PREFIX + r'\s*', '', text, count=1, flags=re.I)
        if text.startswith(('-', '+')):
            return Parsed()
    sign = ''
    if text.startswith(('-', '+')):
        sign, text = text[0], text[1:]
        if not outer_currency:
            text = re.sub(r'^' + CURRENCY_PREFIX + r'\s*', '', text, count=1, flags=re.I)
    if not re.fullmatch(r'\d+(?:[.,]\d+)*', text):
        return Parsed()
    decimal_sep = ',' if locale == 'pt-BR' else '.' if locale == 'en-US' else None
    if decimal_sep is None:
        if '.' in text and ',' in text:
            decimal_sep = '.' if text.rfind('.') > text.rfind(',') else ','
        elif '.' in text or ',' in text:
            sep = '.' if '.' in text else ','
            parts = text.split(sep)
            if len(parts) == 2 and len(parts[-1]) == 3:
                return Parsed(status='ambiguous')
            if len(parts) > 2:
                if len(parts[0]) <= 3 and all(len(p) == 3 for p in parts[1:]):
                    return Parsed(Decimal(('-' if neg else sign) + ''.join(parts)), 'valid')
                return Parsed()
            decimal_sep = sep
        else:
            decimal_sep = '.'
    grouping = ',' if decimal_sep == '.' else '.'
    pattern = rf'(?:\d+|\d{{1,3}}(?:\{grouping}\d{{3}})+)(?:\{decimal_sep}\d+)?'
    if not re.fullmatch(pattern, text):
        return Parsed()
    canonical = text.replace(grouping, '').replace(decimal_sep, '.')
    try:
        d = Decimal(('-' if neg else sign) + canonical)
        return Parsed(d, 'valid') if d.is_finite() else Parsed()
    except InvalidOperation:
        return Parsed()


def date(value, locale=None):
    check_locale(locale)
    if missing(value):
        return Parsed(status='missing')
    if isinstance(value, datetime):
        return Parsed(value.date(), 'valid')
    if isinstance(value, Date):
        return Parsed(value, 'valid')
    if not isinstance(value, str):
        return Parsed()
    text = value.strip()
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:[T ].+)?', text):
            return Parsed(datetime.fromisoformat(text.replace('Z', '+00:00')).date(), 'valid')
        m = re.fullmatch(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if not m:
            return Parsed()
        a, b, year = map(int, m.groups())
        if locale is None and 1 <= a <= 12 and 1 <= b <= 12 and a != b:
            return Parsed(status='ambiguous')
        month, day = (a, b) if locale == 'en-US' or (locale is None and b > 12) else (b, a)
        return Parsed(Date(year, month, day), 'valid')
    except ValueError:
        return Parsed()
