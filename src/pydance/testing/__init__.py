"""
Universal Testing Framework

A comprehensive, framework-agnostic testing framework that can be used
with any Python web framework, providing pytest-like functionality and
advanced mocking capabilities.

This framework is designed to be completely detached from any specific
framework structure, making it reusable across different projects.

Example:
    from universal_testing import TestClient, mock, patch

    def test_my_app():
        with patch('my_module.some_function') as mock_func:
            mock_func.return_value = 'mocked'
            app = MyWebApp()
            client = TestClient(app)
            response = await client.get('/')
            assert response.status_code == 200
"""

# Core testing utilities
from pydance.testing.client import TestClient, TestResponse

# Mocking framework
from pydance.testing.mock import mock, Mock, MagicMock, patch, patch_object, patch_dict, patch_multiple

# Assertions and test utilities
    assert_response_status,
    assert_response_json,
    assert_response_success,
    assert_response_error,
    assert_response_contains
)

# Test fixtures and factories
    create_user,
    create_post,
    create_app,
    database_session
)

__all__ = [
    # HTTP Testing
    'TestClient',
    'TestResponse',

    # Assertions
    'assert_response_status',
    'assert_response_json',
    'assert_response_success',
    'assert_response_error',
    'assert_response_contains',

    # Mocking
    'mock',
    'Mock',
    'MagicMock',
    'patch',
    'patch_object',
    'patch_dict',
    'patch_multiple',

    # Fixtures
    'create_user',
    'create_post',
    'create_app',
    'database_session',
]
