from __future__ import annotations

from flask import session
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan.types import Response

from ckanext.tour.utils import PREVIEW_KEY, parse_step_forms


class TourPreviewView(MethodView):
    """Run the tour currently in the edit form without saving it.

    The submitted (unsaved) form is stashed in the session and the browser is
    bounced to the tour's target page with ``?_tour_preview=session``; there
    ``tour-init`` picks the stashed tour up and plays it. Nothing is persisted.
    """

    def post(self) -> Response:
        endpoint = tk.request.form.get("endpoint", "")

        session[PREVIEW_KEY] = {
            "title": tk.request.form.get("title") or str(tk._("Tour preview")),
            "endpoint": endpoint,
            "steps": parse_step_forms(tk.request.form),
        }
        session.modified = True

        target = _preview_target(endpoint)

        if target is None:
            return tk.redirect_to("/")

        return tk.redirect_to(target, **{PREVIEW_KEY: "session"})


def _preview_target(endpoint: str) -> str | None:
    """Best-effort endpoint to redirect the preview to, or ``None`` if
    nothing is buildable (e.g. a parametrised route like ``dataset.read``
    that's missing its params, or "Everywhere").

    Returns the endpoint *name*, not a built URL -- ``redirect_to`` needs the
    name to attach ``_tour_preview=session`` as a query string itself. Passing
    it an already-built URL (starting with "/") instead would hit its
    single-string fast path, which skips ``url_for`` entirely and silently
    drops any kwargs.
    """
    for candidate in (endpoint, "dataset.search"):
        if not candidate:
            continue

        try:
            tk.url_for(candidate)
        except Exception:  # noqa: BLE001 - any build failure just falls back
            continue

        return candidate

    return None
