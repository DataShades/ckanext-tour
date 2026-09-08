import pytest
import responses

import ckan.plugins.toolkit as tk
from ckan.tests.helpers import call_action

import ckanext.tour.model as tour_model
from ckanext.tour.tests.helpers import FakeFileStorage


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
        assert tour["steps"][0]["intro"]
        assert tour["steps"][0]["position"]
        assert tour["steps"][0]["title"]
        assert tour["steps"][0]["image_url"] == ""
        assert tour["steps"][0]["tour_id"] == tour["id"]

    def test_html_like_anchor_rejected(self, sysadmin):
        with pytest.raises(tk.ValidationError, match="cannot contain"):
            call_action(
                "tour_create",
                title="t",
                anchor="<script>alert(1)</script>",
                author_id=sysadmin["id"],
                steps=[],
            )


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

    def test_missing_element(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError, match="Missing value"):
            tour_step_factory(tour_id=tour["id"], element=None)

    def test_html_like_element_rejected(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError, match="cannot contain"):
            tour_step_factory(
                tour_id=tour["id"], element="<img src=x onerror=alert(1)>"
            )

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

    def test_no_fl_returns_every_field(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list")

        assert set(result[0]) == {
            "id",
            "title",
            "author_id",
            "state",
            "created_at",
            "modified_at",
            "anchor",
            "page",
            "steps",
        }

    def test_fl_as_list_limits_fields(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", fl=["id", "anchor"])

        assert set(result[0]) == {"id", "anchor"}

    def test_fl_as_single_string_field(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", fl="id")

        assert set(result[0]) == {"id"}

    def test_fl_without_steps_omits_them(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", fl=["id"])

        assert "steps" not in result[0]

    def test_fl_with_steps_includes_them(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        tour_step_factory(tour_id=tour["id"])

        result = call_action("tour_list", fl=["id", "steps"])

        assert [step["id"] for step in result[0]["steps"]]

    def test_fl_ignores_unknown_fields(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", fl=["id", "bogus"])

        assert set(result[0]) == {"id"}

    def test_fl_deduplicates(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", fl=["id", "id", "state"])

        assert set(result[0]) == {"id", "state"}


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourVisibility:
    """`tour_list` / `tour_show` are public but hide non-active tours and
    manager-only fields from non-managers."""

    anon = {"ignore_auth": False, "user": ""}

    def _manager(self, sysadmin):
        return {"ignore_auth": False, "user": sysadmin["name"]}

    def test_list_hides_inactive_from_anon(self, tour_factory):
        tour_factory(steps=[], state=tour_model.Tour.State.active)
        tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        result = call_action("tour_list", context=dict(self.anon))

        assert [t["state"] for t in result] == [tour_model.Tour.State.active]

    def test_list_state_param_ignored_for_anon(self, tour_factory):
        tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        result = call_action(
            "tour_list",
            context=dict(self.anon),
            state=tour_model.Tour.State.inactive,
        )

        assert result == []

    def test_list_shows_everything_to_manager(self, tour_factory, sysadmin):
        tour_factory(steps=[], state=tour_model.Tour.State.active)
        tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        result = call_action("tour_list", context=self._manager(sysadmin))

        assert len(result) == 2  # noqa: PLR2004
        assert all("author_id" in t for t in result)

    def test_list_strips_author_id_for_anon(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", context=dict(self.anon))

        assert "author_id" not in result[0]

    def test_show_active_tour_to_anon_without_author(self, tour_factory):
        tour = tour_factory(steps=[])

        result = call_action("tour_show", context=dict(self.anon), id=tour["id"])

        assert result["id"] == tour["id"]
        assert "author_id" not in result

    def test_show_inactive_tour_hidden_from_anon(self, tour_factory):
        tour = tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        with pytest.raises(tk.ObjectNotFound):
            call_action("tour_show", context=dict(self.anon), id=tour["id"])

    def test_show_inactive_tour_visible_to_manager(self, tour_factory, sysadmin):
        tour = tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        result = call_action(
            "tour_show", context=self._manager(sysadmin), id=tour["id"]
        )

        assert result["id"] == tour["id"]
        assert result["author_id"]


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourStepImage:
    """A step can carry one image, from an uploaded file or a URL."""

    def _tour(self, sysadmin):
        return call_action(
            "tour_create",
            context={"user": sysadmin["name"]},
            title="t",
            anchor="#a",
            page="/p",
            author_id=sysadmin["id"],
            steps=[],
        )

    def test_from_upload(self, sysadmin):
        tour = self._tour(sysadmin)

        step = call_action(
            "tour_step_create",
            context={"user": sysadmin["name"]},
            tour_id=tour["id"],
            title="s",
            element=".x",
            intro="i",
            image_upload=FakeFileStorage(),
        )

        assert step["image_id"]

    @responses.activate
    def test_from_url(self, sysadmin):
        responses.add_passthru("http://127.0.0.1:8983")
        responses.head(
            "https://example.com/a.png",
            headers={"content-type": "image/png", "content-length": "72"},
        )
        tour = self._tour(sysadmin)

        step = call_action(
            "tour_step_create",
            context={"user": sysadmin["name"]},
            tour_id=tour["id"],
            title="s",
            element=".x",
            intro="i",
            image_url="https://example.com/a.png",
        )

        assert step["image_id"]
        assert step["image_url"] == "https://example.com/a.png"

    def test_both_sources_rejected(self, sysadmin):
        tour = self._tour(sysadmin)

        with pytest.raises(tk.ValidationError, match="either an image URL or upload"):
            call_action(
                "tour_step_create",
                context={"user": sysadmin["name"]},
                tour_id=tour["id"],
                title="s",
                element=".x",
                intro="i",
                image_upload=FakeFileStorage(),
                image_url="https://example.com/a.png",
            )

    def test_no_source_leaves_image_empty(self, sysadmin):
        tour = self._tour(sysadmin)

        step = call_action(
            "tour_step_create",
            context={"user": sysadmin["name"]},
            tour_id=tour["id"],
            title="s",
            element=".x",
            intro="i",
        )

        assert not step["image_id"]

    @responses.activate
    def test_replacing_image_on_update(self, sysadmin):
        responses.add_passthru("http://127.0.0.1:8983")
        responses.head(
            "https://example.com/a.png",
            headers={"content-type": "image/png"},
        )
        tour = self._tour(sysadmin)
        step = call_action(
            "tour_step_create",
            context={"user": sysadmin["name"]},
            tour_id=tour["id"],
            title="s",
            element=".x",
            intro="i",
            image_upload=FakeFileStorage(),
        )
        original = step["image_id"]

        updated = call_action(
            "tour_step_update",
            context={"user": sysadmin["name"]},
            id=step["id"],
            title="s",
            element=".x",
            intro="i",
            position="bottom",
            image_url="https://example.com/a.png",
        )

        assert updated["image_id"]
        assert updated["image_id"] != original
