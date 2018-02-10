#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/1/14

from flask import request
from ..models import db, Article
from . import api


@api.route('/get_hits/')
def get_hits():
    id = int(request.args.get('id', 0))
    article = Article.query.get(id)
    if article:
        article.hits += 1
        db.session.add(article)
        db.session.commit()
        return str(article.hits)
    return 'err'
