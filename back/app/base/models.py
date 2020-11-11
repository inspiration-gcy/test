# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from sqlalchemy import Binary, Column, Integer, String

from app import db, login_manager

from app.base.util import hash_pass, verify_auth_token


class Users(db.Model, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(Binary)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass( value ) # we need bytes here (not plain str)
                
            setattr(self, property, value)

    # def __repr__(self):
    #     return str(self.username)

    def to_dict(self):
        data = {
           "username": self.username,
           "id": self.id,
           "email": self.email,
        }
        return data


@login_manager.user_loader
def user_loader(token):
    user = verify_auth_token(token)
    print(124)
    return user


@login_manager.request_loader
def request_loader(request):
    token = request.headers.get("token")
    user = verify_auth_token(token)
    return user if user else None


