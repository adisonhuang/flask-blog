#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/12/3

from app.models import User, Article, Source, Category, Tag, Comment, Role, Permission
from ..ext import db

from flask_admin import Admin

from .views import MyAdminIndexView, CategoryAdmin, TagAdmin, ArticleAdmin, UserAdmin, SourceAdmin, CommentAdmin

admin = Admin(name="后台管理系统", index_view=MyAdminIndexView(), base_template='admin/my_master.html')

# add views
admin.add_view(CategoryAdmin(Category, db.session, name='分类'))
admin.add_view(TagAdmin(Tag, db.session, name='标签'))
admin.add_view(ArticleAdmin(Article, db.session, name='文章'))
admin.add_view(CommentAdmin(Comment, db.session, name='评论'))
admin.add_view(SourceAdmin(Source, db.session, name='文章来源'))

admin.add_view(UserAdmin(User, db.session, name='用户'))
