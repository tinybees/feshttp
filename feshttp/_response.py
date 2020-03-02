#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午1:16
"""
from typing import Dict

__all__ = ("Response",)


class Response(object):
    """
    响应对象,需要重新封装对象
    """
    __slots__ = ["status_code", "reason", "headers", "cookies", "resp_body", "content"]

    def __init__(self, status_code: int, reason: str, headers: Dict, cookies: Dict, *, resp_body: Dict,
                 content: bytes):
        """

        Args:

        """
        self.status_code = status_code
        self.reason = reason
        self.headers = headers
        self.cookies = cookies
        self.resp_body = resp_body
        self.content = content

    def json(self, ):
        """
        为了适配
        Args:

        Returns:

        """
        return self.resp_body
