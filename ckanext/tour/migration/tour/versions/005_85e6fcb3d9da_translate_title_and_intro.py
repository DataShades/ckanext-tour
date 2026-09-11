"""Store tour/step title and step intro as per-locale JSON objects

Revision ID: 85e6fcb3d9da
Revises: a1c8e35f9d02
Create Date: 2026-09-11 00:00:00.000000

* ``tour.title``, ``tour_step.title``, ``tour_step.intro``: ``Text`` -> ``JSONB``

No plugin using this schema has shipped translated content yet, so existing
values are dropped rather than migrated -- a fresh, empty JSONB column
replaces each one.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "85e6fcb3d9da"
down_revision = "a1c8e35f9d02"
branch_labels = None
depends_on = None

# (table, column, nullable) -- nullability matches each column's original
# (pre-JSONB) definition, so downgrade restores it exactly.
_TRANSLATED_COLUMNS = (
    ("tour", "title", False),
    ("tour_step", "title", True),
    ("tour_step", "intro", True),
)


def _column_types(table: str) -> dict[str, type]:
    return {c["name"]: type(c["type"]) for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    types_by_table = {table: _column_types(table) for table, _, _ in _TRANSLATED_COLUMNS}

    for table, column, nullable in _TRANSLATED_COLUMNS:
        if types_by_table[table][column] is not JSONB:
            op.drop_column(table, column)
            op.add_column(table, sa.Column(column, JSONB, nullable=nullable, server_default="{}"))


def downgrade() -> None:
    types_by_table = {table: _column_types(table) for table, _, _ in _TRANSLATED_COLUMNS}

    for table, column, nullable in _TRANSLATED_COLUMNS:
        if types_by_table[table][column] is JSONB:
            op.drop_column(table, column)
            default = "" if not nullable else None
            op.add_column(table, sa.Column(column, sa.Text, nullable=nullable, server_default=default))
