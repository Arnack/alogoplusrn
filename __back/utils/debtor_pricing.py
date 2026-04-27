"""Расчёт сниженной цены единицы для исполнителей с активным удержанием."""
import math
from decimal import Decimal


def calculate_reduced_unit_price(
    unit_price: Decimal,
    coefficient: Decimal,
    withholding: int,
) -> Decimal:
    """
    Формула: ((цена × 11 × коэф) − удержание) ÷ 11, округление вниз до рубля.
    Не может быть отрицательной.
    """
    total = unit_price * Decimal('11') * coefficient - Decimal(withholding)
    reduced = total / Decimal('11')
    return max(Decimal('0'), Decimal(math.floor(reduced)))
