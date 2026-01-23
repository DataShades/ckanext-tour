from __future__ import annotations

from flask import Blueprint, Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.ap_main.utils import ap_before_request

tour = Blueprint("tour", __name__)
tour.before_request(ap_before_request)


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
        step_fields = (
            "step_title",
            "step_element",
            "step_intro",
            "step_position",
            "step_image_id"
        )

        steps = {}

        for field_name in step_fields:
            _, field = field_name.split("_", 1)

            for idx, value in enumerate(tk.request.form.getlist(field_name), start=1):
                steps.setdefault(idx, {})
                steps[idx][field] = value

        return {
            "title": tk.request.form.get("title"),
            "anchor": tk.request.form.get("anchor"),
            "page": tk.request.form.get("page"),
            "author_id": tk.current_user.id,  # type: ignore
            "steps": list(steps.values()),
        }


class TourAddStepView(MethodView):
    def post(self) -> str:
        return tk.render("tour/snippets/tour_step.html", extra_vars={"step": {}, "errors": {}})
