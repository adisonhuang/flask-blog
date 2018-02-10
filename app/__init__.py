#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/21

from flask import Flask

from config import config
# from flask_pagedown import PageDown
from .ext import babel, db, login_manager, redis, bootstrap, moment, qiniu

# db = SQLAlchemy()
# pageDown = PageDown()


# login_manager.session_protection = 'strong'
login_manager.login_view = 'admin.login_view'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # app.secret_key = "SESSION_SECRET_KEY"
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    qiniu.init_app(app)
    # pageDown.init_app(app)
    # babel = Babel(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # admin
    from .admin import admin
    admin.init_app(app)

    from .utils.processors import utility_processor
    app.context_processor(utility_processor)

    return app
