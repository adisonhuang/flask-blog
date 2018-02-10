#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/21

from flask import render_template
from . import main

'''
在蓝本中编写错误处理程序稍有不同，如果使用 errorhandler 修饰器，那么只有蓝本中的
错误才能触发处理程序。要想注册程序全局的错误处理程序，必须使用 app_errorhandler
'''


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 400


@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
