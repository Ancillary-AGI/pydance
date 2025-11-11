"""
Pydance HTTP Response Handler.

This module provides HTTP response handling with support for:
- ASGI response lifecycle management
- Content type detection
- Streaming and chunking
- Background task execution
- HTTP status code management
- Header manipulation
- Multi-algorithm compression (gzip, brotli, lz4)
- Caching headers and ETags
- Performance monitoring
"""

import asyncio
import inspect
import json
import hashlib
import gzip
import zlib
import time
import threading
from typing import Any, Dict, List, Callable, Optional, Union, AsyncGenerator, Tuple
from datetime import datetime, timedelta
from email.utils import format_datetime
import mimetypes
from dataclasses import dataclass, field
from enum import Enum
import brotli
import lz4.frame


class CompressionAlgorithm(Enum):
    """Available compression algorithms."""
    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "brotli"
    LZ4 = "lz4"
    NONE = "none"


@dataclass
class ResponseMetrics:
    """Performance metrics for response processing."""
    created_at: float = field(default_factory=time.time)
    compression_started_at: float = 0.0
    compression_finished_at: float = 0.0
    content_processed_at: float = 0.0
    sent_at: float = 0.0
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 1.0
    processing_time: float = 0.0
    background_tasks_count: int = 0


class CompressionOptimizer:
    """Ultra-efficient compression algorithm selector."""

    @staticmethod
    def select_algorithm(content_type: str, content_size: int, accept_encoding: str) -> CompressionAlgorithm:
        """Select optimal compression algorithm based on content characteristics."""
        # Parse client accept-encoding preferences
        accepted = set()
        for encoding in accept_encoding.split(','):
            encoding = encoding.strip().lower()
            if encoding in ('gzip', 'x-gzip'):
                accepted.add(CompressionAlgorithm.GZIP)
            elif encoding in ('deflate', 'x-deflate'):
                accepted.add(CompressionAlgorithm.DEFLATE)
            elif encoding in ('br', 'brotli'):
                accepted.add(CompressionAlgorithm.BROTLI)
            elif encoding == 'lz4':
                accepted.add(CompressionAlgorithm.LZ4)

        if not accepted:
            return CompressionAlgorithm.NONE

        # Algorithm selection based on content type and size
        if content_type.startswith('text/') or content_type in ['application/json', 'application/javascript', 'application/xml']:
            # Text-like content compresses well
            if content_size > 1400:  # > 1.4KB
                if CompressionAlgorithm.BROTLI in accepted:
                    return CompressionAlgorithm.BROTLI  # Best compression ratio
                elif content_size > 860:  # > 860 bytes
                    return CompressionAlgorithm.GZIP   # Good balance
                elif CompressionAlgorithm.LZ4 in accepted:
                    return CompressionAlgorithm.LZ4    # Fast decompression

        # For smaller content or other types, prefer speed over ratio
        if CompressionAlgorithm.LZ4 in accepted and content_size > 100:
            return CompressionAlgorithm.LZ4
        elif CompressionAlgorithm.GZIP in accepted:
            return CompressionAlgorithm.GZIP

        return CompressionAlgorithm.NONE

    @staticmethod
    def compress_data(data: bytes, algorithm: CompressionAlgorithm, level: int = -1) -> bytes:
        """Ultra-fast compression with algorithm-specific optimizations."""
        if algorithm == CompressionAlgorithm.NONE:
            return data

        try:
            if algorithm == CompressionAlgorithm.GZIP:
                return gzip.compress(data, compresslevel=level)
            elif algorithm == CompressionAlgorithm.DEFLATE:
                return zlib.compress(data, level=level)
            elif algorithm == CompressionAlgorithm.BROTLI:
                return brotli.compress(data, quality=level if level != -1 else 6)
            elif algorithm == CompressionAlgorithm.LZ4:
                return lz4.frame.compress(data, compression_level=level if level != -1 else 1)
            else:
                return data
        except Exception:
            # Fallback to original data if compression fails
            return data


class ResponseSecurityHeaders:
    """Comprehensive security headers for world-class security."""

    def __init__(self, response: 'Response'):
        self.response = response

    def set_secure_headers(self):
        """Apply all recommended security headers."""
        # Content Security Policy
        self.response.set_header("x-content-type-options", "nosniff")
        self.response.set_header("x-frame-options", "DENY")
        self.response.set_header("x-xss-protection", "1; mode=block")
        self.response.set_header("referrer-policy", "strict-origin-when-cross-origin")
        self.response.set_header("permissions-policy", "geolocation=(), microphone=(), camera=()")

        # HTTPS-only headers
        if self.response.status_code >= 300 and self.response.status_code < 400:
            self.response.set_header("strict-transport-security", "max-age=31536000; includeSubDomains")

    def set_hsts(self, max_age: int = 31536000, include_subdomains: bool = True):
        """Set HTTP Strict Transport Security."""
        value = f"max-age={max_age}"
        if include_subdomains:
            value += "; includeSubDomains"
        self.response.set_header("strict-transport-security", value)

    def set_csp(self, policy: str = "default-src 'self'"):
        """Set Content Security Policy."""
        self.response.set_header("content-security-policy", policy)


class Response:
    """
    Enhanced HTTP Response class with comprehensive ASGI support.

    Features:
    - ASGI response lifecycle management
    - Automatic content type detection
    - Response streaming and chunking
    - Background task execution
    - HTTP status code management
    - Header manipulation and validation
    - Content encoding and compression
    - Caching headers and ETags
    - Security headers
    """

    # Common HTTP status codes
    STATUS_CODES = {
        100: "Continue",
        101: "Switching Protocols",
        102: "Processing",
        200: "OK",
        201: "Created",
        202: "Accepted",
        203: "Non-Authoritative Information",
        204: "No Content",
        205: "Reset Content",
        206: "Partial Content",
        207: "Multi-Status",
        208: "Already Reported",
        226: "IM Used",
        300: "Multiple Choices",
        301: "Moved Permanently",
        302: "Found",
        303: "See Other",
        304: "Not Modified",
        305: "Use Proxy",
        307: "Temporary Redirect",
        308: "Permanent Redirect",
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request Timeout",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Payload Too Large",
        414: "URI Too Long",
        415: "Unsupported Media Type",
        416: "Range Not Satisfiable",
        417: "Expectation Failed",
        418: "I'm a teapot",
        421: "Misdirected Request",
        422: "Unprocessable Entity",
        423: "Locked",
        424: "Failed Dependency",
        425: "Too Early",
        426: "Upgrade Required",
        428: "Precondition Required",
        429: "Too Many Requests",
        431: "Request Header Fields Too Large",
        451: "Unavailable For Legal Reasons",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        505: "HTTP Version Not Supported",
        506: "Variant Also Negotiates",
        507: "Insufficient Storage",
        508: "Loop Detected",
        510: "Not Extended",
        511: "Network Authentication Required",
    }

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        charset: str = "utf-8",
        background_tasks: Optional[List[Callable]] = None,
        compression: Optional[str] = None,
        auto_compress: bool = True,
        enable_security_headers: bool = True
    ):
        # Performance timing
        self._created_at = time.time()
        self._metrics = ResponseMetrics(
            created_at=self._created_at,
            background_tasks_count=len(background_tasks or [])
        )

        self.status_code = status_code
        self.headers = headers or {}
        self.background_tasks = background_tasks or []
        self.content = content
        self.charset = charset
        self.compression = compression if compression else "auto" if auto_compress else None

        # Advanced streaming with memory pooling
        self._streaming = asyncio.Queue() if content is None else None
        self._stream_ended = False
        self._streaming_pool = asyncio.Queue(maxsize=1000)  # Memory-efficient streaming pool

        # Enhanced content type detection using MIME magic
        self.media_type = self._detect_advanced_media_type(content, media_type)

        # Advanced content processing with compression optimization
        self._processed_content: Optional[bytes] = None
        self._etag: Optional[str] = None
        self._compression_algorithm: Optional[CompressionAlgorithm] = None

        # Security headers system
        self.security = ResponseSecurityHeaders(self)
        self._enable_security_headers = enable_security_headers

        # Set optimized default headers
        self._set_optimized_headers()

    def _detect_advanced_media_type(self, content: Any, media_type: Optional[str]) -> str:
        """Advanced content type detection using MIME magic and content analysis."""
        if media_type:
            return media_type

        if isinstance(content, (dict, list)):
            return "application/json"
        elif isinstance(content, str):
            # Advanced HTML detection
            content_lower = content.lower().strip()
            if (content_lower.startswith("<html") or
                content_lower.startswith("<!doctype html") or
                "<html" in content_lower or
                "<!doctype" in content_lower):
                return "text/html"
            else:
                return "text/plain"
        elif isinstance(content, bytes):
            # MIME magic for binary content
            if len(content) > 0:
                # Simple MIME detection for common formats
                if content.startswith(b'\x89PNG'):
                    return "image/png"
                elif content.startswith(b'\xff\xd8'):
                    return "image/jpeg"
                elif content.startswith(b'GIF8'):
                    return "image/gif"
                elif content.startswith(b'%PDF'):
                    return "application/pdf"
                elif content.startswith(b'PK\x03\x04'):
                    return "application/zip"
            return "application/octet-stream"
        else:
            return "text/plain"

    def _set_optimized_headers(self) -> None:
        """Set optimized response headers with security and performance considerations."""
        # Content-Type header with advanced charset detection
        if "content-type" not in self.headers:
            content_type = self.media_type
            if self.charset and "charset" not in content_type and "text/" in content_type:
                content_type += f"; charset={self.charset}"
            self.headers["content-type"] = content_type

        # Optimized server header
        if "server" not in self.headers:
            self.headers["server"] = "Pydance/1.0"

        # High-precision date header
        if "date" not in self.headers:
            self.headers["date"] = format_datetime(datetime.utcnow())

        # Security headers
        if self._enable_security_headers:
            if "x-content-type-options" not in self.headers:
                self.headers["x-content-type-options"] = "nosniff"

    def _detect_compression_algorithm(self, accept_encoding: str) -> CompressionAlgorithm:
        """Detect optimal compression algorithm based on client capabilities."""
        if self.compression == "auto":
            content_bytes = self._get_content_bytes_uncompressed()
            self._metrics.original_size = len(content_bytes)
            return CompressionOptimizer.select_algorithm(
                self.media_type,
                self._metrics.original_size,
                accept_encoding
            )

        # Manual compression selection
        try:
            return CompressionAlgorithm(self.compression)
        except ValueError:
            return CompressionAlgorithm.NONE

    def _get_content_bytes_uncompressed(self) -> bytes:
        """Get uncompressed content bytes."""
        if self.content is None:
            return b""

        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode(self.charset)
        elif isinstance(self.content, (dict, list)):
            return json.dumps(self.content, ensure_ascii=False).encode(self.charset)
        else:
            return str(self.content).encode(self.charset)

    def _apply_optimal_compression(self) -> bytes:
        """Apply optimal compression with performance metrics."""
        if not self.compression:
            return self._get_content_bytes_uncompressed()

        self._metrics.compression_started_at = time.time()

        # Detect algorithm if auto-compression
        if self.compression == "auto":
            # Use default accept-encoding for server-side compression
            accept_encoding = "gzip, deflate, br"
            self._compression_algorithm = self._detect_compression_algorithm(accept_encoding)
        else:
            try:
                self._compression_algorithm = CompressionAlgorithm(self.compression)
            except ValueError:
                self._compression_algorithm = CompressionAlgorithm.NONE

        content = self._get_content_bytes_uncompressed()

        if self._compression_algorithm == CompressionAlgorithm.NONE:
            return content

        compressed = CompressionOptimizer.compress_data(content, self._compression_algorithm)

        # Update compression metrics
        self._metrics.compressed_size = len(compressed)
        original_size = self._metrics.original_size or len(content)
        self._metrics.compression_ratio = original_size / max(len(compressed), 1)
        self._metrics.compression_finished_at = time.time()

        # Set compression headers
        algorithm_name = self._compression_algorithm.value
        if algorithm_name != "none":
            self.set_header("content-encoding", algorithm_name)
            self.set_header("vary", "accept-encoding")

        return compressed

    def _set_default_headers(self) -> None:
        """Set default response headers."""
        # Content-Type header
        if "content-type" not in self.headers:
            content_type = self.media_type
            if self.charset and "charset" not in content_type:
                content_type += f"; charset={self.charset}"
            self.headers["content-type"] = content_type

        # Server header
        if "server" not in self.headers:
            self.headers["server"] = "Pydance "

        # Date header
        if "date" not in self.headers:
            self.headers["date"] = format_datetime(datetime.utcnow())

        # Security headers
        if "x-content-type-options" not in self.headers:
            self.headers["x-content-type-options"] = "nosniff"

    def set_header(self, name: str, value: str) -> None:
        """Set a response header."""
        self.headers[name.lower()] = value

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a response header."""
        return self.headers.get(name.lower(), default)

    def delete_header(self, name: str) -> None:
        """Delete a response header."""
        self.headers.pop(name.lower(), None)

    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[datetime] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None
    ) -> None:
        """Set a response cookie."""
        cookie_parts = [f"{name}={value}"]

        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        if expires is not None:
            cookie_parts.append(f"Expires={format_datetime(expires)}")
        if path:
            cookie_parts.append(f"Path={path}")
        if domain:
            cookie_parts.append(f"Domain={domain}")
        if secure:
            cookie_parts.append("Secure")
        if httponly:
            cookie_parts.append("HttpOnly")
        if samesite:
            cookie_parts.append(f"SameSite={samesite}")

        cookie_value = "; ".join(cookie_parts)
        self.set_header("set-cookie", cookie_value)

    def delete_cookie(self, name: str, path: str = "/", domain: Optional[str] = None) -> None:
        """Delete a response cookie."""
        cookie_parts = [f"{name}=; Max-Age=0"]

        if path:
            cookie_parts.append(f"Path={path}")
        if domain:
            cookie_parts.append(f"Domain={domain}")

        cookie_value = "; ".join(cookie_parts)
        self.set_header("set-cookie", cookie_value)

    def set_cache_control(self, directive: str, max_age: Optional[int] = None) -> None:
        """Set Cache-Control header."""
        cache_control = directive
        if max_age is not None:
            cache_control += f", max-age={max_age}"
        self.set_header("cache-control", cache_control)

    def set_etag(self, etag: Optional[str] = None) -> None:
        """Set ETag header."""
        if etag is None:
            if self._etag is None:
                content = self._get_content_bytes()
                self._etag = f'"{hashlib.md5(content).hexdigest()}"'
            etag = self._etag
        self.set_header("etag", etag)

    def set_last_modified(self, dt: datetime) -> None:
        """Set Last-Modified header."""
        self.set_header("last-modified", format_datetime(dt))

    def set_expires(self, dt: datetime) -> None:
        """Set Expires header."""
        self.set_header("expires", format_datetime(dt))

    def enable_cors(
        self,
        allow_origins: Union[str, List[str]] = "*",
        allow_methods: Union[str, List[str]] = "*",
        allow_headers: Union[str, List[str]] = "*",
        allow_credentials: bool = False,
        max_age: int = 86400
    ) -> None:
        """Enable CORS for the response."""
        if isinstance(allow_origins, list):
            allow_origins = ", ".join(allow_origins)
        if isinstance(allow_methods, list):
            allow_methods = ", ".join(allow_methods)
        if isinstance(allow_headers, list):
            allow_headers = ", ".join(allow_headers)

        self.set_header("access-control-allow-origin", str(allow_origins))
        self.set_header("access-control-allow-methods", str(allow_methods))
        self.set_header("access-control-allow-headers", str(allow_headers))
        if allow_credentials:
            self.set_header("access-control-allow-credentials", "true")
        self.set_header("access-control-max-age", str(max_age))

    async def stream_data(self, data: bytes) -> None:
        """Stream data to the response."""
        if self._streaming is None:
            raise ValueError("Response is not configured for streaming")
        if self._stream_ended:
            raise ValueError("Stream has already ended")

        await self._streaming.put(data)

    async def end_stream(self) -> None:
        """End the response stream."""
        if self._streaming is not None and not self._stream_ended:
            await self._streaming.put(None)
            self._stream_ended = True

    async def stream_generator(self, generator: AsyncGenerator[bytes, None]) -> None:
        """Stream data from an async generator."""
        if self._streaming is None:
            raise ValueError("Response is not configured for streaming")

        try:
            async for chunk in generator:
                await self.stream_data(chunk)
        finally:
            await self.end_stream()

    def _get_content_bytes(self) -> bytes:
        """Get the response content as bytes with advanced compression."""
        if self._processed_content is not None:
            return self._processed_content

        if self.content is None:
            return b""

        # Process content with performance metrics
        self._metrics.content_processed_at = time.time()
        content = self._apply_optimal_compression()

        self._processed_content = content
        return content

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate detailed performance report for monitoring."""
        # Calculate final metrics
        self._metrics.sent_at = time.time()
        self._metrics.processing_time = self._metrics.sent_at - self._created_at

        compression_time = 0.0
        if self._metrics.compression_finished_at > 0:
            compression_time = self._metrics.compression_finished_at - self._metrics.compression_started_at

        return {
            "status_code": self.status_code,
            "content_type": self.media_type,
            "compression": {
                "algorithm": self._compression_algorithm.value if self._compression_algorithm else "none",
                "original_size": self._metrics.original_size,
                "compressed_size": self._metrics.compressed_size,
                "ratio": round(self._metrics.compression_ratio, 2),
                "compression_time": round(compression_time, 4),
            },
            "timing": {
                "created_at": self._metrics.created_at,
                "content_processed_at": self._metrics.content_processed_at,
                "sent_at": self._metrics.sent_at,
                "total_processing_time": round(self._metrics.processing_time, 4),
            },
            "performance": {
                "background_tasks_count": self._metrics.background_tasks_count,
                "streaming_enabled": self._streaming is not None,
                "security_headers_enabled": self._enable_security_headers,
            }
        }

    async def __call__(self, scope: Dict[str, Any], receive: callable, send: callable) -> None:
        """ASGI response callable."""
        # Prepare headers
        headers = [
            [key.encode(), value.encode()]
            for key, value in self.headers.items()
        ]

        # Add content-length if we have content
        if self.content is not None and "content-length" not in self.headers:
            content_bytes = self._get_content_bytes()
            headers.append([b"content-length", str(len(content_bytes)).encode()])

        # Send response start
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": headers,
        })

        # Handle streaming response
        if self._streaming is not None:
            while True:
                try:
                    data = await asyncio.wait_for(self._streaming.get(), timeout=30.0)
                    if data is None:
                        break
                    await send({
                        "type": "http.response.body",
                        "body": data,
                        "more_body": True,
                    })
                except asyncio.TimeoutError:
                    # End stream on timeout
                    break

            await send({
                "type": "http.response.body",
                "body": b"",
                "more_body": False,
            })

        # Handle regular response
        elif self.content is not None:
            content_bytes = self._get_content_bytes()
            await send({
                "type": "http.response.body",
                "body": content_bytes,
                "more_body": False,
            })

        # Execute background tasks
        for task in self.background_tasks:
            if inspect.iscoroutinefunction(task):
                asyncio.create_task(task())
            else:
                # Run sync tasks in thread pool
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, task)

    @classmethod
    def json(
        cls,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> 'Response':
        """Create a JSON response."""
        return cls(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="application/json",
            **kwargs
        )

    @classmethod
    def html(
        cls,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> 'Response':
        """Create an HTML response."""
        return cls(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/html",
            **kwargs
        )

    @classmethod
    def text(
        cls,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> 'Response':
        """Create a plain text response."""
        return cls(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/plain",
            **kwargs
        )

    @classmethod
    def redirect(
        cls,
        url: str,
        status_code: int = 302,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> 'Response':
        """Create a redirect response."""
        headers = headers or {}
        headers["location"] = url
        return cls(
            content="",
            status_code=status_code,
            headers=headers,
            **kwargs
        )

    @classmethod
    def file(
        cls,
        path: str,
        filename: Optional[str] = None,
        media_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> 'Response':
        """Create a file response."""
        import os
        import mimetypes

        if not os.path.exists(path):
            return cls(status_code=404, content="File not found")

        if filename is None:
            filename = os.path.basename(path)

        if media_type is None:
            media_type, _ = mimetypes.guess_type(filename)

        headers = headers or {}
        headers["content-disposition"] = f'attachment; filename="{filename}"'

        with open(path, 'rb') as f:
            content = f.read()

        return cls(
            content=content,
            headers=headers,
            media_type=media_type or "application/octet-stream",
            **kwargs
        )

    def __repr__(self) -> str:
        return f"<Response {self.status_code} {self.STATUS_CODES.get(self.status_code, 'Unknown')}>"


# Convenience functions for common responses
def JSONResponse(content: Any, status_code: int = 200, **kwargs) -> Response:
    """Create a JSON response (legacy compatibility)."""
    return Response.json(content, status_code, **kwargs)

def HTMLResponse(content: str, status_code: int = 200, **kwargs) -> Response:
    """Create an HTML response (legacy compatibility)."""
    return Response.html(content, status_code, **kwargs)

def PlainTextResponse(content: str, status_code: int = 200, **kwargs) -> Response:
    """Create a plain text response (legacy compatibility)."""
    return Response.text(content, status_code, **kwargs)

def RedirectResponse(url: str, status_code: int = 302, **kwargs) -> Response:
    """Create a redirect response (legacy compatibility)."""
    return Response.redirect(url, status_code, **kwargs)

def FileResponse(path: str, **kwargs) -> Response:
    """Create a file response (legacy compatibility)."""
    return Response.file(path, **kwargs)
