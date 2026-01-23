from __future__ import annotations

from flask import Blueprint

from ckanext.ap_main.utils import ap_before_request

tour = Blueprint("tour_config", __name__)
tour.before_request(ap_before_request)
