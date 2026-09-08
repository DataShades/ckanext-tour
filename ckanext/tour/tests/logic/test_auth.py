import pytest

import ckan.plugins.toolkit as tk


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestTourManageAuth:
    def test_sysadmin_allowed(self, sysadmin):
        assert tk.check_access("tour_manage", {"user": sysadmin["name"]})

    def test_regular_user_denied(self, user):
        with pytest.raises(tk.NotAuthorized):
            tk.check_access("tour_manage", {"user": user["name"]})

    def test_anonymous_denied(self):
        with pytest.raises(tk.NotAuthorized):
            tk.check_access("tour_manage", {"user": ""})


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestPublicReadAuth:
    @pytest.mark.parametrize("action", ["tour_list", "tour_show"])
    def test_anonymous_allowed(self, action):
        assert tk.check_access(action, {"user": ""}, {})
