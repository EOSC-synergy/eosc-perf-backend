"""Defines fixtures available to sites tests."""
from flask import url_for
from pytest import fixture

from backend import models


@fixture(scope='function')
def flavor_id(request):
    """Return flavor id of the flavor to test."""
    return request.param if hasattr(request, 'param') else None


@fixture(scope='function')
def flavor(flavor_id):
    """Return the flavor to test."""
    return models.Flavor.query.get(flavor_id)


@fixture(scope='function')
def request_id(request, flavor_id):
    """Return flavor id to use on the url call."""
    return request.param if hasattr(request, 'param') else flavor_id


@fixture(scope='function')
def url(endpoint, request_id, query):
    """Return the url for the request."""
    return url_for(endpoint, id=request_id, **query)
