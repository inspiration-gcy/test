# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import hashlib, binascii, os

from flask import current_app, jsonify
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


def hash_pass(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return salt + pwdhash  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""
    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def generate_token(api_users):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)  # expiration是过期时间
    token = s.dumps({'id': api_users.id, "username": api_users.username}).decode('ascii')
    return token


def verify_auth_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except Exception:
        return None
    from app.base.models import Users
    user = Users.query.get(data['id'])
    return user


def create_response(message=None, data=None, code=200):
    r_dict = {}
    if message:
        r_dict['message'] = message
    if data:
        r_dict['data'] = data

    return jsonify(r_dict), code





