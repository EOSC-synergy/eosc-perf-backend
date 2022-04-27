#!/usr/bin/env python
# Exports the application Open API specification into the file 'api.json'
# This script should be executed at the project root directory
import json
import os
import sys

cwd = os.getcwd()
sys.path.append(cwd)

from backend import create_app
from backend.app import api

app = create_app() 
with open("api-spec.json", "w") as outfile:
    specs = api.spec.to_dict()
    specs["info"]["title"] = "Swagger client library generator specs"
    specs["servers"] = [
        {
            "url": f"https://perf.test.fedcloud.eu{app.config['BACKEND_ROUTE']}",
            "description": "Development server",
        },
        {
            "url": f"https://performance.services.fedcloud.eu{app.config['BACKEND_ROUTE']}",
            "description": "Production server",
        },
    ]
    json.dump(specs, outfile, indent=4)
