"""Email setting used by the profile and the local CSRF demonstration."""

import datetime
from typing import Annotated
from urllib.parse import parse_qs

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_helpers import require_csrf, unauthorized
from app.core.config import settings
from app.core.email import normalize_email
from app.core.tokens import decode_refresh_token
from app.db.session import get_db_session
from app.models import AuthSession, User

router = APIRouter(prefix="/auth/account", tags=["account"])


class ChangeEmailForm(BaseModel):
    email: EmailStr


@router.post("/email", status_code=status.HTTP_204_NO_CONTENT)
async def change_email_from_cookie(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> None:
    """Change the login email using the existing session cookie.

    The ordinary profile form sends the CSRF header. The local demo flag turns
    that check off so the same account action accepts an attacker's form.
    """
    if not settings.csrf_demo_enabled:
        require_csrf(request)

    if refresh_token is None:
        raise unauthorized("Authentication credentials were not provided")

    try:
        claims = decode_refresh_token(refresh_token)
    except jwt.InvalidTokenError:
        raise unauthorized("Invalid token") from None

    now = datetime.datetime.now(datetime.UTC)
    auth_session_id = await session.scalar(
        select(AuthSession.id).where(
            AuthSession.id == claims.session_id,
            AuthSession.user_id == claims.user_id,
            AuthSession.current_jti == claims.token_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    )
    if auth_session_id is None:
        raise unauthorized("Invalid token")

    content_type = request.headers.get("content-type", "").split(";", 1)[0]
    if content_type.strip().lower() != "application/x-www-form-urlencoded":
        raise HTTPException(status_code=415, detail="Expected a browser form")

    raw_body = await request.body()
    if len(raw_body) > 1024:
        raise HTTPException(status_code=413, detail="Form is too large")

    try:
        values = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        email_values = values.get("email", [])
        if len(email_values) != 1:
            raise ValueError("Expected one email address")
        form = ChangeEmailForm.model_validate({"email": email_values[0]})
    except (UnicodeDecodeError, ValidationError, ValueError) as error:
        raise HTTPException(status_code=422, detail="Invalid email") from error

    user = await session.scalar(select(User).where(User.id == claims.user_id).with_for_update())
    if user is None:
        raise unauthorized("Invalid token")

    user.email = normalize_email(str(form.email))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered") from None
