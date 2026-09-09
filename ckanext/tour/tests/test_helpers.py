import json

import pytest

import ckan.plugins.toolkit as tk

from ckanext.tour import helpers
from ckanext.tour.model import TourStep


@pytest.mark.usefixtures("with_plugins")
class TestTourConfigHelpers:
    def test_get_config_has_all_settings(self):
        cfg = helpers.tour_get_config()

        assert set(cfg) == {"collapse_steps", "launcher_position", "tours"}
        assert isinstance(cfg["collapse_steps"], bool)
        assert cfg["launcher_position"] in ("bottom-right", "bottom-left")
        assert isinstance(cfg["tours"], list)

    def test_tour_config_is_json_and_carries_collapse_steps(self):
        parsed = json.loads(helpers.tour_get_tour_config())

        assert "collapse_steps" in parsed
        assert parsed == helpers.tour_get_config()

    def test_collapse_steps_matches_config(self):
        assert (
            helpers.tour_collapse_steps()
            is helpers.tour_get_config()["collapse_steps"]
        )


@pytest.mark.usefixtures("with_plugins")
class TestMiscHelpers:
    def test_position_options(self):
        values = {option["value"] for option in helpers.tour_get_position_options()}

        assert values == {
            TourStep.Position.bottom,
            TourStep.Position.top,
            TourStep.Position.left,
            TourStep.Position.right,
        }

    def test_random_step_id_is_unique(self):
        assert helpers.tour_random_step_id() != helpers.tour_random_step_id()

    def test_admin_panel_flag_is_bool(self):
        assert isinstance(helpers.tour_is_admin_panel_enabled(), bool)


@pytest.mark.usefixtures("with_plugins")
class TestFlattenErrors:
    def test_empty(self):
        assert helpers.tour_flatten_errors(None) == []
        assert helpers.tour_flatten_errors({}) == []

    def test_top_level_error(self):
        rows = helpers.tour_flatten_errors({"title": ["Missing value"]})

        assert rows == [{"label": "Title", "message": "Missing value"}]

    def test_step_errors_are_labelled_by_position(self):
        rows = helpers.tour_flatten_errors(
            {"steps": [{}, {"element": ["Missing value"], "image": "pick one"}]}
        )

        labels = {row["label"] for row in rows}

        assert labels == {"Step 2 — element", "Step 2 — image"}
        assert {row["message"] for row in rows} == {"Missing value", "pick one"}

    def test_mixed_top_level_and_step_errors(self):
        rows = helpers.tour_flatten_errors(
            {"title": ["Missing value"], "steps": [{"element": ["Missing value"]}]}
        )

        assert {"label": "Title", "message": "Missing value"} in rows
        assert {"label": "Step 1 — element", "message": "Missing value"} in rows


@pytest.mark.usefixtures("with_plugins")
class TestPageOptions:
    def test_first_option_is_everywhere(self, app):
        with app.flask_app.test_request_context("/"):
            options = helpers.tour_get_page_options()

        assert options[0] == {"value": "", "text": "Everywhere"}

    def test_system_endpoints_are_excluded(self, app):
        with app.flask_app.test_request_context("/"):
            values = {o["value"] for o in helpers.tour_get_page_options()}

        assert "home.index" in values
        assert "static" not in values
        assert not any(v.startswith(("api.", "webassets.", "tour.")) for v in values)

    def test_options_are_deduplicated(self, app):
        with app.flask_app.test_request_context("/"):
            values = [o["value"] for o in helpers.tour_get_page_options()]

        assert len(values) == len(set(values))


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestPageTours:
    def test_page_embeds_matching_tours_only(self, app, tour_factory):
        tour_factory(steps=[], endpoint="user.login", title="Loginonlytour")
        tour_factory(steps=[], endpoint="user.register", title="Registeronlytour")

        body = app.get(tk.url_for("user.login")).body

        assert "Loginonlytour" in body
        assert "Registeronlytour" not in body

    def test_everywhere_tour_suppressed_on_auth_pages(self, app, tour_factory):
        tour_factory(steps=[], endpoint="", title="Globaltour")

        assert "Globaltour" in app.get(tk.url_for("home.about")).body
        assert "Globaltour" not in app.get(tk.url_for("user.login")).body


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestHasTours:
    def test_false_when_no_tours(self):
        assert helpers.tour_has_tours() is False

    def test_true_with_any_tour(self, tour_factory):
        tour_factory(steps=[])

        assert helpers.tour_has_tours() is True
