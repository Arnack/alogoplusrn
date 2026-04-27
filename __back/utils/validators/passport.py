import re


def validate_passport_series(value: str) -> bool:
    """Серия паспорта: ровно 4 цифры (например: 4510)."""
    return bool(re.fullmatch(r'\d{4}', value.strip()))


def validate_passport_number(value: str) -> bool:
    """Номер паспорта: ровно 6 цифр."""
    return bool(re.fullmatch(r'\d{6}', value.strip()))


def validate_passport_issue_date(value: str) -> bool:
    """Дата выдачи: DD.MM.YYYY."""
    return bool(re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', value.strip()))


def validate_passport_department_code(value: str) -> bool:
    """Код подразделения: 6 цифр или формат 000-000."""
    v = value.strip()
    if re.fullmatch(r'\d{6}', v):
        return True
    return bool(re.fullmatch(r'\d{3}-\d{3}', v))


def format_department_code(value: str) -> str:
    """Приводит 6-значный код к формату 000-000."""
    v = value.strip()
    if re.fullmatch(r'\d{6}', v):
        return f'{v[:3]}-{v[3:]}'
    return v
