"""Authorization rules for the backend."""
from flaat.config import AccessLevel
from flaat.requirements import IsTrue
from flask import current_app

from backend import models


def is_registered(user_infos):
    """Assert user is registered in the database."""
    user = models.User.read((user_infos.subject, user_infos.issuer))
    return user is not None


def is_admin(user_infos):
    """Assert registration and entitlements."""
    if 'eduperson_entitlement' in user_infos.user_info:
        entitlements = set(user_infos.user_info['eduperson_entitlement'])
    else:
        entitlements = set()
    return all([
        (entitlements & set(current_app.config['ADMIN_ENTITLEMENTS']) or
         not current_app.config['ADMIN_ENTITLEMENTS']),
        is_registered(user_infos),
    ])


access_levels = [
    AccessLevel("user", IsTrue(is_registered)),
    AccessLevel("admin", IsTrue(is_admin)),
]
