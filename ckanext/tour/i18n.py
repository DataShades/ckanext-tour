from __future__ import annotations

import ckan.plugins.toolkit as tk


def localize(value: dict[str, str] | str | None, locale: str | None = None) -> str:
    """Return the best available translation for ``locale``."""
    if not value:
        return ""

    if isinstance(value, str):
        return value

    active_locale: str = tk.h.lang() or ""
    locale = locale or active_locale

    default_locale = tk.config.get("ckan.locale_default", "en")

    for candidate in (locale, default_locale):
        translation = value.get(candidate)

        if translation:
            return translation

    return next(iter(value.values()), "")
