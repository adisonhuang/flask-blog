#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/1/12

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin
from qiniu import Auth, put_file, etag, urlsafe_base64_encode, BucketManager, put_stream
from ..utils.qiniu_uoloader import put_data
from flask import current_app


class Qiniu(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # 要上传的空间
        self._bucket_name = app.config.get('QINIU_BUCKET_NAME', '')
        # Access Key
        self._secret_key = app.config.get('QINIU_SECRET_KEY', '')
        # Secret Key
        self._access_key = app.config.get('QINIU_ACCESS_KEY', '')
        domain = app.config.get('QINIU_BUCKET_DOMAIN')
        if not domain:
            self._base_url = 'http://' + self._bucket_name + '.qiniudn.com'
        else:
            self._base_url = 'http://' + domain

    def save_file(self, localfile, filename=None):

        # 构建鉴权对象
        auth = Auth(self._access_key, self._secret_key)
        # 上传到七牛后保存的文件名
        key = filename
        # 生成上传 Token，可以指定过期时间等
        token = auth.upload_token(self._bucket_name)
        ret, info = put_file(token, key, localfile)
        print(info)
        try:
            assert ret['key'] == key
            assert ret['hash'] == etag(localfile)
        except Exception as e:
            current_app.logger.info(e)
        return ret, info

    def save_data(self, stream, filename=None):
        # 构建鉴权对象
        auth = Auth(self._access_key, self._secret_key)
        # 上传到七牛后保存的文件名
        key = filename
        # 生成上传 Token，可以指定过期时间等
        token = auth.upload_token(self._bucket_name)
        ret, info = put_data(token, key, stream)
        print(info)
        try:
            assert ret['key'] == key
        except Exception as e:
            current_app.logger.info(e)
            return False
        return True

    def delete(self, filename):
        auth = Auth(self._access_key, self._secret_key)
        bucket = BucketManager(auth)
        # 删除bucket_name 中的文件 key
        ret, info = bucket.delete(self._bucket_name, filename)
        print(info)
        try:
            assert ret == {}
        except Exception as e:
            current_app.logger.info(e)
        return ret, info

    def url(self, filename):
        return urljoin(self._base_url, filename)
