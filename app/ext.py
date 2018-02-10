# -*- coding: utf-8 -*-

import redis
from flask import request
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .utils.qiniustorage import Qiniu
from flask_bootstrap import Bootstrap
from flask_moment import Moment


def keywords_split(keywords):
    return keywords.replace(u',', ' ') \
        .replace(u';', ' ') \
        .replace(u'+', ' ') \
        .replace(u'；', ' ') \
        .replace(u'，', ' ') \
        .replace(u'　', ' ') \
        .split(' ')


db = SQLAlchemy()
babel = Babel()
'''LoginManager 对象的 session_protection 属性可以设为 None、'basic' 或 'strong'，
以提 供不同的安全等级防止用户会话遭篡改。设为 'strong' 时，Flask-Login 会记录客户端 IP 地址和浏览器的用户代理信息，
如果发现异动就登出用户。login_view 属性设置登录页面 的端点'''
login_manager = LoginManager()
bootstrap = Bootstrap()
moment = Moment()
qiniu = Qiniu()

redis = redis.StrictRedis(host='localhost', port=6379, db=0)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['en', 'zh_CN', 'zh_TW'])
