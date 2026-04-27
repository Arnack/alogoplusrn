"""Utility for random PIN selection during contract signing.

П.7 ТЗ: PIN is randomly selected from one of 4 types at each signing session:
  1. inn    — last 4 digits of INN
  2. bday   — DD.MM from birthday (e.g. '1503' for 15.03.1990)
  3. byear  — 4-digit birth year (e.g. '1990')
  4. pass   — last 4 digits of passport number
"""

import random
from typing import Optional


PIN_TYPES = ['inn', 'bday', 'byear', 'pass']


def _compute_pin(pin_type: str, inn: str, birthday: str, passport_number: str) -> Optional[str]:
    """Compute the 4-character PIN value for the given type."""
    if pin_type == 'inn' and inn and len(inn) >= 4:
        return inn[-4:]
    if pin_type == 'bday' and birthday:
        # birthday format: DD.MM.YYYY
        parts = birthday.split('.')
        if len(parts) == 3:
            return parts[0] + parts[1]  # DDMM
    if pin_type == 'byear' and birthday:
        parts = birthday.split('.')
        if len(parts) == 3 and len(parts[2]) == 4:
            return parts[2]
    if pin_type == 'pass' and passport_number and len(passport_number) >= 4:
        return passport_number[-4:]
    return None


def choose_pin(
        inn: str,
        birthday: str,
        passport_number: str,
) -> tuple[str, str, str]:
    """Randomly pick an available PIN type and return (pin_type, pin_value, hint_text).

    Falls back through available types until a valid one is found.
    Always returns inn as last resort.
    """
    available = list(PIN_TYPES)
    random.shuffle(available)

    for pin_type in available:
        value = _compute_pin(pin_type, inn or '', birthday or '', passport_number or '')
        if value:
            hint = _hint_text(pin_type)
            return pin_type, value, hint

    # Absolute fallback — INN last 4
    return 'inn', (inn or '')[-4:], _hint_text('inn')


def verify_pin(pin_type: str, entered: str, inn: str, birthday: str, passport_number: str) -> bool:
    """Verify the entered PIN against the expected value for the given type."""
    expected = _compute_pin(pin_type, inn or '', birthday or '', passport_number or '')
    return expected is not None and entered.strip() == expected


def _hint_text(pin_type: str) -> str:
    hints = {
        'inn': '4 последние цифры вашего ИНН',
        'bday': '4 цифры вашей даты рождения в формате ДДММ (например, 1503 — это 15 марта)',
        'byear': 'год вашего рождения (4 цифры)',
        'pass': '4 последние цифры номера вашего паспорта',
    }
    return hints.get(pin_type, '4 последние цифры вашего ИНН')
