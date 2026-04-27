from pathlib import Path


STATIC_CONTRACT_FILENAME = 'РАМОЧНЫЙ_ДОГОВОР_ОБ_ОКАЗАНИИ_ВОЗМЕЗДНЫХ_УСЛУГ_РАБОТ.pdf'


def get_static_contract_path() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    return project_root / STATIC_CONTRACT_FILENAME


def get_static_contract_bytes() -> bytes | None:
    path = get_static_contract_path()
    if not path.exists():
        return None
    return path.read_bytes()
