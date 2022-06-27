from flaat.config import AccessLevel
from flaat.requirements import IsTrue
from flask import current_app

import models


def is_registered(user_infos):
    """Assert user is registered in the database."""
    models.User.read((user_infos.subject, user_infos.issuer))
    return


def is_admin(user_infos):
    """Assert registration and entitlements."""
    entitlements = set(user_infos.user_infos['eduperson_entitlement'])
    return all([
        entitlements & set(current_app.config['ADMIN_ENTITLEMENTS']),
        is_registered(user_infos),
    ])


access_levels = [
    AccessLevel("user", IsTrue(is_registered)),
    AccessLevel("admin", IsTrue(is_admin)),
]
