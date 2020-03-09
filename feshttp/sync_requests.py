#!/usr/bin/env python3
# coding=utf-8

"""
@author: guoyanfeng
@software: PyCharm
@time: 18-7-1 上午10:08
"""
import atexit
from http import cookiejar as cookielib
from io import UnsupportedOperation
from typing import Dict, Mapping

import requests
from requests import PreparedRequest, Session
from requests.cookies import RequestsCookieJar, cookiejar_from_dict, merge_cookies
from requests.exceptions import ConnectTimeout, ConnectionError, HTTPError, RequestException, Timeout
from requests.sessions import merge_hooks, merge_setting
from requests.structures import CaseInsensitiveDict
from requests.utils import get_netrc_auth, super_len

from ._err_msg import http_msg
from ._json import dumps
from ._requests import BaseRequestsMixIn
from ._response import Response
from .err import ClientConnectionError, ClientError, ClientResponseError
from .utils import Singleton, _verify_message

__all__ = ("SyncRequests",)


class CustomPreparedRequest(PreparedRequest):
    """
    自定义prepared类 用于dumps时间使用
    """

    def prepare_body(self, data, files, json=None):
        """Prepares the given HTTP body data."""

        # Check if file, fo, generator, iterator.
        # If not, run through normal process.

        # Nottin' on you.
        body = None
        content_type = None

        if not data and json is not None:
            # urllib3 requires a bytes-like body. Python 2's json.dumps
            # provides this natively, but Python 3 gives a Unicode string.
            content_type = 'application/json'
            body = dumps(json)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')

        is_stream = all([
            hasattr(data, '__iter__'),
            not isinstance(data, ((str, bytes), list, tuple, Mapping))
        ])

        try:
            length = super_len(data)
        except (TypeError, AttributeError, UnsupportedOperation):
            length = None

        if is_stream:
            body = data

            if getattr(body, 'tell', None) is not None:
                # Record the current file position before reading.
                # This will allow us to rewind a file in the event
                # of a redirect.
                try:
                    self._body_position = body.tell()
                except (IOError, OSError):
                    # This differentiates from None, allowing us to catch
                    # a failed `tell()` later when trying to rewind the body
                    self._body_position = object()

            if files:
                raise NotImplementedError('Streamed bodies and files are mutually exclusive.')

            if length:
                self.headers['Content-Length'] = str(length)
            else:
                self.headers['Transfer-Encoding'] = 'chunked'
        else:
            # Multi-part file uploads.
            if files:
                (body, content_type) = self._encode_files(files, data)
            else:
                if data:
                    body = self._encode_params(data)
                    if isinstance(data, (str, bytes)) or hasattr(data, 'read'):
                        content_type = None
                    else:
                        content_type = 'application/x-www-form-urlencoded'

            self.prepare_content_length(body)

            # Add content-type if it wasn't explicitly provided.
            if content_type and ('content-type' not in self.headers):
                self.headers['Content-Type'] = content_type

        self.body = body


class CustomSession(Session):
    """
    自定义session
    """

    def prepare_request(self, request):
        """Constructs a :class:`PreparedRequest <PreparedRequest>` for
        transmission and returns it. The :class:`PreparedRequest` has settings
        merged from the :class:`Request <Request>` instance and those of the
        :class:`Session`.

        :param request: :class:`Request` instance to prepare with this
            session's settings.
        :rtype: requests.PreparedRequest
        """
        cookies = request.cookies or {}

        # Bootstrap CookieJar.
        if not isinstance(cookies, cookielib.CookieJar):
            cookies = cookiejar_from_dict(cookies)

        # Merge with session cookies
        merged_cookies = merge_cookies(
            merge_cookies(RequestsCookieJar(), self.cookies), cookies)

        # Set environment's basic authentication if not explicitly set.
        auth = request.auth
        if self.trust_env and not auth and not self.auth:
            auth = get_netrc_auth(request.url)

        p = CustomPreparedRequest()
        p.prepare(
            method=request.method.upper(),
            url=request.url,
            files=request.files,
            data=request.data,
            json=request.json,
            headers=merge_setting(request.headers, self.headers, dict_class=CaseInsensitiveDict),
            params=merge_setting(request.params, self.params),
            auth=merge_setting(auth, self.auth),
            cookies=merged_cookies,
            hooks=merge_hooks(request.hooks, self.hooks),
        )
        return p


class SyncRequests(BaseRequestsMixIn, Singleton):
    """
    基于requests的同步封装
    """

    def __init__(self, app=None, *, timeout: int = 5 * 60, verify_ssl: bool = True, message: Dict = None,
                 use_zh: bool = True):
        """
        基于requests的同步封装
        Args:
            app: app应用
            timeout:request timeout
            verify_ssl:verify ssl
            message: 提示消息
            use_zh: 消息提示是否使用中文，默认中文

        """
        self.app = app
        self.session = None
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.message = message or {}
        self.use_zh = use_zh
        self.msg_zh = None

        if app is not None:
            self.init_app(app, timeout=self.timeout, verify_ssl=self.verify_ssl, message=self.message,
                          use_zh=self.use_zh)

    def init_app(self, app, *, timeout: int = None, verify_ssl: bool = None, message: Dict = None,
                 use_zh: bool = None):
        """
        基于aiohttp的异步封装
        Args:
            app: app应用
            timeout:request timeout
            verify_ssl:verify ssl
            message: 提示消息
            use_zh: 消息提示是否使用中文，默认中文
        Returns:

        """
        self.app = app
        self._verify_flask_app()  # 校验APP类型是否正确

        self.timeout = timeout or app.config.get("ECLIENTS_HTTP_TIMEOUT", None) or self.timeout
        self.verify_ssl = verify_ssl or app.config.get("ECLIENTS_HTTP_VERIFYSSL", None) or self.verify_ssl
        message = message or app.config.get("ECLIENTS_HTTP_MESSAGE", None) or self.message
        use_zh = use_zh or app.config.get("ECLIENTS_HTTP_MSGZH", None) or self.use_zh

        self.message = _verify_message(http_msg, message)
        self.msg_zh = "msg_zh" if use_zh else "msg_en"

        @app.before_first_request
        def open_connection():
            """

            Args:

            Returns:

            """
            self.session = CustomSession()

        @atexit.register
        def close_connection():
            """
            释放session连接池所有连接
            Args:

            Returns:

            """
            if self.session:
                self.session.close()

    def init_session(self, *, timeout: int = None, verify_ssl: bool = None, message: Dict = None,
                     use_zh: bool = None):
        """
        基于aiohttp的异步封装
        Args:
            timeout:request timeout
            verify_ssl:verify ssl
            message: 提示消息
            use_zh: 消息提示是否使用中文，默认中文
        Returns:

        """
        self.timeout = timeout or self.timeout
        self.verify_ssl = verify_ssl or self.verify_ssl
        use_zh = use_zh or self.use_zh
        self.message = _verify_message(http_msg, message or self.message)
        self.msg_zh = "msg_zh" if use_zh else "msg_en"
        self.session = CustomSession()

        @atexit.register
        def close_connection():
            """
            释放session连接池所有连接
            Args:

            Returns:

            """
            if self.session:
                self.session.close()

    def _request(self, method: str, url: str, *, params: Dict = None, data: Dict = None, json: Dict = None,
                 headers: Dict = None, verify_ssl: bool = None, timeout: int = None, **kwargs) -> Response:
        """

        Args:
            method, url, *,  params=None, data=None, json=None, headers=None, **kwargs
        Returns:

        """

        def _get():
            """

            Args:

            Returns:

            """
            return self.session.get(url, params=params, verify=verify_ssl, headers=headers,
                                    timeout=timeout, **kwargs)

        def _post():
            """

            Args:

            Returns:

            """
            res = self.session.post(url, params=params, data=data, json=json, headers=headers,
                                    verify=verify_ssl, timeout=timeout, **kwargs)
            return res

        def _put():
            """

            Args:

            Returns:

            """
            return self.session.put(url, params=params, data=data, json=json, headers=headers, verify=verify_ssl,
                                    timeout=timeout, **kwargs)

        def _patch():
            """

            Args:

            Returns:

            """
            return self.session.patch(url, params=params, data=data, json=json, headers=headers, verify=verify_ssl,
                                      timeout=timeout, **kwargs)

        def _delete():
            """

            Args:

            Returns:

            """
            return self.session.delete(url, params=params, data=data, json=json, headers=headers, verify=verify_ssl,
                                       timeout=timeout, **kwargs)

        get_resp = {"GET": _get, "POST": _post, "PUT": _put, "DELETE": _delete, "PATCH": _patch}
        try:
            resp = get_resp[method.upper()]()
            resp.raise_for_status()
        except KeyError as e:
            raise ClientError(url=url, message="error method {0}".format(str(e)))
        except (ConnectionError, ConnectTimeout) as e:
            raise ClientConnectionError(url=url, message=str(e))
        except (Timeout, HTTPError) as e:
            resp = e.response
            try:
                resp_data = resp.json()
            except (ValueError, TypeError):
                resp_data = resp.text
            raise ClientResponseError(url=url, status_code=resp.status_code, message=resp.reason, headers=resp.headers,
                                      body=resp_data)
        except RequestException as e:
            raise ClientError(url=url, message="ClientError: {}".format(vars(e)))

        with resp:
            try:
                resp_json = resp.json()
            except (ValueError, TypeError):
                context_type = resp.headers.get("Content-Type", "")
                if "text" in context_type:
                    resp_text = resp.text
                    return Response(resp.status_code, resp.reason, resp.headers, resp.cookies, resp_body=resp_text,
                                    content=b"")
                else:
                    resp_bytes = resp.content
                    return Response(resp.status_code, resp.reason, resp.headers, resp.cookies, resp_body="",
                                    content=resp_bytes)
            else:
                return Response(resp.status_code, resp.reason, resp.headers, resp.cookies, resp_body=resp_json,
                                content=b"")

    def request(self, method: str, url: str, *, params: Dict = None, data: Dict = None, json: Dict = None,
                headers: Dict = None, verify_ssl: bool = None, timeout: int = None, **kwargs) -> Response:
        """

        Args:

        Returns:

        """
        verify_ssl = self.verify_ssl if verify_ssl is None else verify_ssl
        timeout = self.timeout if timeout is None else timeout
        return self._request(method, url, params=params, data=data, json=json, headers=headers,
                             verify_ssl=verify_ssl, timeout=timeout, **kwargs)

    def get(self, url: str, *, params: Dict = None, headers: Dict = None, verify_ssl: bool = None,
            timeout: int = None, **kwargs) -> Response:
        """

        Args:

        Returns:

        """
        verify_ssl = self.verify_ssl if verify_ssl is None else verify_ssl
        timeout = self.timeout if timeout is None else timeout
        return self._request("GET", url, params=params, verify_ssl=verify_ssl, headers=headers,
                             timeout=timeout, **kwargs)

    def post(self, url: str, *, params: Dict = None, data: Dict = None, json: Dict = None, headers: Dict = None,
             verify_ssl: bool = None, timeout: int = None, **kwargs) -> Response:
        """

        Args:

        Returns:

        """
        verify_ssl = self.verify_ssl if verify_ssl is None else verify_ssl
        timeout = self.timeout if timeout is None else timeout
        return self._request("POST", url, params=params, data=data, json=json, headers=headers, verify_ssl=verify_ssl,
                             timeout=timeout, **kwargs)

    def put(self, url: str, *, params: Dict = None, data: Dict = None, json: Dict = None, headers: Dict = None,
            verify_ssl: bool = None, timeout: int = None, **kwargs) -> Response:
        """

        Args:

        Returns:

        """
        verify_ssl = self.verify_ssl if verify_ssl is None else verify_ssl
        timeout = self.timeout if timeout is None else timeout
        return self._request("PUT", url, params=params, data=data, json=json, headers=headers, verify_ssl=verify_ssl,
                             timeout=timeout, **kwargs)

    def patch(self, url: str, *, params: Dict = None, data: Dict = None, json: Dict = None, headers: Dict = None,
              verify_ssl: bool = None, timeout: int = None, **kwargs) -> Response:
        """

        Args:

        Returns:

        """
        verify_ssl = self.verify_ssl if verify_ssl is None else verify_ssl
        timeout = self.timeout if timeout is None else timeout
        return self._request("PATCH", url, params=params, data=data, json=json, headers=headers, verify_ssl=verify_ssl,
                             timeout=timeout, **kwargs)

    def delete(self, url: str, *, params: Dict = None, headers: Dict = None, verify_ssl: bool = None,
               timeout: int = None, **kwargs) -> Response:
        """

        Args:

        Returns:

        """
        verify_ssl = self.verify_ssl if verify_ssl is None else verify_ssl
        timeout = self.timeout if timeout is None else timeout
        return self._request("DELETE", url, params=params, verify_ssl=verify_ssl, headers=headers, timeout=timeout,
                             **kwargs)

    def close(self, ):
        """
        close
        Args:

        Returns:

        """
        self.session.close()
