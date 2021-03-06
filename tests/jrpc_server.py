#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 2020/2/21 下午1:47
"""
import asyncio
from typing import Dict, List

from sanic import Sanic

from feshttp import SanicJsonRPC

app = Sanic()
jsonrpc = SanicJsonRPC()
jsonrpc.init_app(app)


@jsonrpc.jrpc
async def sub(a: int, b: int) -> List[Dict]:
    await asyncio.sleep(0.1)
    return [{"a": a, "b": b, "c": "c"}]


@jsonrpc.jrpc
async def test() -> str:
    await asyncio.sleep(0.1)
    return "中文"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
