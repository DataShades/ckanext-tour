from __future__ import annotations

from ckanext.collection.utils.data.model import ModelData

from dominate import tags

import ckan.plugins.toolkit as tk

from ckanext.collection.types import InputFilter, ButtonFilter, LinkFilter
from ckanext.collection.utils import Filters

from ckanext.ap_main.collection.base import (
    ApCollection,
    ApColumns,
    BulkAction,
    RowAction,
    ApHtmxTableSerializer,
)

from ckanext.tour.model import Tour


def tour_row_dictizer(serializer: ApHtmxTableSerializer, row: Tour):
    data = row.dictize({})
    data["bulk-action"] = data["id"]
    data["steps"] = len(data["steps"])

    return data


class TourListCollection(ApCollection):
    SerializerFactory = ApHtmxTableSerializer.with_attributes(
        record_template="tour/record.html",
        row_dictizer=tour_row_dictizer
    )

    ColumnsFactory = ApColumns.with_attributes(
        names=[
            "bulk-action",
            "title",
            "state",
            "anchor",
            "page",
            "created_at",
            "modified_at",
            "steps",
            "author_id",
            "row_actions",
        ],
        width={"bulk-action": "3%"},
        sortable={"created_at", "modified_at"},
        searchable={"title", "page"},
        labels={
            "bulk-action": tk.literal(
                tags.input_(
                    type="checkbox",
                    name="bulk_check",
                    id="bulk_check",
                    data_module="ap-bulk-check",
                    data_module_selector='input[name="entity_id"]',
                )
            ),
            "title": "Title",
            "state": "State",
            "anchor": "Anchor",
            "page": "Page",
            "created_at": "Created At",
            "modified_at": "Modified At",
            "steps": "Steps",
            "author_id": "Author",
            "row_actions": "Actions",
        },
        serializers={
            "created_at": [("date", {})],
            "modified_at": [("date", {})],
            "author_id": [("user_link", {})],
        },
    )

    DataFactory = ModelData.with_attributes(
        model=Tour,
        is_scalar=True,
        use_naive_search=True,
        use_naive_filters=True,
    )

    FiltersFactory = Filters.with_attributes(
        static_actions=[
            BulkAction(
                name="bulk-action",
                type="bulk_action",
                options={
                    "label": "Action",
                    "options": [
                        {"value": "1", "text": "Disable selected tour(s)"},
                        {"value": "2", "text": "Enable selected tour(s)"},
                        {"value": "3", "text": "Remove selected tour(s)"},
                    ],
                },
            )
        ],
        static_filters=[
            InputFilter(
                name="q",
                type="input",
                options={
                    "label": "Search",
                    "placeholder": "Search",
                },
            ),
            ButtonFilter(
                name="type",
                type="button",
                options={
                    "label": "Clear",
                    "type": "button",
                    "attrs": {
                        "onclick": "$(this).closest('form').find('input,select').val('').prevObject[0].requestSubmit()"
                    },
                },
            ),
        ],
    )
