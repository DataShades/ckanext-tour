from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Self, cast

from sqlalchemy import CursorResult, ForeignKey, Text, select, update
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ckan import model, types
from ckan.model import User
from ckan.model.types import make_uuid
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)


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
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    modified_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
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

    def delete(self) -> None:
        model.Session().autoflush = False
        model.Session.delete(self)

    def dictize(self, context: types.Context) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author_id": self.author_id,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "anchor": self.anchor or "",
            "page": self.page or "",
            "steps": [step.dictize(context) for step in self.steps],
        }

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

        stmt = (
            update(cls)
            .where(cls.id.in_(ids))
            .values(state=state, modified_at=datetime.utcnow())
        )
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
    tour_id: Mapped[str | None] = mapped_column(
        Text,
        ForeignKey("tour.id", ondelete="CASCADE"),
        index=True,
    )
    image_id: Mapped[str | None] = mapped_column(Text)

    tour: Mapped[Tour | None] = relationship(back_populates="steps")

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

    @property
    def image(self) -> str:
        file_info = tk.h.files_link_details(self.image_id or "")

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
