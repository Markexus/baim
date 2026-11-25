from dataclasses import replace

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.routes import product as product_routes
from app.core.config import settings
from app.models import Product, ProductComment
from tests.support import SeededUser


async def test_product_comments_can_be_read_and_posted_by_signed_in_user(
    client: AsyncClient,
    test_user: SeededUser,
    test_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slug = "comment-test-product"
    async with test_session_factory.begin() as session:
        product = Product(
            name="Comment test product",
            slug=slug,
            price=10,
            visibility_status=True,
        )
        session.add(product)
        await session.flush()
        session.add(
            ProductComment(
                product_id=product.id,
                author_name="Mareczek",
                body="Kod MAREK20: http://127.0.0.1:9000/attack.html",
                is_demo=True,
            )
        )

    try:
        monkeypatch.setattr(
            product_routes, "settings", replace(settings, csrf_demo_enabled=False)
        )
        anonymous = await client.post(f"/product/{slug}/comments", json={"body": "Hi"})
        assert anonymous.status_code == 401

        login = await client.post(
            "/auth/login",
            json={"email": test_user.email, "password": test_user.password},
        )
        assert login.status_code == 200

        posted = await client.post(
            f"/product/{slug}/comments",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            json={"body": "  Dobra oferta  "},
        )
        assert posted.status_code == 201
        assert posted.json()["body"] == "Dobra oferta"

        comments = await client.get(f"/product/{slug}/comments")
        assert comments.status_code == 200
        assert [comment["body"] for comment in comments.json()] == ["Dobra oferta"]

        monkeypatch.setattr(
            product_routes, "settings", replace(settings, csrf_demo_enabled=True)
        )
        demo_comments = await client.get(f"/product/{slug}/comments")
        assert demo_comments.status_code == 200
        assert len(demo_comments.json()) == 2
        assert any(
            comment["author_name"] == "Mareczek" for comment in demo_comments.json()
        )

        async with test_session_factory() as session:
            stored = await session.scalar(
                select(ProductComment).where(ProductComment.id == posted.json()["id"])
            )
            assert stored is not None
            assert stored.is_demo is False
    finally:
        async with test_session_factory.begin() as session:
            product = await session.scalar(select(Product).where(Product.slug == slug))
            if product is not None:
                await session.delete(product)
