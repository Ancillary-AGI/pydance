"""
Comprehensive unit tests for the Pydance HTTP Response module.
Tests response creation, header management, compression, streaming, and performance.
"""

import asyncio
import pytest
import json
import gzip
import time
from unittest.mock import Mock, patch
    Response, ResponseMetrics, CompressionOptimizer, ResponseSecurityHeaders,
    CompressionAlgorithm, JSONResponse, HTMLResponse, PlainTextResponse,
    RedirectResponse, FileResponse
)


class TestResponseMetrics:
    """Test cases for ResponseMetrics class"""

    def test_metrics_creation(self):
        """Test metrics creation and initialization"""
        metrics = ResponseMetrics()

        assert metrics.created_at > 0
        assert metrics.compression_started_at == 0.0
        assert metrics.compression_finished_at == 0.0
        assert metrics.content_processed_at == 0.0
        assert metrics.sent_at == 0.0
        assert metrics.original_size == 0
        assert metrics.compressed_size == 0
        assert metrics.compression_ratio == 1.0
        assert metrics.processing_time == 0.0
        assert metrics.background_tasks_count == 0


class TestCompressionOptimizer:
    """Test cases for CompressionOptimizer class"""

    def test_algorithm_selection(self):
        """Test compression algorithm selection"""
        # Test JSON content selection
        algorithm = CompressionOptimizer.select_algorithm(
            'application/json', 2000, 'gzip, deflate, br'
        )
        assert algorithm in [CompressionAlgorithm.GZIP, CompressionAlgorithm.BROTLI]

        # Test text content selection
        algorithm = CompressionOptimizer.select_algorithm(
            'text/html', 1500, 'gzip, deflate'
        )
        assert algorithm == CompressionAlgorithm.GZIP

        # Test small content (no compression)
        algorithm = CompressionOptimizer.select_algorithm(
            'application/json', 100, 'gzip, deflate, br'
        )
        assert algorithm == CompressionAlgorithm.NONE

    def test_gzip_compression(self):
        """Test GZIP compression"""
        test_data = b'Hello, World! This is a test string for compression.'

        compressed = CompressionOptimizer.compress_data(test_data, CompressionAlgorithm.GZIP)
        assert len(compressed) < len(test_data)

        # Verify it's valid gzip
        decompressed = gzip.decompress(compressed)
        assert decompressed == test_data

    def test_no_compression(self):
        """Test no compression algorithm"""
        test_data = b'test data'

        result = CompressionOptimizer.compress_data(test_data, CompressionAlgorithm.NONE)
        assert result == test_data

    def test_compression_fallback(self):
        """Test compression fallback on error"""
        test_data = b'test data'

        # Mock compression to fail
        with patch('gzip.compress', side_effect=Exception("Compression failed")):
            result = CompressionOptimizer.compress_data(test_data, CompressionAlgorithm.GZIP)
            assert result == test_data  # Should return original data


class TestResponseSecurityHeaders:
    """Test cases for ResponseSecurityHeaders class"""

    def test_security_headers_creation(self):
        """Test security headers creation"""
        response = Response.text('test')
        security = ResponseSecurityHeaders(response)

        assert security.response == response

    def test_set_secure_headers(self):
        """Test setting secure headers"""
        response = Response.text('test')
        security = ResponseSecurityHeaders(response)

        security.set_secure_headers()

        assert response.get_header('x-content-type-options') == 'nosniff'
        assert response.get_header('x-frame-options') == 'DENY'
        assert response.get_header('x-xss-protection') == '1; mode=block'
        assert response.get_header('referrer-policy') == 'strict-origin-when-cross-origin'

    def test_set_hsts(self):
        """Test HSTS header setting"""
        response = Response.text('test')
        security = ResponseSecurityHeaders(response)

        security.set_hsts(max_age=31536000, include_subdomains=True)

        hsts_header = response.get_header('strict-transport-security')
        assert 'max-age=31536000' in hsts_header
        assert 'includeSubDomains' in hsts_header

    def test_set_csp(self):
        """Test Content Security Policy setting"""
        response = Response.text('test')
        security = ResponseSecurityHeaders(response)

        security.set_csp("default-src 'self'")

        csp_header = response.get_header('content-security-policy')
        assert csp_header == "default-src 'self'"


class TestResponse:
    """Test cases for Response class"""

    def test_response_creation(self):
        """Test basic response creation"""
        response = Response('Hello', status_code=200)

        assert response.status_code == 200
        assert response.content == 'Hello'
        assert response.media_type == 'text/plain'
        assert response.charset == 'utf-8'

    def test_response_with_headers(self):
        """Test response with custom headers"""
        headers = {'X-Custom': 'value', 'X-Another': 'header'}
        response = Response('test', headers=headers)

        assert response.get_header('x-custom') == 'value'
        assert response.get_header('x-another') == 'header'

    def test_response_json_creation(self):
        """Test JSON response creation"""
        data = {'key': 'value', 'number': 42}
        response = Response.json(data)

        assert response.status_code == 200
        assert response.media_type == 'application/json'
        assert json.loads(response.content) == data

    def test_response_html_creation(self):
        """Test HTML response creation"""
        html_content = '<h1>Hello</h1>'
        response = Response.html(html_content)

        assert response.status_code == 200
        assert response.media_type == 'text/html'
        assert response.content == html_content

    def test_response_text_creation(self):
        """Test text response creation"""
        text_content = 'Hello, World!'
        response = Response.text(text_content)

        assert response.status_code == 200
        assert response.media_type == 'text/plain'
        assert response.content == text_content

    def test_response_redirect_creation(self):
        """Test redirect response creation"""
        redirect_url = 'https://example.com/new-location'
        response = Response.redirect(redirect_url, status_code=301)

        assert response.status_code == 301
        assert response.get_header('location') == redirect_url

    def test_header_operations(self):
        """Test header manipulation operations"""
        response = Response.text('test')

        # Set header
        response.set_header('X-Custom', 'value')
        assert response.get_header('x-custom') == 'value'

        # Delete header
        response.delete_header('x-custom')
        assert response.get_header('x-custom') is None

        # Get with default
        assert response.get_header('missing', 'default') == 'default'

    def test_cookie_operations(self):
        """Test cookie setting and deletion"""
        response = Response.text('test')

        # Set cookie
        response.set_cookie(
            'session', 'abc123',
            max_age=3600,
            path='/',
            secure=True,
            httponly=True,
            samesite='Strict'
        )

        cookie_header = response.get_header('set-cookie')
        assert 'session=abc123' in cookie_header
        assert 'Max-Age=3600' in cookie_header
        assert 'Secure' in cookie_header
        assert 'HttpOnly' in cookie_header
        assert 'SameSite=Strict' in cookie_header

        # Delete cookie
        response.delete_cookie('session')
        delete_cookie_header = response.get_header('set-cookie')
        assert 'Max-Age=0' in delete_cookie_header

    def test_cache_control_headers(self):
        """Test cache control header setting"""
        response = Response.text('test')

        response.set_cache_control('public', max_age=3600)

        cache_header = response.get_header('cache-control')
        assert 'public' in cache_header
        assert 'max-age=3600' in cache_header

    def test_etag_generation(self):
        """Test ETag generation"""
        response = Response.text('test content')

        response.set_etag()

        etag = response.get_header('etag')
        assert etag is not None
        assert etag.startswith('"')
        assert etag.endswith('"')

    def test_cors_headers(self):
        """Test CORS header setting"""
        response = Response.text('test')

        response.enable_cors(
            allow_origins=['https://example.com', 'https://app.example.com'],
            allow_methods=['GET', 'POST'],
            allow_headers=['Content-Type', 'Authorization'],
            allow_credentials=True,
            max_age=86400
        )

        assert response.get_header('access-control-allow-origin') == 'https://example.com, https://app.example.com'
        assert response.get_header('access-control-allow-methods') == 'GET, POST'
        assert response.get_header('access-control-allow-headers') == 'Content-Type, Authorization'
        assert response.get_header('access-control-allow-credentials') == 'true'
        assert response.get_header('access-control-max-age') == '86400'

    def test_content_type_detection(self):
        """Test automatic content type detection"""
        # JSON content
        response = Response({'key': 'value'})
        assert response.media_type == 'application/json'

        # String content (should be text/plain)
        response = Response('plain text')
        assert response.media_type == 'text/plain'

        # HTML content
        response = Response('<html><body>Hello</body></html>')
        assert response.media_type == 'text/html'

    def test_compression_auto_detection(self):
        """Test automatic compression detection"""
        response = Response.text('x' * 2000)  # Large content

        # Should detect optimal compression
        content_bytes = response._get_content_bytes()
        assert len(content_bytes) > 0

    def test_performance_report(self):
        """Test performance report generation"""
        response = Response.text('test')

        report = response.get_performance_report()

        assert 'status_code' in report
        assert 'content_type' in report
        assert 'compression' in report
        assert 'timing' in report
        assert 'performance' in report

        assert report['status_code'] == 200
        assert report['content_type'] == 'text/plain'

    def test_response_repr(self):
        """Test response string representation"""
        response = Response.text('test', status_code=404)

        repr_str = repr(response)
        assert 'Response' in repr_str
        assert '404' in repr_str
        assert 'Not Found' in repr_str


class TestResponseStreaming:
    """Test cases for response streaming"""

    def setup_method(self):
        """Setup for streaming tests"""
        self.response = Response(content=None)  # Enable streaming

    async def test_streaming_initialization(self):
        """Test streaming response initialization"""
        assert self.response._streaming is not None
        assert self.response._stream_ended is False

    async def test_stream_data(self):
        """Test streaming data"""
        test_data = b'Hello, World!'

        await self.response.stream_data(test_data)

        # Check data was queued
        assert not self.response._streaming.empty()

    async def test_end_stream(self):
        """Test ending stream"""
        await self.response.end_stream()

        assert self.response._stream_ended is True

    async def test_stream_generator(self):
        """Test streaming from generator"""
        async def data_generator():
            yield b'chunk1'
            yield b'chunk2'
            yield b'chunk3'

        await self.response.stream_generator(data_generator())

        # Check all chunks were queued
        assert not self.response._streaming.empty()

    async def test_streaming_errors(self):
        """Test streaming error handling"""
        # End stream first
        await self.response.end_stream()

        # Should raise error when trying to stream to ended stream
        with pytest.raises(ValueError):
            await self.response.stream_data(b'test')


class TestResponseASGI:
    """Test cases for ASGI response handling"""

    def setup_method(self):
        """Setup for ASGI tests"""
        self.response = Response.text('Hello, World!')

    async def test_asgi_response_start(self):
        """Test ASGI response start message"""
        scope = {'type': 'http'}
        receive = Mock()
        send = AsyncMock()

        await self.response(scope, receive, send)

        # Check response start was sent
        send.assert_any_call({
            'type': 'http.response.start',
            'status': 200,
            'headers': pytest.any(list)
        })

    async def test_asgi_response_body(self):
        """Test ASGI response body message"""
        scope = {'type': 'http'}
        receive = Mock()
        send = AsyncMock()

        await self.response(scope, receive, send)

        # Check response body was sent
        send.assert_any_call({
            'type': 'http.response.body',
            'body': pytest.any(bytes),
            'more_body': False
        })

    async def test_asgi_with_headers(self):
        """Test ASGI response with custom headers"""
        response = Response.text('test', headers={'X-Custom': 'value'})
        scope = {'type': 'http'}
        receive = Mock()
        send = AsyncMock()

        await response(scope, receive, send)

        # Check headers were sent
        call_args = send.call_args_list
        start_message = None
        for call in call_args:
            if call[0][0]['type'] == 'http.response.start':
                start_message = call[0][0]
                break

        assert start_message is not None
        headers = dict(start_message['headers'])
        assert b'x-custom' in headers
        assert headers[b'x-custom'] == b'value'

    async def test_background_tasks(self):
        """Test background task execution"""
        executed_tasks = []

        def background_task():
            executed_tasks.append('task1')

        async def async_background_task():
            executed_tasks.append('task2')

        response = Response.text('test', background_tasks=[background_task, async_background_task])
        scope = {'type': 'http'}
        receive = Mock()
        send = AsyncMock()

        await response(scope, receive, send)

        # Give tasks time to execute
        await asyncio.sleep(0.1)

        # Check tasks were executed
        assert 'task1' in executed_tasks
        assert 'task2' in executed_tasks


class TestResponseCompression:
    """Test cases for response compression"""

    def test_compression_algorithm_selection(self):
        """Test compression algorithm selection"""
        response = Response.text('x' * 2000)  # Large text content

        # Test with different accept-encoding headers
        accept_gzip = 'gzip, deflate'
        accept_brotli = 'br, gzip'
        no_compression = 'identity'

        # Should select appropriate algorithm
        algorithm = response._detect_compression_algorithm(accept_gzip)
        assert algorithm in [CompressionAlgorithm.GZIP, CompressionAlgorithm.DEFLATE]

    def test_compression_application(self):
        """Test compression is applied correctly"""
        large_content = 'x' * 2000
        response = Response.text(large_content, compression='gzip')

        content_bytes = response._get_content_bytes()

        # Should be compressed
        assert len(content_bytes) < len(large_content.encode())

        # Should have compression header
        assert response.get_header('content-encoding') == 'gzip'

    def test_no_compression_for_small_content(self):
        """Test no compression for small content"""
        small_content = 'small'
        response = Response.text(small_content, compression='auto')

        content_bytes = response._get_content_bytes()

        # Should not be compressed
        assert len(content_bytes) == len(small_content.encode())
        assert response.get_header('content-encoding') is None

    def test_compression_metrics(self):
        """Test compression metrics collection"""
        content = 'x' * 2000
        response = Response.text(content, compression='gzip')

        # Access content to trigger compression
        content_bytes = response._get_content_bytes()

        # Check metrics
        report = response.get_performance_report()
        compression_info = report['compression']

        assert compression_info['algorithm'] == 'gzip'
        assert compression_info['original_size'] > 0
        assert compression_info['compressed_size'] > 0
        assert compression_info['ratio'] > 1.0


class TestResponseFileHandling:
    """Test cases for file response handling"""

    def test_file_response_creation(self):
        """Test file response creation"""
        # This would test file response creation
        # Implementation depends on file system access
        pass

    def test_file_content_disposition(self):
        """Test file content disposition headers"""
        # This would test file download headers
        pass


class TestResponseErrorHandling:
    """Test cases for response error handling"""

    def test_invalid_status_code(self):
        """Test invalid status code handling"""
        # This would test invalid status codes
        pass

    def test_invalid_header_values(self):
        """Test invalid header value handling"""
        response = Response.text('test')

        # Test with invalid header values
        with pytest.raises((TypeError, ValueError)):
            response.set_header('invalid', 123)  # Headers must be strings

    def test_compression_error_handling(self):
        """Test compression error handling"""
        response = Response.text('test')

        # Mock compression to fail
        with patch.object(CompressionOptimizer, 'compress_data', side_effect=Exception("Compression failed")):
            content_bytes = response._get_content_bytes()
            # Should return original content on compression failure
            assert content_bytes == b'test'


class TestResponsePerformance:
    """Test cases for response performance"""

    def test_header_operations_performance(self):
        """Test header operations performance"""
        response = Response.text('test')

        # Add many headers
        for i in range(100):
            response.set_header(f'x-header-{i}', f'value-{i}')

        # Test header access performance
        start_time = time.time()

        for i in range(1000):
            _ = response.get_header(f'x-header-{i % 100}')

        access_time = time.time() - start_time

        # Should be fast (< 1ms for 1000 operations)
        assert access_time < 0.001

    def test_content_processing_performance(self):
        """Test content processing performance"""
        large_content = 'x' * 10000  # 10KB content
        response = Response.text(large_content)

        start_time = time.time()
        content_bytes = response._get_content_bytes()
        processing_time = time.time() - start_time

        # Should be fast (< 10ms for 10KB)
        assert processing_time < 0.01
        assert len(content_bytes) == len(large_content.encode())

    def test_compression_performance(self):
        """Test compression performance"""
        large_content = 'x' * 50000  # 50KB content
        response = Response.text(large_content, compression='gzip')

        start_time = time.time()
        content_bytes = response._get_content_bytes()
        compression_time = time.time() - start_time

        # Compression should be reasonably fast (< 100ms for 50KB)
        assert compression_time < 0.1
        assert len(content_bytes) < len(large_content.encode())


class TestResponseIntegration:
    """Integration tests for Response class"""

    async def test_complete_response_lifecycle(self):
        """Test complete response lifecycle"""
        # Create response with various features
        response = Response.json(
            {'message': 'test', 'data': [1, 2, 3]},
            status_code=201,
            headers={'X-Custom': 'value'}
        )

        # Add security headers
        response.security.set_secure_headers()

        # Add cache control
        response.set_cache_control('public', max_age=3600)

        # Add ETag
        response.set_etag()

        # Test response properties
        assert response.status_code == 201
        assert response.media_type == 'application/json'
        assert response.get_header('x-custom') == 'value'
        assert response.get_header('x-content-type-options') == 'nosniff'
        assert response.get_header('cache-control') is not None
        assert response.get_header('etag') is not None

        # Test ASGI interface
        scope = {'type': 'http'}
        receive = Mock()
        send = AsyncMock()

        await response(scope, receive, send)

        # Verify ASGI calls
        assert send.call_count >= 2  # Start and body messages

    async def test_streaming_response_lifecycle(self):
        """Test complete streaming response lifecycle"""
        response = Response(content=None)  # Enable streaming

        # Stream some data
        await response.stream_data(b'chunk1')
        await response.stream_data(b'chunk2')

        # Test ASGI interface
        scope = {'type': 'http'}
        receive = Mock()
        send = AsyncMock()

        await response(scope, receive, send)

        # Verify streaming was handled
        assert send.call_count >= 2

    def test_response_with_all_features(self):
        """Test response with all features enabled"""
        response = Response(
            content={'test': 'data'},
            status_code=200,
            headers={'X-Custom': 'value'},
            media_type='application/json',
            compression='gzip',
            auto_compress=True,
            enable_security_headers=True
        )

        # Test all features are properly configured
        assert response.status_code == 200
        assert response.media_type == 'application/json'
        assert response.get_header('x-custom') == 'value'
        assert response.get_header('x-content-type-options') == 'nosniff'


class TestResponseLegacyCompatibility:
    """Test legacy response function compatibility"""

    def test_json_response_legacy(self):
        """Test legacy JSONResponse function"""
        data = {'key': 'value'}
        response = JSONResponse(data)

        assert response.status_code == 200
        assert response.media_type == 'application/json'
        assert json.loads(response.content) == data

    def test_html_response_legacy(self):
        """Test legacy HTMLResponse function"""
        html = '<h1>Test</h1>'
        response = HTMLResponse(html)

        assert response.status_code == 200
        assert response.media_type == 'text/html'
        assert response.content == html

    def test_text_response_legacy(self):
        """Test legacy PlainTextResponse function"""
        text = 'Hello, World!'
        response = PlainTextResponse(text)

        assert response.status_code == 200
        assert response.media_type == 'text/plain'
        assert response.content == text

    def test_redirect_response_legacy(self):
        """Test legacy RedirectResponse function"""
        url = 'https://example.com'
        response = RedirectResponse(url, status_code=301)

        assert response.status_code == 301
        assert response.get_header('location') == url


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])
