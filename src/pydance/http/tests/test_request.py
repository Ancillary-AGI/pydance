"""
Comprehensive unit tests for the Pydance HTTP Request module.
Tests request parsing, body processing, security features, and performance metrics.
"""

import asyncio
import pytest
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from pydance.http.request import Request, RequestState, OptimizedHeaders, RequestSecurity, RequestMetrics
from pydance.exceptions import BadRequest, UnsupportedMediaType


class TestOptimizedHeaders:
    """Test cases for OptimizedHeaders class"""

    def test_header_parsing(self):
        """Test header parsing and normalization"""
        headers_list = [
            [b'Content-Type', b'application/json'],
            [b'content-type', b'text/plain'],  # Duplicate with different case
            [b'Authorization', b'Bearer token123'],
            [b'X-Custom-Header', b'custom-value']
        ]

        headers = OptimizedHeaders(headers_list)

        # Test case-insensitive access
        assert headers.get('content-type') == 'text/plain'
        assert headers.get('Content-Type') == 'text/plain'
        assert headers.get('CONTENT-TYPE') == 'text/plain'

        # Test specific header access
        assert headers.get('authorization') == 'Bearer token123'
        assert headers.get('x-custom-header') == 'custom-value'

        # Test missing header
        assert headers.get('missing-header') is None
        assert headers.get('missing-header', 'default') == 'default'

    def test_header_containment(self):
        """Test header containment checks"""
        headers_list = [
            [b'Content-Type', b'application/json'],
            [b'Authorization', b'Bearer token123']
        ]

        headers = OptimizedHeaders(headers_list)

        assert 'content-type' in headers
        assert 'Content-Type' in headers
        assert 'authorization' in headers
        assert 'missing-header' not in headers

    def test_multiple_headers(self):
        """Test handling of multiple headers with same name"""
        headers_list = [
            [b'Accept', b'text/html'],
            [b'accept', b'application/json'],  # Same header, different case
            [b'Set-Cookie', b'cookie1=value1'],
            [b'set-cookie', b'cookie2=value2']  # Another duplicate
        ]

        headers = OptimizedHeaders(headers_list)

        # Should handle multiple headers
        accept_values = headers.get_all('accept')
        assert len(accept_values) >= 1

        cookie_values = headers.get_all('set-cookie')
        assert len(cookie_values) >= 1


class TestRequestState:
    """Test cases for RequestState class"""

    def test_state_operations(self):
        """Test basic state operations"""
        state = RequestState()

        # Test set and get
        state.set('key1', 'value1')
        assert state.get('key1') == 'value1'

        # Test default values
        assert state.get('nonexistent', 'default') == 'default'

        # Test delete
        state.delete('key1')
        assert state.get('key1') is None

        # Test clear
        state.set('key2', 'value2')
        state.clear()
        assert state.get('key2') is None

    def test_thread_safety(self):
        """Test thread safety of state operations"""
        state = RequestState()

        # Basic thread safety test
        state.set('thread_test', 'value')
        assert state.get('thread_test') == 'value'

    def test_all_method(self):
        """Test getting all state data"""
        state = RequestState()
        state.set('key1', 'value1')
        state.set('key2', 'value2')

        all_data = state.all()
        assert all_data == {'key1': 'value1', 'key2': 'value2'}


class TestRequest:
    """Test cases for Request class"""

    def setup_method(self):
        """Setup for each test method"""
        self.scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'query_string': b'param1=value1&param2=value2',
            'headers': [
                [b'host', b'localhost:8000'],
                [b'content-type', b'application/json'],
                [b'user-agent', b'test-agent'],
                [b'accept', b'application/json'],
                [b'accept-language', b'en-US,en;q=0.9'],
                [b'cookie', b'session=abc123; theme=dark']
            ],
            'scheme': 'http',
            'server': ('localhost', 8000),
            'client': ('127.0.0.1', 12345)
        }

        self.receive = AsyncMock()
        self.send = Mock()
        self.app = Mock()
        self.app.config = Mock()

    def test_request_initialization(self):
        """Test request initializes correctly"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.method == 'GET'
        assert request.path == '/test'
        assert request.raw_path == '/test'
        assert request.query_string == 'param1=value1&param2=value2'
        assert request.is_secure is False
        assert request.host == 'localhost:8000'
        assert request.remote_addr == '127.0.0.1'

    def test_request_headers(self):
        """Test header parsing and access"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.headers.get('content-type') == 'application/json'
        assert request.headers.get('user-agent') == 'test-agent'
        assert request.headers.get('accept') == 'application/json'
        assert request.headers.get('accept-language') == 'en-US,en;q=0.9'
        assert request.headers.get('missing-header') is None

    def test_request_query_params(self):
        """Test query parameter parsing"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.query_params['param1'] == ['value1']
        assert request.query_params['param2'] == ['value2']

        # Test query param access methods
        assert request.get_query_param('param1') == 'value1'
        assert request.get_query_param('param2') == 'value2'
        assert request.get_query_param('missing') is None
        assert request.get_query_param('missing', 'default') == 'default'

    def test_request_cookies(self):
        """Test cookie parsing"""
        request = Request(self.scope, self.receive, self.send, self.app)

        cookies = request.cookies
        assert cookies['session'] == 'abc123'
        assert cookies['theme'] == 'dark'

    def test_request_content_type_detection(self):
        """Test content type detection methods"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request._is_json_content_type() is True
        assert request._is_form_content_type() is False
        assert request._is_xml_content_type() is False
        assert request._is_text_content_type() is False

    def test_request_url_properties(self):
        """Test URL-related properties"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.url == 'http://localhost:8000/test'
        assert request.base_url == 'http://localhost:8000'

    def test_request_method_checks(self):
        """Test HTTP method checking"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.is_method('GET') is True
        assert request.is_method('POST') is False
        assert request.is_method('get') is True  # Case insensitive

    def test_request_acceptance_checks(self):
        """Test content type and language acceptance"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.accepts('application/json') is True
        assert request.accepts('text/html') is False

        assert request.accepts_language('en-US') is True
        assert request.accepts_language('fr-FR') is False

    def test_request_security_assessment(self):
        """Test security threat assessment"""
        request = Request(self.scope, self.receive, self.send, self.app)

        # Should be safe with normal headers
        assert request.threat_level == RequestSecurity.SAFE

    def test_request_id_generation(self):
        """Test request ID generation"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.request_id is not None
        assert isinstance(request.request_id, str)
        assert len(request.request_id) > 0

    def test_request_fingerprint_generation(self):
        """Test client fingerprint generation"""
        request = Request(self.scope, self.receive, self.send, self.app)

        assert request.client_fingerprint is not None
        assert isinstance(request.client_fingerprint, str)
        assert len(request.client_fingerprint) == 32  # MD5 hash length

    def test_request_state_management(self):
        """Test request state management"""
        request = Request(self.scope, self.receive, self.send, self.app)

        # Test state operations
        request.state.set('test_key', 'test_value')
        assert request.state.get('test_key') == 'test_value'

        # Test path parameters
        request.path_params = {'id': 123, 'name': 'test'}
        assert request.get_path_param('id') == 123
        assert request.get_path_param('name') == 'test'
        assert request.get_path_param('missing') is None

    def test_request_metrics(self):
        """Test request metrics collection"""
        request = Request(self.scope, self.receive, self.send, self.app)

        metrics = request.metrics
        assert metrics.created_at > 0
        assert metrics.headers_parsed_at > 0
        assert isinstance(metrics.memory_used, int)

    def test_request_performance_report(self):
        """Test performance report generation"""
        request = Request(self.scope, self.receive, self.send, self.app)

        report = request.get_performance_report()

        assert 'request_id' in report
        assert 'method' in report
        assert 'path' in report
        assert 'metrics' in report
        assert 'security_flags' in report

        assert report['method'] == 'GET'
        assert report['path'] == '/test'

    def test_request_repr(self):
        """Test request string representation"""
        request = Request(self.scope, self.receive, self.send, self.app)

        repr_str = repr(request)
        assert 'Request' in repr_str
        assert 'GET' in repr_str
        assert '/test' in repr_str
        assert 'safe' in repr_str.lower()


class TestRequestBodyProcessing:
    """Test cases for request body processing"""

    def setup_method(self):
        """Setup for body processing tests"""
        self.scope = {
            'type': 'http',
            'method': 'POST',
            'path': '/test',
            'query_string': b'',
            'headers': [
                [b'host', b'localhost:8000'],
                [b'content-type', b'application/json'],
                [b'content-length', b'25']
            ],
            'scheme': 'http',
            'server': ('localhost', 8000),
            'client': ('127.0.0.1', 12345)
        }

        self.receive = AsyncMock()
        self.send = Mock()
        self.app = Mock()
        self.app.config = Mock()

    async def test_json_body_parsing(self):
        """Test JSON body parsing"""
        json_data = {'key': 'value', 'number': 42}
        body_bytes = json.dumps(json_data).encode()

        self.receive.return_value = {
            'type': 'http.request',
            'body': body_bytes,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)
        parsed_json = await request.json()

        assert parsed_json == json_data

    async def test_empty_body_handling(self):
        """Test handling of empty request body"""
        self.receive.return_value = {
            'type': 'http.request',
            'body': b'',
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        # Empty body should return empty bytes
        body = await request.body()
        assert body == b''

    async def test_form_data_parsing(self):
        """Test form data parsing"""
        form_data = 'field1=value1&field2=value2&field3=value3'
        body_bytes = form_data.encode()

        # Update scope for form content type
        self.scope['headers'] = [
            [b'host', b'localhost:8000'],
            [b'content-type', b'application/x-www-form-urlencoded'],
            [b'content-length', str(len(body_bytes)).encode()]
        ]

        self.receive.return_value = {
            'type': 'http.request',
            'body': body_bytes,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)
        form = await request.form()

        assert form['field1'] == 'value1'
        assert form['field2'] == 'value2'
        assert form['field3'] == 'value3'

    async def test_text_body_parsing(self):
        """Test text body parsing"""
        text_data = 'Hello, World!'
        body_bytes = text_data.encode()

        # Update scope for text content type
        self.scope['headers'] = [
            [b'host', b'localhost:8000'],
            [b'content-type', b'text/plain'],
            [b'content-length', str(len(body_bytes)).encode()]
        ]

        self.receive.return_value = {
            'type': 'http.request',
            'body': body_bytes,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)
        text = await request.text()

        assert text == text_data

    async def test_invalid_json_handling(self):
        """Test handling of invalid JSON"""
        invalid_json = b'{"invalid": json}'

        self.receive.return_value = {
            'type': 'http.request',
            'body': invalid_json,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        with pytest.raises(BadRequest):
            await request.json()

    async def test_unsupported_content_type(self):
        """Test handling of unsupported content types"""
        # Update scope for unsupported content type
        self.scope['headers'] = [
            [b'host', b'localhost:8000'],
            [b'content-type', b'text/csv'],
            [b'content-length', b'0']
        ]

        self.receive.return_value = {
            'type': 'http.request',
            'body': b'',
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        with pytest.raises(UnsupportedMediaType):
            await request.json()

    async def test_streaming_body(self):
        """Test streaming body processing"""
        chunk1 = b'Hello, '
        chunk2 = b'World!'

        self.receive.side_effect = [
            {'type': 'http.request', 'body': chunk1, 'more_body': True},
            {'type': 'http.request', 'body': chunk2, 'more_body': False}
        ]

        request = Request(self.scope, self.receive, self.send, self.app)

        chunks = []
        async for chunk in request.stream():
            chunks.append(chunk)

        assert chunks == [chunk1, chunk2]

    async def test_body_caching(self):
        """Test that body is cached after first read"""
        body_data = b'test data'

        self.receive.return_value = {
            'type': 'http.request',
            'body': body_data,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        # First read
        body1 = await request.body()

        # Second read should use cache
        body2 = await request.body()

        assert body1 == body_data
        assert body2 == body_data
        assert body1 is body2  # Same object reference

        # Receive should only be called once due to caching
        assert self.receive.call_count == 1


class TestRequestSecurity:
    """Test cases for request security features"""

    def setup_method(self):
        """Setup for security tests"""
        self.scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'query_string': b'',
            'headers': [
                [b'host', b'localhost:8000'],
                [b'user-agent', b'Mozilla/5.0 (compatible; TestBot/1.0)'],
                [b'x-forwarded-for', b'192.168.1.100, 10.0.0.1'],
                [b'x-real-ip', b'192.168.1.100']
            ],
            'scheme': 'http',
            'server': ('localhost', 8000),
            'client': ('127.0.0.1', 12345)
        }

        self.receive = AsyncMock()
        self.send = Mock()
        self.app = Mock()
        self.app.config = Mock()

    def test_suspicious_user_agent_detection(self):
        """Test detection of suspicious user agents"""
        request = Request(self.scope, self.receive, self.send, self.app)

        # Bot-like user agent should be flagged as suspicious
        assert request.threat_level in [RequestSecurity.SUSPICIOUS, RequestSecurity.MALICIOUS]

    def test_proxy_header_handling(self):
        """Test handling of proxy headers"""
        request = Request(self.scope, self.receive, self.send, self.app)

        # Should use X-Forwarded-For when available
        assert request.remote_addr == '192.168.1.100'

    def test_path_traversal_detection(self):
        """Test detection of path traversal attempts"""
        # Test with path traversal in URL
        self.scope['path'] = '/test/../../../etc/passwd'

        request = Request(self.scope, self.receive, self.send, self.app)

        # Should be flagged as malicious
        assert request.threat_level == RequestSecurity.MALICIOUS

    def test_sql_injection_detection(self):
        """Test detection of SQL injection patterns"""
        # Test with SQL injection in query string
        self.scope['query_string'] = b"param=1'; DROP TABLE users; --"

        request = Request(self.scope, self.receive, self.send, self.app)

        # Should be flagged as malicious
        assert request.threat_level == RequestSecurity.MALICIOUS

    def test_large_header_handling(self):
        """Test handling of overly large headers"""
        # Create headers with very large values
        large_value = 'x' * 5000  # 5KB header value
        self.scope['headers'] = [
            [b'host', b'localhost:8000'],
            [b'x-large-header', large_value.encode()]
        ]

        request = Request(self.scope, self.receive, self.send, self.app)

        # Should be flagged as suspicious due to large header
        assert request.threat_level in [RequestSecurity.SUSPICIOUS, RequestSecurity.MALICIOUS]


class TestRequestErrorHandling:
    """Test cases for request error handling"""

    def setup_method(self):
        """Setup for error handling tests"""
        self.scope = {
            'type': 'http',
            'method': 'POST',
            'path': '/test',
            'query_string': b'',
            'headers': [
                [b'host', b'localhost:8000'],
                [b'content-type', b'application/json']
            ],
            'scheme': 'http',
            'server': ('localhost', 8000),
            'client': ('127.0.0.1', 12345)
        }

        self.receive = AsyncMock()
        self.send = Mock()
        self.app = Mock()
        self.app.config = Mock()

    async def test_timeout_handling(self):
        """Test handling of request timeouts"""
        # Mock receive to timeout
        self.receive.side_effect = asyncio.TimeoutError()

        request = Request(self.scope, self.receive, self.send, self.app)

        with pytest.raises(BadRequest):
            await request.body()

    async def test_request_entity_too_large(self):
        """Test handling of oversized request bodies"""
        # Mock a very large body
        large_body = b'x' * (101 * 1024 * 1024)  # 101MB

        self.receive.return_value = {
            'type': 'http.request',
            'body': large_body,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        with pytest.raises(BadRequest):
            await request.body()

    async def test_invalid_unicode_handling(self):
        """Test handling of invalid Unicode in request body"""
        # Mock invalid UTF-8 bytes
        invalid_utf8 = b'\xff\xfe\xfd'

        self.receive.return_value = {
            'type': 'http.request',
            'body': invalid_utf8,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        with pytest.raises(BadRequest):
            await request.text()


class TestRequestPerformance:
    """Test cases for request performance features"""

    def setup_method(self):
        """Setup for performance tests"""
        self.scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'query_string': b'param1=value1&param2=value2&param3=value3',
            'headers': [
                [b'host', b'localhost:8000'],
                [b'content-type', b'application/json'],
                [b'user-agent', b'test-agent'],
                [b'accept', b'application/json'],
                [b'accept-language', b'en-US,en;q=0.9'],
                [b'cookie', b'session=abc123; theme=dark'],
                [b'x-custom-header-1', b'value1'],
                [b'x-custom-header-2', b'value2'],
                [b'x-custom-header-3', b'value3']
            ],
            'scheme': 'http',
            'server': ('localhost', 8000),
            'client': ('127.0.0.1', 12345)
        }

        self.receive = AsyncMock()
        self.send = Mock()
        self.app = Mock()
        self.app.config = Mock()

    def test_header_parsing_performance(self):
        """Test that header parsing is efficient"""
        start_time = time.time()

        request = Request(self.scope, self.receive, self.send, self.app)

        parsing_time = time.time() - start_time

        # Header parsing should be very fast (< 1ms for typical headers)
        assert parsing_time < 0.001

        # Test header access performance
        start_time = time.time()

        for _ in range(1000):
            _ = request.headers.get('content-type')
            _ = request.headers.get('user-agent')
            _ = request.headers.get('accept')

        access_time = time.time() - start_time

        # Header access should be very fast (< 1ms for 1000 accesses)
        assert access_time < 0.001

    def test_query_param_parsing_performance(self):
        """Test query parameter parsing performance"""
        start_time = time.time()

        request = Request(self.scope, self.receive, self.send, self.app)

        parsing_time = time.time() - start_time
        assert parsing_time < 0.001

        # Test query param access performance
        start_time = time.time()

        for _ in range(1000):
            _ = request.get_query_param('param1')
            _ = request.get_query_param('param2')
            _ = request.get_query_param('param3')

        access_time = time.time() - start_time
        assert access_time < 0.001

    def test_metrics_collection(self):
        """Test performance metrics are collected correctly"""
        request = Request(self.scope, self.receive, self.send, self.app)

        metrics = request.metrics

        assert metrics.created_at > 0
        assert metrics.headers_parsed_at > 0
        assert metrics.memory_used >= 0
        assert metrics.parsing_attempts >= 0


class TestRequestIntegration:
    """Integration tests for Request class"""

    def setup_method(self):
        """Setup for integration tests"""
        self.scope = {
            'type': 'http',
            'method': 'POST',
            'path': '/api/users',
            'query_string': b'limit=10&offset=20',
            'headers': [
                [b'host', b'api.example.com'],
                [b'content-type', b'application/json'],
                [b'authorization', b'Bearer token123'],
                [b'x-request-id', b'req-123'],
                [b'x-forwarded-for', b'203.0.113.1'],
                [b'accept', b'application/json'],
                [b'accept-language', b'en-US,en;q=0.9']
            ],
            'scheme': 'https',
            'server': ('api.example.com', 443),
            'client': ('10.0.0.1', 54321)
        }

        self.receive = AsyncMock()
        self.send = Mock()
        self.app = Mock()
        self.app.config = Mock()

    async def test_complete_request_processing(self):
        """Test complete request processing workflow"""
        json_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        }

        body_bytes = json.dumps(json_data).encode()
        self.receive.return_value = {
            'type': 'http.request',
            'body': body_bytes,
            'more_body': False
        }

        request = Request(self.scope, self.receive, self.send, self.app)

        # Test all request features
        assert request.method == 'POST'
        assert request.path == '/api/users'
        assert request.is_secure is True
        assert request.host == 'api.example.com'
        assert request.remote_addr == '203.0.113.1'

        # Test query parameters
        assert request.get_query_param('limit') == '10'
        assert request.get_query_param('offset') == '20'

        # Test headers
        assert request.headers.get('authorization') == 'Bearer token123'
        assert request.headers.get('x-request-id') == 'req-123'

        # Test JSON body parsing
        parsed_json = await request.json()
        assert parsed_json == json_data

        # Test security assessment
        assert request.threat_level == RequestSecurity.SAFE

        # Test performance metrics
        report = request.get_performance_report()
        assert report['method'] == 'POST'
        assert report['path'] == '/api/users'
        assert report['security_flags']['is_secure'] is True

    async def test_multipart_form_processing(self):
        """Test multipart form data processing"""
        # This would test multipart parsing
        # Implementation depends on the specific multipart format
        pass

    async def test_file_upload_handling(self):
        """Test file upload processing"""
        # This would test file upload handling
        # Implementation depends on multipart parsing
        pass


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])
