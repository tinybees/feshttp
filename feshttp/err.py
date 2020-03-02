#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-12-25 下午2:08
"""

__all__ = ("Error", "HttpError", "ClientError", "ClientResponseError", "ClientConnectionError", "FuncArgsError",
           "JsonRPCError")


class Error(Exception):
    """
    异常基类
    """

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return "Error: message='{}'".format(self.message)

    def __repr__(self):
        return "<{} '{}'>".format(self.__class__.__name__, self.message)


class HttpError(Error):
    """
    主要处理http 错误,从接口返回
    """

    def __init__(self, status_code, *, message=None, error=None):
        self.status_code = status_code
        self.message = message
        self.error = error

    def __str__(self):
        return "{}, '{}':'{}'".format(self.status_code, self.message, self.message or self.error)

    def __repr__(self):
        return "<{} '{}: {}'>".format(self.__class__.__name__, self.status_code, self.error or self.message)


class ClientError(Error):
    """
    主要处理异步请求的error
    """

    def __init__(self, url, *, message=None):
        self.url = url
        self.message = message
        super().__init__(message)

    def __str__(self):
        return "Error: url='{}', message='{}'".format(self.url, self.message)

    def __repr__(self):
        return "<{} '{}, {}'>".format(self.__class__.__name__, self.url, self.message)


class ClientResponseError(ClientError):
    """
    响应异常
    """

    def __init__(self, url, *, status_code=None, message=None, headers=None, body=None):
        self.url = url
        self.status_code = status_code
        self.message = message
        self.headers = headers
        self.body = body
        super().__init__(self.url, message=self.message)

    def __str__(self):
        return "Error: code={}, url='{}', message='{}', body='{}'".format(
            self.status_code, self.url, self.message, self.body)

    def __repr__(self):
        return "<{} '{}, {}, {}'>".format(self.__class__.__name__, self.status_code, self.url, self.message)


class ClientConnectionError(ClientError):
    """连接异常"""

    pass


class FuncArgsError(Error):
    """
    处理函数参数不匹配引发的error
    """

    pass


class JsonRPCError(Error):
    """
    jsron rpc error
    """
    pass
