#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2017/12/18
import random
import datetime
from functools import reduce
from app.models import db, User, Article, Source, Category, Tag, Comment, Role, Permission
from .helpers import get_category_ids
from ..ext import redis
from config import Config


def utility_processor():
    """自定义模板处理器"""

    def archives():
        """
        返回从第一篇文章开始到现在所经历的月份列表
        """
        archives = redis.lrange(Config.CACHE_KEY % "archives", 0, -1)
        if not archives:
            begin_post = Article.query.order_by('created').first()

            now = datetime.datetime.now()

            begin_s = begin_post.created if begin_post else now
            end_s = now

            begin = begin_s
            end = end_s

            total = (end.year - begin.year) * 12 - begin.month + end.month
            archives = [begin]

            date = begin
            for i in range(total):
                if date.month < 12:
                    date = datetime.datetime(date.year, date.month + 1, 1)
                else:
                    date = datetime.datetime(date.year + 1, 1, 1)
                archives.append(date)
            archives.reverse()
            for archive in archives:
                redis.lpush(Config.CACHE_KEY % "archives", archive)
        return archives

    def category_child_lists(parent=None):
        """
        返回栏目列表

        :param parent:
            父级栏目，`None`或者`Category`实例
        """
        if parent is None:
            return

        return Category.query.filter_by(parent=parent).order_by(Category.order).all()

    def category_lists():
        """
        返回栏目列表
        """
        _query = Category.query.filter(Category.parent_id.is_(None)).order_by(Category.order)
        return _query.all()

    def category_lists_count():
        """
        返回栏目列表+数量
        """
        cate_list = Category.query.all()
        return [{"category": cate, "count": cate.articles.count()} for cate in cate_list]

    def tag_lists(limit=None):
        """
        返回标签列表

        :param limit:
            返回的个数，`None`或者正整数
        """
        _query = Tag.query
        if isinstance(limit, int):
            _query = _query.limit(limit)
        return _query.all()

    def get_related_articles(article_id, limit=10):
        """
        返回指定文章的相关文章列表

        根据Tag来筛选

        :param article_id:
            文章ID, 正整数
        :param limit:
            返回的个数, 正整数，默认为10
        """
        # 获取与本文章标签相同的所有文章ID
        article = Article.query.get(article_id)
        if article:
            ids = db.session.query('article_id') \
                .from_statement('SELECT article_id FROM '
                                'article_tags WHERE tag_id IN '
                                '(SELECT tag_id FROM article_tags '
                                'WHERE article_id=:article_id)') \
                .params(article_id=article_id).all()

            article_ids = [_id[0] for _id in ids]
            article_ids = list(set(article_ids))

            if article_id in article_ids:
                article_ids.remove(article_id)

            random_ids = random.sample(article_ids, min(limit, len(article_ids)))

            if article_ids:
                return Article.query.public().filter(Article.id.in_(random_ids)).all()
        return None

    def get_latest_articles(limit=10):
        """
        返回最新文章列表

        :param limit:
            返回的个数，正整数，默认为10
        """
        _query = Article.query.public()
        return _query.limit(int(limit)).all()

    def get_top_articles(days=365, limit=10):
        """
        返回热门文章列表

        :param days:
            天数的范围，比如：一周7天，一个月30天。默认为一年
        :param limit:
            返回的个数，正整数，默认为10
        """
        criteria = []

        _start = datetime.date.today() - datetime.timedelta(days)
        criteria.append(Article.created >= _start)

        q = reduce(db.and_, criteria)
        return Article.query.public().filter(q) \
            .order_by(Article.hits.desc()) \
            .limit(int(limit)).all()

    def get_articles_by_category(category_id=0, limit=10):
        """
        根据栏目路径返回文章列表

        :param category_id:
            栏目id，正整数
        :param limit:
            返回的个数，整数
        """
        _query = Article.query.public()
        category = Category.query.filter_by(category_id=category_id).first()
        if category:
            _query = _query.filter_by(category_id=category.id)
        return _query.limit(int(limit)).all()

    return dict(
        Article=Article,
        Category=Category,
        Tag=Tag,
        archives=archives,
        get_category_ids=get_category_ids,
        get_latest_articles=get_latest_articles,
        get_top_articles=get_top_articles,
        get_related_articles=get_related_articles,
        get_articles_by_category=get_articles_by_category,
        category_lists=category_lists,
        category_lists_count=category_lists_count,
        category_child_lists=category_child_lists,
        tag_lists=tag_lists,
    )
