"""Decimal arithmetic sized from operands, independent of process-wide precision."""
from decimal import localcontext


def add(a, b):
    precision = max(a.adjusted(), b.adjusted()) - min(a.as_tuple().exponent, b.as_tuple().exponent) + 3
    with localcontext() as ctx:
        ctx.prec = max(precision, 28)
        return a+b


def subtract(a, b):
    return add(a, b.copy_negate())


def half(value):
    with localcontext() as ctx:
        ctx.prec = max(28, len(value.as_tuple().digits)+2)
        return value/2
