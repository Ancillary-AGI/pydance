"""
Testing utilities for Pydance applications.

Provides helper functions and utilities for common testing patterns.
"""

import time
from typing import Dict, Any, Optional, List, Callable

from pydance.auth.core import create_user, auth_manager


def create_test_user(username: str = None, email: str = None, password: str = None,
                    roles: List[str] = None) -> Dict[str, Any]:
    """
    Create a test user with default values.

    Args:
        username: Username for the test user
        email: Email for the test user
        password: Password for the test user
        roles: Roles to assign to the user

    Returns:
        Dictionary representing the created user
    """
    username = username or f"testuser_{datetime.now().timestamp()}"
    email = email or f"{username}@test.com"
    password = password or "testpass123"

    user = create_user(username, email, password)

    if roles:
        user['roles'] = roles

    return user


def create_test_data(model_class: Any, count: int = 1, **kwargs) -> List[Any]:
    """
    Create test data for a model.

    Args:
        model_class: The model class to create instances of
        count: Number of instances to create
        **kwargs: Field values to set on the instances

    Returns:
        List of created model instances
    """
    instances = []

    for i in range(count):
        # Create instance data with provided kwargs and defaults
        instance_data = {}

        # Add index to make each instance unique
        for key, value in kwargs.items():
            if isinstance(value, str) and '{}' in value:
                instance_data[key] = value.format(i)
            else:
                instance_data[key] = value

        # Create instance (this would depend on the model implementation)
        # For now, return a mock instance
        instance = {
            'id': i + 1,
            'created_at': datetime.now(),
            **instance_data
        }

        instances.append(instance)

    return instances


def assert_response_ok(response: TestResponse, status_code: int = None) -> None:
    """
    Assert that response indicates success.

    Args:
        response: The response to check
        status_code: Expected status code (optional)
    """
    if status_code:
        assert response.status_code == status_code, f"Expected status {status_code}, got {response.status_code}"
    else:
        assert response.status_code < 400, f"Expected success status, got {response.status_code}"


def assert_response_error(response: TestResponse, expected_status: int = None) -> None:
    """
    Assert that response indicates error.

    Args:
        response: The response to check
        expected_status: Expected error status code (optional)
    """
    if expected_status:
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"
    else:
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"


def assert_contains(text: str, container: str) -> None:
    """
    Assert that text contains a substring.

    Args:
        text: The substring to look for
        container: The text to search in
    """
    assert text in container, f"'{text}' not found in '{container}'"


def assert_not_contains(text: str, container: str) -> None:
    """
    Assert that text does not contain a substring.

    Args:
        text: The substring that should not be present
        container: The text to search in
    """
    assert text not in container, f"'{text}' found in '{container}'"


def assert_json_equal(expected: Dict[str, Any], actual: TestResponse) -> None:
    """
    Assert that response JSON matches expected dictionary.

    Args:
        expected: Expected JSON data
        actual: Response object
    """
    actual_json = actual.json()
    assert actual_json == expected, f"JSON mismatch. Expected: {expected}, Got: {actual_json}"


def assert_json_contains(expected: Dict[str, Any], actual: TestResponse) -> None:
    """
    Assert that response JSON contains expected key-value pairs.

    Args:
        expected: Expected key-value pairs that should be present
        actual: Response object
    """
    actual_json = actual.json()

    for key, value in expected.items():
        assert key in actual_json, f"Key '{key}' not found in response JSON"
        assert actual_json[key] == value, f"Value mismatch for key '{key}'. Expected: {value}, Got: {actual_json[key]}"


def assert_has_header(response: TestResponse, header_name: str, expected_value: str = None) -> None:
    """
    Assert that response has a specific header.

    Args:
        response: Response object
        header_name: Name of the header to check
        expected_value: Expected header value (optional)
    """
    assert header_name in response.headers, f"Header '{header_name}' not found in response"

    if expected_value:
        actual_value = response.headers[header_name]
        assert actual_value == expected_value, f"Header '{header_name}' value mismatch. Expected: {expected_value}, Got: {actual_value}"


def wait_for_condition(condition_func: Callable, timeout: float = 5.0, interval: float = 0.1) -> bool:
    """
    Wait for a condition to be true.

    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds

    Returns:
        True if condition was met, False if timeout occurred
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)

    return False


def create_test_token(user_id: int, secret_key: str = None) -> str:
    """
    Create a test JWT token.

    Args:
        user_id: User ID to include in token
        secret_key: Secret key for signing (optional)

    Returns:
        JWT token string
    """
    try:
        import jwt
        from datetime import datetime, timedelta

        secret_key = secret_key or "test-secret-key"
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }

        return jwt.encode(payload, secret_key, algorithm='HS256')

    except ImportError:
        # Return a mock token if PyJWT is not available
        return f"mock_token_{user_id}"


def create_mock_request(method: str = 'GET', path: str = '/', user: Dict[str, Any] = None,
                       headers: Dict[str, str] = None) -> Any:
    """
    Create a mock request object for testing.

    Args:
        method: HTTP method
        path: Request path
        user: User object to attach to request
        headers: Request headers

    Returns:
        Mock request object
    """
    class MockRequest:
        def __init__(self):
            self.method = method
            self.path = path
            self.user = user
            self.headers = headers or {}
            self.query_params = {}
            self.form_data = {}
            self.cookies = {}

    return MockRequest()


def create_mock_response(status_code: int = 200, body: str = None,
                        headers: Dict[str, str] = None) -> Any:
    """
    Create a mock response object for testing.

    Args:
        status_code: HTTP status code
        body: Response body
        headers: Response headers

    Returns:
        Mock response object
    """
    class MockResponse:
        def __init__(self):
            self.status_code = status_code
            self.body = body or ""
            self.headers = headers or {}

    return MockResponse()


def generate_test_data(count: int = 10, **field_templates) -> List[Dict[str, Any]]:
    """
    Generate test data with templates.

    Args:
        count: Number of records to generate
        **field_templates: Field templates with placeholders

    Returns:
        List of generated test data records

    Example:
        data = generate_test_data(
            5,
            name="User {0}",
            email="user{0}@test.com",
            age=25
        )
    """
    records = []

    for i in range(count):
        record = {}

        for field_name, template in field_templates.items():
            if isinstance(template, str) and '{' in template:
                record[field_name] = template.format(i)
            else:
                record[field_name] = template

        # Add default fields
        record['id'] = i + 1
        record['created_at'] = datetime.now()

        records.append(record)

    return records


def benchmark_function(func: Callable, iterations: int = 100, *args, **kwargs) -> Dict[str, float]:
    """
    Benchmark a function's performance.

    Args:
        func: Function to benchmark
        iterations: Number of iterations to run
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function

    Returns:
        Dictionary with timing statistics
    """
    times = []

    for _ in range(iterations):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        times.append(end_time - start_time)

    return {
        'total_time': sum(times),
        'average_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times),
        'iterations': iterations
    }


class PerformanceTester:
    """Performance testing utilities"""

    @staticmethod
    def time_function(func, *args, **kwargs):
        """Time a function execution"""
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return end - start, result

    @staticmethod
    async def time_async_function(func, *args, **kwargs):
        """Time an async function execution"""
        import time
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        return end - start, result

    @staticmethod
    def benchmark_function(func, iterations=100, *args, **kwargs):
        """Benchmark a function"""
        import time
        times = []
        for _ in range(iterations):
            start = time.time()
            func(*args, **kwargs)
            end = time.time()
            times.append(end - start)

        return {
            'total': sum(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'iterations': iterations
        }


class MockDataGenerator:
    """Mock data generation utilities"""

    @staticmethod
    def create_user_data(count=10):
        """Create mock user data"""
        users = []
        for i in range(count):
            users.append({
                'id': i + 1,
                'username': f'user_{i}',
                'email': f'user_{i}@example.com',
                'created_at': datetime.now()
            })
        return users

    @staticmethod
    def create_product_data(count=10):
        """Create mock product data"""
        products = []
        for i in range(count):
            products.append({
                'id': i + 1,
                'name': f'Product {i}',
                'price': 10.99 + i,
                'category': 'test'
            })
        return products


# Test configuration
test_config = {
    'debug': True,
    'database_url': 'sqlite:///:memory:',
    'cache_backend': 'memory'
}

# Performance configuration
performance_config = {
    'max_response_time': 0.1,
    'max_memory_usage': 50 * 1024 * 1024,  # 50MB
    'min_throughput': 100  # requests per second
}

# Load test data
load_test_data = {
    'users': MockDataGenerator.create_user_data(1000),
    'products': MockDataGenerator.create_product_data(500)
}

# Benchmark timer
benchmark_timer = PerformanceTester

# Memory monitor
class MemoryMonitor:
    """Memory monitoring utilities"""

    def __init__(self):
        self.start_memory = 0
        self.end_memory = 0

    def __enter__(self):
        import psutil
        import os
        self.start_memory = psutil.Process(os.getpid()).memory_info().rss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import psutil
        import os
        self.end_memory = psutil.Process(os.getpid()).memory_info().rss

    @property
    def memory_mb(self):
        """Get memory usage in MB"""
        return (self.end_memory - self.start_memory) / (1024 * 1024)

memory_monitor = MemoryMonitor

__all__ = [
    'create_test_user',
    'create_test_data',
    'assert_response_ok',
    'assert_response_error',
    'assert_contains',
    'assert_not_contains',
    'assert_json_equal',
    'assert_json_contains',
    'assert_has_header',
    'wait_for_condition',
    'create_test_token',
    'create_mock_request',
    'create_mock_response',
    'generate_test_data',
    'benchmark_function',
    'PerformanceTester',
    'MockDataGenerator',
    'test_config',
    'performance_config',
    'load_test_data',
    'benchmark_timer',
    'memory_monitor'
]
