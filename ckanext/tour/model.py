from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Self, cast

from sqlalchemy import (
    CursorResult,
    DateTime,
    ForeignKey,
    Text,
    event,
    func,
    select,
    update,
)
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, Mapper, mapped_column, relationship

from ckan import model, types
from ckan.model import User
from ckan.model.types import make_uuid
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Tour(tk.BaseModel):
    __tablename__ = "tour"

    class State:
        active = "active"
        inactive = "inactive"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=make_uuid)

    title: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, default=State.active)
    author_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey(User.id, ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    anchor: Mapped[str] = mapped_column(Text)
    page: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(User)

    steps: Mapped[list[TourStep]] = relationship(
        order_by="TourStep.index",
        primaryjoin="Tour.id == TourStep.tour_id",
        foreign_keys="TourStep.tour_id",
        back_populates="tour",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Tour(title={self.title})"

    @classmethod
    def create(cls, data_dict: dict[str, Any]) -> Self:
        tour = cls(**data_dict)

        model.Session.add(tour)
        model.Session.commit()

        return tour

    def reload_steps(self) -> None:
        """Drop the cached ``steps`` collection so the next access reloads it.

        ``steps`` is ``lazy="selectin"``, so it is (re)populated whenever this
        ``Tour`` is loaded — which in a create/update flow happens *before* the
        steps are written through ``tour_step_create``. Callers that create or
        change steps and then serialise the tour must call this first.
        """
        model.Session.expire(self, ["steps"])

    def delete(self) -> None:
        model.Session().autoflush = False
        model.Session.delete(self)

    def dictize(
        self,
        context: types.Context,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Serialise the tour.

        ``fields`` (the ``fl`` action argument) optionally restricts the output
        to those keys; names that are not tour fields are ignored, and when
        ``"steps"`` is absent the step collection is not loaded or serialised at
        all. ``None`` returns every field.
        """
        data: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "author_id": self.author_id,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "anchor": self.anchor or "",
            "page": self.page or "",
        }

        if fields is None or "steps" in fields:
            data["steps"] = [step.dictize(context) for step in self.steps]

        if fields is None:
            return data

        return {key: data[key] for key in fields if key in data}

    @classmethod
    def get(cls, tour_id: str) -> Self | None:
        stmt = select(cls).where(cls.id == tour_id)

        return model.Session.scalars(stmt).one_or_none()

    @classmethod
    def get_by_anchor(cls, tour_anchor: str) -> Self | None:
        stmt = select(cls).where(cls.anchor == tour_anchor)

        return model.Session.scalars(stmt).one_or_none()

    @classmethod
    def all(cls) -> list[Self]:
        stmt = select(cls).order_by(cls.created_at.desc())

        return list(model.Session.scalars(stmt).all())

    @classmethod
    def set_state(cls, ids: list[str], state: str) -> int:
        """Bulk-update the state of the given tours in a single statement.

        Returns the number of affected rows. Used by the admin table's bulk
        enable/disable actions instead of running ``tour_update`` (with its full
        dictize) once per row.
        """
        if not ids:
            return 0

        stmt = update(cls).where(cls.id.in_(ids)).values(state=state, modified_at=utcnow())
        result = cast("CursorResult[Any]", model.Session.execute(stmt))
        model.Session.commit()

        return result.rowcount


class TourStep(tk.BaseModel):
    __tablename__ = "tour_step"

    class Position:
        bottom = "bottom"
        top = "top"
        right = "right"
        left = "left"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=make_uuid)

    index: Mapped[int | None] = mapped_column()
    title: Mapped[str | None] = mapped_column(Text)
    element: Mapped[str | None] = mapped_column(Text)
    intro: Mapped[str | None] = mapped_column(Text)
    position: Mapped[str | None] = mapped_column(Text, default=Position.bottom)
    tour_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("tour.id", ondelete="CASCADE"),
        index=True,
    )
    image_id: Mapped[str | None] = mapped_column(Text)

    tour: Mapped[Tour] = relationship(back_populates="steps")

    @classmethod
    def create(cls, data_dict: dict[str, Any]) -> Self:
        tour_step = cls(**data_dict)

        model.Session.add(tour_step)
        model.Session.commit()

        return tour_step

    def delete(self) -> None:
        model.Session().autoflush = False
        model.Session.delete(self)

    @classmethod
    def get(cls, tour_step_id: str) -> Self | None:
        stmt = select(cls).where(cls.id == tour_step_id)

        return model.Session.scalars(stmt).one_or_none()

    @classmethod
    def get_by_tour(cls, tour_id: str) -> list[Self]:
        stmt = select(cls).where(cls.tour_id == tour_id)

        return list(model.Session.scalars(stmt).all())

    @classmethod
    def next_index(cls, tour_id: str) -> int:
        """Index to give the next step appended to ``tour_id``.

        Uses ``MAX(index) + 1`` (via a query, so it does not force-load the
        parent's ``steps`` collection) rather than a count, so gaps left by
        deleted steps don't cause a collision.
        """
        stmt = select(func.max(cls.index)).where(cls.tour_id == tour_id)

        return (model.Session.scalar(stmt) or 0) + 1

    @property
    def image(self) -> str:
        if not self.image_id:
            return ""

        file_info = tk.h.files_link_details(self.image_id)

        if not file_info:
            return ""

        return file_info["href"]

    def dictize(self, context: types.Context) -> dict[str, Any]:
        return {
            "id": self.id,
            "index": self.index,
            "title": self.title,
            "element": self.element,
            "intro": self.intro,
            "position": self.position,
            "tour_id": self.tour_id,
            "image_id": self.image_id,
            "image_url": self.image,
        }


@event.listens_for(TourStep, "after_insert")
@event.listens_for(TourStep, "after_update")
@event.listens_for(TourStep, "after_delete")
def _bump_tour_modified_at(
    mapper: Mapper[TourStep],
    connection: Connection,
    target: TourStep,
) -> None:
    """Keep ``tour.modified_at`` current whenever one of its steps changes.

    A step edited on its own (htmx delete, direct API call) would otherwise
    leave the parent untouched, freezing its position in the admin table.
    """
    if not target.tour_id:
        return

    connection.execute(
        update(Tour)
        .where(Tour.id == target.tour_id)
        .values(modified_at=utcnow()),
    )
