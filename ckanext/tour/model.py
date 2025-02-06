from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ckan import model
from ckan.model.types import make_uuid
from ckan.plugins import toolkit as tk
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Query, relationship
from typing_extensions import Self

from ckanext.tour.exception import TourStepFileError

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

    def __repr__(self):
        return f"Tour(title={self.title})"

    @classmethod
    def create(cls, data_dict) -> Self:
        tour = cls(**data_dict)

        model.Session.add(tour)
        model.Session.commit()

        return tour

    def delete(self) -> None:
        model.Session().autoflush = False
        model.Session.delete(self)

    def dictize(self, context):
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

    @property
    def steps(self) -> list[TourStep]:
        return sorted(
            [request_study for request_study in TourStep.get_by_tour(self.id)],
            key=lambda step: step.index,
        )

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

        return query.all()  # type: ignore


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
    tour_id = Column(Text, ForeignKey("tour.id", ondelete="CASCADE"))

    @classmethod
    def create(cls, data_dict) -> Self:
        tour_step = cls(**data_dict)

        model.Session.add(tour_step)
        model.Session.commit()

        return tour_step

    def delete(self) -> None:
        """Drop step and related image"""
        if self.image:
            self.image.delete()

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
    def image(self) -> TourStepImage:
        return TourStepImage.get_by_step(self.id)

    def dictize(self, context):
        return {
            "id": self.id,
            "index": self.index,
            "title": self.title,
            "element": self.element,
            "intro": self.intro,
            "position": self.position,
            "tour_id": self.tour_id,
            "image": self.image.dictize(context) if self.image else None,
        }


class TourStepImage(tk.BaseModel):
    __tablename__ = "tour_step_image"

    id = Column(Text, primary_key=True, default=make_uuid)

    file_id = Column(Text, unique=True, nullable=True)
    url = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    tour_step_id = Column(Text, ForeignKey("tour_step.id", ondelete="CASCADE"))

    @classmethod
    def create(cls, data_dict) -> Self:
        # data_dict.pop("name", None)
        # data_dict.pop("upload", None)

        tour_step_image = cls(**data_dict)

        model.Session.add(tour_step_image)
        model.Session.commit()

        return tour_step_image

    @classmethod
    def get(cls, image_id: str) -> Self | None:
        query: Query = model.Session.query(cls).filter(cls.id == image_id)

        return query.one_or_none()

    @classmethod
    def get_by_step(cls, tour_step_id: str) -> Self | None:
        query: Query = model.Session.query(cls).filter(cls.tour_step_id == tour_step_id)

        return query.one_or_none()  # type: ignore

    def dictize(self, context):
        uploaded_file = self.get_file_data(self.file_id) if self.file_id else None

        return {
            "id": self.id,
            "file_id": self.file_id,
            "tour_step_id": self.tour_step_id,
            "uploaded_at": self.uploaded_at.isoformat(),
            "url": uploaded_file["href"] if uploaded_file else self.url,
        }

    def delete(self, with_file: bool = False) -> None:
        """Drop step image and related file from file system"""
        if with_file:
            try:
                tk.get_action("files_file_delete")(
                    {"ignore_auth": True}, {"id": self.file_id}
                )
            except tk.ObjectNotFound:
                pass

        model.Session().autoflush = False
        model.Session.delete(self)

    def get_file_data(self, file_id: str) -> dict[str, Any]:
        """Return a real uploaded file data"""
        result = tk.h.files_link_details(file_id)

        if not result:
            return {}

        return result
