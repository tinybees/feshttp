#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-25 下午2:42
可配置消息模块
"""

__all__ = ("http_msg",)

# request and schema 从200到300
http_msg = {
    200: {"msg_code": 200, "msg_zh": "获取API响应结果失败.", "msg_en": "Failed to get API response result.",
          "description": "async request 获取API响应结果失败时的提示"},
}
