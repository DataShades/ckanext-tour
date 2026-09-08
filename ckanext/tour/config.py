from __future__ import annotations

import ckan.plugins.toolkit as tk

CONF_AUTOPLAY = "ckanext.tour.autoplay"
CONF_DEFAULT_ANCHOR = "ckanext.tour.default_anchor"
CONF_COLLAPSE_STEPS = "ckanext.tour.collapse_steps"

DEFAULT_AUTOPLAY = False
DEFAULT_ANCHOR = ".breadcrumb .active"
DEFAULT_COLLAPSE_STEPS = True


def _bool(key: str, default: bool) -> bool:
    """Read a runtime-editable boolean option.

    Once an option has been saved through ``config_option_update`` CKAN's
    ``app_globals.reset()`` writes the raw ``system_info`` string straight back
    into ``config`` (bypassing the declared ``bool`` validator), so ``"false"``
    would otherwise read back as a truthy string. Coerce explicitly.
    """
    value = tk.config.get(key)

    if value is None or value == "":
        return default

    return tk.asbool(value)


def is_auto_play_enabled() -> bool:
    return _bool(CONF_AUTOPLAY, DEFAULT_AUTOPLAY)


def get_default_anchor() -> str:
    return tk.config.get(CONF_DEFAULT_ANCHOR) or DEFAULT_ANCHOR


def is_collapse_steps_enabled() -> bool:
    return _bool(CONF_COLLAPSE_STEPS, DEFAULT_COLLAPSE_STEPS)
