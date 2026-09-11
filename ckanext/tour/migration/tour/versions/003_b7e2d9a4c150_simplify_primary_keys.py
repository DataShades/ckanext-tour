"""Tidy up the tour data model

Revision ID: b7e2d9a4c150
Revises: f3a9c1e7b204
Create Date: 2026-09-08 00:00:00.000000

* replace the composite primary keys ``tour(id, author_id)`` and
  ``tour_step(id, tour_id)`` — ``id`` is already globally unique — with a
  plain ``id`` PK
* drop the duplicate ``tour_step`` foreign key
* index ``tour.author_id``
* store ``tour.created_at`` / ``modified_at`` as ``timestamptz``
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7e2d9a4c150"
down_revision = "f3a9c1e7b204"
branch_labels = None
depends_on = None

AUTHOR_INDEX = "ix_tour_author_id"


def _set_pk(table: str, columns: list[str]) -> None:
    insp = sa.inspect(op.get_bind())
    pk = insp.get_pk_constraint(table)

    if sorted(pk["constrained_columns"]) == sorted(columns):
        return

    if pk["name"]:
        op.drop_constraint(pk["name"], table, type_="primary")

    op.create_primary_key(f"{table}_pkey", table, columns)


def _tour_index_names() -> set[str]:
    return {ix["name"] for ix in sa.inspect(op.get_bind()).get_indexes("tour")}


def upgrade() -> None:
    _set_pk("tour", ["id"])
    _set_pk("tour_step", ["id"])

    # tour_step's FK to tour was declared twice (inline column + explicit
    # `tour_step_fk`); keep one
    insp = sa.inspect(op.get_bind())
    tour_fks = [fk for fk in insp.get_foreign_keys("tour_step") if fk["referred_table"] == "tour"]
    for fk in tour_fks[1:]:
        if fk["name"]:
            op.drop_constraint(fk["name"], "tour_step", type_="foreignkey")

    if AUTHOR_INDEX not in _tour_index_names():
        op.create_index(AUTHOR_INDEX, "tour", ["author_id"])

    for column in ("created_at", "modified_at"):
        op.alter_column(
            "tour",
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for column in ("created_at", "modified_at"):
        op.alter_column("tour", column, type_=sa.DateTime(timezone=False))

    if AUTHOR_INDEX in _tour_index_names():
        op.drop_index(AUTHOR_INDEX, table_name="tour")

    _set_pk("tour_step", ["id", "tour_id"])
    _set_pk("tour", ["id", "author_id"])
