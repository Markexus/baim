from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_optional_current_user_id
from app.core.config import settings
from app.db.session import get_db_session
from app.models import Product, ProductComment, User
from app.schemas.product import (
    ProductAvailabilityCalendarResponse,
    ProductAvailabilityResponse,
    ProductFacetsResponse,
    ProductQueryParams,
    ProductResponse,
)
from app.schemas.product_comment import ProductCommentCreate, ProductCommentResponse
from app.services import product as product_service

router = APIRouter(prefix="/product", tags=["product"])

OptionalUser = Annotated[int | None, Depends(get_optional_current_user_id)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[int, Depends(get_current_user_id)]


def not_found(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


def invalid_request(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
    )


@router.get("", response_model=list[ProductResponse])
async def get_products(
    params: Annotated[ProductQueryParams, Query()],
    user_id: OptionalUser,
    session: DatabaseSession,
):
    return await product_service.get_products(session, params, user_id)


@router.get("/count", response_model=ProductFacetsResponse)
async def get_categories_count(
    params: Annotated[ProductQueryParams, Query()],
    session: DatabaseSession,
):
    return await product_service.get_product_facets(session, params)


@router.get("/{product_slug}", response_model=ProductResponse)
async def get_product(
    product_slug: str,
    user_id: OptionalUser,
    session: DatabaseSession,
):
    try:
        return await product_service.get_product(session, product_slug, user_id)
    except product_service.ProductNotFoundError as error:
        raise not_found(error) from error


async def _comment_product(session: AsyncSession, product_slug: str) -> Product:
    product = await session.scalar(
        select(Product).where(
            Product.slug == product_slug, Product.visibility_status.is_(True)
        )
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_slug}/comments", response_model=list[ProductCommentResponse])
async def get_product_comments(
    product_slug: str,
    session: DatabaseSession,
) -> list[ProductComment]:
    product = await _comment_product(session, product_slug)
    query = select(ProductComment).where(ProductComment.product_id == product.id)
    if not settings.csrf_demo_enabled:
        query = query.where(ProductComment.is_demo.is_(False))
    query = query.order_by(ProductComment.created_at.desc(), ProductComment.id.desc())
    return list(
        await session.scalars(query.limit(100))
    )


@router.post(
    "/{product_slug}/comments",
    response_model=ProductCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product_comment(
    product_slug: str,
    payload: ProductCommentCreate,
    user_id: CurrentUser,
    session: DatabaseSession,
) -> ProductComment:
    product = await _comment_product(session, product_slug)
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    author_name = " ".join(
        part for part in (user.first_name, user.last_name) if part
    ) or user.email.split("@", 1)[0]
    comment = ProductComment(
        product_id=product.id,
        author_id=user.id,
        author_name=author_name[:200],
        body=payload.body,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


@router.get("/{product_slug}/accessories", response_model=list[ProductResponse])
async def get_product_accessories(
    product_slug: str,
    user_id: OptionalUser,
    session: DatabaseSession,
) -> list[ProductResponse]:
    try:
        return await product_service.get_product_accessories(
            session, product_slug, user_id
        )
    except product_service.ProductNotFoundError as error:
        raise not_found(error) from error


@router.get("/{product_slug}/availability", response_model=ProductAvailabilityResponse)
async def get_product_availability(
    product_slug: str,
    start_date: date,
    end_date: date,
    session: DatabaseSession,
    size: str | None = None,
):
    try:
        return await product_service.get_product_availability(
            session,
            product_slug,
            start_date,
            end_date,
            size,
        )
    except product_service.InvalidDateRangeError as error:
        raise invalid_request(error) from error
    except product_service.ProductNotFoundError as error:
        raise not_found(error) from error


@router.get(
    "/{product_slug}/availability-calendar",
    response_model=ProductAvailabilityCalendarResponse,
)
async def get_product_availability_calendar(
    product_slug: str,
    session: DatabaseSession,
    quantity: Annotated[int, Query(ge=1, le=100)] = 1,
    size: str | None = None,
) -> ProductAvailabilityCalendarResponse:
    try:
        return await product_service.get_product_availability_calendar(
            session,
            product_slug,
            quantity,
            size,
        )
    except product_service.ProductNotFoundError as error:
        raise not_found(error) from error
