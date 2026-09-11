from __future__ import annotations

from flask import Blueprint

from ckanext.tables.shared import GenericTableView

from ckanext.tour.tables import TourTable
from ckanext.tour.utils import before_request
from ckanext.tour.views.tour_add import TourAddStepView, TourAddView
from ckanext.tour.views.tour_config import TourConfigView
from ckanext.tour.views.tour_delete import TourDeleteView, TourStepDeleteView
from ckanext.tour.views.tour_preview import TourPreviewView
from ckanext.tour.views.tour_update import TourUpdateView

tour = Blueprint("tour", __name__, url_prefix="/ckan-admin/tour")
tour.before_request(before_request)

tour.add_url_rule("/new", view_func=TourAddView.as_view("add"))
tour.add_url_rule("/delete/<tour_id>", view_func=TourDeleteView.as_view("delete"))
tour.add_url_rule("/delete_step/<tour_step_id>", view_func=TourStepDeleteView.as_view("delete_step"))
tour.add_url_rule("/edit/<tour_id>", view_func=TourUpdateView.as_view("edit"))
tour.add_url_rule("/add_step", view_func=TourAddStepView.as_view("add_step"))
tour.add_url_rule("/preview", view_func=TourPreviewView.as_view("preview"))
tour.add_url_rule("/list", view_func=GenericTableView.as_view("list", table=TourTable))
tour.add_url_rule("/config", view_func=TourConfigView.as_view("config"))


def get_blueprints():
    return [tour]
