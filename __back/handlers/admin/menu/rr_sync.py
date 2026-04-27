import asyncio
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters import Admin, Director
from aiogram.filters import or_f
from API.fin.workers import fin_get_worker_by_id
import database as db


router = Router()


def _extract_rr_data(worker_data: dict) -> dict:
    """Извлечь карту и паспорт из ответа РР API."""
    d = worker_data.get('data', worker_data) or {}
    profile = d.get('profile', {}) or {}

    # Карта: пробуем на верхнем уровне и в profile
    card = d.get('card') or profile.get('card') or profile.get('bank_card') or None
    if card:
        card = str(card).replace(' ', '').strip()
        if len(card) > 16:
            card = card[:16]

    # Серия паспорта
    passport_series = (
        profile.get('passport_series')
        or profile.get('passportSeries')
        or d.get('passport_series')
        or None
    )
    if passport_series:
        passport_series = str(passport_series).strip()[:4]

    # Номер паспорта
    passport_number = (
        profile.get('passport_number')
        or profile.get('passportNumber')
        or d.get('passport_number')
        or None
    )
    if passport_number:
        passport_number = str(passport_number).strip()[:6]

    # Дата выдачи паспорта
    passport_issue_date = (
        profile.get('passport_issue_date')
        or profile.get('passportIssueDate')
        or profile.get('passport_date')
        or d.get('passport_issue_date')
        or None
    )
    if passport_issue_date:
        passport_issue_date = str(passport_issue_date).strip()[:10]

    return {
        'card': card,
        'passport_series': passport_series,
        'passport_number': passport_number,
        'passport_issue_date': passport_issue_date,
    }


@router.message(or_f(Admin(), Director()), Command('rr_sync'))
async def cmd_rr_sync(message: Message):
    """Синхронизация данных (карта, паспорт) из РР для всех активных СМЗ."""
    msg = await message.answer(
        '🔄 Синхронизация данных из РР...\nПолучаю список активных СМЗ...'
    )

    workers = await db.get_all_confirmed_smz_workers()
    if not workers:
        await msg.edit_text('ℹ️ Активных СМЗ исполнителей не найдено.')
        return

    await msg.edit_text(
        f'🔄 Найдено СМЗ исполнителей: {len(workers)}\nНачинаю синхронизацию...'
    )

    updated = 0
    skipped = 0
    errors = 0

    for worker in workers:
        try:
            if not worker.api_id:
                skipped += 1
                continue

            rr_data = await get_worker_by_id(worker_id=worker.api_id)
            if not rr_data:
                logging.warning(f'[rr_sync] worker.id={worker.id} api_id={worker.api_id}: РР не ответил')
                skipped += 1
                continue

            extracted = _extract_rr_data(rr_data)
            logging.info(f'[rr_sync] worker.id={worker.id} api_id={worker.api_id}: {extracted}')

            # Синхронизируем только если есть хоть что-то
            if any(v for v in extracted.values()):
                ok = await db.sync_worker_data_from_rr(
                    user_id=worker.id,
                    card=extracted['card'],
                    passport_series=extracted['passport_series'],
                    passport_number=extracted['passport_number'],
                    passport_issue_date=extracted['passport_issue_date'],
                )
                if ok:
                    updated += 1
                else:
                    errors += 1
            else:
                skipped += 1

            # Пауза чтобы не перегружать API
            await asyncio.sleep(0.3)

        except Exception as e:
            logging.exception(f'[rr_sync] worker.id={worker.id}: {e}')
            errors += 1

    await msg.edit_text(
        f'✅ <b>Синхронизация РР завершена</b>\n\n'
        f'Всего СМЗ: <b>{len(workers)}</b>\n'
        f'Обновлено: <b>{updated}</b>\n'
        f'Пропущено (нет данных): <b>{skipped}</b>\n'
        f'Ошибок: <b>{errors}</b>',
        parse_mode='HTML',
    )
