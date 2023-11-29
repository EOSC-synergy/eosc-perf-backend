"""Defines fixtures available to users tests."""
from flask import url_for
from pytest import fixture

from backend import models


@fixture(scope='function')
def user(token_sub, token_iss):
    """Return the tested user."""
    return models.User.query.get((token_sub, token_iss))


@fixture(scope='function')
def url(endpoint, query):
    """Return the url for the request."""
    return url_for(endpoint, **query)
