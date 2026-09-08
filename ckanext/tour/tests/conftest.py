import pytest
from pytest_factoryboy import register

from ckan.lib import uploader
from ckan.tests import factories

import ckanext.tour.tests.factories as tour_factories

register(tour_factories.TourFactory, "tour")
register(tour_factories.TourStepFactory, "tour_step")


def _migrate_plugins(migrate_db_for):
    migrate_db_for("tour")
    migrate_db_for("files")


@pytest.fixture
def clean_db(with_plugins, reset_db, migrate_db_for):
    reset_db()
    _migrate_plugins(migrate_db_for)


@register(_name="user")  # pyright: ignore[reportCallIssue]
class UserFactory(factories.UserWithToken):
    pass


@register(_name="sysadmin")  # pyright: ignore[reportCallIssue]
class SysadminFactory(factories.SysadminWithToken):
    pass


@pytest.fixture
def mock_storage(monkeypatch, ckan_config, tmpdir):
    monkeypatch.setitem(ckan_config, "ckan.storage_path", str(tmpdir))
    monkeypatch.setattr(uploader, "get_storage_path", lambda: str(tmpdir))
