#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/2/21 下午5:00
"""
from typing import Callable, Optional, Tuple

__all__ = ("SanicJsonRPC",)


class SanicJsonRPC(object):
    """
    sanic jsonrpc object
    """

    def __init__(self, app=None, post_route: str = "/api/jrpc/post", ws_route: str = "/api/jrpc/ws"):
        """
        jsonrpc 实例初始化
        Args:
            app: app应用
            post_route: post url
            ws_route: websocket url
        """
        self.jrpc = None
        self.post_route: str = post_route
        self.ws_route: str = ws_route

        if app is not None:
            self.init_app(app)

    def init_app(self, app, post_route: str = "/api/jrpc/post", ws_route: str = "/api/jrpc/ws"):
        """
        jsonrpc 实例初始化
        Args:
            app: app应用
            post_route: post url
            ws_route: websocket url
        Returns:

        """
        try:
            from sanic_jsonrpc import SanicJsonrpc
            from sanic_jsonrpc import __version__
            # noinspection PyProtectedMember
            from sanic_jsonrpc._routing import Route

            if __version__ != "0.2.2":
                raise ImportError("sanic_jsonrpc version error!")
        except ImportError as e:
            raise ImportError(f"import sanic_jsonrpc error, please 'pip install sanic-jsonrpc==0.2.2', {e}")

        # noinspection PyMissingConstructor
        class JsonRPC(SanicJsonrpc):
            """

            """

            def __call__(self, method_: Optional[str] = None, *,
                         is_post_: Tuple[bool, ...] = (True, False),
                         is_request_: Tuple[bool, ...] = (True, False),
                         **annotations: type) -> Callable:
                if isinstance(method_, Callable):
                    return self.__call__(is_post_=is_post_, is_request_=is_request_)(method_)

                def deco(func: Callable) -> Callable:
                    route = Route.from_inspect(func, method_, annotations)
                    route.result = None  # 不进行返回值的类型校验
                    self._routes.update({(ip, ir, route.method): route for ip in is_post_ for ir in is_request_})
                    return func

                return deco

        self.post_route = post_route or self.post_route
        self.ws_route = ws_route or self.ws_route

        self.jrpc = JsonRPC(app, post_route=self.post_route, ws_route=self.ws_route)
