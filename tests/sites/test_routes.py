"""Functional tests using pytest-flask."""
from uuid import uuid4

from flask import url_for
from pytest import fixture, mark

from backend import models
from backend.schemas import schemas
from tests import asserts
from tests.db_instances import flavors, sites, users


@fixture(scope="function")
def url(endpoint, request_id, query):
    """Fixture that return the url for the request."""
    return url_for(endpoint, site_id=request_id, **query)


@mark.parametrize("endpoint", ["sites.list"], indirect=True)
class TestList:
    """Test sites list endpoint."""

    @mark.parametrize("query", indirect=True, argvalues=[
        {"name": sites[0]["name"], "address": sites[0]["address"]},
        {"address": sites[0]["address"]},  # Query with 1 field
        {},  # Multiple results
        {"sort_by": "+name,-address"},
        {"sort_by": "+upload_datetime"},
        {"sort_by": "+id"},
    ])
    def test_200(self, response_GET, url):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_pagination(response_GET.json, url)
        assert response_GET.json["items"] != []
        for item in response_GET.json["items"]:
            site = models.Site.query.get(item["id"])
            asserts.match_query(item, url)
            asserts.match_site(item, site)
            assert site.status.name == "approved"

    @mark.parametrize("query", indirect=True, argvalues=[
        {"bad_key": "This is a non expected query key"},
        {"sort_by": "Bad sort command"},
    ])
    def test_422(self, response_GET):  # noqa N803
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422


@mark.parametrize("endpoint", ["sites.create"], indirect=True)
class TestCreate:
    """Test sites create endpoint."""

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "s3", "address": "addr3", "description": "Text"},
        {"name": "s4", "address": "addr4"},
    ])
    def test_201(self, response_POST, url, body):  # noqa N803
        """POST method succeeded 201."""
        assert response_POST.status_code == 201
        asserts.match_query(response_POST.json, url)
        asserts.match_body(response_POST.json, body)
        site = models.Site.query.get(response_POST.json["id"])
        asserts.match_site(response_POST.json, site)
        asserts.submit_notification(site.submit_report)

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "s3", "address": "addr2", "description": "Text"},
        {},  # Empty body
    ])
    def test_401(self, response_POST):  # noqa N803
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401

    @mark.parametrize("token_sub", ["no-registered"], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "s3", "address": "addr2", "description": "Text"},
    ])
    def test_403(self, response_POST):  # noqa N803
        """POST method fails 403 if user not registered."""
        assert response_POST.status_code == 403

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": sites[0]["name"], "address": sites[0]["address"]},
    ])
    def test_409(self, response_POST):  # noqa N803
        """POST method fails 409 if resource already exists."""
        assert response_POST.status_code == 409

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new-site"},  # Missingaddress
        {"address": "new-address"},  # Missingname
        {},  # Empty body
    ])
    def test_422(self, response_POST):  # noqa N803
        """POST method fails 422 if missing required."""
        assert response_POST.status_code == 422


@mark.parametrize("endpoint", ["sites.search"], indirect=True)
class TestSearch:
    """Test sites search endpoint."""

    @mark.parametrize("query", indirect=True, argvalues=[
        {"terms": [sites[0]["name"]]},
        {"terms[]": [sites[0]["name"]]},
        {"terms": [sites[0]["address"]]},
        {"terms[]": [sites[0]["address"]]},
        {"terms": [sites[0]["description"]]},
        {"terms[]": [sites[0]["description"]]},
        {"terms": [sites[0]["name"], sites[0]["description"]]},
        {"terms[]": [sites[0]["name"], sites[0]["description"]]},
        {"terms": []},  # Empty terms
        {"terms[]": []},  # Empty terms
        {"sort_by": "+name,-address"},
        {"sort_by": "+upload_datetime"},
        {"sort_by": "+id"},
    ])
    def test_200(self, response_GET, url):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_pagination(response_GET.json, url)
        assert response_GET.json["items"] != []
        for item in response_GET.json["items"]:
            site = models.Site.query.get(item["id"])
            asserts.match_query(item, url)
            asserts.match_site(item, site)
            assert site.status.name == "approved"

    @mark.parametrize("query", indirect=True, argvalues=[
        {"bad_key": "This is a non expected query key"},
        {"sort_by": "Bad sort command"},
    ])
    def test_422(self, response_GET):  # noqa N803
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422


@mark.parametrize("endpoint", ["sites.get"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[1]["id"],
])
class TestGet:
    """Test sites get endpoint."""

    def test_200(self, site, response_GET):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_site(response_GET.json, site)

    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_GET):  # noqa N803
        """GET method fails 404 if no id found."""
        assert response_GET.status_code == 404


@mark.parametrize("endpoint", ["sites.update"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[1]["id"],
])
class TestUpdate:
    """Test sites update endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name1", "address": "addr1"},
    ])
    def test_204(self, body, response_PUT, site):  # noqa N803
        """PUT method succeeded 204."""
        assert response_PUT.status_code == 204
        json = schemas.Site().dump(site)
        asserts.match_body(json, body)

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name", "address": "new_addr"},
    ])
    def test_401(self, site, response_PUT):  # noqa N803
        """PUT method fails 401 if not authorized."""
        assert response_PUT.status_code == 401
        assert site == models.Site.query.get(site.id)

    @mark.parametrize("token_sub", ["no-registered"], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name", "address": "new_addr"},
    ])
    def test_403(self, site, response_PUT):  # noqa N803
        """PUT method fails 403 if user not registered."""
        assert response_PUT.status_code == 403
        assert site == models.Site.query.get(site.id)

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "new_name", "address": "new_addr"},
    ])
    def test_404(self, site, response_PUT):  # noqa N803
        """PUT method fails 404 if no id found."""
        assert response_PUT.status_code == 404
        assert site == models.Site.query.get(site.id)

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"bad_field": ""},
    ])
    def test_422(self, site, response_PUT):  # noqa N803
        """PUT method fails 422 if bad request body."""
        assert response_PUT.status_code == 422
        assert site == models.Site.query.get(site.id)


@mark.parametrize("endpoint", ["sites.delete"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[1]["id"],
])
class TestDelete:
    """Test sites delete endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_204(self, site, response_DELETE):  # noqa N803
        """DELETE method succeeded 204."""
        assert response_DELETE.status_code == 204
        assert models.Site.query.get(site.id) is None
        for flavor in site.flavors:  # Flavors are removed
            assert models.Flavor.query.get(flavor.id) is None

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    def test_401(self, site, response_DELETE):  # noqa N803
        """DELETE method fails 401 if not authorized."""
        assert response_DELETE.status_code == 401
        assert models.Site.query.get(site.id) is not None
        for flavor in site.flavors:  # Flavors exist
            assert models.Flavor.query.get(flavor.id) is not None

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_403(self, site, response_DELETE):  # noqa N803
        """DELETE method fails 403 if forbidden."""
        assert response_DELETE.status_code == 403
        assert models.Site.query.get(site.id) is not None
        for flavor in site.flavors:  # Flavors exist
            assert models.Flavor.query.get(flavor.id) is not None

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, site, response_DELETE):  # noqa N803
        """DELETE method fails 404 if no id found."""
        assert response_DELETE.status_code == 404
        assert models.Site.query.get(site.id) is not None
        for flavor in site.flavors:  # Flavors exist
            assert models.Flavor.query.get(flavor.id) is not None


@mark.parametrize("endpoint", ["sites.approve"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[2]["id"],
])
class TestApprove:
    """Test sites approve endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_204(self, response_POST, site):  # noqa N803
        """POST method succeeded 200."""
        assert response_POST.status_code == 204
        assert site.status.name == "approved"

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    def test_401(self, response_POST, site):  # noqa N803
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401
        assert site.status.name == "on_review"

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_403(self, response_POST, site):  # noqa N803
        """POST method fails 403 if method forbidden."""
        assert response_POST.status_code == 403
        assert site.status.name == "on_review"

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_POST, site):  # noqa N803
        """POST method fails 404 if no id found."""
        assert response_POST.status_code == 404
        assert site.status.name == "on_review"


@mark.parametrize("endpoint", ["sites.reject"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[2]["id"],
])
class TestReject:
    """Test sites reject endpoint."""

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_204(self, response_POST, site):  # noqa N803
        """POST method succeeded 200."""
        assert response_POST.status_code == 204
        assert site is None

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    def test_401(self, response_POST, site):  # noqa N803
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401
        assert site.status.name == "on_review"

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    def test_403(self, response_POST, site):  # noqa N803
        """POST method fails 403 if method forbidden."""
        assert response_POST.status_code == 403
        assert site.status.name == "on_review"

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    def test_404(self, response_POST, site):  # noqa N803
        """POST method fails 404 if no id found."""
        assert response_POST.status_code == 404
        assert site.status.name == "on_review"


@mark.parametrize("endpoint", ["sites.list_flavors"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[sites[0]["id"]])
class TestListFlavors:
    """Test sites list flavors endpoint."""

    @mark.parametrize("query", indirect=True, argvalues=[
        {"name": flavors[0]["name"]},
        {"name": flavors[2]["name"]},
        {"upload_before": "3000-01-01"},
        {"upload_after": "1000-01-01"},
        {},  # Multiple results
        {"sort_by": "+name"},
        {"sort_by": "+upload_datetime"},
        {"sort_by": "+id"},
    ])
    def test_200(self, response_GET, url):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_pagination(response_GET.json, url)
        assert response_GET.json["items"] != []
        for item in response_GET.json["items"]:
            flavor = models.Flavor.query.get(item["id"])
            asserts.match_query(item, url)
            asserts.match_flavor(item, flavor)
            assert flavor.status.name == "approved"

    @mark.parametrize("query", indirect=True, argvalues=[
        {"bad_key": "This is a non expected query key"},
        {"sort_by": "Bad sort command"},
    ])
    def test_422(self, response_GET):  # noqa N803
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422


@mark.parametrize("endpoint", ["sites.create_flavor"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[0]["id"],
])
class TestCreateFlavor:
    """Test sites create flavor endpoint."""

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "flavorN", "description": "FlavorN for siteX"},
        {"name": "flavorN"},
    ])
    def test_201(self, response_POST, site, url, body):  # noqa N803
        """POST method succeeded 201."""
        assert response_POST.status_code == 201
        asserts.match_query(response_POST.json, url)
        asserts.match_body(response_POST.json, body)
        flavor = models.Flavor.query.get(response_POST.json["id"])
        assert flavor in site.flavors
        asserts.match_flavor(response_POST.json, flavor)
        asserts.submit_notification(flavor.submit_report)

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "flavorN", "description": "FlavorN for siteX"},
        {},  # Empty body
    ])
    def test_401(self, response_POST):  # noqa N803
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401

    @mark.parametrize("token_sub", ["no-registered"], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "flavorN", "description": "FlavorN for siteX"},
    ])
    def test_403(self, response_POST):  # noqa N803
        """POST method fails 403 if user not registered."""
        assert response_POST.status_code == 403

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("request_id", [uuid4()], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": "flavorN", "description": "FlavorN for siteX"},
    ])
    def test_404(self, response_POST):  # noqa N803
        """POST method fails 404 if no id found."""
        assert response_POST.status_code == 404

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"name": flavors[0]["name"]},
    ])
    def test_409(self, response_POST):  # noqa N803
        """POST method fails 409 if resource already exists."""
        assert response_POST.status_code == 409

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("body", indirect=True, argvalues=[
        {"description": "New flavor for site"},
        {},  # Empty body
    ])
    def test_422(self, response_POST):  # noqa N803
        """POST method fails 422 if missing required."""
        assert response_POST.status_code == 422


@mark.parametrize("endpoint", ["sites.search_flavors"], indirect=True)
@mark.parametrize("site_id", indirect=True, argvalues=[
    sites[0]["id"],
])
class TestSearchFlavors:
    """Test sites search flavors endpoint."""

    @mark.parametrize("query", indirect=True, argvalues=[
        {"terms": [flavors[0]["name"]]},
        {"terms[]": [flavors[0]["name"]]},
        {"terms": [flavors[0]["description"]]},
        {"terms[]": [flavors[0]["description"]]},
        {"terms": [flavors[0]["name"], flavors[0]["description"]]},
        {"terms[]": [flavors[0]["name"], flavors[0]["description"]]},
        {"terms": []},  # Empty terms
        {"terms[]": []},  # Empty terms
        {"sort_by": "+name"},
        {"sort_by": "+upload_datetime"},
        {"sort_by": "+id"},
    ])
    def test_200(self, response_GET, url):  # noqa N803
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_pagination(response_GET.json, url)
        assert response_GET.json["items"] != []
        for item in response_GET.json["items"]:
            flavor = models.Flavor.query.get(item["id"])
            asserts.match_query(item, url)
            asserts.match_flavor(item, flavor)
            assert flavor.status.name == "approved"

    @mark.parametrize("query",  indirect=True, argvalues=[
        {"bad_key": "This is a non expected query key"},
        {"sort_by": "Bad sort command"},
    ])
    def test_422(self, response_GET):  # noqa N803
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422
