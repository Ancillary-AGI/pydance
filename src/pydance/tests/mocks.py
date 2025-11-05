"""
Mock objects for testing.

Provides mock implementations of common Pydance components for testing.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from unittest.mock import Mock, MagicMock


class MockRequest:
    """
    Mock HTTP request for testing.

    Provides a realistic request object that can be used in place
    of actual HTTP requests during testing.
    """

    def __init__(self,
                 method: str = 'GET',
                 path: str = '/',
                 headers: Dict[str, str] = None,
                 query_params: Dict[str, str] = None,
                 form_data: Dict[str, Any] = None,
                 body: str = None,
                 user: Dict[str, Any] = None,
                 cookies: Dict[str, str] = None):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.form_data = form_data or {}
        self.body = body or ''
        self.user = user
        self.cookies = cookies or {}

        # Additional attributes that might be expected
        self.args = {}
        self.kwargs = {}
        self.remote_addr = '127.0.0.1'
        self.client_ip = '127.0.0.1'

    def get_header(self, name: str, default: str = None) -> str:
        """Get header value"""
        return self.headers.get(name, default)

    def get_query_param(self, name: str, default: str = None) -> str:
        """Get query parameter value"""
        return self.query_params.get(name, default)

    def get_form_data(self, name: str, default: Any = None) -> Any:
        """Get form data value"""
        return self.form_data.get(name, default)

    def is_authenticated(self) -> bool:
        """Check if request has authenticated user"""
        return self.user is not None


class MockResponse:
    """
    Mock HTTP response for testing.

    Provides a realistic response object that can be used to test
    response handling and middleware.
    """

    def __init__(self,
                 status_code: int = 200,
                 headers: Dict[str, str] = None,
                 body: str = '',
                 json_data: Dict[str, Any] = None):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body
        self._json_data = json_data

    def set_header(self, name: str, value: str):
        """Set response header"""
        self.headers[name] = value

    def set_cookie(self, name: str, value: str, **kwargs):
        """Set response cookie"""
        self.headers[f'Set-Cookie'] = f'{name}={value}'

    def get_json(self) -> Dict[str, Any]:
        """Get response as JSON"""
        if self._json_data:
            return self._json_data
        elif self.body:
            try:
                return json.loads(self.body)
            except json.JSONDecodeError:
                return {}
        else:
            return {}

    def get_text(self) -> str:
        """Get response as text"""
        return self.body


class MockDatabase:
    """
    Mock database for testing.

    Provides an in-memory database implementation for testing
    database operations without requiring an actual database.
    """

    def __init__(self):
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
        self.indexes: Dict[str, Dict[str, List]] = {}

    def create_table(self, table_name: str, columns: List[str] = None):
        """Create a mock table"""
        self.tables[table_name] = []
        if columns:
            # Create indexes for columns
            for column in columns:
                self.indexes[f"{table_name}_{column}"] = []

    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert data into table"""
        if table_name not in self.tables:
            self.tables[table_name] = []

        # Add ID if not present
        if 'id' not in data:
            data['id'] = len(self.tables[table_name]) + 1

        self.tables[table_name].append(data.copy())
        return data['id']

    def select(self, table_name: str, conditions: Dict[str, Any] = None,
               limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Select data from table"""
        if table_name not in self.tables:
            return []

        results = self.tables[table_name]

        # Apply conditions
        if conditions:
            filtered_results = []
            for row in results:
                match = True
                for key, value in conditions.items():
                    if row.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_results.append(row)
            results = filtered_results

        # Apply pagination
        if offset > 0:
            results = results[offset:]

        if limit:
            results = results[:limit]

        return results

    def update(self, table_name: str, data: Dict[str, Any],
               conditions: Dict[str, Any]) -> int:
        """Update data in table"""
        if table_name not in self.tables:
            return 0

        updated_count = 0
        for row in self.tables[table_name]:
            match = True
            for key, value in conditions.items():
                if row.get(key) != value:
                    match = False
                    break

            if match:
                row.update(data)
                updated_count += 1

        return updated_count

    def delete(self, table_name: str, conditions: Dict[str, Any] = None) -> int:
        """Delete data from table"""
        if table_name not in self.tables:
            return 0

        if not conditions:
            # Delete all rows
            deleted_count = len(self.tables[table_name])
            self.tables[table_name] = []
            return deleted_count

        # Delete matching rows
        new_table = []
        deleted_count = 0

        for row in self.tables[table_name]:
            match = True
            for key, value in conditions.items():
                if row.get(key) != value:
                    match = False
                    break

            if match:
                deleted_count += 1
            else:
                new_table.append(row)

        self.tables[table_name] = new_table
        return deleted_count

    def count(self, table_name: str, conditions: Dict[str, Any] = None) -> int:
        """Count rows in table"""
        results = self.select(table_name, conditions)
        return len(results)

    def clear_table(self, table_name: str):
        """Clear all data from table"""
        if table_name in self.tables:
            self.tables[table_name] = []


class MockCache:
    """
    Mock cache for testing.

    Provides an in-memory cache implementation for testing
    caching functionality.
    """

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.expirations: Dict[str, datetime] = {}

    def get(self, key: str) -> Any:
        """Get value from cache"""
        # Check expiration
        if key in self.expirations:
            if datetime.now() > self.expirations[key]:
                del self.data[key]
                del self.expirations[key]
                return None

        return self.data.get(key)

    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        self.data[key] = value

        if ttl:
            self.expirations[key] = datetime.now() + timedelta(seconds=ttl)

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self.data:
            del self.data[key]
            if key in self.expirations:
                del self.expirations[key]
            return True
        return False

    def clear(self):
        """Clear all cache data"""
        self.data.clear()
        self.expirations.clear()

    def has_key(self, key: str) -> bool:
        """Check if key exists in cache"""
        return self.get(key) is not None


class MockAuth:
    """
    Mock authentication for testing.

    Provides mock authentication functionality for testing
    protected routes and user management.
    """

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, str] = {}  # session_id -> username
        self.current_user: Optional[Dict[str, Any]] = None

    def create_user(self, username: str, password: str, **kwargs) -> Dict[str, Any]:
        """Create a mock user"""
        user = {
            'id': len(self.users) + 1,
            'username': username,
            'password': password,
            'is_active': True,
            'roles': ['user'],
            **kwargs
        }

        self.users[username] = user
        return user

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user"""
        user = self.users.get(username)
        if user and user['password'] == password and user['is_active']:
            self.current_user = user
            return True
        return False

    def login(self, username: str) -> str:
        """Login user and return session ID"""
        user = self.users.get(username)
        if user and user['is_active']:
            session_id = f"session_{username}_{datetime.now().timestamp()}"
            self.sessions[session_id] = username
            self.current_user = user
            return session_id
        return None

    def logout(self, session_id: str = None):
        """Logout user"""
        if session_id and session_id in self.sessions:
            del self.sessions[session_id]
        self.current_user = None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        return self.current_user

    def require_auth(self, func: callable):
        """Decorator to require authentication"""
        def wrapper(*args, **kwargs):
            if not self.current_user:
                raise Exception("Authentication required")
            return func(*args, **kwargs)
        return wrapper


# Global mock instances
mock_db = MockDatabase()
mock_cache = MockCache()
mock_auth = MockAuth()


__all__ = [
    'MockRequest',
    'MockResponse',
    'MockDatabase',
    'MockCache',
    'MockAuth',
    'mock_db',
    'mock_cache',
    'mock_auth'
]
