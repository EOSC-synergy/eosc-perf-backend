"""Functional tests using pytest-flask."""
from backend import models
from flask import url_for
from pytest import fixture, mark
from tests import asserts
from tests.db_instances import users


@fixture(scope="function")
def url(endpoint, request_id, query):
    """Fixture that return the url for the request."""
    return url_for(endpoint, report_id=request_id, **query)


@mark.parametrize("endpoint", ["reports.list_submits"], indirect=True)
class TestListSubmits:

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"resource_type": "benchmark"},
        {"resource_type": "site"},
        {"resource_type": "flavor"},
        {"upload_before": "3000-01-01"},
        {"upload_after": "2000-01-01"},
        {},  # Multiple reports
        {"sort_by": "+upload_datetime"},
    ])
    def test_200(self, response_GET, url):
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_pagination(response_GET.json, url)
        assert response_GET.json["items"] != []
        for item in response_GET.json["items"]:
            asserts.match_submit(item)
            asserts.match_query(item, url)

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"upload_before": "3000-01-01"},
    ])
    def test_401(self, response_GET):
        """GET method fails 401 if not logged in."""
        assert response_GET.status_code == 401

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"upload_before": "3000-01-01"},
    ])
    def test_403(self, response_GET):
        """GET method fails 403 if forbidden."""
        assert response_GET.status_code == 403

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"bad_key": "This is a non expected query key"},
        {"sort_by": "Bad sort command"},
    ])
    def test_422(self, response_GET):
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422


@mark.parametrize("endpoint", ["reports.list_claims"], indirect=True)
class TestListClaims:
    
    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"upload_before": "3000-01-01"},
        {"upload_after": "1000-01-01"},
        {},  # Empty query
        {"sort_by": "+upload_datetime"},
    ]
    )
    def test_200(self, response_GET, url):
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.match_pagination(response_GET.json, url)
        assert response_GET.json["items"] != []
        for item in response_GET.json["items"]:
            asserts.match_query(item, url)
            item.pop("uploader")
            item.pop("resource_type")
            assert models.Result._claim_report_class.query.filter_by(
                **item).first()

    @mark.parametrize("token_sub", [None], indirect=True)
    @mark.parametrize("token_iss", [None], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"upload_before": "3000-01-01"},
    ])
    def test_401(self, response_GET):
        """GET method fails 401 if not logged in."""
        assert response_GET.status_code == 401

    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"upload_before": "3000-01-01"},
    ])
    def test_403(self, response_GET):
        """GET method fails 403 if forbidden."""
        assert response_GET.status_code == 403

    @mark.usefixtures("grant_admin")
    @mark.parametrize("token_sub", [users[0]["sub"]], indirect=True)
    @mark.parametrize("token_iss", [users[0]["iss"]], indirect=True)
    @mark.parametrize("query", indirect=True, argvalues=[
        {"bad_key": "This is a non expected query key"},
        {"sort_by": "Bad sort command"},
    ])
    def test_422(self, response_GET):
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422
