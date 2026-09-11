from __future__ import annotations

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.tour.utils import parse_step_forms, parse_translated_field


class TourAddView(MethodView):
    def get(self) -> str:
        return tk.render("tour/tour_add.html", extra_vars={"data": {}, "errors": {}})

    def post(self) -> Response | str:
        data_dict = self._prepare_payload()

        try:
            tk.get_action("tour_create")(
                {
                    "user": tk.current_user.name,
                    "auth_user_obj": tk.current_user,
                },
                data_dict,
            )
        except tk.ValidationError as e:
            return tk.render(
                "tour/tour_add.html",
                extra_vars={
                    "data": data_dict,
                    "errors": e.error_dict,
                    "error_summary": e.error_summary,
                },
            )

        tk.h.flash_success(tk._("The tour has been created!"))

        return tk.redirect_to("tour.list")

    def _prepare_payload(self):
        return {
            "title": parse_translated_field(tk.request.form, "title"),
            "endpoint": tk.request.form.get("endpoint", ""),
            "auto_start": bool(tk.request.form.get("auto_start")),
            "author_id": tk.current_user.id,  # type: ignore
            "steps": parse_step_forms(tk.request.form),
        }


class TourAddStepView(MethodView):
    def post(self) -> str:
        return tk.render("tour/snippets/tour_step.html", extra_vars={"step": {}, "errors": {}})
