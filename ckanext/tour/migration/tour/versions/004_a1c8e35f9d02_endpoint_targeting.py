"""Switch tour targeting from a CSS anchor to a Flask endpoint

Revision ID: a1c8e35f9d02
Revises: b7e2d9a4c150
Create Date: 2026-09-08 00:00:00.000000

* drop ``tour.anchor``
* rename ``tour.page`` -> ``tour.endpoint``
* add ``tour.auto_start`` (bool)
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c8e35f9d02"
down_revision = "b7e2d9a4c150"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("tour")}


def upgrade() -> None:
    columns = _columns()

    if "anchor" in columns:
        op.drop_column("tour", "anchor")

    if "page" in columns and "endpoint" not in columns:
        op.alter_column("tour", "page", new_column_name="endpoint")

    if "auto_start" not in columns:
        op.add_column(
            "tour",
            sa.Column(
                "auto_start",
                sa.Boolean,
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    columns = _columns()

    if "auto_start" in columns:
        op.drop_column("tour", "auto_start")

    if "endpoint" in columns and "page" not in columns:
        op.alter_column("tour", "endpoint", new_column_name="page")

    if "anchor" not in columns:
        op.add_column(
            "tour",
            sa.Column("anchor", sa.Text, nullable=True, server_default=""),
        )
