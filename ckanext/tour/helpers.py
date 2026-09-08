from __future__ import annotations

import json
from typing import Any

import ckan.plugins as p
from ckan.model.types import make_uuid

from ckanext.tour import config
from ckanext.tour.model import TourStep


def tour_is_admin_panel_enabled() -> bool:
    return p.plugin_loaded("admin_panel")


def tour_get_position_options():
    return [
        {"value": step, "text": step}
        for step in (
            TourStep.Position.bottom,
            TourStep.Position.top,
            TourStep.Position.right,
            TourStep.Position.left,
        )
    ]


def tour_random_step_id() -> str:
    return make_uuid()


def tour_get_config() -> dict[str, Any]:
    """All runtime-editable tour settings, coerced to their real types."""
    return {
        "autoplay": config.is_auto_play_enabled(),
        "default_anchor": config.get_default_anchor(),
        "collapse_steps": config.is_collapse_steps_enabled(),
    }


def tour_get_tour_config() -> str:
    """JSON blob for the ``tour-init`` module's ``data-module-config``."""
    return json.dumps(tour_get_config())


def tour_collapse_steps() -> bool:
    return tour_get_config()["collapse_steps"]
