from __future__ import annotations

from typing import Any, cast

import ckan.plugins.toolkit as tk
from ckan import model, types
from ckan.logic import validate

from ckanext.tour.logic import schema
from ckanext.tour.model import Tour, TourStep


@tk.side_effect_free
@validate(schema.tour_show)
def tour_show(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_show", context, data_dict)

    return cast(Tour, Tour.get(data_dict["id"])).dictize(context)


@tk.side_effect_free
@validate(schema.tour_list)
def tour_list(context: types.Context, data_dict: types.DataDict) -> list[dict[str, Any]]:
    """Return a list of tours from database"""
    tk.check_access("tour_list", context, data_dict)

    query = model.Session.query(Tour)

    if data_dict.get("state"):
        query = query.filter(Tour.state == data_dict["state"])

    query = query.order_by(Tour.created_at.desc())

    return [tour.dictize(context) for tour in query.all()]


@validate(schema.tour_create)
def tour_create(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    steps: list[dict[str, Any]] = data_dict.pop("steps", [])
    tour = Tour.create(data_dict)

    for step in steps:
        step["tour_id"] = tour.id

        try:
            tk.get_action("tour_step_create")(
                {"ignore_auth": True},
                step,
            )
        except tk.ValidationError as e:
            tk.get_action("tour_remove")(
                {"ignore_auth": True},
                {"id": tour.id},
            )

            raise tk.ValidationError(e.error_dict if e else {}) from e

    return tour.dictize(context)


@validate(schema.tour_remove)
def tour_remove(context: types.Context, data_dict: types.DataDict) -> bool:
    tk.check_access("tour_manage", context, data_dict)

    tour = cast(Tour, Tour.get(data_dict["id"]))

    for step in tour.steps:
        step.delete()

    tour.delete()

    model.Session.commit()

    return True


@validate(schema.tour_update)
def tour_update(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    tour = cast(Tour, Tour.get(data_dict["id"]))

    tour.title = data_dict.get("title", tour.title)
    tour.anchor = data_dict.get("anchor", tour.anchor)
    tour.page = data_dict.get("page", tour.page)
    tour.state = data_dict.get("state", tour.page)

    steps: list[dict[str, Any]] = data_dict.pop("steps", [])

    for step in steps:
        action = "tour_step_update" if step.get("id") else "tour_step_create"
        step["tour_id"] = tour.id

        try:
            tk.get_action(action)({"ignore_auth": True}, step)
        except tk.ValidationError as e:
            raise tk.ValidationError(e.error_dict) from e

    model.Session.commit()

    return tour.dictize(context)


@validate(schema.tour_step_schema)
def tour_step_create(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    image_id = _upload_step_image(data_dict)

    if image_id:
        data_dict["image_id"] = image_id

    tour = cast(Tour, Tour.get(data_dict["tour_id"]))
    data_dict["index"] = len(tour.steps) + 1
    tour_step = TourStep.create(data_dict)

    return tour_step.dictize(context)


def _upload_step_image(data_dict: dict[str, Any]) -> str | None:
    image_upload = data_dict.pop("image_upload", None)
    image_url = data_dict.pop("image_url", None)

    if not image_upload and not image_url:
        return None

    if image_upload and image_url:
        raise tk.ValidationError({"image": "Please provide either an image URL or upload a file, not both."})

    result = tk.get_action("files_file_create")(
        {"ignore_auth": True},
        {
            "upload": image_upload or image_url,
            "storage": "tour_image" if image_upload else "tour_link",
        },
    )

    return result["id"]


@validate(schema.tour_step_update)
def tour_step_update(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    image_id = _upload_step_image(data_dict)

    tour_step = cast(TourStep, TourStep.get(data_dict["id"]))

    tour_step.index = data_dict.get("index") or tour_step.index
    tour_step.title = data_dict["title"]
    tour_step.element = data_dict["element"]
    tour_step.intro = data_dict["intro"]
    tour_step.position = data_dict["position"]
    tour_step.image_id = image_id or data_dict.get("image_id", tour_step.image_id)

    return tour_step.dictize(context)


@validate(schema.tour_step_remove)
def tour_step_remove(context: types.Context, data_dict: types.DataDict) -> bool:
    tk.check_access("tour_manage", context, data_dict)

    tour_step = cast(TourStep, TourStep.get(data_dict["id"]))

    tour_step.delete()
    model.Session.commit()

    return True


@validate(schema.tour_upload_storage)
def tour_upload_image(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    return tk.get_action("files_file_create")(
        {"ignore_auth": True},
        {
            "upload": data_dict["upload"],
            "storage": "tour_image",
        },
    )


@validate(schema.tour_upload_storage)
def tour_upload_link(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    return tk.get_action("files_file_create")(
        {"ignore_auth": True},
        {
            "upload": data_dict["upload"],
            "storage": "tour_link",
        },
    )
