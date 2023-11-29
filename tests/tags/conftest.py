"""Defines fixtures available to tags tests."""
from flask import url_for
from pytest import fixture

from backend import models


@fixture(scope='function')
def tag_id(request):
    """Return tag id of the tag to test."""
    return request.param if hasattr(request, 'param') else None


@fixture(scope='function')
def tag(tag_id):
    """Return the tag to test."""
    return models.Tag.query.get(tag_id)


@fixture(scope='function')
def request_id(request, tag_id):
    """Tag id to use on the url call."""
    return request.param if hasattr(request, 'param') else tag_id


@fixture(scope='function')
def url(endpoint, request_id, query):
    """Return the url for the request."""
    return url_for(endpoint, id=request_id, **query)
