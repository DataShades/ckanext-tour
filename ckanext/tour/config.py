from __future__ import annotations

import ckan.plugins.toolkit as tk

CONF_COLLAPSE_STEPS = "ckanext.tour.collapse_steps"
CONF_LAUNCHER_POSITION = "ckanext.tour.launcher_position"

DEFAULT_COLLAPSE_STEPS = True
DEFAULT_LAUNCHER_POSITION = "bottom-right"
LAUNCHER_POSITIONS = ("bottom-right", "bottom-left")


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


def is_collapse_steps_enabled() -> bool:
    return _bool(CONF_COLLAPSE_STEPS, DEFAULT_COLLAPSE_STEPS)


def get_launcher_position() -> str:
    value = tk.config.get(CONF_LAUNCHER_POSITION) or DEFAULT_LAUNCHER_POSITION

    return value if value in LAUNCHER_POSITIONS else DEFAULT_LAUNCHER_POSITION
