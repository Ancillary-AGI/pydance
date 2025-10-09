"""
Shared test fixtures for both frontend and backend testing.

This module provides reusable fixtures that can be used across
all test files to ensure consistency and reduce duplication.
"""

import asyncio
import pytest
import tempfile
import os
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock

from .test_utils import TestDataFactory, MockDataGenerator, test_config


# ==================== BACKEND FIXTURES ====================

@pytest.fixture
def test_settings():
    """Test settings fixture"""
    from pydance.settings import Settings

    class TestSettings(Settings):
        DEBUG = True
        SECRET_KEY = "test-secret-key-for-testing-only"
        DATABASES = {
            'default': {
                'ENGINE': 'pydance.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
        TEMPLATES = []
        CACHES = {
            'default': {
                'BACKEND': 'pydance.caching.backends.locmem.LocMemCache',
            }
        }

    return TestSettings()


@pytest.fixture
def test_app(test_settings):
    """Test application fixture"""
    from pydance import Application

    app = Application(test_settings)

    # Add common middleware
    from pydance.middleware.base import LoggingMiddleware, CORSMiddleware

    app.middleware_manager.add(LoggingMiddleware())
    app.middleware_manager.add(CORSMiddleware())

    yield app

    # Cleanup
    if hasattr(app, 'shutdown'):
        asyncio.run(app.shutdown())


@pytest.fixture
def test_database():
    """Test database fixture"""
    from pydance.db.config import DatabaseConfig
    from pydance.db.connections.sqlite_connection import SQLiteConnection

    config = DatabaseConfig.from_url(test_config.test_database_url)
    db = SQLiteConnection(config)

    asyncio.run(db.connect())

    yield db

    # Cleanup
    asyncio.run(db.disconnect())


@pytest.fixture
async def test_models():
    """Test models fixture"""
    from pydance.db.models.base import BaseModel, Field

    class TestUser(BaseModel):
        username = Field(type='VARCHAR', max_length=150, unique=True)
        email = Field(type='VARCHAR', max_length=255, unique=True)
        password = Field(type='VARCHAR', max_length=128)
        is_active = Field(type='BOOLEAN', default=True)

        class Meta:
            table_name = 'test_users'

    class TestProduct(BaseModel):
        name = Field(type='VARCHAR', max_length=255)
        price = Field(type='DECIMAL', precision=10, scale=2)
        category = Field(type='VARCHAR', max_length=100)
        in_stock = Field(type='BOOLEAN', default=True)

        class Meta:
            table_name = 'test_products'

    # Create tables
    await TestUser.create_table(if_not_exists=True)
    await TestProduct.create_table(if_not_exists=True)

    yield TestUser, TestProduct

    # Cleanup
    await TestUser.objects.all().delete()
    await TestProduct.objects.all().delete()


@pytest.fixture
def test_user_data():
    """Test user data fixture"""
    return TestDataFactory.create_user_data()


@pytest.fixture
def test_product_data():
    """Test product data fixture"""
    return TestDataFactory.create_product_data()


@pytest.fixture
def mock_request():
    """Mock HTTP request fixture"""
    return TestDataFactory.create_http_request()


@pytest.fixture
def sample_users():
    """Sample users data fixture"""
    return MockDataGenerator.generate_users(5)


@pytest.fixture
def sample_products():
    """Sample products data fixture"""
    return MockDataGenerator.generate_products(5)


# ==================== FRONTEND FIXTURES ====================

@pytest.fixture
def jsdom_setup():
    """JSDOM setup for frontend testing"""
    # Note: JSDOM would need to be installed for this to work
    # For now, we'll create a mock DOM environment

    class MockWindow:
        def __init__(self):
            self.document = MockDocument()
            self.navigator = MockNavigator()

    class MockDocument:
        def __init__(self):
            self.body = MockElement()

        def createElement(self, tag):
            return MockElement()

    class MockElement:
        def __init__(self):
            self.id = None
            self.parentNode = None

        def appendChild(self, child):
            pass

    class MockNavigator:
        def __init__(self):
            self.userAgent = "Mock Browser"

    # Create mock DOM
    window = MockWindow()
    document = window.document
    navigator = window.navigator

    yield {
        'window': window,
        'document': document,
        'navigator': navigator
    }

    # Cleanup
    pass


@pytest.fixture
def test_container(jsdom_setup):
    """Test DOM container fixture"""
    container = document.createElement('div')
    container.id = 'test-container'
    document.body.appendChild(container)

    yield container

    # Cleanup
    if container.parentNode:
        container.parentNode.removeChild(container)


@pytest.fixture
def mock_component():
    """Mock component fixture"""
    # This would be implemented based on your component system
    def create_mock_component(name='MockComponent'):
        return {
            'name': name,
            'render': Mock(return_value=f'<div>{name}</div>'),
            'mount': Mock(),
            'unmount': Mock(),
            'update': Mock()
        }

    return create_mock_component


@pytest.fixture
def mock_signal():
    """Mock signal fixture"""
    class MockSignal:
        def __init__(self, initial_value=None):
            self.value = initial_value
            self.subscribers = []

        def subscribe(self, callback):
            self.subscribers.append(callback)
            return lambda: self.subscribers.remove(callback)

        def set_value(self, new_value):
            self.value = new_value
            for subscriber in self.subscribers:
                subscriber(new_value)

    return MockSignal


# ==================== PERFORMANCE FIXTURES ====================

@pytest.fixture
def performance_config():
    """Performance test configuration"""
    return {
        'max_response_time': 1.0,  # seconds
        'max_memory_usage': 100 * 1024 * 1024,  # 100MB
        'min_throughput': 100,  # requests per second
        'timeout': 30.0  # seconds
    }


@pytest.fixture
def load_test_data():
    """Load test data fixture"""
    return {
        'users': MockDataGenerator.generate_users(100),
        'products': MockDataGenerator.generate_products(50),
        'requests': MockDataGenerator.generate_http_requests(200)
    }


# ==================== INTEGRATION FIXTURES ====================

@pytest.fixture
async def integration_app(test_app, test_database):
    """Full integration test application"""
    # Set up database
    test_app.db = test_database

    # Add test routes
    from pydance.http.response import Response

    async def health_check(request):
        return Response.json({'status': 'healthy'})

    async def api_info(request):
        return Response.json({
            'framework': 'pydance',
            'version': '1.0.0',
            'database': 'connected'
        })

    test_app.router.add_route('/health', health_check, methods=['GET'])
    test_app.router.add_route('/api/info', api_info, methods=['GET'])

    yield test_app


@pytest.fixture
async def test_client(integration_app):
    """Test HTTP client fixture"""
    from httpx import AsyncClient

    async with AsyncClient(app=integration_app, base_url="http://testserver") as client:
        yield client


# ==================== MOCK FIXTURES ====================

@pytest.fixture
def mock_cache():
    """Mock cache fixture"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.clear = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_logger():
    """Mock logger fixture"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_event_bus():
    """Mock event bus fixture"""
    event_bus = Mock()
    event_bus.emit = AsyncMock()
    event_bus.on = Mock(return_value=Mock())  # Return unsubscribe function
    event_bus.off = Mock()
    return event_bus


# ==================== TEMPORARY FILE FIXTURES ====================

@pytest.fixture
def temp_file():
    """Temporary file fixture"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write('test content')
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_directory():
    """Temporary directory fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# ==================== ASYNC FIXTURES ====================

@pytest.fixture
async def async_fixture():
    """Example async fixture"""
    # Setup
    data = await async_setup_function()
    yield data
    # Cleanup
    await async_cleanup_function(data)


async def async_setup_function():
    """Async setup function"""
    await asyncio.sleep(0.1)  # Simulate async work
    return {'status': 'ready'}


async def async_cleanup_function(data):
    """Async cleanup function"""
    await asyncio.sleep(0.1)  # Simulate async cleanup
    pass


# ==================== FRONTEND-SPECIFIC FIXTURES ====================

@pytest.fixture
def react_hooks():
    """React-style hooks for testing"""
    hooks = {
        'useState': Mock(side_effect=lambda initial: [initial, Mock()]),
        'useEffect': Mock(side_effect=lambda effect, deps: Mock()),
        'useMemo': Mock(side_effect=lambda factory, deps: factory()),
        'useCallback': Mock(side_effect=lambda callback, deps: callback),
        'useRef': Mock(side_effect=lambda initial: Mock(current=initial)),
        'useContext': Mock(side_effect=lambda context: context._current_value)
    }
    return hooks


@pytest.fixture
def component_lifecycle():
    """Component lifecycle fixture"""
    lifecycle = {
        'onMount': Mock(),
        'onUpdate': Mock(),
        'onUnmount': Mock(),
        'onError': Mock()
    }
    return lifecycle


# ==================== DATABASE FIXTURES ====================

@pytest.fixture
async def test_db_session(test_database):
    """Database session fixture"""
    # Start transaction
    transaction = await test_database.begin_transaction()

    yield transaction

    # Rollback transaction
    await transaction.rollback()


@pytest.fixture
def db_models():
    """Database models fixture"""
    # This would contain your actual model classes
    return {
        'User': None,  # Replace with actual model
        'Product': None,  # Replace with actual model
        'Order': None  # Replace with actual model
    }


# ==================== CONFIGURATION FIXTURES ====================

@pytest.fixture
def test_env():
    """Test environment variables"""
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ['TEST_MODE'] = 'true'
    os.environ['DEBUG'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ==================== UTILITY FIXTURES ====================

@pytest.fixture
def benchmark_timer():
    """Benchmark timer fixture"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time.time()

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0

    return Timer


@pytest.fixture
def memory_monitor():
    """Memory usage monitor fixture"""
    import psutil
    import os

    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.start_memory = None

        def __enter__(self):
            self.start_memory = self.process.memory_info().rss
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            end_memory = self.process.memory_info().rss
            self.memory_used = end_memory - self.start_memory

        @property
        def memory_mb(self):
            return self.memory_used / (1024 * 1024) if self.memory_used else 0

    return MemoryMonitor


# ==================== EXPORT ALL FIXTURES ====================

__all__ = [
    # Backend fixtures
    'test_settings',
    'test_app',
    'test_database',
    'test_models',
    'test_user_data',
    'test_product_data',
    'mock_request',
    'sample_users',
    'sample_products',

    # Frontend fixtures
    'jsdom_setup',
    'test_container',
    'mock_component',
    'mock_signal',

    # Performance fixtures
    'performance_config',
    'load_test_data',

    # Integration fixtures
    'integration_app',
    'test_client',

    # Mock fixtures
    'mock_cache',
    'mock_logger',
    'mock_event_bus',

    # Utility fixtures
    'temp_file',
    'temp_directory',
    'async_fixture',
    'react_hooks',
    'component_lifecycle',
    'test_db_session',
    'db_models',
    'test_env',
    'benchmark_timer',
    'memory_monitor'
]
