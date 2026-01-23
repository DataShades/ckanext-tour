"""Create Tour, TourStep, TourStepImage tables

Revision ID: c9e5d4235e58
Revises:
Create Date: 2023-07-23 13:20:58.129326

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9e5d4235e58"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tour",
        sa.Column("id", sa.Text, primary_key=True, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("state", sa.Text, nullable=False, server_default="active"),
        sa.Column("anchor", sa.Text, nullable=False),
        sa.Column("page", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "modified_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "author_id",
            sa.Text,
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "tour_step",
        sa.Column("id", sa.Text, primary_key=True, unique=True),
        sa.Column("index", sa.Integer),
        sa.Column("title", sa.Text),
        sa.Column("element", sa.Text),
        sa.Column("intro", sa.Text),
        sa.Column("position", sa.Text),
        sa.Column("image_id", sa.Text, nullable=True),
        sa.Column(
            "tour_id",
            sa.Text,
            sa.ForeignKey("tour.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_foreign_key(
        "tour_step_fk",
        "tour_step",
        "tour",
        ["tour_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("tour_step_fk", "tour_step", type_="foreignkey")

    op.drop_table("tour_step")
    op.drop_table("tour")
