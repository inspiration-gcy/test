# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import request
from flask_login import login_user, logout_user, login_required

from app import db
from app.base import blueprint
from app.base.models import Users
from app.base.util import verify_pass, create_response, hash_pass, generate_token


# Login & Registration


@blueprint.route('/login', methods=['POST'])
def login():
    username = request.json.get("username")
    password = request.json.get('password')

    user = Users.query.filter_by(username=username).first()
    # Check the password
    if user and verify_pass(password, user.password):
        login_user(user)
        token = generate_token(user)
        data = dict(user.to_dict(), **{"token": token})

        return create_response(data=data)

    return create_response(message="Authentication failed", code=401)


@blueprint.route('/register', methods=['POST'])
def register():
    username = request.json.get("username")
    password = request.json.get('password')
    email = request.json.get('email')

    # Check usename exists
    user = Users.query.filter_by(username=username).first()
    if user:
        return create_response(message="Username already registered", code=400)

    # Check email exists
    user = Users.query.filter_by(email=email).first()
    if user:
        return create_response(message="Username already registered", code=400)

    # else we can create the user
    user = Users(username=username, email=email, password=hash_pass(password))
    db.session.add(user)
    db.session.commit()

    login_user(user)
    user = Users.query.filter_by(username=username).first()
    token = generate_token(user)
    data = dict(user.to_dict(), **{"token": token})
    return create_response(data=data)


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return create_response(message="success")


@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@blueprint.route('/test')
@login_required
def test():

    return create_response(message="123")