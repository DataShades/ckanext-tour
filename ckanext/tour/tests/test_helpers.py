import json

import pytest

from ckanext.tour import helpers
from ckanext.tour.model import TourStep


@pytest.mark.usefixtures("with_plugins")
class TestTourConfigHelpers:
    def test_get_config_has_all_settings(self):
        cfg = helpers.tour_get_config()

        assert set(cfg) == {"autoplay", "default_anchor", "collapse_steps"}
        assert isinstance(cfg["autoplay"], bool)
        assert isinstance(cfg["collapse_steps"], bool)
        assert cfg["default_anchor"]

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
