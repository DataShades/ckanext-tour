from __future__ import annotations

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan import types


class TourUpdateView(MethodView):
    def get(self, tour_id: str) -> Response | str | tuple[str, int]:
        tour = self._load_tour(tour_id)

        if tour is None:
            return tk.render("tour/tour_404.html"), 404

        return tk.render("tour/tour_edit.html", extra_vars={"data": tour, "errors": {}})

    def post(self, tour_id: str) -> Response | str | tuple[str, int]:
        tour = self._load_tour(tour_id)

        if tour is None:
            return tk.render("tour/tour_404.html"), 404

        data_dict = self._prepare_payload(tour_id)

        try:
            tk.get_action("tour_update")(self._build_context(), data_dict)
        except tk.ValidationError as e:
            return tk.render(
                "tour/tour_edit.html",
                extra_vars={
                    "data": tour,
                    "errors": e.error_dict,
                    "error_summary": e.error_summary,
                },
            )

        tk.h.flash_success(tk._("The tour has been updated!"))

        return tk.redirect_to("tour.list")

    def _load_tour(self, tour_id: str) -> dict | None:
        try:
            return tk.get_action("tour_show")(self._build_context(), {"id": tour_id})
        except tk.ValidationError:
            return None

    def _build_context(self) -> types.Context:
        return {
            "user": tk.current_user.name,  # type: ignore
            "auth_user_obj": tk.current_user,
        }

    def _prepare_payload(self, tour_id: str):
        step_fields = (
            "step_id",
            "step_title",
            "step_element",
            "step_intro",
            "step_position",
            "step_clear",
            "step_index",
            "step_image_id",
        )

        steps = {}

        for field_name in step_fields:
            _, field = field_name.split("_", 1)

            for idx, value in enumerate(tk.request.form.getlist(field_name), start=1):
                steps.setdefault(idx, {})
                steps[idx][field] = value

        return {
            "id": tour_id,
            "title": tk.request.form.get("title"),
            "anchor": tk.request.form.get("anchor"),
            "page": tk.request.form.get("page"),
            "steps": list(steps.values()),
        }
