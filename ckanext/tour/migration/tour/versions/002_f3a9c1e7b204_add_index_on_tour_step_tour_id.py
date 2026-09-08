"""Add index on tour_step.tour_id

Revision ID: f3a9c1e7b204
Revises: c9e5d4235e58
Create Date: 2026-09-08 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3a9c1e7b204"
down_revision = "c9e5d4235e58"
branch_labels = None
depends_on = None

INDEX_NAME = "ix_tour_step_tour_id"
TABLE_NAME = "tour_step"


def upgrade():
    bind = op.get_bind()
    indexes = {ix["name"] for ix in sa.inspect(bind).get_indexes(TABLE_NAME)}

    if INDEX_NAME not in indexes:
        op.create_index(INDEX_NAME, TABLE_NAME, ["tour_id"], unique=False)


def downgrade():
    bind = op.get_bind()
    indexes = {ix["name"] for ix in sa.inspect(bind).get_indexes(TABLE_NAME)}

    if INDEX_NAME in indexes:
        op.drop_index(INDEX_NAME, table_name=TABLE_NAME)
