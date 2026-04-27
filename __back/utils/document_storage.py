"""Утилиты для хранения документов на диске.

П.11 ТЗ: Структура хранения — <base_dir>/<ФИО_ИНН>/<дата_акта>/
Типы документов: договор (contract), акт (act), чек (receipt).
"""
import os
import re
import aiofiles
import logging
from typing import Optional
import shutil


DOCUMENTS_BASE_DIR = 'documents'


def _sanitize(name: str) -> str:
    """Удаляет символы, недопустимые в именах файлов/папок."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def build_worker_dir(
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
) -> str:
    """Возвращает путь к папке документов работника для конкретного акта.

    Пример: documents/Иванов_И.И._123456789012/28_03_2026/
    """
    first_initial = f'{(first_name or "")[:1]}.' if first_name else ''
    middle_initial = f'{(middle_name or "")[:1]}.' if middle_name else ''
    fio = _sanitize(f'{last_name} {first_initial}{middle_initial}'.strip())
    clean_inn = _sanitize(inn)
    clean_date = _sanitize((act_date or '').replace('.', '_'))
    return os.path.join(DOCUMENTS_BASE_DIR, f'{fio}_{clean_inn}', clean_date)


def build_doc_path(worker_dir: str, doc_type: str, extension: str = 'pdf') -> str:
    """Возвращает полный путь к файлу документа.

    doc_type: 'contract' | 'act' | 'receipt'
    """
    return os.path.join(worker_dir, f'{doc_type}.{extension}')


async def save_document(
        content: bytes,
        worker_dir: str,
        doc_type: str,
        extension: str = 'pdf',
) -> str:
    """Сохраняет байты документа на диск и возвращает путь к файлу."""
    os.makedirs(worker_dir, exist_ok=True)
    file_path = build_doc_path(worker_dir, doc_type, extension)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    logging.info(f'[document_storage] Сохранён {doc_type}: {file_path}')
    return file_path


def get_document_path(
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        doc_type: str,
        extension: str = 'pdf',
) -> Optional[str]:
    """Возвращает путь к документу если он существует, иначе None."""
    worker_dir = build_worker_dir(last_name, first_name, middle_name, inn, act_date)
    file_path = build_doc_path(worker_dir, doc_type, extension)
    return file_path if os.path.exists(file_path) else None


# ── Функции для сохранения конкретных типов документов ────────────────────────

async def save_contract_pdf(
        pdf_content: bytes,
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        contract_id: Optional[int] = None,
) -> str:
    """Сохраняет PDF договора в хранилище (п.11 ТЗ)."""
    worker_dir = build_worker_dir(last_name, first_name, middle_name, inn, act_date)
    file_name = f'contract_{contract_id}.pdf' if contract_id else 'contract.pdf'
    os.makedirs(worker_dir, exist_ok=True)
    file_path = os.path.join(worker_dir, file_name)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(pdf_content)
    logging.info(f'[document_storage] Сохранён договор: {file_path}')
    return file_path


async def save_act_pdf(
        pdf_content: bytes,
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        act_id: Optional[int] = None,
) -> str:
    """Сохраняет PDF акта в хранилище (п.11 ТЗ)."""
    worker_dir = build_worker_dir(last_name, first_name, middle_name, inn, act_date)
    file_name = f'act_{act_id}.pdf' if act_id else 'act.pdf'
    os.makedirs(worker_dir, exist_ok=True)
    file_path = os.path.join(worker_dir, file_name)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(pdf_content)
    logging.info(f'[document_storage] Сохранён акт: {file_path}')
    return file_path


async def save_receipt_pdf(
        pdf_content: bytes,
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        receipt_id: Optional[int] = None,
) -> str:
    """Сохраняет PDF чека в хранилище (п.11 ТЗ)."""
    worker_dir = build_worker_dir(last_name, first_name, middle_name, inn, act_date)
    file_name = f'receipt_{receipt_id}.pdf' if receipt_id else 'receipt.pdf'
    os.makedirs(worker_dir, exist_ok=True)
    file_path = os.path.join(worker_dir, file_name)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(pdf_content)
    logging.info(f'[document_storage] Сохранён чек: {file_path}')
    return file_path


async def save_receipt_txt(
        receipt_url: str,
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        receipt_id: Optional[int] = None,
) -> str:
    """Сохраняет TXT со ссылкой на чек. По ТЗ TXT создаётся всегда."""
    worker_dir = build_worker_dir(last_name, first_name, middle_name, inn, act_date)
    file_name = f'receipt_{receipt_id}.txt' if receipt_id else 'receipt.txt'
    os.makedirs(worker_dir, exist_ok=True)
    file_path = os.path.join(worker_dir, file_name)
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write((receipt_url or '').strip())
    logging.info(f'[document_storage] Сохранён TXT чека: {file_path}')
    return file_path


async def save_receipt_image(
        image_content: bytes,
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        receipt_id: Optional[int] = None,
        extension: str = 'jpg',
) -> str:
    """Сохраняет скриншот чека от исполнителя или кассира."""
    worker_dir = build_worker_dir(last_name, first_name, middle_name, inn, act_date)
    file_name = f'receipt_{receipt_id}_screen.{extension}' if receipt_id else f'receipt_screen.{extension}'
    os.makedirs(worker_dir, exist_ok=True)
    file_path = os.path.join(worker_dir, file_name)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(image_content)
    logging.info(f'[document_storage] Сохранён скрин чека: {file_path}')
    return file_path


async def download_and_save_receipt(
        receipt_url: str,
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        act_date: str,
        receipt_id: Optional[int] = None,
) -> Optional[str]:
    """Скачивает PDF чека по ссылке и сохраняет в хранилище.

    Args:
        receipt_url: Ссылка на чек (например, https://lknpd.nalog.ru/api/v1/receipt/.../print)
    """
    import aiohttp

    # Добавляем /print если нет в URL для получения печатной версии
    if not receipt_url.endswith('/print'):
        receipt_url = receipt_url.rstrip('/') + '/print'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(receipt_url) as response:
                if response.status == 200:
                    pdf_content = await response.read()
                    file_path = await save_receipt_pdf(
                        pdf_content=pdf_content,
                        last_name=last_name,
                        first_name=first_name,
                        middle_name=middle_name,
                        inn=inn,
                        act_date=act_date,
                        receipt_id=receipt_id,
                    )
                    return file_path
                else:
                    logging.error(f'[document_storage] Не удалось скачать чек: {receipt_url} -> {response.status}')
                    return None
    except Exception as e:
        logging.exception(f'[document_storage] Ошибка скачивания чека: {e}')
        return None


async def archive_document_file(file_path: Optional[str]) -> Optional[str]:
    """Перемещает документ в подпапку archive рядом с рабочими файлами."""
    if not file_path or not os.path.exists(file_path):
        return None
    archive_dir = os.path.join(os.path.dirname(file_path), 'archive')
    os.makedirs(archive_dir, exist_ok=True)
    archived_path = os.path.join(archive_dir, os.path.basename(file_path))
    shutil.move(file_path, archived_path)
    logging.info(f'[document_storage] Документ перемещён в архив: {archived_path}')
    return archived_path
