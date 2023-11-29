"""Create an application instance."""
from flask_migrate import upgrade

from backend import create_app

app = create_app()
with app.app_context():
    upgrade()
