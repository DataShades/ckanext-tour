from __future__ import annotations

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.tour.utils import parse_step_forms


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
                    "data": dict(data_dict, id=tour_id),
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
        return {
            "id": tour_id,
            "title": tk.request.form.get("title"),
            "endpoint": tk.request.form.get("endpoint", ""),
            "auto_start": bool(tk.request.form.get("auto_start")),
            "state": tk.request.form.get("state"),
            "steps": parse_step_forms(tk.request.form),
        }
