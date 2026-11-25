"""Add Mareczek's local CSRF demonstration comment to a seeded product."""

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_factory, engine
from app.models import Product, ProductComment

DEMO_PRODUCT_SLUG = "rower-szosowy"
DEMO_AUTHOR = "Mareczek"
DEMO_BODY = (
    "Kod promocyjny MAREK20 na wypożyczenie! Szczegóły promocji: "
    "http://127.0.0.1:9000/attack.html"
)


async def seed_csrf_demo_comment() -> None:
    if not settings.csrf_demo_enabled:
        raise RuntimeError(
            "Set CSRF_DEMO_ENABLED=true before seeding the demo comment"
        )

    async with async_session_factory.begin() as session:
        product = await session.scalar(
            select(Product).where(Product.slug == DEMO_PRODUCT_SLUG)
        )
        if product is None:
            raise RuntimeError(f"Seed product {DEMO_PRODUCT_SLUG!r} is missing")

        existing = await session.scalar(
            select(ProductComment).where(
                ProductComment.product_id == product.id,
                ProductComment.is_demo.is_(True),
                ProductComment.author_name == DEMO_AUTHOR,
            )
        )
        if existing is None:
            session.add(
                ProductComment(
                    product_id=product.id,
                    author_name=DEMO_AUTHOR,
                    body=DEMO_BODY,
                    is_demo=True,
                )
            )
        else:
            existing.body = DEMO_BODY


async def main() -> None:
    try:
        await seed_csrf_demo_comment()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
