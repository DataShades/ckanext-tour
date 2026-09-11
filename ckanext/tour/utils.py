from __future__ import annotations

import re
from typing import Any

from werkzeug.datastructures import MultiDict

import ckan.plugins.toolkit as tk


_STEP_FIELD_RE = re.compile(r"^step\[(?P<sid>[^\[\]]+)\]\[(?P<field>[^\[\]]+)\](?:\[(?P<locale>[^\[\]]+)\])?$")
PREVIEW_KEY = "_tour_preview"


def before_request() -> None:
    """Guard the tour admin blueprint."""
    try:
        tk.check_access("tour_manage", {"user": tk.current_user.name})
    except tk.NotAuthorized:
        tk.abort(403, tk._("You are not authorized to manage tours"))


def parse_step_forms(form: MultiDict) -> list[dict[str, Any]]:
    """Group the namespaced ``step[...]`` form fields into one dict per step.

    A field posted as ``step[sid][field][locale]`` (a translated field, e.g.
    title/intro) collects into a ``{locale: value}`` dict under ``field``;
    ``step[sid][field]`` (untranslated) stays a plain value.

    Step order follows the repeated ``step_ids`` field, which lists the step ids
    in the order the steps appear in the form; any step whose id is missing from
    it is appended in submission order.
    """
    by_id: dict[str, dict[str, Any]] = {}

    for name in form:
        match = _STEP_FIELD_RE.match(name)

        if not match:
            continue

        step = by_id.setdefault(match.group("sid"), {})
        field, locale = match.group("field"), match.group("locale")

        if locale:
            step.setdefault(field, {})[locale] = form.get(name, "")
        else:
            step[field] = form.get(name, "")

    order = form.getlist("step_ids")
    seen = set(order)
    ordered_ids = list(order) + [sid for sid in by_id if sid not in seen]

    return [by_id[sid] for sid in ordered_ids if sid in by_id]


def parse_translated_field(form: MultiDict, name: str) -> dict[str, str]:
    """Collect ``name[locale]`` form fields into a ``{locale: value}`` dict."""
    pattern = re.compile(rf"^{re.escape(name)}\[(?P<locale>[^\[\]]+)\]$")
    result: dict[str, str] = {}

    for key in form:
        match = pattern.match(key)

        if match:
            result[match.group("locale")] = form.get(key, "")

    return result
