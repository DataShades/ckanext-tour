from __future__ import annotations

import contextlib

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk


class TourDeleteView(MethodView):
    def get(self, tour_id: str) -> str:
        return tk.render("tour/tour_delete.html", extra_vars={"tour_id": tour_id})

    def post(self, tour_id: str) -> Response:
        try:
            tk.get_action("tour_remove")({}, {"id": tour_id})
        except tk.ObjectNotFound as e:
            tk.h.flash_error(str(e))
            return tk.redirect_to("tour.delete", tour_id=tour_id)
        else:
            tk.h.flash_success("Done!")

        return tk.redirect_to("tour.list")


class TourStepDeleteView(MethodView):
    def post(self, tour_step_id: str) -> str:
        with contextlib.suppress(tk.ValidationError):
            tk.get_action("tour_step_remove")({}, {"id": tour_step_id})

        return ""
