from __future__ import annotations

from typing import Any

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.tour import config


class TourConfigView(MethodView):
    """Standalone settings page.

    Saving tour settings writes CKAN runtime config via ``config_option_update``,
    which is sysadmin-only — a stricter bar than the blueprint's ``tour_manage``
    guard. Enforce it here so a site that delegates ``tour_manage`` to a
    non-sysadmin gets a clean 403 instead of a 500 from the action on save.
    """

    def dispatch_request(self, **kwargs: Any) -> Response | str:
        try:
            tk.check_access("config_option_update", {"user": tk.current_user.name})
        except tk.NotAuthorized:
            tk.abort(403, tk._("You need to be a system administrator to manage tour settings"))

        return super().dispatch_request(**kwargs)

    def get(self) -> str:
        return tk.render(
            "tour/tour_config.html",
            extra_vars={"data": self._current_values(), "errors": {}},
        )

    def post(self) -> Response | str:
        data_dict = {
            config.CONF_COLLAPSE_STEPS: tk.request.form.get(config.CONF_COLLAPSE_STEPS, "false"),
            config.CONF_LAUNCHER_POSITION: tk.request.form.get(
                config.CONF_LAUNCHER_POSITION,
                config.DEFAULT_LAUNCHER_POSITION,
            ),
        }

        try:
            tk.get_action("config_option_update")(
                {"user": tk.current_user.name, "auth_user_obj": tk.current_user},
                data_dict,
            )
        except tk.ValidationError as e:
            return tk.render(
                "tour/tour_config.html",
                extra_vars={
                    "data": data_dict,
                    "errors": e.error_dict,
                    "error_summary": e.error_summary,
                },
            )

        tk.h.flash_success(tk._("The tour settings have been updated!"))

        return tk.redirect_to("tour.config")

    def _current_values(self) -> dict[str, object]:
        return {
            config.CONF_COLLAPSE_STEPS: config.is_collapse_steps_enabled(),
            config.CONF_LAUNCHER_POSITION: config.get_launcher_position(),
        }
