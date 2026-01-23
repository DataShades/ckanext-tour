from __future__ import annotations

import string
from typing import Any
from urllib.parse import urlparse

import ckan.plugins.toolkit as tk
from ckan import types

import ckanext.tour.model as tour_model


def tour_tour_exist(v: str, context) -> Any:
    """Ensures that the tour with a given id exists"""
    result = tour_model.Tour.get(v)

    if not result:
        raise tk.Invalid(f"The tour with an id {v} doesn't exist.")

    return v


def tour_tour_step_exist(v: str, context) -> Any:
    """Ensures that the tour step with a given id exists"""
    result = tour_model.TourStep.get(v)

    if not result:
        raise tk.Invalid(f"The tour step with an id {v} doesn't exist.")

    return v


def tour_url_validator(
    key: types.FlattenKey,
    data: types.FlattenDataDict,
    errors: types.FlattenErrorDict,
    context: types.Context,
) -> Any:
    """Checks that the provided value is a valid URL."""
    url = data.get(key, None)
    if not url:
        return

    try:
        pieces = urlparse(url)
        if (
            all([pieces.scheme, pieces.netloc])
            and set(pieces.netloc) <= set(string.ascii_letters + string.digits + "-.:")
            and pieces.scheme in ["http", "https"]
        ):
            return
    except ValueError:
        # url is invalid
        pass

    errors[key].append(tk._("Please provide a valid URL"))


def tour_duplicate_anchor(
    key: types.FlattenKey,
    data: types.FlattenDataDict,
    errors: types.FlattenErrorDict,
    context: types.Context,
) -> Any:
    """Ensures that the tour step with a given anchor doesn't exist."""
    result = tour_model.Tour.get_by_anchor(data[key])

    if result and result.id != data.get(("id",)):
        raise tk.Invalid(f"The tour step with an anchor `{data[key]}` already exists.")
