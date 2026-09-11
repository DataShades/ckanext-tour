from __future__ import annotations

import json
from typing import Any

from flask import current_app, has_request_context, session

import ckan.plugins.toolkit as tk
import ckan.plugins as p
from ckan.model.types import make_uuid

from ckanext.tour import config, i18n
from ckanext.tour.model import Tour, TourStep
from ckanext.tour.utils import PREVIEW_KEY

EVERYWHERE_SUPPRESSED = frozenset(
    {
        "user.login",
        "user.logout",
        "user.register",
        "user.request_reset",
        "user.perform_reset",
    },
)

WIDGET_FIELDS = ["id", "title", "auto_start", "steps", "modified_at"]


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
    not part of a system blueprint or the API, and not individually excluded
    via ``ckanext.tour.ignore_endpoints`` (for a blueprint that should
    otherwise stay visible), deduplicated and sorted, with an "Everywhere"
    entry (stored as an empty string) on top.
    """
    seen: dict[str, str] = {}

    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint

        if "GET" not in (rule.methods or set()):
            continue

        if endpoint == "static" or endpoint.endswith(".static"):
            continue

        blueprint = endpoint.split(".", 1)[0] if "." in endpoint else ""

        if blueprint in config.get_ignore_blueprints():
            continue

        if endpoint in config.get_ignore_endpoints():
            continue

        if rule.rule.startswith("/api/"):
            continue

        # keep the shortest path we have seen for the endpoint, purely for a
        # tidier label
        if endpoint not in seen or len(rule.rule) < len(seen[endpoint]):
            seen[endpoint] = rule.rule

    options = [{"value": "", "text": p.toolkit._("Everywhere")}]

    options.extend({"value": endpoint, "text": f"{endpoint}  —  {path}"} for endpoint, path in sorted(seen.items()))

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

    payload = [tour.dictize({}, WIDGET_FIELDS) for tour in tours]

    for tour in payload:
        tour["title"] = i18n.localize(tour.get("title"))

        for step in tour.get("steps", []):
            step["title"] = i18n.localize(step.get("title"))
            step["intro"] = tk.h.render_markdown(i18n.localize(step.get("intro")))

    preview = _preview_tour()

    if preview:
        payload.append(preview)

    return payload


def _preview_tour() -> dict[str, Any] | None:
    """The unsaved tour stashed by the "Preview" button, shaped like a dictized
    tour so ``tour-init`` can play it. Only served to tour managers, and only
    when the current URL carries ``?_tour_preview=session``."""
    if tk.request.args.get(PREVIEW_KEY) != "session":
        return None

    if not _may_manage_tours():
        return None

    stashed = session.get(PREVIEW_KEY)

    if not stashed or not stashed.get("steps"):
        return None

    steps = [
        {
            "id": step.get("id") or f"preview-{idx}",
            "element": step.get("element") or "",
            "position": step.get("position") or TourStep.Position.bottom,
            "title": step.get("title") or "",
            "intro": tk.h.render_markdown(step.get("intro") or ""),
            "image_url": _step_image_href(step.get("image_id")),
        }
        for idx, step in enumerate(stashed["steps"])
    ]

    return {
        "id": "tour-preview",
        "title": stashed.get("title") or str(tk._("Tour preview")),
        "auto_start": True,
        "preview": True,
        "steps": steps,
        "modified_at": "",
    }


def _may_manage_tours() -> bool:
    try:
        tk.check_access("tour_manage", {"user": tk.current_user.name})
    except tk.NotAuthorized:
        return False

    return True


def _step_image_href(image_id: str | None) -> str:
    if not image_id:
        return ""

    file_info = tk.h.files_link_details(image_id)

    return file_info["href"] if file_info else ""


def tour_has_tours() -> bool:
    """Whether any tour exists at all — drives the tours-list empty state."""
    return Tour.exists()


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


def tour_flatten_errors(errors: dict[str, Any] | None) -> list[dict[str, str]]:
    """Flatten a tour-form error dict into ``[{"label", "message"}]`` rows for
    the error summary at the top of the form.

    Per-step errors live under ``errors["steps"]`` as a list aligned with the
    rendered steps; each non-empty entry is labelled ``Step N`` so the summary
    points at the step that failed.
    """
    if not errors:
        return []

    def _message(value: Any) -> str:
        if isinstance(value, (list, tuple)):
            return "; ".join(str(item) for item in value)
        return str(value)

    rows: list[dict[str, str]] = []

    for key, value in errors.items():
        if key == "steps":
            continue

        rows.append({"label": key.replace("_", " ").capitalize(), "message": _message(value)})

    for idx, step_errors in enumerate(errors.get("steps") or [], start=1):
        if not step_errors:
            continue

        for field, value in step_errors.items():
            label = tk._("Step {number}").format(number=idx)

            if field != "steps":
                label = f"{label} — {field.replace('_', ' ')}"

            rows.append({"label": label, "message": _message(value)})

    return rows
