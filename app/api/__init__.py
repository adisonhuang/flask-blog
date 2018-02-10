#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/1/14

from flask import Blueprint

api = Blueprint('api', __name__)

from . import views