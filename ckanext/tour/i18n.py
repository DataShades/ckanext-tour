from __future__ import annotations

import ckan.plugins.toolkit as tk


def default_locale() -> str:
    """The site's default locale (``ckan.locale_default``, "en" if unset)."""
    return tk.config.get("ckan.locale_default", "en")


def current_locale() -> str:
    """The active request's locale, falling back to :func:`default_locale`
    outside a request (or before one has set a language)."""
    return tk.h.lang() or default_locale()


def localize(value: dict[str, str] | str | None, locale: str | None = None) -> str:
    """Return the best available translation for ``locale``."""
    if not value:
        return ""

    if isinstance(value, str):
        return value

    locale = locale or current_locale()

    for candidate in (locale, default_locale()):
        translation = value.get(candidate)

        if translation:
            return translation

    return next(iter(value.values()), "")
