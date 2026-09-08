from __future__ import annotations

import contextlib

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk


class TourDeleteView(MethodView):
    def get(self, tour_id: str) -> str | tuple[str, int]:
        if not self._tour_exists(tour_id):
            return tk.render("tour/tour_404.html"), 404

        return tk.render("tour/tour_delete.html", extra_vars={"tour_id": tour_id})

    def post(self, tour_id: str) -> Response:
        try:
            tk.get_action("tour_remove")({}, {"id": tour_id})
        except (tk.ObjectNotFound, tk.ValidationError):
            tk.h.flash_error(tk._("Tour not found."))
            return tk.redirect_to("tour.list")

        tk.h.flash_success(tk._("The tour has been deleted."))

        return tk.redirect_to("tour.list")

    @staticmethod
    def _tour_exists(tour_id: str) -> bool:
        try:
            tk.get_action("tour_show")({}, {"id": tour_id})
        except (tk.ObjectNotFound, tk.ValidationError):
            return False

        return True


class TourStepDeleteView(MethodView):
    def post(self, tour_step_id: str) -> str:
        with contextlib.suppress(tk.ValidationError):
            tk.get_action("tour_step_remove")({}, {"id": tour_step_id})

        return ""
