#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/3/2 下午1:48
"""
from feshttp.err import FuncArgsError

__all__ = ("BaseRequestsMixIn",)


# noinspection PyUnresolvedReferences
class BaseRequestsMixIn(object):
    """
    请求混入类
    """

    def _verify_sanic_app(self, ):
        """
        校验APP类型是否正确

        暂时只支持sanic框架
        Args:

        Returns:

        """

        try:
            from sanic import Sanic
        except ImportError as e:
            raise ImportError(f"Sanic import error {e}.")
        else:
            if not isinstance(self.app, Sanic):
                raise FuncArgsError("app type must be Sanic.")

    def _verify_flask_app(self, ):
        """
        校验APP类型是否正确

        暂时只支持flask框架
        Args:

        Returns:

        """

        try:
            from flask import Flask
        except ImportError as e:
            raise ImportError(f"Flask import error {e}.")
        else:
            if not isinstance(self.app, Flask):
                raise FuncArgsError("app type must be Flask.")
