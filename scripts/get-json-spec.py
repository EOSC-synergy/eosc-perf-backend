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
with open("api.json", "w") as outfile:
    json.dump(api.spec.to_dict(), outfile, indent=4)
