"""
Custom Assertions for Pydance Testing

Provides specialized assertions for testing Pydance applications.
"""

from pydance.testing.client import TestResponse


def assert_response_status(response: TestResponse, expected_status: int):
    """Assert that response has expected status code."""
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}"
    )


def assert_response_json(response: TestResponse, expected_data=None):
    """Assert that response contains valid JSON."""
    try:
        data = response.json()
        if expected_data is not None:
            assert data == expected_data, f"Expected {expected_data}, got {data}"
    except ValueError as e:
        raise AssertionError(f"Response is not valid JSON: {e}")


def assert_response_contains(response: TestResponse, key: str, value=None):
    """Assert that response JSON contains a key with optional value."""
    try:
        data = response.json()
        assert key in data, f"Key '{key}' not found in response"
        if value is not None:
            assert data[key] == value, f"Expected {value} for key '{key}', got {data[key]}"
    except ValueError as e:
        raise AssertionError(f"Response is not valid JSON: {e}")


def assert_response_success(response: TestResponse):
    """Assert that response indicates success (2xx status)."""
    assert 200 <= response.status_code < 300, (
        f"Expected success status (2xx), got {response.status_code}"
    )


def assert_response_error(response: TestResponse, expected_status=None):
    """Assert that response indicates error (4xx or 5xx status)."""
    assert response.status_code >= 400, (
        f"Expected error status (4xx/5xx), got {response.status_code}"
    )
    if expected_status is not None:
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}"
        )


def assert_response_headers(response: TestResponse, expected_headers: dict):
    """Assert that response contains expected headers."""
    for header_name, expected_value in expected_headers.items():
        header_name_lower = header_name.lower()
        actual_value = response.headers.get(header_name_lower)
        assert actual_value is not None, f"Header '{header_name}' not found"
        assert actual_value == expected_value, (
            f"Expected header '{header_name}' to be '{expected_value}', got '{actual_value}'"
        )


def assert_response_content_type(response: TestResponse, expected_type: str):
    """Assert that response has expected content type."""
    content_type = response.headers.get('content-type', '')
    assert expected_type in content_type, (
        f"Expected content-type to contain '{expected_type}', got '{content_type}'"
    )


def assert_response_redirect(response: TestResponse, expected_location=None):
    """Assert that response is a redirect (3xx status)."""
    assert 300 <= response.status_code < 400, (
        f"Expected redirect status (3xx), got {response.status_code}"
    )
    if expected_location is not None:
        location = response.headers.get('location')
        assert location == expected_location, (
            f"Expected redirect to '{expected_location}', got '{location}'"
        )


__all__ = [
    'assert_response_status',
    'assert_response_json',
    'assert_response_contains',
    'assert_response_success',
    'assert_response_error',
    'assert_response_headers',
    'assert_response_content_type',
    'assert_response_redirect',
]
