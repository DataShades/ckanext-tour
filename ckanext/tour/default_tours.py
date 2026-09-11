from __future__ import annotations

from typing import Any, NotRequired, TypedDict

import ckan.plugins.toolkit as tk

from ckanext.tour.i18n import default_locale
from ckanext.tour.model import Tour, TourStep


class DefaultTourStep(TypedDict):
    """One step of a :data:`DefaultTour`.

    ``title``/``intro`` are plain strings for the site's default locale --
    ``tour_create`` (via ``tour_translated_valid``) wraps them into the
    ``{locale: text}`` mapping the model stores. No ``image_*`` key is
    supported on purpose: default tours are meant to stay simple to define
    and free of upload/storage concerns.
    """

    element: str
    title: str
    intro: str
    position: NotRequired[str]


class DefaultTour(TypedDict):
    """A built-in tour definition, shaped for :func:`create_default_tours`."""

    title: str
    endpoint: NotRequired[str]
    auto_start: NotRequired[bool]
    steps: list[DefaultTourStep]


DEFAULT_TOURS: list[DefaultTour] = [
    {
        "title": "Searching for datasets",
        "endpoint": "dataset.search",
        "steps": [
            {
                "element": "#field-giant-search",
                "title": "Search bar",
                "intro": "Type keywords here to search across every dataset's title, description and tags.",
            },
            {
                "element": "#search-facets",
                "title": "Filters",
                "intro": "Narrow the results down by organization, format, tag or any other facet listed here.",
                "position": TourStep.Position.right,
            },
            {
                "element": "#field-order-by",
                "title": "Sorting",
                "intro": "Change how the results are ordered -- by relevance, name or last modified date.",
            },
            {
                "element": "#search-results",
                "title": "Dataset list",
                "intro": "Matching datasets are listed here. Click one to see its resources and details.",
            },
        ],
    },
    {
        "title": "Exploring a dataset",
        "endpoint": "dataset.read",
        "steps": [
            {
                "element": "#dataset-resources",
                "title": "Data and resources",
                "intro": "A dataset is a collection of resources -- files, APIs or links. "
                "Click one to preview or download it.",
            },
            {
                "element": ".additional-info",
                "title": "Additional info",
                "intro": "Metadata about this dataset -- source, license, update frequency and more -- "
                "lives in this table.",
            },
            {
                "element": "#package-info",
                "title": "Follow this dataset",
                "intro": "Follow a dataset to be notified about its changes, "
                "and see how many other people follow it too.",
                "position": TourStep.Position.right,
            },
        ],
    },
    {
        "title": "Browsing organizations",
        "endpoint": "organization.index",
        "steps": [
            {
                "element": "#field-giant-search",
                "title": "Search bar",
                "intro": "Type here to search for an organization by name or description.",
            },
            {
                "element": ".groups-list",
                "title": "Organization list",
                "intro": "Every organization publishing data on this portal is listed here. "
                "Click one to see its datasets.",
            },
        ],
    },
    {
        "title": "Welcome to the portal",
        "endpoint": "home.index",
        "steps": [
            {
                "element": "#field-main-search",
                "title": "Search bar",
                "intro": "Start here -- search across every dataset published on this portal.",
            },
            {
                "element": ".featured-groups",
                "title": "Featured organizations",
                "intro": "A few organizations publishing data on this portal are highlighted here.",
            },
            {
                "element": ".recent-packages",
                "title": "Recently added datasets",
                "intro": "The newest datasets added to the portal show up here.",
            },
        ],
    },
]


def create_default_tours(author_id: str, tours: list[DefaultTour] | None = None) -> list[dict[str, Any]]:
    """Create every ``tours`` entry (:data:`DEFAULT_TOURS` by default) that
    isn't already present.

    Idempotent: matches on the default locale's title text, so calling this
    again -- e.g. by clicking the table action a second time -- never creates
    duplicates, even if some default tours already exist and others don't.
    """
    existing_titles = {tour.title.get(default_locale(), "") for tour in Tour.all()}
    created: list[dict[str, Any]] = []

    for default_tour in tours if tours is not None else DEFAULT_TOURS:
        if default_tour["title"] in existing_titles:
            continue

        result = tk.get_action("tour_create")(
            {"ignore_auth": True},
            {
                "title": default_tour["title"],
                "endpoint": default_tour.get("endpoint", ""),
                "auto_start": default_tour.get("auto_start", False),
                "author_id": author_id,
                "steps": [dict(step) for step in default_tour["steps"]],
            },
        )
        created.append(result)

    return created
