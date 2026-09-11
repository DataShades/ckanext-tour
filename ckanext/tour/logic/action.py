from __future__ import annotations

import contextlib
from typing import Any, cast

from sqlalchemy import select

import ckan.plugins.toolkit as tk
from ckan import model, types
from ckan.logic import validate
from ckan.model.types import make_uuid

from ckanext.files.shared import make_upload

from ckanext.tour.logic import schema
from ckanext.tour.model import Tour, TourStep, utcnow

_MANAGER_ONLY_FIELDS = ("author_id",)


def _delete_files(*file_ids: str | None) -> None:
    """Best-effort removal of ``files`` records left behind by a step image."""
    for file_id in file_ids:
        if not file_id:
            continue
        with contextlib.suppress(tk.ObjectNotFound, tk.ValidationError):
            tk.get_action("files_file_delete")({"ignore_auth": True}, {"id": file_id})


def _namespace_step_errors(error_dict: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    """Re-shape a single step's error dict into the ``{"steps": [...]}`` list the
    tour form expects.

    ``tour_step_create`` / ``tour_step_update`` raise flat field errors (e.g.
    ``{"image": "..."}``). Without this the tour form can't tell which step
    failed and renders no message at all.
    """
    steps: list[dict[str, Any]] = [{} for _ in range(total)]

    if 0 <= index < total:
        steps[index] = dict(error_dict)

    return {"steps": steps}


def _user_manages_tours(context: types.Context) -> bool:
    try:
        tk.check_access("tour_manage", context)
    except tk.NotAuthorized:
        return False

    return True


@tk.side_effect_free
@validate(schema.tour_show)
def tour_show(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_show", context, data_dict)

    tour = cast(Tour, Tour.get(data_dict["id"]))
    is_manager = _user_manages_tours(context)

    if not is_manager and tour.state != Tour.State.active:
        raise tk.ObjectNotFound(tk._("Tour not found"))

    result = tour.dictize(context)

    if not is_manager:
        for field in _MANAGER_ONLY_FIELDS:
            result.pop(field, None)

    return result


@tk.side_effect_free
@validate(schema.tour_list)
def tour_list(context: types.Context, data_dict: types.DataDict) -> list[dict[str, Any]]:
    """Return a list of tours from the database.

    Non-managers only ever see ``active`` tours and never the ``author_id``.

    :param state: (managers only) keep only ``active`` or ``inactive`` tours
    :param fl: optional field list (a list, or a comma/space separated string)
        restricting the keys returned per tour, like ``fl`` in
        ``package_search``. Omitting ``steps`` also skips loading them.
    """
    tk.check_access("tour_list", context, data_dict)

    is_manager = _user_manages_tours(context)

    stmt = select(Tour)

    if not is_manager:
        stmt = stmt.where(Tour.state == Tour.State.active)
    elif data_dict.get("state"):
        stmt = stmt.where(Tour.state == data_dict["state"])

    stmt = stmt.order_by(Tour.created_at.desc())

    fields = data_dict.get("fl")

    result = [tour.dictize(context, fields) for tour in model.Session.scalars(stmt)]

    if not is_manager:
        for row in result:
            for field in _MANAGER_ONLY_FIELDS:
                row.pop(field, None)

    return result


@validate(schema.tour_create)
def tour_create(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    steps: list[dict[str, Any]] = data_dict.pop("steps", [])
    tour = Tour.create(data_dict)

    created_ids: list[str] = []

    for index, step in enumerate(steps):
        step["tour_id"] = tour.id

        try:
            result = tk.get_action("tour_step_create")(
                {"ignore_auth": True},
                step,
            )
        except Exception as e:
            # Any step failure -- validation or otherwise (e.g. a storage
            # backend erroring on the image upload) -- must not leave `tour`
            # behind with no steps, or fewer than intended.
            tk.get_action("tour_remove")(
                {"ignore_auth": True},
                {"id": tour.id},
            )

            if isinstance(e, tk.ValidationError):
                raise tk.ValidationError(_namespace_step_errors(e.error_dict, index, len(steps))) from e

            raise

        created_ids.append(result["id"])

    # tour_step_create always appends (see its own next_index() default);
    # this is what actually makes the saved order match the submitted one.
    TourStep.renumber(created_ids)
    model.Session.commit()

    tour.reload_steps()

    return tour.dictize(context)


@validate(schema.tour_remove)
def tour_remove(context: types.Context, data_dict: types.DataDict) -> bool:
    tk.check_access("tour_manage", context, data_dict)

    tour = cast(Tour, Tour.get(data_dict["id"]))
    image_ids = [step.image_id for step in tour.steps]

    model.Session.delete(tour)
    model.Session.commit()

    _delete_files(*image_ids)

    return True


@validate(schema.tour_update)
def tour_update(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    tour = cast(Tour, Tour.get(data_dict["id"]))

    tour.title = data_dict.get("title", tour.title)
    tour.endpoint = data_dict.get("endpoint", tour.endpoint)
    tour.auto_start = data_dict.get("auto_start", tour.auto_start)
    tour.state = data_dict.get("state", tour.state)
    tour.modified_at = utcnow()

    steps: list[dict[str, Any]] = data_dict.pop("steps", [])

    # the submitted list is authoritative: any step of this tour that is no
    # longer present was removed in the form, so drop it (and its image). The
    # form also deletes steps eagerly over htmx; this is the no-JS / failed
    # request safety net.
    submitted_ids = {step["id"] for step in steps if step.get("id")}

    for step_id in [existing.id for existing in tour.steps]:
        if step_id not in submitted_ids:
            tk.get_action("tour_step_remove")({"ignore_auth": True}, {"id": step_id})

    step_ids: list[str] = []

    for index, step in enumerate(steps):
        action = "tour_step_update" if step.get("id") else "tour_step_create"
        step["tour_id"] = tour.id

        try:
            result = tk.get_action(action)({"ignore_auth": True}, step)
        except tk.ValidationError as e:
            raise tk.ValidationError(_namespace_step_errors(e.error_dict, index, len(steps))) from e

        step_ids.append(result["id"])

    TourStep.renumber(step_ids)
    model.Session.commit()

    tour.reload_steps()

    return tour.dictize(context)


@validate(schema.tour_step_schema)
def tour_step_create(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    image_id = _upload_step_image(data_dict)

    if image_id:
        data_dict["image_id"] = image_id

    data_dict["index"] = TourStep.next_index(data_dict["tour_id"])
    tour_step = TourStep.create(data_dict)

    return tour_step.dictize(context)


def _upload_step_image(data_dict: dict[str, Any]) -> str | None:
    image_upload = data_dict.pop("image_upload", None)
    image_url = data_dict.pop("image_url", None)

    if not image_upload and not image_url:
        return None

    if image_upload and image_url:
        raise tk.ValidationError({"image": "Please provide either an image URL or upload a file, not both."})

    if image_upload:
        payload = {"upload": image_upload, "storage": "tour_image"}
    else:
        # the `files:link` storage reads the URL from the upload's stream, so
        # the raw string has to be wrapped into an Upload with a unique name
        payload = {
            "upload": make_upload(str(image_url).encode()),
            "name": make_uuid(),
            "storage": "tour_link",
        }

    result = tk.get_action("files_file_create")({"ignore_auth": True}, payload)

    return result["id"]


@validate(schema.tour_step_update)
def tour_step_update(context: types.Context, data_dict: types.DataDict) -> dict[str, Any]:
    tk.check_access("tour_manage", context, data_dict)

    image_id = _upload_step_image(data_dict)

    tour_step = cast(TourStep, TourStep.get(data_dict["id"]))
    previous_image_id = tour_step.image_id

    tour_step.index = data_dict.get("index") or tour_step.index
    tour_step.title = data_dict.get("title", tour_step.title)
    tour_step.element = data_dict.get("element", tour_step.element)
    tour_step.intro = data_dict.get("intro", tour_step.intro)
    tour_step.position = data_dict.get("position", tour_step.position)
    tour_step.image_id = image_id or data_dict.get("image_id", tour_step.image_id)

    model.Session.commit()

    if previous_image_id and previous_image_id != tour_step.image_id:
        _delete_files(previous_image_id)

    return tour_step.dictize(context)


@validate(schema.tour_step_remove)
def tour_step_remove(context: types.Context, data_dict: types.DataDict) -> bool:
    tk.check_access("tour_manage", context, data_dict)

    tour_step = cast(TourStep, TourStep.get(data_dict["id"]))
    image_id = tour_step.image_id

    tour_step.delete()
    model.Session.commit()

    _delete_files(image_id)

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
