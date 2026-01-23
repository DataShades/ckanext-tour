from __future__ import annotations

from flask import Blueprint

from ckanext.ap_main.utils import ap_before_request
from ckanext.ap_main.views.generics import ApConfigurationPageView
from ckanext.tables.shared import GenericTableView

from ckanext.tour.tables import TourTable
from ckanext.tour.views.tour_add import TourAddStepView, TourAddView
from ckanext.tour.views.tour_delete import TourDeleteView, TourStepDeleteView
from ckanext.tour.views.tour_update import TourUpdateView

tour = Blueprint("tour", __name__, url_prefix="/admin_panel/config/tour")
tour.before_request(ap_before_request)


tour.add_url_rule("/new", view_func=TourAddView.as_view("add"))
tour.add_url_rule("/delete/<tour_id>", view_func=TourDeleteView.as_view("delete"))
tour.add_url_rule("/delete_step/<tour_step_id>", view_func=TourStepDeleteView.as_view("delete_step"))
tour.add_url_rule("/edit/<tour_id>", view_func=TourUpdateView.as_view("edit"))
tour.add_url_rule("/add_step", view_func=TourAddStepView.as_view("add_step"))

tour.add_url_rule(
    "/config",
    view_func=ApConfigurationPageView.as_view("config", "tour_config"),
)

tour.add_url_rule("/list", view_func=GenericTableView.as_view("list", table=TourTable))


def get_blueprints():
    return [tour]
