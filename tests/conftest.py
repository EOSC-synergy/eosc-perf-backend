"""Defines fixtures available to all tests.
See: https://pytest-flask.readthedocs.io/en/latest/features.html
"""
import logging
import os

import factories
from backend import create_app, extensions
from backend.utils import dockerhub
from flaat.user_infos import UserInfos
from pytest import fixture
from pytest_postgresql.janitor import DatabaseJanitor

from tests import db_instances

TEST_DB = 'test_database'
VERSION = 12.2  # postgresql version number


@fixture(scope='session')
def sql_database(postgresql_proc):
    """Create a temp Postgres database for the tests."""
    USER = postgresql_proc.user
    HOST = postgresql_proc.host
    PORT = postgresql_proc.port
    with DatabaseJanitor(USER, HOST, PORT, TEST_DB, VERSION) as db:
        yield db


@fixture(scope='session')
def session_environment(sql_database):
    """Patch fixture to set test env variables."""
    # Flask framework environments
    os.environ['SECRET_KEY'] = 'not-so-secret-for-testing'
    # Database environments
    os.environ['DB_USER'] = str(sql_database.user)
    os.environ['DB_PASSWORD'] = ""
    os.environ['DB_HOST'] = str(sql_database.host)
    os.environ['DB_PORT'] = str(sql_database.port)
    os.environ['DB_NAME'] = str(sql_database.dbname)
    # OIDC environments
    os.environ['OIDC_CLIENT_ID'] = "eosc-perf"
    os.environ['OIDC_CLIENT_SECRET'] = "not-so-secret-for-testing"
    os.environ['ADMIN_ENTITLEMENTS'] = "admins"
    # Email and notification configuration.
    os.environ['MAIL_SUPPORT'] = "support@example.com"
    os.environ['MAIL_SERVER'] = "localhost"
    os.environ['MAIL_PORT'] = str(5025)
    os.environ['MAIL_FROM'] = "no-reply@example.com"


@fixture(scope="session")
def app(session_environment):
    """Create application for the tests."""
    app = create_app(config_base="backend.settings", TESTING=True)
    app.logger.setLevel(logging.CRITICAL)
    with app.app_context():
        yield app


@fixture(scope='session')
def db(app):
    """Create database for the tests."""
    extensions.db.create_all()
    [factories.DBUser(**x) for x in db_instances.users]
    [factories.DBTag(**x) for x in db_instances.tags]
    [factories.DBBenchmark(**x) for x in db_instances.benchmarks]
    [factories.DBSite(**x) for x in db_instances.sites]
    [factories.DBFlavor(**x) for x in db_instances.flavors]
    [factories.DBResult(**x) for x in db_instances.results]
    extensions.db.session.commit()
    yield extensions.db
    extensions.db.drop_all()


@fixture(scope='function', autouse=True)
def session(db):
    """Uploads a new database session for a test."""
    db.session.begin(nested=True)  # Rollback app commits
    yield db.session
    db.session.rollback()   # Discard test changes
    db.session.close()      # Next test gets a new session


@fixture(scope='function')
def token_sub(request):
    """Returns the sub to include on the user token."""
    return request.param if hasattr(request, 'param') else None


@fixture(scope='function')
def token_iss(request):
    """Returns the iss to include on the user token."""
    return request.param if hasattr(request, 'param') else None


@fixture(scope='function')
def access_token(token_sub, token_iss):
    """Patch fixture to test function with valid oidc token."""
    return "some-access-token" if token_sub and token_iss else None


@fixture(scope='function')
def user_email(request):
    """Returns the email to be returned by the introspection endpoint."""
    return request.param if hasattr(request, 'param') else None


@fixture(scope='function', autouse=True)
def user_infos(mocker, token_sub, token_iss, user_email):
    """Patches flaat to edit provided user_infos."""
    mocker.patch.object(
        extensions.flaat, "get_user_infos_from_access_token",
        return_value=UserInfos(
            access_token_info=None, introspection_info=None,
            user_info={
                'email_verified': True, 'email': user_email,
                'eduperson_entitlement': [],
                'sub': token_sub, 'iss': token_iss,
            },
        )
    )


@fixture(scope='function')
def grant_admin(monkeypatch):
    """Patch fixture to test function as admin user."""
    admin_assert = extensions.flaat.access_levels[1].requirement
    monkeypatch.setattr(admin_assert, "func", lambda *args: True)


@fixture(scope='function')
def mock_docker_registry(monkeypatch):
    """Patch fixture to test function with valid oidc token."""
    def always_true(*arg, **kwarg): return True
    monkeypatch.setattr(dockerhub, "valid_image", always_true)


@fixture(scope='function')
def endpoint(request):
    """Fixture that return the endpoint for the request."""
    return request.param


@fixture(scope='function')
def query(request):
    """Fixture that return the query for the request."""
    return request.param if hasattr(request, 'param') else {}


@fixture(scope='function')
def headers(request, access_token):
    """Fixture that return the body for the request."""
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


@fixture(scope='function')
def body(request):
    """Fixture that return the body for the request."""
    return request.param if hasattr(request, 'param') else {}


@fixture(scope='function')
def response_GET(client, url, headers):
    """Fixture that return the result of a GET request."""
    return client.get(url, headers=headers)


@fixture(scope='function')
def response_POST(client, url, headers, body):
    """Fixture that return the result of a POST request."""
    return client.post(url, headers=headers, json=body)


@fixture(scope='function')
def response_PUT(client, url, headers, body):
    """Fixture that return the result of a PUT request."""
    return client.put(url, headers=headers, json=body)


@fixture(scope='function')
def response_PATCH(client, url, headers, body):
    """Fixture that return the result of a PATCH request."""
    return client.patch(url, headers=headers, json=body)


@fixture(scope='function')
def response_DELETE(client, url, headers):
    """Fixture that return the result of a DELETE request."""
    return client.delete(url, headers=headers)
