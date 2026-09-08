import pytest

from ckan import model

from ckanext.tour.model import Tour, TourStep


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourModel:
    def test_get_and_get_by_anchor(self, tour_factory):
        tour = tour_factory(steps=[], anchor="#uniq")

        assert Tour.get(tour["id"]).id == tour["id"]
        assert Tour.get_by_anchor("#uniq").id == tour["id"]
        assert Tour.get("no-such-id") is None

    def test_all_returns_every_tour(self, tour_factory):
        ids = {tour_factory(steps=[])["id"] for _ in range(3)}

        assert {t.id for t in Tour.all()} == ids

    def test_set_state_bulk_update(self, tour_factory):
        t1 = tour_factory(steps=[])
        t2 = tour_factory(steps=[])

        affected = Tour.set_state([t1["id"], t2["id"]], Tour.State.inactive)

        assert affected == 2  # noqa: PLR2004
        assert Tour.get(t1["id"]).state == Tour.State.inactive
        assert Tour.get(t2["id"]).state == Tour.State.inactive

    def test_set_state_empty_ids_is_noop(self):
        assert Tour.set_state([], Tour.State.inactive) == 0

    def test_dictize_field_selection(self, tour_factory):
        tour = Tour.get(tour_factory(steps=[])["id"])

        assert set(tour.dictize({}, ["id", "state"])) == {"id", "state"}
        assert "steps" not in tour.dictize({}, ["id"])

    def test_delete_cascades_to_steps(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        tour_step_factory(tour_id=tour["id"])
        tour_step_factory(tour_id=tour["id"])

        Tour.get(tour["id"]).delete()
        model.Session.commit()

        assert TourStep.get_by_tour(tour["id"]) == []


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourStepModel:
    def test_next_index_walks_up(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])

        assert TourStep.next_index(tour["id"]) == 1

        tour_step_factory(tour_id=tour["id"])

        assert TourStep.next_index(tour["id"]) == 2  # noqa: PLR2004

    def test_image_empty_without_file(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        step = TourStep.get(tour_step_factory(tour_id=tour["id"])["id"])

        assert step.image == ""
