import pytest

from enum import IntEnum

import ckan.plugins.toolkit as tk

from ckanext.tour import config


class Status(IntEnum):
    success = 200
    forbidden = 403
    not_found = 404


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourConfigView:
    def test_settings_page_renders_for_sysadmin(self, app, sysadmin):
        env = {"REMOTE_USER": sysadmin["name"]}
        resp = app.get(tk.url_for("tour.config"), extra_environ=env)

        assert resp.status_code == Status.success

    def test_settings_page_forbidden_for_regular_user(self, app, user):
        env = {"REMOTE_USER": user["name"]}
        resp = app.get(tk.url_for("tour.config"), extra_environ=env, status=Status.forbidden)

        assert resp.status_code == Status.forbidden

    def test_settings_update_persists_options(self, app, sysadmin):
        env = {"REMOTE_USER": sysadmin["name"]}

        app.post(
            tk.url_for("tour.config"),
            data={
                config.CONF_AUTOPLAY: "true",
                config.CONF_DEFAULT_ANCHOR: ".custom-anchor",
                config.CONF_COLLAPSE_STEPS: "false",
            },
            extra_environ=env,
        )

        assert tk.config[config.CONF_AUTOPLAY] is True
        assert tk.config[config.CONF_DEFAULT_ANCHOR] == ".custom-anchor"
        assert tk.config[config.CONF_COLLAPSE_STEPS] is False


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourListView:
    def test_list_page_renders_for_sysadmin(self, app, sysadmin):
        env = {"REMOTE_USER": sysadmin["name"]}
        resp = app.get(tk.url_for("tour.list"), extra_environ=env)

        assert resp.status_code == Status.success

    def test_list_page_forbidden_for_regular_user(self, app, user):
        env = {"REMOTE_USER": user["name"]}
        app.get(tk.url_for("tour.list"), extra_environ=env, status=Status.forbidden)

    def test_add_tour_table_action_redirects_to_add_page(self, app, sysadmin):
        env = {"REMOTE_USER": sysadmin["name"]}

        resp = app.post(
            tk.url_for("tour.list"),
            data={"table_action": "add_tour"},
            extra_environ=env,
        )

        assert resp.json["success"] is True
        assert resp.json["redirect"] == tk.url_for("tour.add")
