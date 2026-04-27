from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

import database as db
from filters import Admin

router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())

logger = logging.getLogger(__name__)

# ─── FSM states ─────────────────────────────────────────────────────────────
# CreatePromo:type → name → description → n_orders → period_days → bonus_amount
# ─────────────────────────────────────────────────────────────────────────────


def _promo_list_keyboard(promos, customer_id: int) -> InlineKeyboardMarkup:
    rows = []
    for p in promos:
        label = f"{'🔁' if p.type == 'streak' else '📅'} {p.name}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f'PromoInfo:{p.id}:{customer_id}')])
    rows.append([InlineKeyboardButton(text='➕ Создать акцию', callback_data=f'PromoCreate:{customer_id}')])
    rows.append([InlineKeyboardButton(text='📊 PDF-отчёт по акциям', callback_data=f'PromoReport:{customer_id}')])
    rows.append([InlineKeyboardButton(text='Назад', callback_data=f'Customer:{customer_id}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _promo_detail_keyboard(promo_id: int, customer_id: int, is_active: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_active:
        rows.append([InlineKeyboardButton(text='❌ Деактивировать', callback_data=f'PromoDeactivate:{promo_id}:{customer_id}')])
    rows.append([InlineKeyboardButton(text='Назад', callback_data=f'CustomerPromotions:{customer_id}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─── Список акций Получателя ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith('CustomerPromotions:'))
async def open_customer_promotions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    customer_id = int(callback.data.split(':')[1])
    promos = await db.get_active_promotions_by_customer(customer_id=customer_id)
    text = f'🎁 <b>Акции Получателя услуг</b>\n\nАктивных акций: {len(promos)}'
    await callback.message.edit_text(text=text, reply_markup=_promo_list_keyboard(promos, customer_id), parse_mode='HTML')


# ─── Карточка акции ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('PromoInfo:'))
async def show_promo_info(callback: CallbackQuery):
    await callback.answer()
    parts = callback.data.split(':')
    promo_id, customer_id = int(parts[1]), int(parts[2])
    promo = await db.get_promotion_by_id(promo_id)
    if not promo:
        await callback.answer('Акция не найдена', show_alert=True)
        return
    if promo.type == 'streak':
        condition = f'серия из {promo.n_orders} заявок подряд'
    else:
        condition = f'{promo.n_orders} заявок за {promo.period_days} дн.'
    text = (
        f'🎁 <b>{promo.name}</b>\n\n'
        f'Тип: {"🔁 Серия" if promo.type == "streak" else "📅 Период"}\n'
        f'Условие: {condition}\n'
        f'Вознаграждение: {promo.bonus_amount} ₽ за заявку\n'
        f'Итого за цикл: {promo.n_orders * promo.bonus_amount} ₽\n'
        f'Город: {promo.city}\n\n'
        f'📝 {promo.description or "—"}\n\n'
        f'Статус: {"✅ Активна" if promo.is_active else "❌ Неактивна"}'
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=_promo_detail_keyboard(promo_id, customer_id, promo.is_active),
        parse_mode='HTML'
    )


# ─── Деактивация ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('PromoDeactivate:'))
async def deactivate_promo(callback: CallbackQuery):
    await callback.answer()
    parts = callback.data.split(':')
    promo_id, customer_id = int(parts[1]), int(parts[2])
    await db.deactivate_promotion(promo_id)
    await callback.answer('Акция деактивирована', show_alert=True)
    promos = await db.get_active_promotions_by_customer(customer_id=customer_id)
    text = f'🎁 <b>Акции Получателя услуг</b>\n\nАктивных акций: {len(promos)}'
    await callback.message.edit_text(text=text, reply_markup=_promo_list_keyboard(promos, customer_id), parse_mode='HTML')


# ─── Создание акции — FSM ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('PromoCreate:'))
async def promo_create_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])
    await state.set_state('PromoType')
    await state.update_data(promo_customer_id=customer_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔁 Серия', callback_data='PromoTypeStreak')],
        [InlineKeyboardButton(text='📅 Период', callback_data='PromoTypePeriod')],
        [InlineKeyboardButton(text='Отмена', callback_data=f'CustomerPromotions:{customer_id}')],
    ])
    await callback.message.edit_text(
        text='🎁 <b>Создание акции</b>\n\nВыберите тип акции:\n\n'
             '• <b>Серия</b> — N заявок подряд без пропусков\n'
             '• <b>Период</b> — K заявок за D дней',
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_({'PromoTypeStreak', 'PromoTypePeriod'}), StateFilter('PromoType'))
async def promo_set_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    promo_type = 'streak' if callback.data == 'PromoTypeStreak' else 'period'
    await state.update_data(promo_type=promo_type)
    await state.set_state('PromoName')
    await callback.message.edit_text(
        text='Введите <b>название</b> акции (до 100 символов):',
        parse_mode='HTML'
    )


@router.message(F.text, StateFilter('PromoName'))
async def promo_set_name(message: Message, state: FSMContext):
    name = message.text.strip()[:100]
    await state.update_data(promo_name=name)
    await state.set_state('PromoDescription')
    await message.answer('Введите <b>описание</b> акции (или отправьте «-» чтобы пропустить):', parse_mode='HTML')


@router.message(F.text, StateFilter('PromoDescription'))
async def promo_set_description(message: Message, state: FSMContext):
    desc = '' if message.text.strip() == '-' else message.text.strip()
    await state.update_data(promo_description=desc)
    data = await state.get_data()
    promo_type = data.get('promo_type')
    await state.set_state('PromoNOrders')
    label = 'N (длина серии)' if promo_type == 'streak' else 'K (кол-во заявок за период)'
    await message.answer(f'Введите <b>{label}</b> — целое число ≥ 1:', parse_mode='HTML')


@router.message(F.text, StateFilter('PromoNOrders'))
async def promo_set_n_orders(message: Message, state: FSMContext):
    try:
        n = int(message.text.strip())
        if n < 1:
            raise ValueError
    except ValueError:
        await message.answer('Введите целое число ≥ 1.')
        return
    await state.update_data(promo_n_orders=n)
    data = await state.get_data()
    promo_type = data.get('promo_type')
    if promo_type == 'period':
        await state.set_state('PromoPeriodDays')
        await message.answer('Введите <b>D</b> — количество дней в периоде (целое число ≥ 1):', parse_mode='HTML')
    else:
        await state.set_state('PromoBonusAmount')
        await message.answer('Введите <b>сумму вознаграждения</b> за одну заявку (₽, целое число):', parse_mode='HTML')


@router.message(F.text, StateFilter('PromoPeriodDays'))
async def promo_set_period_days(message: Message, state: FSMContext):
    try:
        d = int(message.text.strip())
        if d < 1:
            raise ValueError
    except ValueError:
        await message.answer('Введите целое число ≥ 1.')
        return
    await state.update_data(promo_period_days=d)
    await state.set_state('PromoBonusAmount')
    await message.answer('Введите <b>сумму вознаграждения</b> за одну заявку (₽, целое число):', parse_mode='HTML')


@router.message(F.text, StateFilter('PromoBonusAmount'))
async def promo_set_bonus_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            raise ValueError
    except ValueError:
        await message.answer('Введите целое число ≥ 1.')
        return
    await state.update_data(promo_bonus_amount=amount)
    data = await state.get_data()
    # Показываем подтверждение
    promo_type = data['promo_type']
    n = data['promo_n_orders']
    bonus = amount
    period_days = data.get('promo_period_days')
    if promo_type == 'streak':
        condition = f'серия из {n} заявок подряд'
    else:
        condition = f'{n} заявок за {period_days} дн.'
    text = (
        f'🎁 <b>Подтвердите создание акции</b>\n\n'
        f'Название: {data["promo_name"]}\n'
        f'Тип: {"🔁 Серия" if promo_type == "streak" else "📅 Период"}\n'
        f'Условие: {condition}\n'
        f'Вознаграждение: {bonus} ₽ × {n} = {bonus * n} ₽\n'
        f'Описание: {data["promo_description"] or "—"}\n\n'
        f'Акция будет создана для <b>всех городов</b> получателя услуг.'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Создать', callback_data='PromoConfirmCreate')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data=f'CustomerPromotions:{data["promo_customer_id"]}')],
    ])
    await state.set_state('PromoConfirm')
    await message.answer(text=text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data == 'PromoConfirmCreate', StateFilter('PromoConfirm'))
async def promo_confirm_create(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await state.clear()

    customer_id = data['promo_customer_id']
    promo_type = data['promo_type']
    n = data['promo_n_orders']
    bonus = data['promo_bonus_amount']
    period_days = data.get('promo_period_days')

    # Получаем города получателя
    cities = await db.get_customer_cities(customer_id=customer_id)
    if not cities:
        await callback.message.edit_text('❌ Нет городов у этого получателя услуг.')
        return

    created = []
    for city_obj in cities:
        city_name = city_obj.city
        promo = await db.create_promotion(
            customer_id=customer_id,
            type=promo_type,
            name=data['promo_name'],
            description=data['promo_description'],
            n_orders=n,
            period_days=period_days,
            bonus_amount=bonus,
            city=city_name,
        )
        created.append(promo)

    # Уведомляем исполнителей городов
    for promo in created:
        workers = await db.get_users_by_city(city=promo.city)
        for w in workers:
            if w.tg_id:
                try:
                    if promo_type == 'streak':
                        condition_text = f'выполните {n} заявок подряд без пропусков'
                    else:
                        condition_text = f'выполните {n} заявок за {period_days} дней'
                    await callback.bot.send_message(
                        chat_id=w.tg_id,
                        text=(
                            f'🎁 <b>Новая акция!</b>\n\n'
                            f'<b>{promo.name}</b>\n\n'
                            f'{promo.description or ""}\n\n'
                            f'Условие: {condition_text}\n'
                            f'Вознаграждение: {bonus * n} ₽\n\n'
                            f'Примите участие в разделе «🎁 Акции» в меню.'
                        ),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.warning('[promo] Ошибка уведомления работника %s: %s', w.tg_id, e)

    promos = await db.get_active_promotions_by_customer(customer_id=customer_id)
    text = f'✅ Акция создана в {len(created)} городах.\n\n🎁 <b>Акции Получателя услуг</b>\n\nАктивных акций: {len(promos)}'
    await callback.message.edit_text(text=text, reply_markup=_promo_list_keyboard(promos, customer_id), parse_mode='HTML')


# ─── PDF отчёт по акциям ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('PromoReport:'))
async def promo_report_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])
    await state.set_state('PromoReportPeriod')
    await state.update_data(promo_report_customer_id=customer_id)
    await callback.message.edit_text(
        text='📊 Введите период для отчёта в формате <b>ДД.ММ.ГГГГ-ДД.ММ.ГГГГ</b>\nПример: 01.03.2026-31.03.2026',
        parse_mode='HTML'
    )


@router.message(F.text, StateFilter('PromoReportPeriod'))
async def promo_report_generate(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        parts = text.split('-')
        date_from = datetime.strptime(parts[0].strip(), '%d.%m.%Y')
        date_to = datetime.strptime(parts[1].strip(), '%d.%m.%Y').replace(hour=23, minute=59, second=59)
    except Exception:
        await message.answer('Неверный формат. Введите период как ДД.ММ.ГГГГ-ДД.ММ.ГГГГ')
        return

    data = await state.get_data()
    await state.clear()
    customer_id = data['promo_report_customer_id']

    bonuses = await db.get_bonuses_by_customer_period(
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
    )

    if not bonuses:
        await message.answer('За указанный период начислений по акциям не найдено.')
        return

    from utils.pdf.promotion_report import generate_promotion_report_pdf
    pdf_buf = await generate_promotion_report_pdf(bonuses, date_from, date_to)
    await message.answer_document(
        document=BufferedInputFile(pdf_buf.getvalue(), filename='promo_report.pdf'),
        caption=f'Отчёт по акциям за {parts[0].strip()}–{parts[1].strip()}'
    )
