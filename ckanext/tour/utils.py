from __future__ import annotations

import ckan.plugins.toolkit as tk


def before_request() -> None:
    """Guard the tour admin blueprint."""
    try:
        tk.check_access("tour_manage", {"user": tk.current_user.name})
    except tk.NotAuthorized:
        tk.abort(403, tk._("You are not authorized to manage tours"))
