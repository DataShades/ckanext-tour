from io import BytesIO

import pytest
from faker import Faker
from pytest_factoryboy import register

from ckan.lib import uploader
from ckan.tests import factories

import ckanext.tour.tests.factories as tour_factories
from ckanext.tour.tests.helpers import IMAGE_DATA, FakeFileStorage

fake = Faker()

register(tour_factories.TourFactory, "tour")
register(tour_factories.TourStepFactory, "tour_step")
register(tour_factories.TourStepImageFactory)


def _migrate_plugins(migrate_db_for):
    migrate_db_for("tour")
    migrate_db_for("files")


@pytest.fixture
def clean_db(with_plugins, reset_db, migrate_db_for):
    reset_db()
    _migrate_plugins(migrate_db_for)


@register
class UserFactory(factories.User):
    pass


@register(_name="sysadmin")
class SysadminFactory(factories.Sysadmin):
    pass


@pytest.fixture
def mock_storage(monkeypatch, ckan_config, tmpdir):
    monkeypatch.setitem(ckan_config, "ckan.storage_path", str(tmpdir))
    monkeypatch.setattr(uploader, "get_storage_path", lambda: str(tmpdir))


@pytest.fixture
def tour_image_data():
    def _prepare_data(**kwargs):
        data = {
            "upload": FakeFileStorage(BytesIO(IMAGE_DATA), "step.jpeg"),
            "url": None,
        }

        data.update(**kwargs)

        return data

    return _prepare_data
