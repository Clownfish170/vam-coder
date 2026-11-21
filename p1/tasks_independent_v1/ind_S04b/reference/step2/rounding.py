"""Rounding."""


def round1(x):
    from decimal import ROUND_HALF_UP, Decimal
    return float(
        Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    )


def round2(x):
    from decimal import ROUND_HALF_UP, Decimal
    return float(
        Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
