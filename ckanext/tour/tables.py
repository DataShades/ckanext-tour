from __future__ import annotations

from sqlalchemy import select, func

import ckan.plugins.toolkit as tk
from ckan.types import Context

import ckanext.tables.shared as t

from ckanext.tour.model import Tour, TourStep


class TourTable(t.TableDefinition):
    @classmethod
    def check_access(cls, context: Context) -> None:
        tk.check_access("tour_manage", context)

    def __init__(self):
        steps_count = (
            select(TourStep.tour_id, func.count(TourStep.id).label("steps")).group_by(TourStep.tour_id).subquery()
        )

        super().__init__(
            name="tours",
            table_template="tour/tour_table.html",
            data_source=t.DatabaseDataSource(
                stmt=select(
                    Tour.id,
                    Tour.title,
                    Tour.state,
                    Tour.endpoint,
                    Tour.created_at,
                    Tour.modified_at,
                    Tour.author_id,
                    func.coalesce(steps_count.c.steps, 0).label("steps"),
                )
                .outerjoin(steps_count, steps_count.c.tour_id == Tour.id)
                .order_by(Tour.modified_at.desc()),
            ),
            columns=[
                t.ColumnDefinition(field="title"),
                t.ColumnDefinition(field="state"),
                t.ColumnDefinition(field="endpoint", title=tk._("Shown on")),
                t.ColumnDefinition(
                    field="created_at",
                    formatters=[(t.formatters.DateFormatter, {"date_format": "%d %B %Y"})],
                ),
                t.ColumnDefinition(field="steps", title=tk._("Steps")),
            ],
            row_actions=[
                t.RowActionDefinition(
                    action="edit",
                    label=tk._("Edit"),
                    icon="fa fa-edit",
                    callback=self.row_action_edit,
                ),
                t.RowActionDefinition(
                    action="delete",
                    label=tk._("Delete"),
                    icon="fa fa-trash",
                    callback=self.row_action_delete,
                    with_confirmation=True,
                ),
            ],
            bulk_actions=[
                t.BulkActionDefinition(
                    action="remove_tours",
                    label=tk._("Remove Selected Tours"),
                    icon="fa fa-trash",
                    callback=self.remove_tours,
                ),
                t.BulkActionDefinition(
                    action="disable_tours",
                    label=tk._("Disable Selected Tours"),
                    icon="fa fa-ban",
                    callback=self.disable_tours,
                ),
                t.BulkActionDefinition(
                    action="enable_tours",
                    label=tk._("Enable Selected Tours"),
                    icon="fa fa-check",
                    callback=self.enable_tours,
                ),
            ],
            table_actions=[
                t.TableActionDefinition(
                    action="add_tour",
                    label=tk._("Add Tour"),
                    icon="fa fa-plus",
                    callback=self.table_action_add_tour,
                ),
            ],
        )

    def table_action_add_tour(self) -> t.ActionHandlerResult:
        return t.ActionHandlerResult(
            success=True,
            redirect=tk.url_for("tour.add"),
        )

    def row_action_edit(self, row: t.Row) -> t.ActionHandlerResult:
        return t.ActionHandlerResult(
            success=True,
            redirect=tk.url_for("tour.edit", tour_id=row["id"]),
        )

    def row_action_delete(self, row: t.Row) -> t.ActionHandlerResult:
        try:
            tk.get_action("tour_remove")({"ignore_auth": True}, {"id": row["id"]})
        except tk.ValidationError:
            return t.ActionHandlerResult(success=False, error=tk._("Error deleting tour."))

        return t.ActionHandlerResult(success=True)

    def disable_tours(self, rows: list[t.Row]) -> t.ActionHandlerResult:
        Tour.set_state([row["id"] for row in rows], Tour.State.inactive)

        return t.ActionHandlerResult(success=True, message=tk._("Tour(s) disabled."))

    def enable_tours(self, rows: list[t.Row]) -> t.ActionHandlerResult:
        Tour.set_state([row["id"] for row in rows], Tour.State.active)

        return t.ActionHandlerResult(success=True, message=tk._("Tour(s) enabled."))

    def remove_tours(self, rows: list[t.Row]) -> t.ActionHandlerResult:
        for row in rows:
            tk.get_action("tour_remove")({"ignore_auth": True}, {"id": row["id"]})

        return t.ActionHandlerResult(success=True, message=tk._("Tour(s) removed."))
