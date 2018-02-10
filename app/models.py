#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/11/30
import os
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app, request
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
from markdown import markdown
from flask import url_for
import bleach
from flask_sqlalchemy import BaseQuery
import re
from functools import reduce

from jinja2.filters import do_striptags, do_truncate
from .ext import keywords_split

pattern_hasmore = re.compile(r'<!--more-->', re.I)


def markitup(text):
    """
    把Markdown转换为HTML
    """

    # 删除与段落相关的标签，只留下格式化字符的标签
    # allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
    #                 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
    #                 'h1', 'h2', 'h3', 'p', 'img']
    return bleach.linkify(markdown(text, ['extra'], output_format='html5'))
    # return bleach.linkify(bleach.clean(
    #     # markdown默认不识别三个反引号的code-block，需开启扩展
    #     markdown(text, ['extra'], output_format='html5'),
    #     tags=allowed_tags, strip=True))


# 权限
class Permission:
    # 发布评论
    COMMENT = 0x01
    # 写文章
    WRITE_ARTICLES = 0x02
    # 管理评论
    MODERATE_COMMENTS = 0x04
    # 管理员
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 只有一个角色的 default 字段要设为 True，其他都设为 False。用户注册时，其角色会被 设为默认角色
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    __mapper_args__ = {'order_by': [id.desc()]}

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.COMMENT, True),
            'Moderator': (Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __str__(self):
        return self.name

    # 可以用来表示对象的可打印字符串
    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    avatar_hash = db.Column(db.String(32))
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    __mapper_args__ = {'order_by': [id.desc()]}

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    @staticmethod
    def insert_admin():
        user = User(email=current_app.config['ADMIN_EMAIL'], username=current_app.config['ADMIN_USERNAME'],
                    password=current_app.config['ADMIN_PASSWORD'])
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def reset_password(new_password):
        user = User.query.filter_by(id=1).first()
        user.password = new_password
        db.session.add(user)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return '<User %r>' % self.username

    # Required for administrative interface
    def __str__(self):
        return self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    print('user_id', user_id)
    return db.session.query(User).get(user_id)


class Source(db.Model):
    """来源"""
    __tablename__ = 'sources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    articles = db.relationship('Article', backref='source', lazy='dynamic')

    @staticmethod
    def insert_sources():
        sources = (u'原创',
                   u'转载',
                   u'翻译')
        for s in sources:
            source = Source.query.filter_by(name=s).first()
            if source is None:
                source = Source(name=s)
            db.session.add(source)
        db.session.commit()

    __mapper_args__ = {'order_by': [name]}

    @property
    def link(self):
        return url_for('main.source', id=self.id, _external=True)

    @property
    def count(self):
        return Article.query.public().filter(Article.source_id.in_(id=self.id)).count()

    def __repr__(self):
        return '<Source %r>' % self.name

    def __str__(self):
        return self.name


class Category(db.Model):
    """目录"""
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(64), unique=True)
    parent_id = db.Column(db.Integer(), db.ForeignKey('categories.id'))
    parent = db.relationship('Category',
                             primaryjoin='Category.parent_id == Category.id',
                             remote_side=id, backref=db.backref("children"))

    introduction = db.Column(db.Text, default=None)
    articles = db.relationship('Article', backref='category', lazy='dynamic')

    __mapper_args__ = {'order_by': [name]}

    @property
    def link(self):
        return url_for('main.category', id=self.id, _external=True)

    @property
    def count(self):
        cates = db.session.query(Category.id).all()
        cate_ids = [cate.id for cate in cates]
        return Article.query.public().filter(Article.category_id.in_(cate_ids)).count()

    @property
    def parents(self):
        lst = [self]
        c = self.parent
        while c is not None:
            lst.append(c)
            c = c.parent
        lst.reverse()
        return lst

    def __repr__(self):
        return '<Category %r>' % self.name

    def __str__(self):
        return self.name


# Create M2M table
article_tags_table = db.Table('article_tags',
                              db.Column('article_id', db.Integer, db.ForeignKey('articles.id', ondelete='CASCADE')),
                              db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE')))


class TagQuery(BaseQuery):

    def search(self, keyword):
        keyword = u'%{0}%'.format(keyword.strip())
        return self.filter(Tag.name.ilike(keyword))


class Tag(db.Model):
    """标签"""
    __tablename__ = 'tags'
    query_class = TagQuery
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, index=True, nullable=False)

    __mapper_args__ = {'order_by': [id.desc()]}

    @property
    def link(self):
        return url_for('main.tag', name=self.name.lower(), _external=True)

    def __repr__(self):
        return '<Tag %r>' % self.name

    def __str__(self):
        return self.name

    @property
    def count(self):
        return Article.query.public().filter(Article.tags.any(id=self.id)).count()


class ArticleQuery(BaseQuery):

    def public(self):
        return self.filter_by(published=True)

    def search(self, keyword):
        criteria = []

        for keyword in keywords_split(keyword):
            keyword = u'%{0}%'.format(keyword)
            criteria.append(db.or_(Article.title.ilike(keyword), ))

        q = reduce(db.or_, criteria)
        return self.public().filter(q)

    def archives(self, year, month):
        if not year:
            return self

        criteria = [db.extract('year', Article.created) == year]
        if month:
            criteria.append(db.extract('month', Article.created) == month)

        q = reduce(db.and_, criteria)
        return self.public().filter(q)


class Article(db.Model):
    """文章"""
    __tablename__ = 'articles'
    query_class = ArticleQuery

    PER_PAGE = 10

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    summary = db.Column(db.Text)
    published = db.Column(db.Boolean, default=True)
    hits = db.Column(db.Integer, default=0)
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    created = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    category_id = db.Column(db.Integer(), db.ForeignKey(Category.id), nullable=False, )
    tags = db.relationship(Tag, secondary=article_tags_table, backref=db.backref("articles"))
    source_id = db.Column(db.Integer, db.ForeignKey(Source.id), nullable=False, )
    comments = db.relationship('Comment', backref='article', lazy='dynamic')
    author_id = db.Column(db.Integer, db.ForeignKey(User.id))

    __mapper_args__ = {'order_by': [id.desc()]}

    def __repr__(self):
        return '<Article %r>' % (self.title)

    def __str__(self):
        return self.title

    @property
    def year(self):
        return int(self.created.year)

    @property
    def month_and_day(self):
        return str(self.created.month) + "-" + str(self.created.day)

    @property
    def has_more(self):
        return pattern_hasmore.search(self.body) is not None or \
               self.summary.find('...') >= 0

    @property
    def link(self):
        return url_for('main.article', id=self.id, _external=True)

    @property
    def get_next(self):
        _query = db.and_(Article.category_id.in_([self.category.id]),
                         Article.id > self.id)
        return self.query.public().filter(_query) \
            .order_by(Article.id.asc()) \
            .first()

    @property
    def get_prev(self):
        _query = db.and_(Article.category_id.in_([self.category.id]),
                         Article.id < self.id)
        return self.query.public().filter(_query) \
            .order_by(Article.id.desc()) \
            .first()

    @staticmethod
    def before_insert(mapper, connection, target):
        def _format(_html):
            return do_truncate(do_striptags(_html), length=200)

        value = target.content
        if target.summary is None or target.summary.strip() == '':
            # 新增文章时，如果 summary 为空，则自动生成

            _match = pattern_hasmore.search(value)
            if _match is not None:
                more_start = _match.start()
                target.summary = _format(markitup(value[:more_start]))
            else:
                target.summary = _format(target.body_html)

    @staticmethod
    def on_change_content(target, value, oldvalue, initiator):
        target.content_html = markitup(value)

        # TODO 有问题
        def _format(_html):
            return do_truncate(do_striptags(_html), length=200)

        if target.summary is None or target.summary.strip() == '':
            # 新增文章时，如果 summary 为空，则自动生成

            _match = pattern_hasmore.search(value)
            if _match is not None:
                more_start = _match.start()
                # target.summary = _format(markitup(value[:more_start]))
                target.summary = markitup(value[:more_start])
            else:
                target.summary = target.body_html


db.event.listen(Article.content, 'set', Article.on_change_content)
db.event.listen(Article, 'before_insert', Article.before_insert)


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                            primary_key=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    PER_PAGE = 30
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    author_name = db.Column(db.String(64))
    author_email = db.Column(db.String(64))
    avatar_hash = db.Column(db.String(32))
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    disabled = db.Column(db.Boolean, default=False)
    comment_type = db.Column(db.String(64), default='comment')
    reply_to = db.Column(db.String(128), default='notReply')

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        if self.author_email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.author_email.encode('utf-8')).hexdigest()

    @property
    def replys(self):
        return [i.follower for i in self.followers]

    def gravatar(self, size=40, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.author_email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        post_count = Article.query.count()
        for i in range(count):
            a = Article.query.offset(randint(0, post_count - 1)).first()
            c = Comment(content=forgery_py.lorem_ipsum.sentences(randint(3, 5)),
                        timestamp=forgery_py.date.date(True),
                        author_name=forgery_py.internet.user_name(True),
                        author_email=forgery_py.internet.email_address(),
                        article=a)
            db.session.add(c)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    @staticmethod
    def generate_fake_replies(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        comment_count = Comment.query.count()
        for i in range(count):
            followed = Comment.query.offset(randint(0, comment_count - 1)).first()
            c = Comment(content=forgery_py.lorem_ipsum.sentences(randint(3, 5)),
                        timestamp=forgery_py.date.date(True),
                        author_name=forgery_py.internet.user_name(True),
                        author_email=forgery_py.internet.email_address(),
                        post=followed.post, comment_type='reply',
                        reply_to=followed.author_name)
            f = Follow(follower=c, followed=followed)
            db.session.add(f)
            db.session.commit()

    def is_reply(self):
        if self.followed.count() == 0:
            return False
        else:
            return True

    # to confirm whether the comment is a reply or not

    def followed_name(self):
        if self.is_reply():
            return self.followed.first().followed.author_name

    def __repr__(self):
        return '<Comment %r>' % self.id

    # Required for administrative interface
    def __str__(self):
        return self.id
