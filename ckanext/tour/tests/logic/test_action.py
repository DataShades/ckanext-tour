import pytest

import ckan.plugins.toolkit as tk
from ckan.tests.helpers import call_action

import ckanext.tour.model as tour_model


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourCreate:
    def test_basic_create(self, tour_factory):
        tour = tour_factory()

        assert tour["id"]
        assert tour["anchor"]
        assert tour["author_id"]
        assert tour["created_at"]
        assert tour["modified_at"]
        assert tour["title"]
        assert tour["page"]
        assert tour["state"] == tour_model.Tour.State.active
        assert tour["steps"][0]["id"]
        assert tour["steps"][0]["element"]
        assert tour["steps"][0]["image"]
        assert tour["steps"][0]["intro"]
        assert tour["steps"][0]["position"]
        assert tour["steps"][0]["title"]
        assert tour["steps"][0]["tour_id"] == tour["id"]


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourStepCreate:
    def test_basic_create(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        tour_step = tour_step_factory(tour_id=tour["id"])

        tour = call_action("tour_show", id=tour["id"])

        assert tour["steps"][0]["id"] == tour_step["id"]
        assert tour["steps"][0]["index"] == 1

    def test_wrong_position(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError, match="Value must be one of"):
            tour_step_factory(tour_id=tour["id"], position="xxx")

    def test_upload_image(self, tour_factory, tour_step_factory, tour_image_data):
        tour = tour_factory(steps=[])

        assert tour_step_factory(tour_id=tour["id"], image=[tour_image_data()])

    def test_upload_multiple_image(self, tour_factory, tour_step_factory, tour_image_data):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError, match="only 1 image for step allowed"):
            tour_step_factory(tour_id=tour["id"], image=[tour_image_data(), tour_image_data()])

    def test_missing_element(self, tour_factory, tour_step_factory, tour_image_data):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError, match="Missing value"):
            tour_step_factory(tour_id=tour["id"], element=None)

    def test_error_on_child_should_clear_parent(self, sysadmin):
        """Test error on creating step should not create the tour.

        When we are creating from the UI, we are passing all the tour data at
        once and if something is wrong, do not create anything.

        TODO: currently I wasn't able to check if something is wrong with Image data
        """
        with pytest.raises(tk.ValidationError):
            call_action(
                "tour_create",
                title="test tour",
                anchor="#page",
                page="/datasets/",
                steps=[
                    {
                        "title": "step #1",
                        "element": ".header",
                        "intro": "test intro",
                    }
                ],
            )

        assert not tour_model.Tour.all()

        call_action(
            "tour_create",
            title="test tour",
            anchor="#page",
            page="/datasets/",
            author_id=sysadmin["id"],
            steps=[
                {
                    "title": "step #1",
                    "element": ".header",
                    "intro": "test intro",
                }
            ],
        )

        assert tour_model.Tour.all()


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourUpdate:
    def test_update_not_existing(self):
        with pytest.raises(
            tk.ValidationError,
            match="The tour with an id xxx doesn't exist",
        ):
            call_action("tour_update", id="xxx")

    def test_update_existing(self, tour_factory):
        tour = tour_factory(steps=[], title="test-1")

        tour = call_action("tour_show", id=tour["id"])
        tour["title"] = "xxx"
        tour["page"] = "yyy"
        tour["anchor"] = "zzz"

        updated_tour = call_action("tour_update", **tour)

        assert updated_tour["title"] == "xxx"
        assert updated_tour["page"] == "yyy"
        assert updated_tour["anchor"] == "zzz"


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourStepUpdate:
    def test_update_not_existing(self):
        with pytest.raises(
            tk.ValidationError,
            match="The tour step with an id xxx doesn't exist",
        ):
            call_action("tour_step_update", id="xxx")


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourList:
    def test_empty_list(self):
        result = call_action("tour_list")

        assert not result

    def test_with_items(self, tour):
        result = call_action("tour_list")

        assert result
        assert result[0]["id"] == tour["id"]

    def test_filter_by_state(self, tour_factory):
        tour_factory(steps=[])
        tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        result = call_action("tour_list")

        assert len(result) == 2  # noqa: PLR2004

        result = call_action("tour_list", state=tour_model.Tour.State.inactive)

        assert len(result) == 1

    def test_filter_by_wrong_state(self):
        with pytest.raises(tk.ValidationError, match="Value must be one of"):
            call_action("tour_list", state="deleted")


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestStepImageCreate:
    """Each step could have 1 image.

    It could be created either from uploaded file, or by URL
    """

    def test_create_from_url(self, tour_step, tour_step_image_factory):
        """You should be able to create a step image entity from a URL.

        We are not checking that this URL somehow related to an image, it's up
        to user

        We are not validating URL, because if user choose to upload a file,
        the URL will be a filename which is obviosly not a valid URL.

        """
        image_from_url = tour_step_image_factory(tour_step_id=tour_step["id"], url="https://image.url", upload=None)

        assert not image_from_url["file_id"]
        assert image_from_url["url"] == "https://image.url"

    def test_create_from_file(self, tour_step, tour_step_image_factory):
        """You should be able to create a step image entity from a real file.

        The factory has a mock file object by default.
        """
        image_from_file = tour_step_image_factory(tour_step_id=tour_step["id"])

        assert image_from_file["file_id"]
        assert image_from_file["url"]

    def test_create_from_nothing(self, tour_step, tour_step_image_factory):
        """You have to provide at least 1 source of image."""
        with pytest.raises(tk.ValidationError, match="You have to provide either file or URL"):
            tour_step_image_factory(tour_step_id=tour_step["id"], url=None, upload=None)
