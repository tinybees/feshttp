#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/2/21 下午5:00
"""
import asyncio
from asyncio import Queue
from typing import Optional

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
            from sanic_jsonrpc import Jsonrpc
            from sanic_jsonrpc import __version__
            if __version__ != "0.1.1":
                raise ImportError("sanic_jsonrpc version error!")
        except ImportError as e:
            raise ImportError(f"import sanic_jsonrpc error, please 'pip install sanic-jsonrpc==0.1.1', {e}")

        # noinspection PyMissingConstructor
        class JsonRPC(Jsonrpc):
            """

            """

            def __init__(self, app_, post_route_: Optional[str] = None, ws_route_: Optional[str] = None):
                self.app = app_

                if post_route_:
                    self.app.add_route(self._post, post_route_, methods=frozenset({'POST'}))

                if ws_route_:
                    self.app.add_websocket_route(self._ws, ws_route_)

                self._routes = {}
                self._calls = None
                self._processing_task = None

                @app_.listener('after_server_start')
                async def start_processing(_app, _loop):
                    self._calls = Queue(loop=_loop)
                    self._processing_task = asyncio.ensure_future(self._processing())

                @app_.listener('before_server_stop')
                async def finish_calls(_app, _loop):
                    self._processing_task.cancel()
                    await self._processing_task

        self.post_route = post_route or self.post_route
        self.ws_route = ws_route or self.ws_route

        self.jrpc = JsonRPC(app, post_route_=self.post_route, ws_route_=self.ws_route)
