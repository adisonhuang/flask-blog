#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'adison'
# @Time    : 2018/1/12
from qiniu.services.storage import uploader


def put_data(
        up_token, key, data, params=None, mime_type='application/octet-stream', check_crc=False,
        progress_handler=None,
        fname=None):
    """上传二进制流到七牛,修复七牛云原始方法不支持 python3问题

    Args:
        up_token:         上传凭证
        key:              上传文件名
        data:             上传二进制流
        params:           自定义变量，规格参考 http://developer.qiniu.com/docs/v6/api/overview/up/response/vars.html#xvar
        mime_type:        上传数据的mimeType
        check_crc:        是否校验crc32
        progress_handler: 上传进度

    Returns:
        一个dict变量，类似 {"hash": "<Hash string>", "key": "<Key string>"}
        一个ResponseInfo对象
    """
    final_data = b''
    if hasattr(data, 'read'):
        while True:
            tmp_data = data.read(uploader.config._BLOCK_SIZE)
            if len(tmp_data) == 0:
                break
            else:
                final_data += tmp_data
    else:
        final_data = data

    crc = uploader.crc32(final_data)
    return uploader._form_put(up_token, key, final_data, params, mime_type, crc, progress_handler, fname)
