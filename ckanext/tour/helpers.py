from __future__ import annotations

import json
from typing import Any

from flask import current_app, has_request_context

import ckan.plugins.toolkit as tk
import ckan.plugins as p
from ckan.model.types import make_uuid

from ckanext.tour import config
from ckanext.tour.model import Tour, TourStep

IGNORE_BLUEPRINTS = frozenset(
    {
        "api",
        "webassets",
        "static",
        "util",
        "feeds",
        "debugtoolbar",
        "tour",
        "file",
        "files",
        "tables"
    },
)


EVERYWHERE_SUPPRESSED = frozenset(
    {
        "user.login",
        "user.logout",
        "user.register",
        "user.request_reset",
        "user.perform_reset",
    },
)

WIDGET_FIELDS = ["id", "title", "auto_start", "steps"]


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


def _is_suppressed_endpoint(endpoint: str | None) -> bool:
    if not endpoint:
        return True

    if endpoint in EVERYWHERE_SUPPRESSED:
        return True

    blueprint = endpoint.split(".", 1)[0]

    return blueprint in {"error", "tour"}


def tour_get_page_options() -> list[dict[str, str]]:
    """Options for the "show on" picklist in the tour form.

    Built from the app's registered URL rules: every ``GET`` endpoint that is
    not part of a system blueprint or the API, deduplicated and sorted, with an
    "Everywhere" entry (stored as an empty string) on top.
    """
    seen: dict[str, str] = {}

    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint

        if "GET" not in (rule.methods or set()):
            continue

        if endpoint == "static" or endpoint.endswith(".static"):
            continue

        blueprint = endpoint.split(".", 1)[0] if "." in endpoint else ""

        if blueprint in IGNORE_BLUEPRINTS:
            continue

        if rule.rule.startswith("/api/"):
            continue

        # keep the shortest path we have seen for the endpoint, purely for a
        # tidier label
        if endpoint not in seen or len(rule.rule) < len(seen[endpoint]):
            seen[endpoint] = rule.rule

    options = [{"value": "", "text": p.toolkit._("Everywhere")}]

    options.extend(
        {"value": endpoint, "text": f"{endpoint}  —  {path}"}
        for endpoint, path in sorted(seen.items())
    )

    return options


def tour_get_page_tours() -> list[dict[str, Any]]:
    """Active tours that should be offered on the current request's page."""
    if not has_request_context():
        return []

    endpoint = tk.request.endpoint

    tours = Tour.active_for_endpoint(endpoint)

    if _is_suppressed_endpoint(endpoint):
        # keep only tours explicitly bound to this endpoint, drop "Everywhere"
        tours = [tour for tour in tours if tour.endpoint]

    return [tour.dictize({}, WIDGET_FIELDS) for tour in tours]


def tour_get_config() -> dict[str, Any]:
    """Runtime settings plus the tours for the current page."""
    return {
        "collapse_steps": config.is_collapse_steps_enabled(),
        "launcher_position": config.get_launcher_position(),
        "tours": tour_get_page_tours(),
    }


def tour_get_tour_config() -> str:
    """JSON blob for the ``tour-init`` module's ``data-module-config``."""
    return json.dumps(tour_get_config())


def tour_collapse_steps() -> bool:
    return config.is_collapse_steps_enabled()
