"""Декодирование QR-кода из изображения и разбор содержимого чека."""
import re
from io import BytesIO
from typing import Optional

_RECEIPT_URL_RE = re.compile(r'https?://(lknpd\.nalog\.ru|check\.nalog\.ru)/\S+')


def decode_qr_from_bytes(image_bytes: bytes) -> Optional[str]:
    """Декодирует первый QR-код из изображения. Возвращает строку или None."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
        image = Image.open(BytesIO(image_bytes))
        results = decode(image)
        if results:
            return results[0].data.decode('utf-8')
        return None
    except Exception:
        return None


def extract_receipt_url(raw: str) -> Optional[str]:
    """Если строка из QR является ссылкой на чек — возвращает её, иначе None."""
    raw = raw.strip()
    if _RECEIPT_URL_RE.match(raw):
        return raw
    return None
