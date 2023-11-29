"""Functional tests using pytest-flask."""
from uuid import uuid4

from flask import url_for
from pytest import fixture, mark

from backend import models
from backend.schemas import schemas
from tests import asserts
from tests.db_instances import flavors, users


@fixture(scope="function")
def url(endpoint, request_id, query):
    """Fixture that return the url for the request."""
    return url_for(endpoint, flavor_id=request_id, **query)


@mark.parametrize("endpoint", ["flavors.get"], indirect=True)
@mark.parametrize("flavor_id", indirect=True, argvalues=[
    # flavors[0]['id'], # Used in flavors search
    flavors[1]["id"],
    flavors[2]["id"],
    flavors[3]["id"],
])
class TestGet:
    """Test flavors get endpoint."""

    def test_200(self, flavor, response_GET):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_flavor(response_GET.json, flavor)

    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_GET):  # noqa N803
        """GET method fails 404 if no id found."""
        assert response_GET.status_code == 404


@mark.parametrize("endpoint", ["flavors.update"], indirect=True)
@mark.parametrize("flavor_id", indirect=True, argvalues=[
    # flavors[0]['id'], # Used in flavors search
    flavors[1]["id"],
    flavors[2]["id"],
    flavors[3]["id"],
])
class TestUpdate:
    """Test flavors update endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name", "description": "new_text"},
        {"name": "new_name"},
    ])
    def test_204(self, body, response_PUT, flavor):  # noqa N803
        """PUT method succeeded 204."""
        assert response_PUT.status_code == 204
        json = schemas.Flavor().dump(flavor)
        asserts.match_body(json, body)

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name", "description": "new_text"},
    ])
    def test_401(self, flavor, response_PUT):  # noqa N803
        """PUT method fails 401 if not authorized."""
        assert response_PUT.status_code == 401
        assert flavor == models.Flavor.query.get(flavor.id)

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name", "description": "new_text"},
    ])
    def test_404(self, flavor, response_PUT):  # noqa N803
        """PUT method fails 404 if no id found."""
        assert response_PUT.status_code == 404
        assert flavor == models.Flavor.query.get(flavor.id)

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"bad_field": ""},
    ])
    def test_422(self, flavor, response_PUT):  # noqa N803
        """PUT method fails 422 if bad request body."""
        assert response_PUT.status_code == 422
        assert flavor == models.Flavor.query.get(flavor.id)


@mark.parametrize("endpoint", ["flavors.delete"], indirect=True)
@mark.parametrize("flavor_id", indirect=True, argvalues=[
    # flavors[0]['id'], # Used in flavors search
    flavors[1]["id"],
    flavors[2]["id"],
    flavors[3]["id"],
])
class TestDelete:
    """Test flavors delete endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_204(self, flavor, response_DELETE):  # noqa N803
        """DELETE method succeeded 204."""
        assert response_DELETE.status_code == 204
        assert models.Flavor.query.get(flavor.id) is None
        site = models.Site.query.get(flavor.site_id)
        assert site is not None
        assert flavor not in site.flavors

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    def test_401(self, flavor, response_DELETE):  # noqa N803
        """DELETE method fails 401 if not authorized."""
        assert response_DELETE.status_code == 401
        assert models.Flavor.query.get(flavor.id) is not None
        site = models.Site.query.get(flavor.site_id)
        assert site is not None
        assert flavor in site.flavors

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_403(self, flavor, response_DELETE):  # noqa N803
        """DELETE method fails 403 if no admin."""
        assert response_DELETE.status_code == 403
        assert models.Flavor.query.get(flavor.id) is not None
        site = models.Site.query.get(flavor.site_id)
        assert site is not None
        assert flavor in site.flavors

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, flavor, response_DELETE):  # noqa N803
        """DELETE method fails 404 if no id found."""
        assert response_DELETE.status_code == 404
        assert models.Flavor.query.get(flavor.id) is not None
        site = models.Site.query.get(flavor.site_id)
        assert site is not None
        assert flavor in site.flavors


@mark.parametrize("endpoint", ["flavors.approve"], indirect=True)
@mark.parametrize("flavor_id", indirect=True, argvalues=[
    flavors[4]["id"],
])
class TestApprove:
    """Test flavors approve endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_204(self, response_POST, flavor):  # noqa N803
        """POST method succeeded 200."""
        assert response_POST.status_code == 204
        assert flavor.status.name == "approved"

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    def test_401(self, response_POST, flavor):  # noqa N803
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401
        assert flavor.status.name == "on_review"

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_403(self, response_POST, flavor):  # noqa N803
        """POST method fails 403 if method forbidden."""
        assert response_POST.status_code == 403
        assert flavor.status.name == "on_review"

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_POST, flavor):  # noqa N803
        """POST method fails 404 if no id found."""
        assert response_POST.status_code == 404
        assert flavor.status.name == "on_review"


@mark.parametrize("endpoint", ["flavors.reject"], indirect=True)
@mark.parametrize("flavor_id", indirect=True, argvalues=[
    flavors[4]["id"],
])
class TestReject:
    """Test flavors reject endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_204(self, response_POST, flavor):  # noqa N803
        """POST method succeeded 200."""
        assert response_POST.status_code == 204
        assert flavor is None

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    def test_401(self, response_POST, flavor):  # noqa N803
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401
        assert flavor.status.name == "on_review"

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_403(self, response_POST, flavor):  # noqa N803
        """POST method fails 403 if method forbidden."""
        assert response_POST.status_code == 403
        assert flavor.status.name == "on_review"

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_POST, flavor):  # noqa N803
        """POST method fails 404 if no id found."""
        assert response_POST.status_code == 404
        assert flavor.status.name == "on_review"


@mark.parametrize("endpoint", ["flavors.site"], indirect=True)
@mark.parametrize("flavor_id", indirect=True, argvalues=[
    flavors[0]["id"], flavors[1]["id"],
    flavors[2]["id"], flavors[3]["id"],
])
class TestSite:
    """Test flavors site endpoint."""

    def test_200(self, flavor, response_GET):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        site = models.Site.query.get(flavor.site_id)
        asserts.match_site(response_GET.json, site)

    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_GET):  # noqa N803
        """GET method fails 404 if no id found."""
        assert response_GET.status_code == 404
