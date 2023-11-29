"""Defines fixtures available to results tests."""
from flask import url_for
from pytest import fixture

from backend import models


@fixture(scope='function')
def result_id(request):
    """Return result id of the result to test."""
    return request.param if hasattr(request, 'param') else None


@fixture(scope='function')
def result(result_id):
    """Return the result to test."""
    return models.Result.query.get(result_id)


@fixture(scope='function')
def request_id(request, result_id):
    """Return result id to use on the url call."""
    return request.param if hasattr(request, 'param') else result_id


@fixture(scope='function')
def url(endpoint, request_id, query):
    """Return the url for the request."""
    return url_for(endpoint, id=request_id, **query)
