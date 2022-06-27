from flaat.config import AccessLevel
from flaat.requirements import get_vo_requirement
from flask import current_app


def is_user():
    # TODO assert user is registered
    return


def is_admin():
    # TODO assert user is registered
    # TODO assert user has required vo
    return


access_levels = [
    AccessLevel("user", is_user),
    AccessLevel("admin", is_admin),
]
