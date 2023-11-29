#!/usr/bin/env python
"""Get JSON specification of the OpenAPI API.

Exports the application Open API specification into the file 'api.json'
This script should be executed at the project root directory
"""
import json
import os
import sys

from backend import create_app
from backend.app import api

cwd = os.getcwd()
sys.path.append(cwd)


app = create_app()
with open("api-spec.json", "w") as outfile:
    specs = api.spec.to_dict()
    specs["info"]["title"] = "Swagger client library generator specs"
    specs["servers"] = [
        {
            "url": f"https://perf.test.fedcloud.eu{app.config['BACKEND_ROUTE']}",  # noqa: E501
            "description": "Development server",
        },
        {
            "url": f"https://performance.services.fedcloud.eu{app.config['BACKEND_ROUTE']}",  # noqa: E501
            "description": "Production server",
        },
    ]
    # attempt setting fixed order here, as the auto-generated keeps changing
    specs["components"]["schemas"]["Error"] = {
        "type": "object",
        "properties": {
            "code": {"type": "integer", "description": "Error code"},
            "errors": {"type": "object", "description": "Errors"},
            "message": {"type": "string", "description": "Error message"},
            "status": {"type": "string", "description": "Error name"},
        },
    }
    json.dump(specs, outfile, indent=4)
