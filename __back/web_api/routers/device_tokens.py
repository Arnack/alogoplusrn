from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import database as db
from database.models import User
from web_api.deps import get_current_worker

router = APIRouter()


class RegisterTokenBody(BaseModel):
    token: str = Field(..., min_length=1, max_length=200)


@router.post('', status_code=204)
async def register_device_token(
    body: RegisterTokenBody,
    user: Annotated[User, Depends(get_current_worker)],
):
    await db.upsert_device_token(user.id, body.token)


@router.delete('/{token}', status_code=204)
async def deregister_device_token(
    token: str,
    user: Annotated[User, Depends(get_current_worker)],
):
    await db.delete_device_token(token)
