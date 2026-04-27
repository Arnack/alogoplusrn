from __future__ import annotations

import html as html_module
import logging
from typing import Annotated

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, InputMediaDocument, InputMediaPhoto
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import joinedload

import database as db
import texts as txt
from config_reader import config
from database.models import User
from utils import get_rating

from web_api.deps import get_current_foreman, get_current_supervisor, get_current_worker
from web_api.extras_friend import (
    clear_friend_session,
    clear_friend_verified,
    friend_progress,
    lookup_inn,
    lookup_phone,
    set_city_and_send_code,
    verify_code,
)
from web_api.schemas import (
    CoordinatorCityOut,
    CoordinatorCustomerOut,
    CoordinatorOrderOut,
    FriendLookupBody,
    FriendProgressResponse,
    FriendSetCityBody,
    FriendVerifyCodeBody,
    HelpInfoResponse,
    MessageResponse,
    OrderForFriendInfoResponse,
    ShoutItemOut,
    ShoutSendBody,
    ShoutStatusResponse,
)

router = APIRouter()

_HELP_MAX_FILES = 3
_HELP_MAX_BYTES_PER_FILE = 20 * 1024 * 1024
_HELP_MAX_TEXT = 3500


async def _load_worker_with_security(user: User) -> User | None:
    if user.tg_id:
        w = await db.get_user_with_data_for_security(tg_id=user.tg_id)
        if w:
            return w
    async with db.async_session() as session:
        return await session.scalar(
            select(User).where(User.id == user.id).options(joinedload(User.security))
        )


def _help_worker_names(worker: User) -> tuple[str, str]:
    sec = getattr(worker, 'security', None)
    if sec:
        fn = f'{sec.last_name} {sec.first_name} {sec.middle_name}'.strip()
        phone = sec.phone_number or worker.phone_number or '—'
        return fn, phone
    fn = f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip()
    return fn, worker.phone_number or '—'


async def _send_help_to_group_telegram(
    session_user: User,
    worker: User,
    help_chat_id: int,
    help_plain: str,
    photos: list[tuple[bytes, str]],
    docs: list[tuple[bytes, str]],
) -> None:
    user_rating = await db.get_user_rating(user_id=worker.id)
    if not user_rating:
        await db.set_rating(user_id=worker.id)
        user_rating = await db.get_user_rating(user_id=worker.id)
    if not user_rating:
        raise HTTPException(500, 'Рейтинг исполнителя недоступен')
    rating = await get_rating(user_id=worker.id)
    fn, phone = _help_worker_names(worker)
    cap = txt.help_message_caption(full_name=html_module.escape(fn))
    body = txt.help_message_to_group(
        real_full_name=html_module.escape(fn),
        real_phone_number=html_module.escape(phone),
        tg_id=int(session_user.tg_id or 0),
        max_id=int(worker.max_id or 0),
        city=html_module.escape(worker.city or '—'),
        total_orders=user_rating.total_orders,
        successful_orders=user_rating.successful_orders,
        rating=html_module.escape(str(rating)),
        help_text=html_module.escape(help_plain),
    )
    bot_token = config.bot_token
    if not bot_token:
        raise HTTPException(500, 'BOT_TOKEN не задан')
    bot = Bot(token=bot_token.get_secret_value())
    try:
        await bot.send_message(
            chat_id=help_chat_id,
            text=body,
            parse_mode=ParseMode.HTML,
        )
        if len(photos) > 1:
            media: list[InputMediaPhoto] = []
            for i, (raw, name) in enumerate(photos):
                media.append(
                    InputMediaPhoto(
                        media=BufferedInputFile(raw, filename=name),
                        caption=cap if i == 0 else None,
                        parse_mode=ParseMode.HTML if i == 0 else None,
                    )
                )
            await bot.send_media_group(chat_id=help_chat_id, media=media)
        elif len(photos) == 1:
            raw, name = photos[0]
            await bot.send_photo(
                chat_id=help_chat_id,
                photo=BufferedInputFile(raw, filename=name),
                caption=cap,
                parse_mode=ParseMode.HTML,
            )
        if len(docs) > 1:
            media_d: list[InputMediaDocument] = []
            for i, (raw, name) in enumerate(docs):
                media_d.append(
                    InputMediaDocument(
                        media=BufferedInputFile(raw, filename=name),
                        caption=cap if i == 0 else None,
                        parse_mode=ParseMode.HTML if i == 0 else None,
                    )
                )
            await bot.send_media_group(chat_id=help_chat_id, media=media_d)
        elif len(docs) == 1:
            raw, name = docs[0]
            await bot.send_document(
                chat_id=help_chat_id,
                document=BufferedInputFile(raw, filename=name),
                caption=cap,
                parse_mode=ParseMode.HTML,
            )
    finally:
        await bot.session.close()


@router.get('/help', response_model=HelpInfoResponse)
async def help_info(user: Annotated[User, Depends(get_current_worker)]):
    settings = await db.get_settings()
    help_chat_id = settings.help_group_chat_id if settings else None
    configured = bool(help_chat_id)
    can_send = await db.can_use_help(worker_id=user.id)
    cool = await db.help_cooldown_remaining_seconds(worker_id=user.id)

    text = f'{txt.request_help_text()}\n\n{txt.request_help_files_or_photos()}'
    note = None
    if not configured:
        note = 'Канал поддержки не настроен в системе — обратитесь к администратору.'
    elif not can_send and cool:
        note = f'Следующее обращение будет доступно примерно через {max(1, cool // 60)} мин.'

    return HelpInfoResponse(
        text=text,
        note=note,
        help_configured=configured,
        can_send_signal=configured and can_send,
        cooldown_seconds=cool if not can_send else None,
    )


@router.get('/order-for-friend', response_model=OrderForFriendInfoResponse)
async def order_for_friend_info(user: Annotated[User, Depends(get_current_worker)]):
    cities = await db.get_cities_name()
    return OrderForFriendInfoResponse(
        available=True,
        message='Найдите друга по телефону или ИНН, выберите город и подтвердите код из SMS.',
        cities=cities,
    )


@router.get('/friend/progress', response_model=FriendProgressResponse)
async def friend_progress_ep(user: Annotated[User, Depends(get_current_worker)]):
    snap = await friend_progress(user.id)
    return FriendProgressResponse(
        step=snap['step'],
        message=snap.get('message', ''),
        cities=snap.get('cities', []),
        friend_label=snap.get('friend_label'),
    )


@router.post('/friend/lookup-phone', response_model=FriendProgressResponse)
async def friend_lookup_phone(
    user: Annotated[User, Depends(get_current_worker)],
    body: FriendLookupBody,
):
    if not body.phone:
        raise HTTPException(400, 'Укажите телефон')
    r = await lookup_phone(user.id, body.phone)
    if not r['ok']:
        return FriendProgressResponse(step='idle', message=r['message'], cities=[], friend_label=None)
    return FriendProgressResponse(
        step='need_city',
        message=r['message'],
        cities=r.get('cities', []),
        friend_label=r.get('friend_label'),
    )


@router.post('/friend/lookup-inn', response_model=FriendProgressResponse)
async def friend_lookup_inn(
    user: Annotated[User, Depends(get_current_worker)],
    body: FriendLookupBody,
):
    if not body.inn:
        raise HTTPException(400, 'Укажите ИНН')
    r = await lookup_inn(user.id, body.inn)
    if not r['ok']:
        return FriendProgressResponse(step='idle', message=r['message'], cities=[], friend_label=None)
    return FriendProgressResponse(
        step='need_city',
        message=r['message'],
        cities=r.get('cities', []),
        friend_label=r.get('friend_label'),
    )


@router.post('/friend/set-city', response_model=FriendProgressResponse)
async def friend_set_city(
    user: Annotated[User, Depends(get_current_worker)],
    body: FriendSetCityBody,
):
    log_tg = int(user.tg_id or 0)
    r = await set_city_and_send_code(user.id, body.city.strip(), log_tg_id=log_tg)
    if not r['ok']:
        raise HTTPException(400, r['message'])
    return FriendProgressResponse(
        step='need_code',
        message=r['message'],
        cities=[],
        friend_label=None,
    )


@router.post('/friend/verify-code', response_model=FriendProgressResponse)
async def friend_verify(
    user: Annotated[User, Depends(get_current_worker)],
    body: FriendVerifyCodeBody,
):
    r = await verify_code(user.id, body.code.strip())
    if not r['ok']:
        raise HTTPException(400, r['message'])
    return FriendProgressResponse(
        step='verified',
        message=r['message'],
        cities=[],
        friend_label=None,
    )


@router.post('/friend/cancel', response_model=MessageResponse)
async def friend_cancel(user: Annotated[User, Depends(get_current_worker)]):
    clear_friend_session(user.id)
    clear_friend_verified(user.id)
    return MessageResponse(message='Сценарий сброшен'    )


@router.post('/help/send', response_model=MessageResponse)
async def help_send(
    user: Annotated[User, Depends(get_current_worker)],
    message: Annotated[str, Form()],
    files: Annotated[list[UploadFile] | None, File()] = None,
):
    msg = (message or '').strip()
    if not msg:
        raise HTTPException(400, 'Введите текст обращения')

    if not await db.can_use_help(worker_id=user.id):
        raise HTTPException(429, 'Обращение можно отправлять не чаще, чем раз в 6 часов')

    settings = await db.get_settings()
    help_chat_id = settings.help_group_chat_id if settings else None
    if not help_chat_id:
        raise HTTPException(503, 'Канал поддержки не настроен')

    if len(msg) > _HELP_MAX_TEXT:
        msg = msg[:_HELP_MAX_TEXT] + '…'

    file_list = files or []
    if len(file_list) > _HELP_MAX_FILES:
        raise HTTPException(400, f'Не более {_HELP_MAX_FILES} файлов или фото')

    photos: list[tuple[bytes, str]] = []
    docs: list[tuple[bytes, str]] = []
    for uf in file_list:
        raw = await uf.read()
        if len(raw) > _HELP_MAX_BYTES_PER_FILE:
            raise HTTPException(400, 'Каждый файл не больше 20 МБ')
        name = uf.filename or 'file'
        ct = (uf.content_type or '').lower()
        if ct.startswith('image/'):
            photos.append((raw, name))
        else:
            docs.append((raw, name))

    worker = await _load_worker_with_security(user)
    if not worker:
        raise HTTPException(500, 'Не удалось загрузить профиль исполнителя')

    try:
        await _send_help_to_group_telegram(
            session_user=user,
            worker=worker,
            help_chat_id=help_chat_id,
            help_plain=msg,
            photos=photos,
            docs=docs,
        )
    except HTTPException:
        raise
    except Exception:
        logging.exception('help_send telegram')
        raise HTTPException(502, 'Не удалось отправить обращение руководству') from None

    await db.update_help_last_use(worker_id=user.id)
    return MessageResponse(message=txt.help_message_sent().split('\n')[0])


@router.post('/help/signal', response_model=MessageResponse)
async def help_signal(user: Annotated[User, Depends(get_current_worker)]):
    if not await db.can_use_help(worker_id=user.id):
        raise HTTPException(429, 'Сигнал можно отправлять не чаще, чем раз в 6 часов')

    settings = await db.get_settings()
    help_chat_id = settings.help_group_chat_id if settings else None
    if not help_chat_id:
        raise HTTPException(503, 'Канал поддержки не настроен')

    bot_token = config.bot_token
    if not bot_token:
        raise HTTPException(500, 'BOT_TOKEN не задан')

    text = (
        '🆘 SOS из Web-панели\n\n'
        f'Исполнитель: {user.last_name} {user.first_name} {user.middle_name}\n'
        f'ID: {user.id}\n'
        f'Телефон: {user.phone_number}\n'
        f'Город: {user.city}'
    )

    bot = Bot(token=bot_token.get_secret_value())
    try:
        await bot.send_message(chat_id=help_chat_id, text=text)
    except Exception:
        raise HTTPException(502, 'Не удалось отправить сигнал руководству') from None
    finally:
        await bot.session.close()

    await db.update_help_last_use(worker_id=user.id)
    return MessageResponse(message='Сигнал отправлен руководству')


# ── Shout (foreman) ─────────────────────────────────────────


@router.get('/shout/status', response_model=ShoutStatusResponse)
async def shout_status(user: Annotated[User, Depends(get_current_foreman)]):
    foreman = await db.get_foreman_by_tg_id(foreman_tg_id=user.tg_id)
    if not foreman:
        raise HTTPException(403, 'Профиль представителя не найден')

    order = await db.get_foreman_shout_order(customer_id=foreman.customer_id)
    if not order:
        org = await db.get_customer_organization(customer_id=foreman.customer_id)
        return ShoutStatusResponse(
            can_send=False,
            message=f'Нет активной заявки на объекте ({org or "заказчик"}).',
        )

    workers = await db.get_workers_from_order_workers(order_id=order.id)
    n = len(workers)
    if n <= 1:
        return ShoutStatusResponse(
            can_send=False,
            message='На объекте меньше двух исполнителей — оповещение недоступно.',
            order_id=order.id,
            job_name=order.job_name,
            order_date=order.date,
            city=order.city,
            workers_on_site=n,
        )

    return ShoutStatusResponse(
        can_send=True,
        message='Можно отправить текстовое оповещение бригаде на объекте.',
        order_id=order.id,
        job_name=order.job_name,
        order_date=order.date,
        city=order.city,
        workers_on_site=n,
    )


@router.post('/shout/send', response_model=MessageResponse)
async def shout_send(
    user: Annotated[User, Depends(get_current_foreman)],
    body: ShoutSendBody,
):
    foreman = await db.get_foreman_by_tg_id(foreman_tg_id=user.tg_id)
    if not foreman:
        raise HTTPException(403, 'Профиль представителя не найден')

    order = await db.get_foreman_shout_order(customer_id=foreman.customer_id)
    if not order:
        raise HTTPException(409, 'Нет подходящей активной заявки для оповещения')

    workers = await db.get_workers_for_shout(order_id=order.id)
    if len(workers) <= 1:
        raise HTTPException(409, 'Недостаточно исполнителей для рассылки')

    shout_id = await db.set_shout_stat(sender_tg_id=user.tg_id, order_id=order.id)

    safe_text = html_module.escape(body.text)
    shout_text = txt.shout_text(
        sender_full_name=html_module.escape(foreman.full_name),
        text=safe_text,
    )

    bot_token = config.bot_token
    if not bot_token:
        raise HTTPException(500, 'BOT_TOKEN не задан')

    max_bot = None
    if config.max_bot_token:
        try:
            from maxapi import Bot as MaxBot

            max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
        except Exception:
            max_bot = None

    bot = Bot(token=bot_token.get_secret_value())
    count = 0
    try:
        for worker in workers:
            if worker.tg_id and worker.tg_id == user.tg_id:
                continue
            sent = False
            if worker.tg_id and worker.tg_id != 0:
                try:
                    await bot.send_message(
                        chat_id=worker.tg_id,
                        text=shout_text,
                        parse_mode=ParseMode.HTML,
                        protect_content=True,
                    )
                    sent = True
                except Exception:
                    logging.exception('shout telegram send')
            if max_bot and worker.max_id and worker.max_id > 1:
                try:
                    await max_bot.send_message(user_id=worker.max_id, text=shout_text)
                    sent = True
                except Exception as e:
                    logging.warning('Max shout: %s', e)
            if sent:
                count += 1
    finally:
        await bot.session.close()
        if max_bot:
            await max_bot.close_session()

    await db.update_shout_workers(shout_id=shout_id, workers_count=count)
    return MessageResponse(message=f'Сообщение отправлено ({count} доставок)')


@router.get('/shout/history', response_model=list[ShoutItemOut])
async def shout_history(user: Annotated[User, Depends(get_current_foreman)]):
    rows = await db.get_sender_shouts(sender_tg_id=user.tg_id)
    out: list[ShoutItemOut] = []
    for row in rows:
        order = await db.get_order(order_id=row.order_id)
        if not order:
            continue
        out.append(
            ShoutItemOut(
                id=row.id,
                order_id=row.order_id,
                workers_reached=row.workers,
                views=row.views,
                job_name=order.job_name,
                order_date=order.date,
                city=order.city,
            )
        )
    out.sort(key=lambda x: x.id, reverse=True)
    return out


# ── Coordinator (supervisor) ────────────────────────────────


@router.get('/coordinator/cities', response_model=list[CoordinatorCityOut])
async def coordinator_cities(_: Annotated[User, Depends(get_current_supervisor)]):
    names = await db.get_cities_name()
    return [CoordinatorCityOut(name=n) for n in names]


@router.get('/coordinator/customers', response_model=list[CoordinatorCustomerOut])
async def coordinator_customers(
    _: Annotated[User, Depends(get_current_supervisor)],
    city: str,
):
    customers = await db.get_customers_by_city(city=city)
    out: list[CoordinatorCustomerOut] = []
    for c in customers:
        out.append(
            CoordinatorCustomerOut(
                customer_id=c.id,
                organization=c.organization,
            )
        )
    return out


@router.get('/coordinator/orders', response_model=list[CoordinatorOrderOut])
async def coordinator_orders(
    _: Annotated[User, Depends(get_current_supervisor)],
    customer_id: int,
):
    orders = await db.get_orders_for_supervisor(customer_id=customer_id)
    return [
        CoordinatorOrderOut(
            id=o.id,
            job_name=o.job_name,
            date=o.date,
            city=o.city,
            in_progress=o.in_progress,
            moderation=o.moderation,
        )
        for o in orders
    ]
