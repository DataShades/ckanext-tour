import pytest

import ckanext.tour.model as tour_model
from ckanext.tour.default_tours import DEFAULT_TOURS, create_default_tours


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestCreateDefaultTours:
    def test_creates_every_default_tour(self, sysadmin):
        created = create_default_tours(sysadmin["id"])

        assert len(created) == len(DEFAULT_TOURS)
        assert len(tour_model.Tour.all()) == len(DEFAULT_TOURS)

    def test_created_tour_matches_its_definition(self, sysadmin):
        definition = DEFAULT_TOURS[0]

        created = create_default_tours(sysadmin["id"])[0]

        assert created["title"] == {"en": definition["title"]}
        assert created["endpoint"] == definition.get("endpoint", "")
        assert created["author_id"] == sysadmin["id"]
        assert len(created["steps"]) == len(definition["steps"])

        for step, expected in zip(created["steps"], definition["steps"], strict=True):
            assert step["element"] == expected["element"]
            assert step["title"] == {"en": expected["title"]}
            assert step["intro"] == {"en": expected["intro"]}

    def test_running_twice_creates_nothing_new(self, sysadmin):
        create_default_tours(sysadmin["id"])

        second_run = create_default_tours(sysadmin["id"])

        assert second_run == []
        assert len(tour_model.Tour.all()) == len(DEFAULT_TOURS)

    def test_skips_only_the_tours_that_already_exist(self, sysadmin, tour_factory):
        tour_factory(steps=[], title=DEFAULT_TOURS[0]["title"])

        created = create_default_tours(sysadmin["id"])

        assert len(created) == len(DEFAULT_TOURS) - 1
        assert len(tour_model.Tour.all()) == len(DEFAULT_TOURS)

    def test_accepts_a_custom_list_of_tours(self, sysadmin):
        custom = [
            {
                "title": "Custom tour",
                "steps": [{"element": "#x", "title": "Step", "intro": "Intro"}],
            },
        ]

        created = create_default_tours(sysadmin["id"], tours=custom)

        assert len(created) == 1
        assert created[0]["title"] == {"en": "Custom tour"}
