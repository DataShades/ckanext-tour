from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Self

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Query, relationship

from ckan import model, types
from ckan.model.types import make_uuid
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)


class Tour(tk.BaseModel):
    __tablename__ = "tour"

    class State:
        active = "active"
        inactive = "inactive"

    id = Column(Text, primary_key=True, default=make_uuid)

    title = Column(Text, nullable=False)
    state = Column(Text, nullable=False, default=State.active)
    author_id = Column(ForeignKey(model.User.id, ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    anchor = Column(Text, nullable=False)
    page = Column(Text, nullable=True)

    user = relationship(model.User)

    # Loaded once per instance (batched across a result set thanks to
    # ``lazy="selectin"``) and ordered in SQL, instead of re-querying and
    # re-sorting in Python on every ``tour.steps`` access.
    steps = relationship(
        "TourStep",
        order_by="TourStep.index",
        primaryjoin="Tour.id == TourStep.tour_id",
        foreign_keys="TourStep.tour_id",
        back_populates="tour",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self):
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
        query: Query = model.Session.query(cls).filter(cls.id == tour_id)

        return query.one_or_none()

    @classmethod
    def get_by_anchor(cls, tour_anchor: str) -> Self | None:
        query: Query = model.Session.query(cls).filter(cls.anchor == tour_anchor)

        return query.one_or_none()

    @classmethod
    def all(cls) -> list[Tour]:
        query: Query = model.Session.query(cls).order_by(cls.created_at.desc())

        return query.all()


class TourStep(tk.BaseModel):
    __tablename__ = "tour_step"

    class Position:
        bottom = "bottom"
        top = "top"
        right = "right"
        left = "left"

    id = Column(Text, primary_key=True, default=make_uuid)

    index = Column(Integer)
    title = Column(Text, nullable=True)
    element = Column(Text)
    intro = Column(Text, nullable=True)
    position = Column(Text, default=Position.bottom)
    tour_id = Column(Text, ForeignKey("tour.id", ondelete="CASCADE"), index=True)
    image_id = Column(Text, nullable=True)

    tour = relationship("Tour", back_populates="steps")

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
        query: Query = model.Session.query(cls).filter(cls.id == tour_step_id)

        return query.one_or_none()

    @classmethod
    def get_by_tour(cls, tour_id: str) -> list[Self]:
        query: Query = model.Session.query(cls).filter(cls.tour_id == tour_id)

        return query.all()

    @property
    def image(self) -> str:
        file_info = tk.h.files_link_details(self.image_id or "")

        if not file_info:
            return ""

        return file_info["href"]

    def dictize(self, context):
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
