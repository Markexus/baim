"""Verify the normal email setting and its opt-in CSRF failure mode."""

from collections.abc import AsyncIterator
from dataclasses import replace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.routes import account_email
from app.core.config import settings
from app.db.session import get_db_session
from app.models import User
from tests.support import SeededUser


async def test_email_setting_requires_csrf_unless_demo_enabled(
    client: AsyncClient,
    test_user: SeededUser,
    test_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    login = await client.post(
        "/auth/login",
        json={"email": test_user.email, "password": test_user.password},
    )
    assert login.status_code == 200
    refresh_token = login.cookies["refresh_token"]
    csrf_token = login.cookies["csrf_token"]

    demo_app = FastAPI()
    demo_app.include_router(account_email.router)

    async def test_db_session() -> AsyncIterator[AsyncSession]:
        async with test_session_factory() as session:
            yield session

    demo_app.dependency_overrides[get_db_session] = test_db_session
    transport = ASGITransport(app=demo_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1:8000",
    ) as attacker:
        form = {"email": "attacker@example.com"}
        monkeypatch.setattr(
            account_email, "settings", replace(settings, csrf_demo_enabled=False)
        )
        protected = await attacker.post(
            "/auth/account/email",
            data=form,
            headers={
                "Cookie": f"refresh_token={refresh_token}",
                "Origin": "http://127.0.0.1:9000",
            },
        )
        assert protected.status_code == 403

        normal_change = await attacker.post(
            "/auth/account/email",
            data={"email": "new-owner@example.org"},
            headers={
                "Cookie": f"refresh_token={refresh_token}; csrf_token={csrf_token}",
                "X-CSRF-Token": csrf_token,
                "Origin": "http://127.0.0.1:5173",
            },
        )
        assert normal_change.status_code == 204

        async with test_session_factory() as session:
            current_email = await session.scalar(
                select(User.email).where(User.id == test_user.id)
            )
        assert current_email == "new-owner@example.org"

        monkeypatch.setattr(
            account_email, "settings", replace(settings, csrf_demo_enabled=True)
        )
        response = await attacker.post(
            "/auth/account/email",
            data=form,
            headers={
                "Cookie": f"refresh_token={refresh_token}",
                "Origin": "http://127.0.0.1:9000",
            },
        )
        assert response.status_code == 204

        missing_cookie = await attacker.post("/auth/account/email", data=form)
        assert missing_cookie.status_code == 401

    async with test_session_factory() as session:
        user = await session.scalar(select(User).where(User.id == test_user.id))

    assert user is not None
    assert user.email == "attacker@example.com"
