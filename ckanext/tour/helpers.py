from __future__ import annotations

import json
import uuid

import ckan.plugins as p

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
    return str(uuid.uuid4())


def tour_get_tour_config() -> str:
    return json.dumps(
        {
            "autoplay": config.is_auto_play_enabled(),
            "default_anchor": config.get_default_anchor(),
        }
    )


def tour_collapse_steps() -> bool:
    return config.is_collapse_steps_enabled()
