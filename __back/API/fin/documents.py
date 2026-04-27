"""
Подписание документов через старый (желтый) кабинет: fin-api.handswork.pro
"""
import logging

from API.fin.client import fin_get, fin_post


async def get_unsigned_document(transaction_id: int) -> tuple:
    """
    Возвращает (document_id, type, is_contract).
    """
    result = await fin_get(f'/documents/{transaction_id}/get-unsigned-document')
    if not result:
        return None, None, None
    is_contract = result.get('type') == 'contract'
    return result.get('documentId'), result.get('type'), is_contract


async def sign_worker_document(document_id: int, document_type: str, sign: str = None) -> bool:
    status, result = await fin_post(
        f'/documents/{document_type}/{document_id}/sign-document-by-worker'
    )
    if status == 200:
        return True
    logging.error(f'[FIN documents] sign_worker_document {document_type}/{document_id} -> {status}: {result}')
    return False
