import pytest

import ckan.plugins.toolkit as tk

from ckanext.tour.logic import validators


class TestTourUrlValidator:
    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/image.png",
            "http://example.com",
            "https://sub.example.com:8000/a/b",
        ],
    )
    def test_valid_urls_pass(self, url):
        errors = {("image_url",): []}
        validators.tour_url_validator(("image_url",), {("image_url",): url}, errors, {})

        assert errors[("image_url",)] == []

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/x",
            "javascript:alert(1)",
            "not a url",
            "example.com/no-scheme",
        ],
    )
    def test_invalid_urls_add_error(self, url):
        errors = {("image_url",): []}
        validators.tour_url_validator(("image_url",), {("image_url",): url}, errors, {})

        assert errors[("image_url",)]

    @pytest.mark.parametrize("value", ["", None])
    def test_empty_value_is_skipped(self, value):
        errors = {("image_url",): []}
        validators.tour_url_validator(("image_url",), {("image_url",): value}, errors, {})

        assert errors[("image_url",)] == []


class TestTourSelectorValidator:
    @pytest.mark.parametrize(
        "selector",
        ["#step-1", ".foo > .bar", "[data-x='y']", "a.link:hover", "", None],
    )
    def test_plausible_selectors_pass(self, selector):
        assert validators.tour_selector_validator(selector) == selector

    @pytest.mark.parametrize(
        "selector",
        [
            "<img src=x onerror=alert(1)>",
            "<script>alert(1)</script>",
            ".foo<bar",
        ],
    )
    def test_html_like_values_rejected(self, selector):
        with pytest.raises(tk.Invalid, match="cannot contain"):
            validators.tour_selector_validator(selector)


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestExistenceValidators:
    def test_tour_exists(self, tour_factory):
        tour = tour_factory(steps=[])

        assert validators.tour_tour_exist(tour["id"], {}) == tour["id"]

    def test_tour_missing(self):
        with pytest.raises(tk.Invalid, match="doesn't exist"):
            validators.tour_tour_exist("no-such-id", {})

    def test_step_exists(self, tour_factory, tour_step_factory):
        tour = tour_factory(steps=[])
        step = tour_step_factory(tour_id=tour["id"])

        assert validators.tour_tour_step_exist(step["id"], {}) == step["id"]

    def test_step_missing(self):
        with pytest.raises(tk.Invalid, match="doesn't exist"):
            validators.tour_tour_step_exist("no-such-id", {})


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestTourDuplicateAnchor:
    def _run(self, anchor, data_id=None):
        data = {("anchor",): anchor}
        if data_id is not None:
            data[("id",)] = data_id
        validators.tour_duplicate_anchor(("anchor",), data, {}, {})

    def test_free_anchor_passes(self, tour_factory):
        tour_factory(steps=[], anchor="#taken")

        self._run("#free")

    def test_duplicate_anchor_rejected(self, tour_factory):
        tour_factory(steps=[], anchor="#taken")

        with pytest.raises(tk.Invalid, match="already exists"):
            self._run("#taken")

    def test_same_tour_keeping_its_anchor_passes(self, tour_factory):
        tour = tour_factory(steps=[], anchor="#taken")

        self._run("#taken", data_id=tour["id"])
