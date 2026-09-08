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
        assert tour["author_id"]
        assert tour["created_at"]
        assert tour["modified_at"]
        assert tour["title"]
        assert tour["endpoint"] == ""
        assert tour["auto_start"] is False
        assert tour["state"] == tour_model.Tour.State.active
        assert tour["steps"][0]["id"]
        assert tour["steps"][0]["element"]
        assert tour["steps"][0]["intro"]
        assert tour["steps"][0]["position"]
        assert tour["steps"][0]["title"]
        assert tour["steps"][0]["image_url"] == ""
        assert tour["steps"][0]["tour_id"] == tour["id"]

    def test_auto_start_defaults_to_false(self, sysadmin):
        tour = call_action(
            "tour_create",
            title="t",
            author_id=sysadmin["id"],
            steps=[],
        )

        assert tour["auto_start"] is False

    def test_endpoint_and_auto_start_are_stored(self, sysadmin):
        tour = call_action(
            "tour_create",
            title="t",
            endpoint="dataset.read",
            auto_start=True,
            author_id=sysadmin["id"],
            steps=[],
        )

        assert tour["endpoint"] == "dataset.read"
        assert tour["auto_start"] is True

    def test_step_error_is_namespaced_under_steps(self, sysadmin):
        """A step failure inside the action body must come back as
        ``{"steps": [...]}`` so the form can point at the offending step."""
        with pytest.raises(tk.ValidationError) as excinfo:
            call_action(
                "tour_create",
                context={"user": sysadmin["name"]},
                title="t",
                author_id=sysadmin["id"],
                steps=[
                    {"title": "ok", "element": ".a", "intro": "i"},
                    {
                        "title": "bad",
                        "element": ".b",
                        "intro": "i",
                        "image_upload": FakeFileStorage(),
                        "image_url": "https://example.com/a.png",
                    },
                ],
            )

        errors = excinfo.value.error_dict

        assert errors["steps"][0] == {}
        assert "image" in errors["steps"][1]
        assert not tour_model.Tour.all()


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
                endpoint="dataset.read",
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
            endpoint="dataset.read",
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
        tour["endpoint"] = "dataset.read"
        tour["auto_start"] = True

        updated_tour = call_action("tour_update", **tour)

        assert updated_tour["title"] == "xxx"
        assert updated_tour["endpoint"] == "dataset.read"
        assert updated_tour["auto_start"] is True

    def test_update_without_state_keeps_current_state(self, tour_factory):
        tour = tour_factory(steps=[], state=tour_model.Tour.State.inactive)

        updated = call_action("tour_update", id=tour["id"], title="t")

        assert updated["state"] == tour_model.Tour.State.inactive

    def test_update_without_auto_start_keeps_current_value(self, tour_factory):
        tour = tour_factory(steps=[], auto_start=True)

        updated = call_action("tour_update", id=tour["id"], title="t")

        assert updated["auto_start"] is True

    def test_update_can_change_state(self, tour_factory):
        tour = tour_factory(steps=[])

        updated = call_action(
            "tour_update",
            id=tour["id"],
            title="t",
            state=tour_model.Tour.State.inactive,
        )

        assert updated["state"] == tour_model.Tour.State.inactive

    def test_update_bumps_modified_at(self, tour_factory):
        tour = tour_factory(steps=[])

        updated = call_action("tour_update", id=tour["id"], title="t")

        assert updated["modified_at"] >= tour["modified_at"]

    def test_update_rejects_unknown_state(self, tour_factory):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError, match="Value must be one of"):
            call_action(
                "tour_update",
                id=tour["id"],
                title="t",
                state="deleted",
            )

    def test_step_error_is_namespaced_under_steps(self, tour_factory):
        tour = tour_factory(steps=[])

        with pytest.raises(tk.ValidationError) as excinfo:
            call_action(
                "tour_update",
                id=tour["id"],
                title="t",
                steps=[
                    {
                        "title": "bad",
                        "element": ".b",
                        "intro": "i",
                        "image_upload": FakeFileStorage(),
                        "image_url": "https://example.com/a.png",
                    },
                ],
            )

        assert "image" in excinfo.value.error_dict["steps"][0]

    def test_add_step_via_update(self, tour_factory):
        tour = tour_factory(steps=[])

        result = call_action(
            "tour_update",
            id=tour["id"],
            title="t",
            steps=[
                {"title": "s1", "element": ".x", "intro": "i", "position": "bottom"},
            ],
        )

        assert [s["title"] for s in result["steps"]] == ["s1"]

    def test_update_existing_step_via_update(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        step = tour_step_factory(tour_id=tour["id"], title="old")

        result = call_action(
            "tour_update",
            id=tour["id"],
            title="t",
            steps=[
                {
                    "id": step["id"],
                    "title": "new",
                    "element": ".x",
                    "intro": "i",
                    "position": "top",
                },
            ],
        )

        assert result["steps"][0]["title"] == "new"
        assert result["steps"][0]["position"] == "top"

    def test_step_missing_from_payload_is_deleted(
        self, tour_factory, tour_step_factory
    ):
        tour = tour_factory(steps=[])
        keep = tour_step_factory(tour_id=tour["id"], title="keep")
        drop = tour_step_factory(tour_id=tour["id"], title="drop")

        result = call_action(
            "tour_update",
            id=tour["id"],
            title="t",
            steps=[
                {
                    "id": keep["id"],
                    "title": "keep",
                    "element": ".x",
                    "intro": "i",
                    "position": "bottom",
                },
            ],
        )

        assert [s["id"] for s in result["steps"]] == [keep["id"]]
        assert tour_model.TourStep.get(drop["id"]) is None

    def test_empty_steps_payload_clears_all_steps(
        self, tour_factory, tour_step_factory
    ):
        tour = tour_factory(steps=[])
        tour_step_factory(tour_id=tour["id"])
        tour_step_factory(tour_id=tour["id"])

        result = call_action("tour_update", id=tour["id"], title="t", steps=[])

        assert result["steps"] == []
        assert tour_model.TourStep.get_by_tour(tour["id"]) == []

    def test_deleted_step_image_is_cleaned_up(self, sysadmin):
        tour = call_action(
            "tour_create",
            context={"user": sysadmin["name"]},
            title="t",
            author_id=sysadmin["id"],
            steps=[],
        )
        step = call_action(
            "tour_step_create",
            context={"user": sysadmin["name"]},
            tour_id=tour["id"],
            title="s",
            element=".x",
            intro="i",
            image_upload=FakeFileStorage(),
        )
        file_id = step["image_id"]

        call_action(
            "tour_update",
            context={"user": sysadmin["name"]},
            id=tour["id"],
            title="t",
            steps=[],
        )

        with pytest.raises(tk.ObjectNotFound):
            call_action("files_file_show", id=file_id)


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourRemove:
    def test_remove_deletes_the_tour_and_its_steps(
        self, tour_factory, tour_step_factory
    ):
        tour = tour_factory(steps=[])
        tour_step_factory(tour_id=tour["id"])
        tour_step_factory(tour_id=tour["id"])

        assert call_action("tour_remove", id=tour["id"]) is True

        assert not tour_model.Tour.all()
        assert tour_model.TourStep.get_by_tour(tour["id"]) == []

    def test_remove_missing_tour_raises(self):
        with pytest.raises(tk.ValidationError, match="doesn't exist"):
            call_action("tour_remove", id="no-such-id")


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourStepUpdate:
    def test_update_not_existing(self):
        with pytest.raises(
            tk.ValidationError,
            match="The tour step with an id xxx doesn't exist",
        ):
            call_action("tour_step_update", id="xxx")

    def test_update_persists(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        step = tour_step_factory(tour_id=tour["id"], title="old")

        call_action(
            "tour_step_update",
            id=step["id"],
            title="new",
            element=".y",
            intro="i",
            position="top",
        )

        shown = call_action("tour_show", id=tour["id"])
        assert shown["steps"][0]["title"] == "new"

    def test_partial_update_keeps_omitted_optional_fields(
        self, tour_factory, tour_step_factory
    ):
        """`title` / `intro` are `ignore_missing`; omitting them must keep the
        stored value, not raise a KeyError."""
        tour = tour_factory(steps=[])
        step = tour_step_factory(
            tour_id=tour["id"], title="keep-title", intro="keep-intro"
        )

        call_action("tour_step_update", id=step["id"], element=".changed")

        shown = call_action("tour_show", id=tour["id"])["steps"][0]
        assert shown["element"] == ".changed"
        assert shown["title"] == "keep-title"
        assert shown["intro"] == "keep-intro"


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
            "endpoint",
            "auto_start",
            "steps",
        }

    def test_fl_as_list_limits_fields(self, tour_factory):
        tour_factory(steps=[])

        result = call_action("tour_list", fl=["id", "endpoint"])

        assert set(result[0]) == {"id", "endpoint"}

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

    def test_replacing_image_deletes_the_old_file(self, sysadmin):
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
        old_file_id = step["image_id"]

        call_action(
            "tour_step_update",
            context={"user": sysadmin["name"]},
            id=step["id"],
            title="s",
            element=".x",
            intro="i",
            position="bottom",
            image_upload=FakeFileStorage(),
        )

        with pytest.raises(tk.ObjectNotFound):
            call_action("files_file_show", id=old_file_id)

    def test_removing_a_step_deletes_its_file(self, sysadmin):
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
        file_id = step["image_id"]

        call_action("tour_step_remove", id=step["id"])

        with pytest.raises(tk.ObjectNotFound):
            call_action("files_file_show", id=file_id)

    def test_removing_a_tour_deletes_its_step_files(self, sysadmin):
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
        file_id = step["image_id"]

        call_action("tour_remove", id=tour["id"])

        assert not tour_model.TourStep.get_by_tour(tour["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("files_file_show", id=file_id)
