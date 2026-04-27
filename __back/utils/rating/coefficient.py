from decimal import Decimal


def get_rating_coefficient(
        rating: str
) -> Decimal:
    if Decimal(rating) >= Decimal('93'):
        coefficient = Decimal('1')
    elif Decimal(rating) >= Decimal('83'):
        coefficient = Decimal('0.95')
    else:
        coefficient = Decimal('0.9')
    return coefficient
