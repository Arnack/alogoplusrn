from __future__ import annotations

import logging
import time
from typing import Annotated

import aiohttp
from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

import database as db
import texts as txt
from database.models import User
from texts.shared import show_rules_text_for_web_panel

from config_reader import config
from web_api.deps import get_current_worker
from web_api.roles import menu_items_for_role, resolve_panel_role
from web_api.schemas import CityOut, MenuItem, PanelMenuResponse, WorkerRulesOut

router = APIRouter()
_log = logging.getLogger(__name__)

# Кэш аватарки бота (то же изображение, что в шапке Telegram Web App у мини-приложения)
_bot_logo_cache: tuple[bytes, str] | None = None
_bot_logo_cache_mono: float = 0.0
_BOT_LOGO_TTL_SEC = 6 * 3600

# Кэш картинки инструкции по подключению к «Рабочие Руки»
_rr_pic_cache: tuple[bytes, str] | None = None
_rr_pic_cache_mono: float = 0.0
_RR_PIC_TTL_SEC = 6 * 3600


@router.get('/bot-logo')
async def bot_logo():
    """Аватар бота из Telegram (getUserProfilePhotos) — без утечки токена в URL для клиента."""
    global _bot_logo_cache, _bot_logo_cache_mono
    now = time.monotonic()
    if _bot_logo_cache is not None and (now - _bot_logo_cache_mono) < _BOT_LOGO_TTL_SEC:
        data, mime = _bot_logo_cache
        return Response(
            content=data,
            media_type=mime,
            headers={'Cache-Control': 'public, max-age=3600'},
        )

    tok = config.bot_token
    if not tok:
        raise HTTPException(503, 'BOT_TOKEN не задан')
    token = tok.get_secret_value()

    async with Bot(token=token) as bot:
        me = await bot.get_me()
        photos = await bot.get_user_profile_photos(me.id, limit=1)
        if not photos.total_count:
            raise HTTPException(404, 'У бота в Telegram не задано фото профиля (BotFather → описание бота)')
        largest = photos.photos[0][-1]
        tf = await bot.get_file(largest.file_id)
        file_path = tf.file_path
    if not file_path:
        raise HTTPException(502, 'Не удалось получить путь к файлу фото бота')

    url = f'https://api.telegram.org/file/bot{token}/{file_path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status != 200:
                    _log.warning('telegram file download failed: %s', resp.status)
                    raise HTTPException(502, 'Не удалось загрузить фото бота')
                data = await resp.read()
                mime = resp.headers.get('Content-Type', 'image/jpeg')
    except HTTPException:
        raise
    except Exception as e:
        _log.exception('bot-logo fetch failed')
        raise HTTPException(502, f'Ошибка загрузки фото: {e!s}') from e

    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(502, 'Слишком большой файл фото бота')

    _bot_logo_cache = (data, mime)
    _bot_logo_cache_mono = now
    return Response(
        content=data,
        media_type=mime,
        headers={'Cache-Control': 'public, max-age=3600'},
    )


@router.get('/rr-partner-pic')
async def rr_partner_pic():
    """Картинка инструкции по подключению к «Рабочие Руки» из настроек бота."""
    global _rr_pic_cache, _rr_pic_cache_mono
    now = time.monotonic()
    if _rr_pic_cache is not None and (now - _rr_pic_cache_mono) < _RR_PIC_TTL_SEC:
        data, mime = _rr_pic_cache
        return Response(content=data, media_type=mime, headers={'Cache-Control': 'public, max-age=3600'})

    tok = config.bot_token
    if not tok:
        raise HTTPException(503, 'BOT_TOKEN не задан')
    token = tok.get_secret_value()

    settings = await db.get_settings()
    if not settings or not settings.rr_partner_pic:
        raise HTTPException(404, 'Картинка не настроена')

    async with Bot(token=token) as bot:
        tf = await bot.get_file(settings.rr_partner_pic)
        file_path = tf.file_path
    if not file_path:
        raise HTTPException(502, 'Не удалось получить путь к файлу')

    url = f'https://api.telegram.org/file/bot{token}/{file_path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status != 200:
                    raise HTTPException(502, 'Не удалось загрузить картинку')
                data = await resp.read()
                mime = resp.headers.get('Content-Type', 'image/jpeg')
    except HTTPException:
        raise
    except Exception as e:
        _log.exception('rr-partner-pic fetch failed')
        raise HTTPException(502, f'Ошибка загрузки: {e!s}') from e

    _rr_pic_cache = (data, mime)
    _rr_pic_cache_mono = now
    return Response(content=data, media_type=mime, headers={'Cache-Control': 'public, max-age=3600'})


@router.get('/cities', response_model=list[CityOut])
async def list_cities():
    cities = await db.get_cities()
    return [CityOut(id=c.id, name=c.city_name) for c in cities]


@router.get('/panel-menu', response_model=PanelMenuResponse)
async def panel_menu(user: Annotated[User, Depends(get_current_worker)]):
    role = await resolve_panel_role(int(user.tg_id))
    items = [MenuItem(id=k, title=v) for k, v in menu_items_for_role(role)]
    return PanelMenuResponse(role=role, items=items)


@router.get('/worker-rules', response_model=WorkerRulesOut)
async def worker_rules(_: Annotated[User, Depends(get_current_worker)]):
    rules = await db.get_rules(rules_for='workers')
    if not rules:
        raise HTTPException(404, txt.no_rules())
    return WorkerRulesOut(
        text=rules.rules,
        date=rules.date,
        formatted_html=show_rules_text_for_web_panel(text=rules.rules, date=rules.date),
    )
