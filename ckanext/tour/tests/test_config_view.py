import pytest

from enum import IntEnum

from werkzeug.datastructures import MultiDict

from ckan import authz, types
import ckan.plugins.toolkit as tk

from ckanext.tour import config
from ckanext.tour.model import Tour, TourStep
from ckanext.tour.utils import parse_step_forms


@pytest.fixture
def delegated_tour_manager(monkeypatch):
    """Simulate a site that overrides ``tour_manage`` to grant a non-sysadmin
    access to the tour admin (which ``auth.py`` explicitly invites)."""
    authz.auth_functions_list()  # force the lazy cache to build first
    monkeypatch.setitem(
        authz._AuthFunctions._functions,
        "tour_manage",
        lambda context, data_dict: {"success": True},
    )


class Status(IntEnum):
    success = 200
    redirect = 302
    forbidden = 403
    not_found = 404


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourConfigView:
    def test_settings_page_renders_for_sysadmin(self, app, sysadmin):
        resp = app.get(tk.url_for("tour.config"), headers={"Authorization": sysadmin["token"]})

        assert resp.status_code == Status.success

    def test_settings_page_forbidden_for_regular_user(self, app, user):
        resp = app.get(tk.url_for("tour.config"), headers={"Authorization": user["token"]}, status=Status.forbidden)

        assert resp.status_code == Status.forbidden

    def test_settings_page_forbidden_for_delegated_manager(self, app, user, delegated_tour_manager):
        # passes the blueprint's tour_manage guard, but settings are sysadmin-only
        resp = app.get(
            tk.url_for("tour.config"),
            headers={"Authorization": user["token"]},
            status=Status.forbidden,
        )

        assert resp.status_code == Status.forbidden

    def test_settings_update_forbidden_not_500_for_delegated_manager(self, app, user, delegated_tour_manager):
        before = config.get_launcher_position()
        target = "bottom-left" if before != "bottom-left" else "bottom-right"

        resp = app.post(
            tk.url_for("tour.config"),
            data={
                config.CONF_LAUNCHER_POSITION: target,
                config.CONF_COLLAPSE_STEPS: "false",
            },
            headers={"Authorization": user["token"]},
            status=Status.forbidden,
        )

        assert resp.status_code == Status.forbidden
        assert config.get_launcher_position() == before

    def test_settings_update_persists_options(self, app, sysadmin):
        app.post(
            tk.url_for("tour.config"),
            data={
                config.CONF_LAUNCHER_POSITION: "bottom-left",
                config.CONF_COLLAPSE_STEPS: "false",
            },
            headers={"Authorization": sysadmin["token"]},
        )

        # assert via the helpers: CKAN stores runtime-editable options back as
        # raw strings, so tk.config[...] is not the coerced value
        assert config.get_launcher_position() == "bottom-left"
        assert config.is_collapse_steps_enabled() is False


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourListView:
    def test_list_page_renders_for_sysadmin(self, app, sysadmin):
        resp = app.get(tk.url_for("tour.list"), headers={"Authorization": sysadmin["token"]})

        assert resp.status_code == Status.success

    def test_list_page_forbidden_for_regular_user(self, app, user):
        app.get(tk.url_for("tour.list"), headers={"Authorization": user["token"]}, status=Status.forbidden)

    def test_add_tour_table_action_redirects_to_add_page(self, app, sysadmin):
        resp = app.post(
            tk.url_for("tour.list"),
            data={"table_action": "add_tour"},
            headers={"Authorization": sysadmin["token"]},
        )

        assert resp.json["success"] is True
        assert resp.json["redirect"] == tk.url_for("tour.add")


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourFormViews:
    def test_add_page_renders(self, app, sysadmin):
        resp = app.get(tk.url_for("tour.add"), headers={"Authorization": sysadmin["token"]})

        assert resp.status_code == Status.success

    def test_add_page_forbidden_for_regular_user(self, app, user):
        app.get(
            tk.url_for("tour.add"),
            headers={"Authorization": user["token"]},
            status=Status.forbidden,
        )

    def test_edit_page_renders(self, app, sysadmin, tour_factory):
        tour = tour_factory(steps=[])

        resp = app.get(
            tk.url_for("tour.edit", tour_id=tour["id"]),
            headers={"Authorization": sysadmin["token"]},
        )

        assert resp.status_code == Status.success

    def test_edit_missing_tour_returns_404(self, app, sysadmin):
        resp = app.get(
            tk.url_for("tour.edit", tour_id="no-such-id"),
            headers={"Authorization": sysadmin["token"]},
            status=Status.not_found,
        )

        assert resp.status_code == Status.not_found

    def test_edit_post_updates_and_redirects(self, app, sysadmin, tour_factory):
        tour = tour_factory(steps=[], title="Original", endpoint="")

        resp = app.post(
            tk.url_for("tour.edit", tour_id=tour["id"]),
            data=MultiDict(
                [
                    ("title[en]", "Updated"),
                    ("endpoint", "dataset.search"),
                    ("state", Tour.State.active),
                ]
            ),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.redirect
        assert tk.url_for("tour.list") in resp.headers["location"]

        updated = TourStep.get_by_tour(tour["id"])
        assert updated == []

        shown = tk.get_action("tour_show")(
            {"user": sysadmin["name"], "ignore_auth": True},
            {"id": tour["id"]},
        )
        assert shown["title"] == {"en": "Updated"}
        assert shown["endpoint"] == "dataset.search"

    def test_edit_post_missing_tour_returns_404(self, app, sysadmin):
        resp = app.post(
            tk.url_for("tour.edit", tour_id="no-such-id"),
            data=MultiDict([("title[en]", "Updated")]),
            headers={"Authorization": sysadmin["token"]},
            status=Status.not_found,
        )

        assert resp.status_code == Status.not_found

    def test_edit_post_missing_default_locale_rerenders_with_errors(self, app, sysadmin, tour_factory):
        """Submitting a translation for a non-default locale only must not
        silently drop the requirement that the default locale be filled in --
        the form re-renders with the validation error instead of saving."""
        tour = tour_factory(steps=[], title="Original")

        resp = app.post(
            tk.url_for("tour.edit", tour_id=tour["id"]),
            data=MultiDict([("title[es]", "Solo en espanol")]),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.success

        body = resp.get_data(as_text=True)
        assert "Missing value for the default language" in body

        shown = tk.get_action("tour_show")(
            {"user": sysadmin["name"], "ignore_auth": True},
            {"id": tour["id"]},
        )
        assert shown["title"] == {"en": "Original"}

    def test_delete_confirmation_page_renders(self, app, sysadmin, tour_factory):
        tour = tour_factory(steps=[])

        resp = app.get(
            tk.url_for("tour.delete", tour_id=tour["id"]),
            headers={"Authorization": sysadmin["token"]},
        )

        assert resp.status_code == Status.success

    def test_delete_confirmation_missing_tour_returns_404(self, app, sysadmin):
        resp = app.get(
            tk.url_for("tour.delete", tour_id="no-such-id"),
            headers={"Authorization": sysadmin["token"]},
            status=Status.not_found,
        )

        assert resp.status_code == Status.not_found

    def test_delete_post_removes_the_tour(self, app, sysadmin, tour_factory):
        tour = tour_factory(steps=[])

        resp = app.post(
            tk.url_for("tour.delete", tour_id=tour["id"]),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.redirect
        assert tk.url_for("tour.list") in resp.headers["location"]
        assert Tour.get(tour["id"]) is None

    def test_delete_post_missing_tour_does_not_500(self, app, sysadmin):
        # a missing tour must redirect back to the list.
        resp = app.post(
            tk.url_for("tour.delete", tour_id="no-such-id"),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.redirect
        assert tk.url_for("tour.list") in resp.headers["location"]


class TestParseStepForms:
    """The step form fields are namespaced per step (``step[<id>][title]``) so a
    missing or duplicated field for one step can't shift another step's data."""

    def test_fields_are_grouped_by_step_id(self):
        form = MultiDict()
        form.add("step_ids", "s1")
        form.add("step_ids", "s2")
        for name, value in [
            ("step[s1][id]", ""),
            ("step[s1][title]", "First"),
            ("step[s1][element]", ".a"),
            ("step[s1][image_id]", "img-1"),
            ("step[s2][id]", "db-2"),
            ("step[s2][title]", "Second"),
            ("step[s2][element]", ".b"),
        ]:
            form.add(name, value)

        steps = parse_step_forms(form)

        assert [s["title"] for s in steps] == ["First", "Second"]
        assert [s["element"] for s in steps] == [".a", ".b"]
        # s1 keeps its image; s2 simply has no image_id key -- no shifting
        assert steps[0]["image_id"] == "img-1"
        assert "image_id" not in steps[1]
        assert steps[1]["id"] == "db-2"

    def test_step_ids_field_drives_ordering(self):
        form = MultiDict()
        form.add("step_ids", "s2")
        form.add("step_ids", "s1")
        form.add("step[s1][title]", "First")
        form.add("step[s2][title]", "Second")

        assert [s["title"] for s in parse_step_forms(form)] == ["Second", "First"]

    def test_step_missing_from_step_ids_is_still_returned(self):
        form = MultiDict()
        form.add("step_ids", "s1")
        form.add("step[s1][title]", "First")
        form.add("step[s2][title]", "Second")

        assert {s["title"] for s in parse_step_forms(form)} == {"First", "Second"}

    def test_no_steps(self):
        assert parse_step_forms(MultiDict({"title": "t"})) == []


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourStepFormSubmission:
    def _context(self, sysadmin) -> types.Context:
        return types.Context(user=sysadmin["name"], ignore_auth=True)

    def test_create_keeps_step_fields_grouped_when_a_step_omits_a_field(self, app, sysadmin):
        data = MultiDict(
            [
                ("title[en]", "Grouped tour"),
                ("endpoint", ""),
                ("step_ids", "s1"),
                ("step_ids", "s2"),
                ("step[s1][title]", "Step one"),
                ("step[s1][element]", ".one"),
                ("step[s1][position]", "bottom"),
                ("step[s1][intro]", "intro one"),
                # s2 deliberately omits `intro` entirely
                ("step[s2][title]", "Step two"),
                ("step[s2][element]", ".two"),
                ("step[s2][position]", "top"),
            ]
        )

        resp = app.post(
            tk.url_for("tour.add"),
            data=data,
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.redirect

        tour = tk.get_action("tour_list")(self._context(sysadmin), {})[0]
        full = tk.get_action("tour_show")(self._context(sysadmin), {"id": tour["id"]})
        steps = full["steps"]

        assert [s["title"] for s in steps] == [{"en": "Step one"}, {"en": "Step two"}]
        assert [s["element"] for s in steps] == [".one", ".two"]
        assert steps[0]["intro"] == {"en": "intro one"}
        assert not steps[1]["intro"]


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourStepDeleteView:
    def test_delete_step_removes_it_and_returns_204(self, app, sysadmin, tour_factory):
        tour = tour_factory()
        step_id = tour["steps"][0]["id"]

        app.post(
            tk.url_for("tour.delete_step", tour_step_id=step_id),
            headers={"Authorization": sysadmin["token"]},
            status=204,
        )

        assert TourStep.get(step_id) is None

    def test_delete_missing_step_reports_an_error(self, app, sysadmin):
        resp = app.post(
            tk.url_for("tour.delete_step", tour_step_id="no-such-step"),
            headers={"Authorization": sysadmin["token"]},
            status=409,
        )

        # the body carries the actual reason for the client to surface
        body = resp.get_data(as_text=True)
        assert "Could not delete step" in body
        assert "no-such-step" in body


@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestTourPreview:
    def _preview_form(self):
        return MultiDict(
            [
                ("title[en]", "Preview me"),
                ("endpoint", "dataset.search"),
                ("step_ids", "s1"),
                ("step[s1][element]", ".dataset-list"),
                ("step[s1][intro]", "a preview step"),
                ("step[s1][position]", "bottom"),
            ]
        )

    def test_preview_redirects_to_the_target_page_with_the_flag(self, app, sysadmin):
        resp = app.post(
            tk.url_for("tour.preview"),
            data=self._preview_form(),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.redirect
        location = resp.headers["location"]
        assert "/dataset/" in location
        assert "_tour_preview=session" in location

    def test_preview_tour_is_embedded_on_the_target_page(self, app, sysadmin):
        app.post(
            tk.url_for("tour.preview"),
            data=self._preview_form(),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        # the test client keeps the session cookie set by the preview POST
        page = app.get(
            "/dataset/?_tour_preview=session",
            headers={"Authorization": sysadmin["token"]},
        )

        body = page.get_data(as_text=True)
        assert "Preview me" in body
        assert "a preview step" in body

    def test_preview_is_not_persisted(self, app, sysadmin):
        app.post(
            tk.url_for("tour.preview"),
            data=self._preview_form(),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert Tour.all() == []
