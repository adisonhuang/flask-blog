#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/21

import os
from app import create_app, db
from app.models import User, Article, Source, Category, Tag, Comment, Role, Permission

from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

# 默认环境
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

app.jinja_env.globals['Category'] = Category
app.jinja_env.globals['Source'] = Source
app.jinja_env.globals['Article'] = Article
app.jinja_env.globals['Comment'] = Comment


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Article=Article, Comment=Comment, Source=Source,
                Category=Category, Tag=Tag)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(use_debugger=True))


@manager.command
def test():
    # 运行单元测试
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    """Run deployment tasks."""
    # 插入角色
    Role.insert_roles()
    # 插入管理员
    User.insert_admin()


if __name__ == '__main__':
    manager.run()
