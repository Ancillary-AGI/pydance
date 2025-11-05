"""
Base test case classes for Pydance applications.

Provides comprehensive testing utilities including database setup, user creation,
and common testing patterns.
"""

import asyncio
import unittest
import json
from typing import Dict, Any, Optional, List, Type
from datetime import datetime

from pydance.config.settings import settings
from pydance.db.connections import DatabaseConnection
from pydance.db.config import DatabaseConfig
from pydance.auth.core import create_user, auth_manager
from pydance.exceptions import BaseFrameworkException


class TestCase(unittest.TestCase):
    """
    Base test case for Pydance applications.

    Provides common testing utilities and setup/teardown methods.
    """

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.test_data = {}
        self.test_user = None

    def tearDown(self):
        """Clean up after test"""
        super().tearDown()
        # Clean up any test data
        if hasattr(self, 'test_data'):
            self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Clean up test data (override in subclasses)"""
        pass

    def create_test_user(self, username: str = None, email: str = None, password: str = None) -> Dict[str, Any]:
        """Create a test user"""
        username = username or f"testuser_{datetime.now().timestamp()}"
        email = email or f"{username}@test.com"
        password = password or "testpass123"

        user = create_user(username, email, password)
        self.test_data['users'] = self.test_data.get('users', [])
        self.test_data['users'].append(user)

        return user

    def create_test_data(self, model_class, **kwargs) -> Any:
        """Create test data for a model"""
        # This would create test instances of models
        # Implementation depends on the specific model structure
        pass

    def assert_response_ok(self, response) -> None:
        """Assert that response indicates success"""
        if hasattr(response, 'status_code'):
            self.assertIn(response.status_code, [200, 201, 202])
        elif hasattr(response, 'status'):
            self.assertIn(response.status, [200, 201, 202])

    def assert_response_error(self, response, expected_status: int = None) -> None:
        """Assert that response indicates error"""
        if expected_status:
            if hasattr(response, 'status_code'):
                self.assertEqual(response.status_code, expected_status)
            elif hasattr(response, 'status'):
                self.assertEqual(response.status, expected_status)
        else:
            if hasattr(response, 'status_code'):
                self.assertGreaterEqual(response.status_code, 400)
            elif hasattr(response, 'status'):
                self.assertGreaterEqual(response.status, 400)

    def assert_contains(self, text: str, container: str) -> None:
        """Assert that text contains a substring"""
        self.assertIn(text, container)

    def assert_not_contains(self, text: str, container: str) -> None:
        """Assert that text does not contain a substring"""
        self.assertNotIn(text, container)

    def assert_json_equal(self, expected: Dict[str, Any], actual: str) -> None:
        """Assert that JSON string matches expected dictionary"""
        actual_dict = json.loads(actual)
        self.assertEqual(expected, actual_dict)

    def assert_raises_framework_exception(self, exception_class: Type[BaseFrameworkException],
                                         callable_obj=None, *args, **kwargs):
        """Assert that a framework exception is raised"""
        return self.assertRaises(exception_class, callable_obj, *args, **kwargs)


class DatabaseTestCase(TestCase):
    """
    Test case with database support.

    Provides database setup, teardown, and utilities for database testing.
    """

    def setUp(self):
        """Set up database test environment"""
        super().setUp()

        # Create test database configuration
        self.test_db_config = DatabaseConfig(
            engine='sqlite',
            name=':memory:',  # In-memory database for testing
            host='',
            port=0,
            user='',
            password=''
        )

        # Initialize database connection
        self.db_connection = DatabaseConnection.get_instance(self.test_db_config)

    def tearDown(self):
        """Clean up database test environment"""
        super().tearDown()

        # Close database connections
        if self.db_connection:
            asyncio.run(self.db_connection.disconnect())

    async def setup_test_database(self):
        """Set up test database schema"""
        # Create test tables
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)

    async def cleanup_test_database(self):
        """Clean up test database"""
        # Drop test tables
        await self.db_connection.execute("DROP TABLE IF EXISTS test_users")

    def create_test_database_user(self, username: str = None, email: str = None) -> Dict[str, Any]:
        """Create a test user in the database"""
        username = username or f"db_testuser_{datetime.now().timestamp()}"
        email = email or f"{username}@dbtest.com"

        user = {
            'username': username,
            'email': email,
            'created_at': datetime.now()
        }

        # Insert into database
        asyncio.run(self._insert_test_user(user))

        self.test_data['db_users'] = self.test_data.get('db_users', [])
        self.test_data['db_users'].append(user)

        return user

    async def _insert_test_user(self, user: Dict[str, Any]):
        """Insert test user into database"""
        await self.db_connection.execute("""
            INSERT INTO test_users (username, email, created_at)
            VALUES (?, ?, ?)
        """, (user['username'], user['email'], user['created_at']))

    async def get_test_database_users(self) -> List[Dict[str, Any]]:
        """Get all test users from database"""
        result = await self.db_connection.fetch_all("SELECT * FROM test_users")
        return result


class AsyncTestCase(unittest.IsolatedAsyncioTestCase):
    """
    Base async test case for Pydance applications.

    Provides async testing utilities and setup/teardown methods.
    """

    def setUp(self):
        """Set up async test environment"""
        super().setUp()
        self.test_data = {}
        self.test_user = None

    def tearDown(self):
        """Clean up after async test"""
        super().tearDown()

    async def asyncSetUp(self):
        """Async setup method"""
        await super().asyncSetUp()
        # Additional async setup can be added here

    async def asyncTearDown(self):
        """Async cleanup method"""
        await super().asyncTearDown()
        # Additional async cleanup can be added here

    def create_test_user(self, username: str = None, email: str = None, password: str = None) -> Dict[str, Any]:
        """Create a test user for async tests"""
        username = username or f"async_testuser_{datetime.now().timestamp()}"
        email = email or f"{username}@asynctest.com"
        password = password or "async_testpass123"

        user = create_user(username, email, password)
        self.test_data['users'] = self.test_data.get('users', [])
        self.test_data['users'].append(user)

        return user

    async def wait_for_condition(self, condition_func: callable, timeout: float = 5.0) -> bool:
        """Wait for a condition to be true"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(0.1)
        return False


class APITestCase(TestCase):
    """
    Test case for API testing.

    Provides utilities for testing API endpoints, authentication, and responses.
    """

    def setUp(self):
        """Set up API test environment"""
        super().setUp()
        self.api_client = None  # Would be initialized with actual test client

    def authenticate_test_user(self, username: str = None, password: str = None) -> Dict[str, Any]:
        """Authenticate a test user for API testing"""
        user = self.create_test_user(username, password=password)
        # In a real implementation, this would return authentication tokens
        return {
            'user': user,
            'access_token': f"test_token_{user['id']}",
            'refresh_token': f"refresh_token_{user['id']}"
        }

    def make_authenticated_request(self, method: str, url: str, token: str = None, **kwargs) -> Any:
        """Make an authenticated API request"""
        if token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f'Bearer {token}'
            kwargs['headers'] = headers

        # This would make actual HTTP requests in a real implementation
        # For now, return a mock response
        return {"status": "mock_response", "authenticated": True}


__all__ = [
    'TestCase',
    'DatabaseTestCase',
    'AsyncTestCase',
    'APITestCase'
]
