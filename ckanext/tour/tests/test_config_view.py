import pytest

from enum import IntEnum

import ckan.plugins.toolkit as tk

from ckanext.tour import config
from ckanext.tour.model import Tour


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
        resp = app.get(
            tk.url_for("tour.add"), headers={"Authorization": sysadmin["token"]}
        )

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
        # a missing tour must redirect back to the list, not 500 (B1). Asserting
        # on the redirect rather than a flash message in the rendered list page
        # keeps this stable across CKAN versions / session backends.
        resp = app.post(
            tk.url_for("tour.delete", tour_id="no-such-id"),
            headers={"Authorization": sysadmin["token"]},
            follow_redirects=False,
        )

        assert resp.status_code == Status.redirect
        assert tk.url_for("tour.list") in resp.headers["location"]
