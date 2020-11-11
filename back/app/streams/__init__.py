# -*- encoding: utf-8 -*-
"""
MIT License
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Blueprint

blueprint = Blueprint(
    'stream_blueprint',
    __name__,
    url_prefix='',
    template_folder='templates',
    static_folder='static'
)