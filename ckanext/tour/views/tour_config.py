from __future__ import annotations

from flask import Response
from flask.views import MethodView

import ckan.plugins.toolkit as tk

from ckanext.tour import config


class TourConfigView(MethodView):
    """Standalone settings page."""

    def get(self) -> str:
        return tk.render(
            "tour/tour_config.html",
            extra_vars={"data": self._current_values(), "errors": {}},
        )

    def post(self) -> Response | str:
        data_dict = {
            config.CONF_AUTOPLAY: tk.request.form.get(config.CONF_AUTOPLAY, "false"),
            config.CONF_DEFAULT_ANCHOR: tk.request.form.get(config.CONF_DEFAULT_ANCHOR, ""),
            config.CONF_COLLAPSE_STEPS: tk.request.form.get(config.CONF_COLLAPSE_STEPS, "false"),
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
            config.CONF_AUTOPLAY: config.is_auto_play_enabled(),
            config.CONF_DEFAULT_ANCHOR: config.get_default_anchor(),
            config.CONF_COLLAPSE_STEPS: config.is_collapse_steps_enabled(),
        }
