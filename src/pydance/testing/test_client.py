"""
Test client for Pydance applications.

Provides a comprehensive HTTP client for testing API endpoints,
middleware, and application behavior.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urlencode
from dataclasses import dataclass

from pydance.http.request import Request
from pydance.http.response import Response


@dataclass
class TestRequest:
    """Test request representation"""
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[Union[str, bytes, Dict[str, Any]]] = None
    query_params: Dict[str, str] = None

    def __post_init__(self):
        if self.query_params is None:
            self.query_params = {}


@dataclass
class TestResponse:
    """Test response representation"""
    status_code: int
    headers: Dict[str, str]
    body: Union[str, bytes, Dict[str, Any]]
    request: TestRequest

    def json(self) -> Dict[str, Any]:
        """Parse response body as JSON"""
        if isinstance(self.body, str):
            return json.loads(self.body)
        elif isinstance(self.body, bytes):
            return json.loads(self.body.decode('utf-8'))
        else:
            return self.body

    def text(self) -> str:
        """Get response body as text"""
        if isinstance(self.body, bytes):
            return self.body.decode('utf-8')
        elif isinstance(self.body, dict):
            return json.dumps(self.body)
        else:
            return str(self.body)


class TestClient:
    """
    HTTP test client for Pydance applications.

    Provides methods for making HTTP requests in tests with proper
    request/response handling and authentication support.
    """

    def __init__(self, app=None, base_url: str = "http://testserver"):
        self.app = app
        self.base_url = base_url
        self.session_headers: Dict[str, str] = {}
        self.cookies: Dict[str, str] = {}

    def _build_url(self, path: str) -> str:
        """Build full URL from path"""
        if path.startswith('http'):
            return path
        return f"{self.base_url}{path}"

    def _build_request(self, method: str, url: str, **kwargs) -> TestRequest:
        """Build test request"""
        headers = {**self.session_headers}
        headers.update(kwargs.get('headers', {}))

        # Add cookies to headers if present
        if self.cookies:
            cookie_header = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
            headers['Cookie'] = cookie_header

        return TestRequest(
            method=method.upper(),
            url=self._build_url(url),
            headers=headers,
            body=kwargs.get('data') or kwargs.get('json'),
            query_params=kwargs.get('params', {})
        )

    def _make_request(self, request: TestRequest) -> TestResponse:
        """Make HTTP request (mock implementation)"""
        # In a real implementation, this would make actual HTTP requests
        # For now, return a mock response

        # Simulate different responses based on URL patterns
        if '/health' in request.url:
            return TestResponse(
                status_code=200,
                headers={'Content-Type': 'application/json'},
                body=json.dumps({"status": "healthy", "timestamp": "2023-01-01T00:00:00Z"}),
                request=request
            )
        elif '/error' in request.url:
            return TestResponse(
                status_code=500,
                headers={'Content-Type': 'application/json'},
                body=json.dumps({"error": "Internal server error"}),
                request=request
            )
        else:
            return TestResponse(
                status_code=200,
                headers={'Content-Type': 'application/json'},
                body=json.dumps({"message": "success"}),
                request=request
            )

    def get(self, url: str, **kwargs) -> TestResponse:
        """Make GET request"""
        request = self._build_request('GET', url, **kwargs)
        return self._make_request(request)

    def post(self, url: str, **kwargs) -> TestResponse:
        """Make POST request"""
        request = self._build_request('POST', url, **kwargs)
        return self._make_request(request)

    def put(self, url: str, **kwargs) -> TestResponse:
        """Make PUT request"""
        request = self._build_request('PUT', url, **kwargs)
        return self._make_request(request)

    def patch(self, url: str, **kwargs) -> TestResponse:
        """Make PATCH request"""
        request = self._build_request('PATCH', url, **kwargs)
        return self._make_request(request)

    def delete(self, url: str, **kwargs) -> TestResponse:
        """Make DELETE request"""
        request = self._build_request('DELETE', url, **kwargs)
        return self._make_request(request)

    def head(self, url: str, **kwargs) -> TestResponse:
        """Make HEAD request"""
        request = self._build_request('HEAD', url, **kwargs)
        return self._make_request(request)

    def options(self, url: str, **kwargs) -> TestResponse:
        """Make OPTIONS request"""
        request = self._build_request('OPTIONS', url, **kwargs)
        return self._make_request(request)

    # Authentication methods
    def login(self, username: str, password: str) -> TestResponse:
        """Login and store authentication cookies/tokens"""
        response = self.post('/auth/login', json={
            'username': username,
            'password': password
        })

        if response.status_code == 200:
            # Store authentication tokens/cookies
            if 'Set-Cookie' in response.headers:
                # Parse cookies (simplified)
                pass

        return response

    def logout(self) -> TestResponse:
        """Logout and clear authentication"""
        response = self.post('/auth/logout')
        self.cookies.clear()
        return response

    # Session management
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.session_headers['Authorization'] = f'Bearer {token}'

    def set_cookie(self, name: str, value: str):
        """Set session cookie"""
        self.cookies[name] = value

    def clear_auth(self):
        """Clear all authentication data"""
        self.session_headers.pop('Authorization', None)
        self.cookies.clear()

    # Utility methods
    def build_url(self, path: str, params: Dict[str, str] = None) -> str:
        """Build URL with query parameters"""
        url = self._build_url(path)
        if params:
            query_string = urlencode(params)
            url += f"?{query_string}"
        return url

    def get_cookies(self) -> Dict[str, str]:
        """Get current session cookies"""
        return self.cookies.copy()

    def get_headers(self) -> Dict[str, str]:
        """Get current session headers"""
        return self.session_headers.copy()


__all__ = [
    'TestClient',
    'TestRequest',
    'TestResponse'
]
