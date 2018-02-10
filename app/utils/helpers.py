# -*- coding: utf-8 -*-

import requests
from flask import current_app, request, url_for
from ..models import Category


def get_category_ids():
    """"返回所有栏目的ID列表"""
    cates = Category.query.all()
    if cates:
        return [cate.id for cate in cates.all()]
    else:
        return []


def page_url(page):
    """根据页码返回URL"""
    _kwargs = request.view_args
    if 'page' in _kwargs:
        _kwargs.pop('page')
    if page > 1:
        return url_for(request.endpoint, page=page, **_kwargs)
    return url_for(request.endpoint, **_kwargs)


def baidu_ping(url):
    """
    :ref: https://ziyuan.baidu.com/linksubmit/index

    链接提交百度
    """

    r = requests.post("http://data.zz.baidu.com/urls?site=blog.adisonhyh.com&token=G2ZJrhG7Oe0pAPZo", data=url)
    # 返回0表示提交成功
    current_app.logger.info('begin to ping baidu: <%s>' % url)
    result = r.json()

    if 'error' in result:
        current_app.logger.warning('<%s> ping to baidu failed due to %s' % url, result)
        return False

    return True
