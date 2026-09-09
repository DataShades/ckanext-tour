from __future__ import annotations

import re

from werkzeug.datastructures import MultiDict

import ckan.plugins.toolkit as tk


_STEP_FIELD_RE = re.compile(r"^step\[(?P<sid>[^\[\]]+)\]\[(?P<field>[^\[\]]+)\]$")


def before_request() -> None:
    """Guard the tour admin blueprint."""
    try:
        tk.check_access("tour_manage", {"user": tk.current_user.name})
    except tk.NotAuthorized:
        tk.abort(403, tk._("You are not authorized to manage tours"))


def parse_step_forms(form: MultiDict) -> list[dict[str, str]]:
    """Group the namespaced ``step[...]`` form fields into one dict per step.

    Step order follows the repeated ``step_ids`` field, which lists the step ids
    in the order the steps appear in the form; any step whose id is missing from
    it is appended in submission order.
    """
    by_id: dict[str, dict[str, str]] = {}

    for name in form:
        match = _STEP_FIELD_RE.match(name)

        if not match:
            continue

        by_id.setdefault(match.group("sid"), {})[match.group("field")] = form.get(name, "")

    order = form.getlist("step_ids")
    seen = set(order)
    ordered_ids = list(order) + [sid for sid in by_id if sid not in seen]

    return [by_id[sid] for sid in ordered_ids if sid in by_id]
