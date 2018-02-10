#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/21
import os
from fabric.api import local, env, run, cd, sudo, prefix, settings, execute, task, put
from fabric.contrib.files import exists

from contextlib import contextmanager

env.hosts = ['xxx']
env.user = 'root'
env.password = 'xxx'
env.group = "root"

DEPLOY_DIR = '/home/www/blog'
LOG_DIR = os.path.join(DEPLOY_DIR, 'log')
VENV_DIR = os.path.join(DEPLOY_DIR, 'venv')
VENV_PATH = os.path.join(VENV_DIR, 'bin/activate')


@contextmanager
def source_virtualenv():
    with prefix("source {}".format(VENV_PATH)):
        yield


def update():
    with cd('/home/www/blog/'):
        sudo('git pull')


def restart():
    with cd(DEPLOY_DIR):
        if not exists(VENV_DIR):
            run("virtualenv {}".format(VENV_DIR))
        with settings(warn_only=True):
            with source_virtualenv():
                # 更换正式环境
                env_vars = {'FLASK_CONFIG': 'production'}
                os.environ.update(env_vars)
                run("pip install -r {}/requirements.txt".format(DEPLOY_DIR))
                with settings(warn_only=True):
                    stop_result = sudo("supervisorctl -c {}/supervisor.conf stop all".format(DEPLOY_DIR))
                    if not stop_result.failed:
                        kill_result = sudo("pkill supervisor")
                        if not kill_result:
                            sudo("supervisord -c {}/supervisor.conf".format(DEPLOY_DIR))
                            sudo("supervisorctl -c {}/supervisor.conf reload".format(DEPLOY_DIR))
                            sudo("supervisorctl -c {}/supervisor.conf status".format(DEPLOY_DIR))
                            sudo("supervisorctl -c {}/supervisor.conf start all".format(DEPLOY_DIR))


@task
def deploy():
    execute(update)
    execute(restart)
