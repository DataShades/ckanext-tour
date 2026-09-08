from __future__ import annotations

from typing import Any

from ckan.logic.schema import validator_args

from ckanext.tour.model import Tour, TourStep

Schema = dict[str, Any]


@validator_args
def tour_show(not_empty, unicode_safe, tour_tour_exist) -> Schema:
    return {"id": [not_empty, unicode_safe, tour_tour_exist]}


@validator_args
def tour_create(
    not_empty,
    default,
    ignore_missing,
    unicode_safe,
    user_id_or_name_exists,
    one_of,
    ignore,
    tour_duplicate_anchor,
    tour_selector_validator,
) -> Schema:
    step_schema = tour_step_schema()
    step_schema["tour_id"] = [ignore_missing]

    return {
        "title": [not_empty, unicode_safe],
        "anchor": [ignore_missing, unicode_safe, tour_selector_validator, tour_duplicate_anchor],
        "page": [ignore_missing, unicode_safe],
        "author_id": [not_empty, user_id_or_name_exists],
        "state": [
            default(Tour.State.active),
            one_of([Tour.State.active, Tour.State.inactive]),
        ],
        "steps": step_schema,
        "__extras": [ignore],
    }


@validator_args
def tour_update(not_empty, unicode_safe, tour_tour_exist, ignore_empty) -> Schema:
    tour_schema = tour_create()
    tour_schema["id"] = [not_empty, unicode_safe, tour_tour_exist]
    tour_schema["steps"] = tour_step_update()

    # non-mandatory
    tour_schema["title"] = [ignore_empty, unicode_safe]

    # we shouldn't be able to change an author_id
    tour_schema.pop("author_id")

    return tour_schema


@validator_args
def tour_step_schema(  # noqa: PLR0913
    not_empty,
    ignore,
    ignore_missing,
    unicode_safe,
    default,
    one_of,
    tour_tour_exist,
    tour_url_validator,
    tour_selector_validator,
) -> Schema:
    return {
        "title": [ignore_missing, unicode_safe],
        "element": [not_empty, unicode_safe, tour_selector_validator],
        "intro": [ignore_missing, unicode_safe],
        "position": [
            default(TourStep.Position.bottom),
            one_of(
                [
                    TourStep.Position.bottom,
                    TourStep.Position.top,
                    TourStep.Position.left,
                    TourStep.Position.right,
                ]
            ),
        ],
        "image_id": [ignore_missing, unicode_safe],
        "image_upload": [ignore_missing],
        "image_url": [ignore_missing, unicode_safe, tour_url_validator],
        "tour_id": [not_empty, unicode_safe, tour_tour_exist],
        "__extras": [ignore],
    }


@validator_args
def tour_step_update(
    ignore_empty,
    unicode_safe,
    tour_tour_step_exist,
    default,
    boolean_validator,
    int_validator,
) -> Schema:
    step_schema = tour_step_schema()
    step_schema.pop("tour_id")
    step_schema["id"] = [ignore_empty, unicode_safe, tour_tour_step_exist]
    step_schema["clear"] = [default("false"), boolean_validator]
    step_schema["index"] = [ignore_empty, int_validator]

    return step_schema


@validator_args
def tour_list(ignore_empty, one_of, convert_to_list_if_string) -> Schema:
    return {
        "state": [ignore_empty, one_of([Tour.State.active, Tour.State.inactive])],
        "fl": [ignore_empty, convert_to_list_if_string],
    }


@validator_args
def tour_remove(not_empty, unicode_safe, tour_tour_exist) -> Schema:
    return {"id": [not_empty, unicode_safe, tour_tour_exist]}


@validator_args
def tour_step_remove(not_empty, unicode_safe, tour_tour_step_exist) -> Schema:
    return {"id": [not_empty, unicode_safe, tour_tour_step_exist]}


@validator_args
def tour_upload_storage(not_empty) -> Schema:
    return {"upload": [not_empty]}
