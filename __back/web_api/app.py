from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import database as db
from config_reader import config

from web_api.rate_limit import connect_redis
from web_api.routers import build_api_router

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_BASE_DIR, 'frontend')
# Статика панели: frontend/static (иконки). Лого страницы — GET /api/v1/meta/bot-logo (фото бота из Telegram); опционально /static/logo.png как запасной файл.
_FRONTEND_STATIC_DIR = os.path.join(_FRONTEND_DIR, 'static')
_LEGACY_STATIC_DIR = os.path.join(_BASE_DIR, 'static')


def _cors_origins() -> list[str]:
    raw = (config.web_api_cors_origins or '*').strip()
    if raw == '*':
        return ['*']
    return [p.strip() for p in raw.split(',') if p.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_models()
    app.state.redis = await connect_redis()
    try:
        yield
    finally:
        r = getattr(app.state, 'redis', None)
        if r is not None:
            await r.aclose()


app = FastAPI(
    title='AlgoritmPlus Web API',
    description='Панель исполнителя: этап 1 (авторизация и данные через существующую БД).',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts='*')
_origins = _cors_origins()
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials='*' not in _origins,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware('http')
async def www_redirect(request: Request, call_next):
    host = request.headers.get('host', '')
    if host.startswith('www.'):
        url = request.url.replace(netloc=host[4:])
        return RedirectResponse(url=str(url), status_code=301)
    return await call_next(request)

app.include_router(build_api_router(), prefix='/api/v1')


@app.get('/health')
async def health():
    return {'status': 'ok'}


# ── Serve static assets: приоритет frontend/static (иконки, лого панели) ──
_static_mount = _FRONTEND_STATIC_DIR if os.path.isdir(_FRONTEND_STATIC_DIR) else _LEGACY_STATIC_DIR
if os.path.isdir(_static_mount):
    app.mount('/static', StaticFiles(directory=_static_mount), name='static')

_ICONS_DIR = os.path.join(_FRONTEND_DIR, 'icons')
if os.path.isdir(_ICONS_DIR):
    app.mount('/icons', StaticFiles(directory=_ICONS_DIR), name='icons')


# ── SEO: явные маршруты для robots.txt, sitemap.xml и icons ──
@app.get('/robots.txt', include_in_schema=False)
async def robots_txt():
    path = os.path.join(_FRONTEND_DIR, 'robots.txt')
    if os.path.isfile(path):
        return FileResponse(path, media_type='text/plain')
    return HTMLResponse('User-agent: *\nAllow: /\n', media_type='text/plain')


@app.get('/sitemap.xml', include_in_schema=False)
async def sitemap_xml():
    path = os.path.join(_FRONTEND_DIR, 'sitemap.xml')
    if os.path.isfile(path):
        return FileResponse(path, media_type='application/xml')
    return HTMLResponse('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>', media_type='application/xml')


# SEO-страницы: отдаём отдельные HTML файлы с контентом (не SPA)
_SEO_PAGES = {
    'samozanyatye': 'samozanyatye.html',
    'zayavki': 'zayavki.html',
    'podrabotka': 'podrabotka.html',
    'kak-nachat': 'kak-nachat.html',
    'platforma': 'platforma.html',
    'blog': 'blog.html',
}

for _slug, _filename in _SEO_PAGES.items():
    _html_path = os.path.join(_FRONTEND_DIR, _filename)
    if os.path.isfile(_html_path):
        def _make_seo_handler(p):
            async def _handler():
                return FileResponse(p, media_type='text/html')
            return _handler
        app.add_api_route(f'/{_slug}', _make_seo_handler(_html_path), methods=['GET'], include_in_schema=False)


# ── PDF-документы: пользовательское соглашение и политика конфиденциальности ──
_PDF_DOCS = {
    'user-agreement': 'user_agreement.pdf',
    'docs/privacy-policy': 'privacy_policy.pdf',
}

for _route, _pdf_filename in _PDF_DOCS.items():
    _pdf_path = os.path.join(_FRONTEND_STATIC_DIR, _pdf_filename)
    if os.path.isfile(_pdf_path):
        def _make_pdf_handler(p):
            async def _handler():
                return FileResponse(p, media_type='application/pdf')
            return _handler
        app.add_api_route(f'/{_route}', _make_pdf_handler(_pdf_path), methods=['GET'], include_in_schema=False)


_STATIC_EXTENSIONS = {'.png', '.svg', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf', '.jpg', '.jpeg', '.webp'}
_CACHE_HEADERS = {'Cache-Control': 'public, max-age=2592000'}  # 30 дней


# ── Страницы ошибок ───────────────────────────────────────────
_ERROR_HTML = '''<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f5f5;color:#1c1c1e}}
.c{{text-align:center}}.c h1{{font-size:4rem;margin:0;color:#007aff}}.c p{{font-size:1.2rem;color:#6c6c70}}
a{{color:#007aff;text-decoration:none;font-weight:600;padding:12px 24px;border:2px solid #007aff;border-radius:12px;display:inline-block;margin-top:20px}}
a:hover{{background:#007aff;color:#fff}}</style></head>
<body><div class="c"><h1>{code}</h1><p>{message}</p><a href="/">На главную</a></div></body></html>'''


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return HTMLResponse(
        _ERROR_HTML.format(title='Ошибка сервера', code='500', message='Внутренняя ошибка сервера. Попробуйте позже.'),
        status_code=500,
    )


# ── SPA catch-all: must be LAST ──────────────────────────────
if os.path.isdir(_FRONTEND_DIR):
    @app.get('/{full_path:path}', include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        candidate = os.path.join(_FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            ext = os.path.splitext(full_path)[1].lower()
            headers = _CACHE_HEADERS if ext in _STATIC_EXTENSIONS else {}
            return FileResponse(candidate, headers=headers)
        # Запросы к несуществующим файлам (с расширением) — 404
        if full_path and '.' in full_path.split('/')[-1]:
            return HTMLResponse(
                _ERROR_HTML.format(title='Не найдено', code='404', message='Страница не найдена.'),
                status_code=404,
            )
        # Всё остальное — SPA
        return FileResponse(os.path.join(_FRONTEND_DIR, 'index.html'))
