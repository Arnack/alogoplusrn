from fastapi import APIRouter

from web_api.routers import (
    applications,
    auth,
    device_tokens,
    extras,
    meta,
    notifications,
    profile,
    promotions,
    register,
    search,
)


def build_api_router() -> APIRouter:
    root = APIRouter()
    root.include_router(auth.router, prefix='/auth', tags=['auth'])
    root.include_router(register.router, prefix='/register', tags=['register'])
    root.include_router(meta.router, prefix='/meta', tags=['meta'])
    root.include_router(profile.router, prefix='/users', tags=['users'])
    root.include_router(search.router, prefix='/search', tags=['search'])
    root.include_router(applications.router, prefix='/applications', tags=['applications'])
    root.include_router(notifications.router, prefix='/notifications', tags=['notifications'])
    root.include_router(device_tokens.router, prefix='/device-tokens', tags=['device-tokens'])
    root.include_router(extras.router, prefix='/extras', tags=['extras'])
    root.include_router(promotions.router, prefix='/promotions', tags=['promotions'])
    return root
