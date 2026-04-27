"""
Workaround для бага maxapi: bot.session создаётся с base_url="https://platform-api.max.ru",
поэтому upload_file_buffer падает с AssertionError когда пытается POST на абсолютный URL
upload-сервера через эту же сессию.

Решение: загружаем файл через отдельную aiohttp.ClientSession без base_url,
затем вручную формируем AttachmentUpload с полученным токеном.
"""
import logging
import mimetypes
from json import loads, JSONDecodeError
from uuid import uuid4

import aiohttp
import puremagic

from maxapi.types.attachments.upload import AttachmentPayload, AttachmentUpload
from maxapi.enums.upload_type import UploadType


async def upload_buffer(bot, buffer: bytes, upload_type: UploadType, filename: str = None) -> AttachmentUpload | None:
    """
    Загружает bytes-буфер в Max через отдельную сессию (без base_url).
    Возвращает AttachmentUpload готовый для передачи в attachments=[...].
    """
    try:
        upload_info = await bot.get_upload_url(upload_type)
        upload_url = upload_info.url
        upload_token = getattr(upload_info, 'token', None)
    except Exception as e:
        logging.error(f'[max_upload] get_upload_url failed: {e}')
        return None

    try:
        try:
            matches = puremagic.magic_string(buffer[:4096])
            mime_type = matches[0].mime_type if matches else f'{upload_type.value}/*'
            if not mime_type or not isinstance(mime_type, str):
                mime_type = f'{upload_type.value}/*'
        except Exception:
            mime_type = f'{upload_type.value}/*'

        ext = mimetypes.guess_extension(mime_type) or ''
        basename = (filename or str(uuid4())) + ext

        form = aiohttp.FormData(quote_fields=False)
        form.add_field(
            name='data',
            value=buffer,
            filename=basename,
            content_type=mime_type,
        )

        # Отдельная сессия без base_url — обходим баг maxapi
        async with aiohttp.ClientSession() as session:
            async with session.post(url=upload_url, data=form) as resp:
                response_text = await resp.text()

    except Exception as e:
        logging.error(f'[max_upload] upload POST failed: {e}')
        return None

    try:
        if upload_type in (UploadType.VIDEO, UploadType.AUDIO):
            if not upload_token:
                logging.error('[max_upload] VIDEO/AUDIO: no token in upload_info')
                return None
            token = upload_token
        elif upload_type == UploadType.FILE:
            data = loads(response_text)
            token = data.get('token')
            if not token:
                logging.error(f'[max_upload] FILE: no token in response: {response_text[:200]}')
                return None
        elif upload_type == UploadType.IMAGE:
            data = loads(response_text)
            photos = data.get('photos', {})
            if not photos:
                logging.error(f'[max_upload] IMAGE: no photos in response: {response_text[:200]}')
                return None
            first = next(iter(photos.values()))
            token = first.get('token') if isinstance(first, dict) else None
            if not token:
                logging.error(f'[max_upload] IMAGE: no token in photos: {response_text[:200]}')
                return None
        else:
            logging.error(f'[max_upload] unsupported type: {upload_type}')
            return None
    except (JSONDecodeError, Exception) as e:
        logging.error(f'[max_upload] parse response failed: {e}, response: {response_text[:200]}')
        return None

    return AttachmentUpload(type=upload_type, payload=AttachmentPayload(token=token))
