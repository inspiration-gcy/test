# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from sys import exit

from decouple import config
from flask_migrate import Migrate

from app import create_app, db
from app.mock.stub_db_data import create_stub_data
from app.streams.camstreaming import CamHandler
from config import config_dict

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True)

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values 
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)
app.app_context().push()

create_stub_data()
CamHandler()

Migrate(app, db)

if __name__ == "__main__":
    app.run()
