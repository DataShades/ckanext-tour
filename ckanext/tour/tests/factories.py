from factory.declarations import LazyFunction
from factory.faker import Faker

from ckan.tests import factories

from ckanext.tour import model as tour_model


class TourStepFactory(factories.CKANFactory):
    class Meta:  # type: ignore
        model = tour_model.TourStep
        action = "tour_step_create"

    id = Faker("uuid4")
    title = Faker("sentence")
    element = ".dataset-list"
    intro = Faker("sentence")
    position = tour_model.TourStep.Position.bottom
    tour_id = LazyFunction(lambda: TourFactory()["id"])
    image_id = None


class TourFactory(factories.CKANFactory):
    class Meta:  # type: ignore
        model = tour_model.Tour
        action = "tour_create"

    id = Faker("uuid4")
    title = Faker("sentence")
    anchor = Faker("sentence")
    page = "/dataset"
    author_id = LazyFunction(lambda: factories.User()["id"])  # type: ignore
    steps = LazyFunction(lambda self: [vars(TourStepFactory.stub(tour_id=self.id))])
