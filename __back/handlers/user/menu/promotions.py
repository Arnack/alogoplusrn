from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database as db
import keyboards.reply as kb
from filters import Worker

router = Router()
logger = logging.getLogger(__name__)


def _promotions_keyboard(promos, participations: dict) -> InlineKeyboardMarkup:
    """participations: dict {promotion_id: participation}"""
    rows = []
    for p in promos:
        part = participations.get(p.id)
        if part:
            if p.type == 'streak':
                progress = f'{part.current_streak}/{p.n_orders}'
            else:
                progress = f'{part.period_completed}/{p.n_orders}'
            label = f'✅ {p.name} [{progress}]'
        else:
            label = f'🎁 {p.name} — принять участие'
        rows.append([InlineKeyboardButton(text=label, callback_data=f'WorkerPromo:{p.id}')])
    if participations:
        rows.append([InlineKeyboardButton(text='❌ Отказаться от всех акций', callback_data='WorkerCancelAllPromos')])
    rows.append([InlineKeyboardButton(text='◀️ Назад', callback_data='WorkerBackToMain')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_promotions_menu(event: Message | CallbackQuery, user_id: int, city: str):
    promos = await db.get_active_promotions_by_city(city=city)
    all_parts = await db.get_worker_participations(worker_id=user_id)
    parts_by_promo = {p.promotion_id: p for p in all_parts}

    text = '🎁 <b>Акции</b>\n\n'
    if not promos:
        text += 'Активных акций в вашем городе нет.'
    else:
        for p in promos:
            part = parts_by_promo.get(p.id)
            if p.type == 'streak':
                condition = f'{p.n_orders} заявок подряд без пропусков'
            else:
                condition = f'{p.n_orders} заявок за {p.period_days} дн.'
            reward = p.n_orders * p.bonus_amount
            text += f'<b>{p.name}</b>\n'
            text += f'Условие: {condition} → +{reward} ₽\n'
            if part:
                if p.type == 'streak':
                    text += f'Ваш прогресс: {part.current_streak}/{p.n_orders} 🔥\n'
                else:
                    text += f'Ваш прогресс: {part.period_completed}/{p.n_orders}\n'
            text += '\n'

    keyboard = _promotions_keyboard(promos, parts_by_promo)
    if isinstance(event, Message):
        await event.answer(text=text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await event.answer()
        try:
            await event.message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML')
        except Exception:
            await event.message.answer(text=text, reply_markup=keyboard, parse_mode='HTML')


@router.message(Worker(), F.text == '🎁 Акции')
async def open_promotions(message: Message):
    user = await db.get_user(tg_id=message.from_user.id)
    if not user:
        return
    await show_promotions_menu(message, user.id, user.city)


@router.callback_query(Worker(), F.data == 'OpenPromotions')
async def open_promotions_callback(callback: CallbackQuery):
    user = await db.get_user(tg_id=callback.from_user.id)
    if not user:
        await callback.answer()
        return
    await show_promotions_menu(callback, user.id, user.city)


@router.callback_query(Worker(), F.data.startswith('WorkerPromo:'))
async def worker_promo_action(callback: CallbackQuery):
    promo_id = int(callback.data.split(':')[1])
    user = await db.get_user(tg_id=callback.from_user.id)
    if not user:
        await callback.answer()
        return

    promo = await db.get_promotion_by_id(promo_id)
    if not promo or not promo.is_active:
        await callback.answer('Акция недоступна.', show_alert=True)
        return

    existing = await db.get_active_participation(worker_id=user.id, promotion_id=promo_id)
    if existing:
        # Уже участвует — показываем детали
        if promo.type == 'streak':
            progress = f'{existing.current_streak}/{promo.n_orders} 🔥'
        else:
            progress = f'{existing.period_completed}/{promo.n_orders}'
        await callback.answer(
            f'Вы уже участвуете: {progress}\nЦиклов завершено: {existing.cycles_completed}',
            show_alert=True
        )
    else:
        await db.join_promotion(worker_id=user.id, promotion_id=promo_id)
        await callback.answer(f'✅ Вы приняли участие в акции «{promo.name}»!', show_alert=True)

    await show_promotions_menu(callback, user.id, user.city)


@router.callback_query(Worker(), F.data == 'WorkerBackToMain')
async def worker_back_to_main(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer('Главное меню', reply_markup=kb.user_menu())


@router.callback_query(Worker(), F.data == 'WorkerCancelAllPromos')
async def worker_cancel_all_promos(callback: CallbackQuery):
    user = await db.get_user(tg_id=callback.from_user.id)
    if not user:
        await callback.answer()
        return
    await db.cancel_all_participations(worker_id=user.id)
    await callback.answer('Вы отказались от участия во всех акциях.', show_alert=True)
    await show_promotions_menu(callback, user.id, user.city)
