#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/2/21 上午10:17
"""
import uuid
from typing import Any, Dict, List, NoReturn, Tuple, Union

from .aio_requests import AIORequests
from .err import FuncArgsError, JsonRPCError

__all__ = ("AIOJRPClient",)


class AIOJRPClient(object):
    """
    async json rpc client

    暂时不支持单个和批量的通知调用
    """
    aio_requests: AIORequests = None
    jrpc_router: str = None
    jrpc_server_maps: Dict = {}

    def __init__(self, aio_requests: AIORequests, jrpc_server: str = None, jrpc_router: str = "/api/jrpc/post"):
        """
        async json rpc client
        Args:
            aio_requests: AIORequests class
            jrpc_server: jrpc server name
            jrpc_router: jrpc router
        """
        if self.__class__.aio_requests is None:
            self.__class__.aio_requests = aio_requests
        if self.__class__.jrpc_router is None:
            self.__class__.jrpc_router = jrpc_router
        self.jrpc_server: str = jrpc_server
        self.methods: List[Tuple[str, Union[List, Dict, None]]] = []

    def __getitem__(self, jrpc_server) -> 'AIOJRPClient':
        """
        获取jrpc server
        Args:

        Returns:

        """
        if jrpc_server not in self.jrpc_server_maps:
            raise ValueError(f"{jrpc_server} is does not exist, please register it")
        return AIOJRPClient(self.aio_requests, jrpc_server, self.jrpc_router)

    def __getattr__(self, method) -> 'AIOJRPClient':
        """

        Args:

        Returns:

        """
        self.method = method
        return self

    def __call__(self, *args, **kwargs) -> 'AIOJRPClient':
        """

        Args:

        Returns:

        """
        if args and kwargs:
            raise FuncArgsError("Either a positional parameter or a keyword parameter, "
                                "cannot exist at the same time")
        self.methods.append((self.method, args or kwargs or None))
        return self

    async def done(self, ) -> Union[Any, List[Any]]:
        """
        批量执行结束
        Args:

        Returns:

        """
        jrpc_body, jrpc_ids = [], []
        for method, params in self.methods:
            _jrpc_id = uuid.uuid4().hex
            _body = {'jsonrpc': '2.0', 'method': method, 'id': _jrpc_id}
            if params:
                _body['params'] = params
            jrpc_ids.append(_jrpc_id)
            jrpc_body.append(_body)
        jrpc_body = jrpc_body[0] if len(jrpc_body) == 1 else jrpc_body

        rpc_result = await self._jrpc_post(jrpc_body=jrpc_body)

        if "error" in rpc_result:
            raise JsonRPCError(rpc_result["error"])
        if len(self.methods) == 1:
            return rpc_result["result"]
        else:
            rpc_result = {val["id"]: val for val in rpc_result}
            return [rpc_result[jrpc_id].get("result") or rpc_result[jrpc_id]["error"] for jrpc_id in jrpc_ids]

    @classmethod
    def register(cls, jrpc_server: str, jrpc_address: Tuple[str, int]) -> NoReturn:
        """
        注册jrpc server 名称和地址
        Args:
            jrpc_server: json rpc server name
            jrpc_address: json rpc server address, eg: 127.0.0.1:8000
        Returns:

        """
        if not isinstance(jrpc_address, (tuple, list)):
            raise FuncArgsError("jrpc_address value error")

        if jrpc_server not in cls.jrpc_server_maps:
            cls.jrpc_server_maps[jrpc_server] = f"http://{jrpc_address[0]}:{jrpc_address[1]}{cls.jrpc_router}"

    async def _jrpc_post(self, *, jrpc_body: Dict) -> Union[Dict, List]:
        """
        jsonrpc request
        Args:
            jrpc_body: json rpc request body
        Returns:

        """
        rpc_result = await self.aio_requests.async_post(self.jrpc_server_maps[self.jrpc_server], json=jrpc_body)
        return rpc_result.json()
