"""
Test fixtures for Pydance testing framework.
"""

import pytest
from pydance import Application
from pydance.config.settings import Settings


@pytest.fixture
def test_settings():
    """Create test settings for testing"""
    settings = Settings()
    settings.DEBUG = True
    settings.SECRET_KEY = "test-secret-key-for-testing-only"
    # Comment out DATABASE_URL to avoid auto db setup in tests
    # settings.DATABASE_URL = 'sqlite:///:memory:'
    settings.DATABASES = {
        'default': {
            'ENGINE': 'pydance.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    settings.CACHES = {
        'default': {
            'BACKEND': 'pydance.caching.backends.locmem.LocMemCache',
        }
    }
    return settings


@pytest.fixture
def test_app():
    """Create test application instance"""
    from pydance.server.application import Application
    app = Application()
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client for application"""
    from pydance.testing.test_client import TestClient
    return TestClient(test_app)


@pytest.fixture
def db_session():
    """Create test database session"""
    # This would set up a test database session
    # For now, return a mock
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def authenticated_user():
    """Create authenticated user for testing"""
    from pydance.db.models.user import BaseUser
    user = BaseUser(
        username="testuser",
        email="test@example.com",
        is_active=True
    )
    return user


@pytest.fixture
def test_database():
    """Create test database for testing"""
    from unittest.mock import Mock
    db = Mock()
    db.connect.return_value = None
    db.disconnect.return_value = None
    db.session = Mock()
    db.engine = Mock()
    return db


__all__ = [
    'test_settings', 'test_app', 'test_client', 'test_database', 'db_session', 'authenticated_user'
]
