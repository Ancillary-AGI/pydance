"""
Test Client for Pydance Applications

Provides a test client for making HTTP requests to Pydance applications during testing.
"""

import json
from typing import Dict, Any, Optional, Union, List


class TestResponse:
    """
    Response object returned by the test client.
    """

    def __init__(self, status_code: int, headers: Dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.body = body
        self._json_data = None

    @property
    def content(self) -> bytes:
        """Get response content as bytes."""
        return self.body

    @property
    def text(self) -> str:
        """Get response content as text."""
        return self.body.decode('utf-8', errors='replace')

    def json(self) -> Any:
        """Parse response content as JSON."""
        if self._json_data is None:
            self._json_data = json.loads(self.text)
        return self._json_data

    def __repr__(self):
        return f"<TestResponse {self.status_code}>"


class TestClient:
    """
    Test client for making HTTP requests to Pydance applications.

    This client bypasses the ASGI server and directly calls the application,
    making it fast and suitable for unit testing.
    """

    def __init__(self, app, base_url: str = "http://testserver"):
        self.app = app
        self.base_url = base_url.rstrip('/')

    async def _make_request(self, method: str, path: str,
                           query_params: Optional[Dict[str, Any]] = None,
                           headers: Optional[Dict[str, str]] = None,
                           data: Optional[Union[Dict[str, Any], str, bytes]] = None,
                           json_data: Optional[Any] = None,
                           cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """
        Make an HTTP request to the application.
        """
        # Build the full URL
        url = f"{self.base_url}{path}"
        if query_params:
            query_string = urlencode(query_params)
            url += f"?{query_string}"

        # Prepare headers
        request_headers = {
            'host': 'testserver',
            'user-agent': 'pydance-test-client/1.0',
        }
        if headers:
            request_headers.update(headers)

        # Prepare body
        body = b''
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            request_headers['content-type'] = 'application/json'
        elif isinstance(data, dict):
            body = urlencode(data).encode('utf-8')
            request_headers['content-type'] = 'application/x-www-form-urlencoded'
        elif isinstance(data, str):
            body = data.encode('utf-8')
            request_headers.setdefault('content-type', 'text/plain')
        elif isinstance(data, bytes):
            body = data
            request_headers.setdefault('content-type', 'application/octet-stream')

        # Set content-length
        request_headers['content-length'] = str(len(body))

        # Prepare ASGI scope
        scope = {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': method.upper(),
            'path': path,
            'raw_path': path.encode('utf-8'),
            'query_string': urlencode(query_params or {}).encode('utf-8'),
            'root_path': '',
            'headers': [[k.encode('latin-1'), v.encode('latin-1')] for k, v in request_headers.items()],
            'server': ('testserver', 80),
            'client': ('127.0.0.1', 12345),
        }

        # Prepare cookies
        if cookies:
            cookie_header = '; '.join(f"{k}={v}" for k, v in cookies.items())
            scope['headers'].append([b'cookie', cookie_header.encode('latin-1')])

        # Response collection
        response_started = False
        response_status = None
        response_headers = {}
        response_body = b''

        async def receive():
            """Receive function for ASGI."""
            return {
                'type': 'http.request',
                'body': body,
                'more_body': False,
            }

        async def send(message):
            """Send function for ASGI."""
            nonlocal response_started, response_status, response_headers, response_body

            if message['type'] == 'http.response.start':
                response_started = True
                response_status = message['status']
                response_headers = {k.decode('latin-1'): v.decode('latin-1')
                                  for k, v in message.get('headers', [])}

            elif message['type'] == 'http.response.body':
                response_body += message.get('body', b'')

        # Make the request
        await self.app(scope, receive, send)

        return TestResponse(response_status, response_headers, response_body)

    async def get(self, path: str, query_params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make a GET request."""
        return await self._make_request('GET', path, query_params, headers, cookies=cookies)

    async def post(self, path: str, data: Optional[Union[Dict[str, Any], str, bytes]] = None,
                   json_data: Optional[Any] = None,
                   query_params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make a POST request."""
        return await self._make_request('POST', path, query_params, headers, data, json_data, cookies)

    async def put(self, path: str, data: Optional[Union[Dict[str, Any], str, bytes]] = None,
                  json_data: Optional[Any] = None,
                  query_params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None,
                  cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make a PUT request."""
        return await self._make_request('PUT', path, query_params, headers, data, json_data, cookies)

    async def patch(self, path: str, data: Optional[Union[Dict[str, Any], str, bytes]] = None,
                    json_data: Optional[Any] = None,
                    query_params: Optional[Dict[str, Any]] = None,
                    headers: Optional[Dict[str, str]] = None,
                    cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make a PATCH request."""
        return await self._make_request('PATCH', path, query_params, headers, data, json_data, cookies)

    async def delete(self, path: str, query_params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None,
                     cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make a DELETE request."""
        return await self._make_request('DELETE', path, query_params, headers, cookies=cookies)

    async def head(self, path: str, query_params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make a HEAD request."""
        return await self._make_request('HEAD', path, query_params, headers, cookies=cookies)

    async def options(self, path: str, query_params: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None,
                      cookies: Optional[Dict[str, str]] = None) -> TestResponse:
        """Make an OPTIONS request."""
        return await self._make_request('OPTIONS', path, query_params, headers, cookies=cookies)

    def __repr__(self):
        return f"<TestClient {self.base_url}>"


__all__ = [
    'TestClient',
    'TestResponse',
]
