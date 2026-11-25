"""add product comments

Revision ID: a17c9e4d2b60
Revises: 4e2f8a7c1d90
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a17c9e4d2b60"
down_revision: str | Sequence[str] | None = "4e2f8a7c1d90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_product_comments_product_id", "product_comments", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_product_comments_product_id", table_name="product_comments")
    op.drop_table("product_comments")
