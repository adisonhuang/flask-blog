#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/12/3

import datetime
import os
import random
import json
from flask import current_app, flash
import flask_login as login
from flask_admin.contrib import sqla
from .forms import LoginForm
import flask_admin as admin
from flask import redirect, url_for, request
from flask_admin import helpers, expose
from wtforms.fields import TextAreaField
from werkzeug.utils import secure_filename

from config import Config
from flask_babelex import lazy_gettext as _
from app.models import User, Article
from .. import qiniu
from ..utils.helpers import baidu_ping

cache_key = Config.CACHE_KEY

bpdir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app')
ALLOWED_file_EXTENSIONS = set(['md', 'MD', 'word', 'txt', 'py', 'java', 'c', 'c++', 'xlsx'])
ALLOWED_photo_EXTENSIONS = set(['png', 'jpg', 'xls', 'JPG', 'PNG', 'gif', 'GIF'])


def random_str(randomlength=5):
    _str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    for i in range(randomlength):
        _str += chars[random.randint(0, length)]
    return _str


def allowed_photo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_photo_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_file_EXTENSIONS


def format_datetime(self, request, obj, fieldname, *args, **kwargs):
    return getattr(obj, fieldname).strftime("%Y-%m-%d %H:%M")


# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        if not login.current_user.is_administrator():
            return redirect(url_for('.index'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.verify_password(form.password.data):
                login.login_user(user)
            else:
                flash("密码错误")
        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        # self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


# Customized User model admin
class UserAdmin(sqla.ModelView):
    # inline_models = (User,)
    # 这三个变量定义管理员是否可以增删改，默认为True
    # can_delete = False
    # can_edit = False
    # can_create = False

    column_list = ('email', 'username', 'role')
    # 如果不想显示某些字段，可以重载这个变量
    form_excluded_columns = ('password_hash', 'avatar_hash', 'articles', 'comments')

    column_searchable_list = ('email', 'username')

    form_overrides = dict(about_me=TextAreaField)
    # 这里是为了自定义显示的column名字
    column_labels = dict(
        email=_('邮箱'),
        username=_('用户名'),
        role=_('角色'),
    )

    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_administrator()


class ArticleAdmin(sqla.ModelView):
    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"

    column_list = ('title', 'category', 'tags', 'source', 'published', 'summary', 'created', 'hits')

    form_excluded_columns = ('author', 'content_html', 'created',
                             'last_modified', 'comments')

    column_searchable_list = ('title',)

    column_formatters = dict(created=format_datetime)

    form_create_rules = (
        'title', 'category', 'tags', 'source',
        'summary', 'published', 'content'
    )
    form_edit_rules = form_create_rules

    form_overrides = dict(
        summary=TextAreaField)

    column_labels = dict(
        title=_('标题'),
        category=_('分类'),
        source=_('来源'),
        tags=_('标签'),
        content=_('正文'),
        summary=_('简介'),
        published=_('是否已发布'),
        created=_('创建时间'),
        hits=_('阅读数'),
    )

    form_widget_args = {
        'title': {'style': 'width:480px;'},
        'summary': {'style': 'width:680px; height:80px;'},
    }

    @expose('/editor_pic', methods=["POST"])
    def editor_pic(self):
        image_file = request.files['editormd-image-file']
        if image_file and allowed_photo(image_file.filename):
            try:
                filename = secure_filename(image_file.filename)
                filename = str(datetime.date.today()) + '-' + random_str() + '-' + filename
                upload = qiniu.save_data(image_file.stream, filename)
                if upload:
                    qiniu_link = qiniu.url(filename)
                    data = {
                        'success': 1,
                        'message': 'image of editor.md',
                        'url': qiniu_link
                    }
                else:
                    data = {
                        'success': 0,
                        'message': 'error',
                        'url': ""
                    }
                return json.dumps(data)
            except Exception as e:
                current_app.logger.error(e)
        else:
            return u"没有获得图片或图片类型不支持"

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.author_id = login.current_user.id
            model.created = datetime.datetime.now()
            model.last_modified = model.created
        else:
            model.last_modified = datetime.datetime.now()

    def after_model_change(self, form, model, is_created):
        # 如果发布新文章，则PING通知百度
        if is_created and model.published and os.getenv('FLASK_CONFIG') == 'production':
            baidu_ping(model.link)

    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_administrator()

    @expose('/pingbaidu', methods=["POST"])
    def action_ping_baidu(self, ids):
        for id in ids:
            obj = Article.query.get(id)
            baidu_ping(obj.link)
        flash(u'PING请求已发送，请等待百度处理')


class CategoryAdmin(sqla.ModelView):
    # create_template = "admin/model/a_create.html"
    # edit_template = "admin/model/a_edit.html"

    column_list = ('name', 'introduction', 'order')

    column_searchable_list = ('name',)

    form_excluded_columns = ('articles', 'children')

    # form_overrides = dict(seodesc=TextAreaField, body=EDITOR_WIDGET)

    # column_formatters = dict(view_on_site=view_on_site)

    column_labels = dict(
        parent=_('父节点'),
        name=_('名称'),
        order=_('次序'),
        introduction=_('介绍'),
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }

    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_administrator()


class TagAdmin(sqla.ModelView):
    # create_template = "admin/model/a_create.html"
    # edit_template = "admin/model/a_edit.html"

    column_list = ('name',)

    column_searchable_list = ('name',)

    form_excluded_columns = 'articles'

    # column_formatters = dict(view_on_site=view_on_site)

    column_labels = dict(
        name=_('名称'),
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }


    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_administrator()


class SourceAdmin(sqla.ModelView):
    column_list = ('name',)

    column_searchable_list = ('name',)

    form_excluded_columns = ('articles',)

    # column_formatters = dict(view_on_site=view_on_site)

    column_labels = dict(
        name=_('名称'),
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }

    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_administrator()


class CommentAdmin(sqla.ModelView):
    can_create = False
    column_list = (
        'content', 'created', 'author_name', 'article_id', 'author_email', 'disabled', 'comment_type', 'reply_to')

    form_excluded_columns = ('avatar_hash', 'author_id')

    column_searchable_list = ('article_id', 'comment_type')

    column_formatters = dict(created=format_datetime)

    form_edit_rules = (
        'disabled', 'content',
    )
    form_overrides = dict(
        content=TextAreaField)

    form_widget_args = {
        'content': {'style': 'width:680px; height:80px;'},
    }

    column_labels = dict(
        content=_('内容'),
        author_name=_('评论人'),
        author_email=_('评论邮件'),
        article_id=_('文章 id'),
        disabled=_('禁止'),
        comment_type=_('类型'),
        reply_to=_('回复'),
        created=_('创建时间'),
    )

    def is_accessible(self):
        return login.current_user.is_authenticated and login.current_user.is_administrator()
