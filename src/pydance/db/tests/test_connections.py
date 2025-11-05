"""
Unit tests for database connections
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from pydance.db.config import DatabaseConfig
from pydance.db.connections.base import DatabaseConnection, ConnectionState, ConnectionStats


class TestDatabaseConnection:
    """Test DatabaseConnection functionality"""

    def test_connection_stats(self):
        """Test connection statistics"""
        stats = ConnectionStats()
        assert stats.total_connections_created == 0
        assert stats.current_active_connections == 0
        assert stats.current_idle_connections == 0

    def test_connection_state_enum(self):
        """Test connection state enumeration"""
        assert ConnectionState.IDLE.value == "idle"
        assert ConnectionState.ACTIVE.value == "active"
        assert ConnectionState.BROKEN.value == "broken"
        assert ConnectionState.CLOSED.value == "closed"

    def test_database_config_creation(self):
        """Test database configuration creation"""
        config = DatabaseConfig(
            engine='sqlite',
            name='test.db',
            host='localhost',
            port=5432,
            user='test',
            password='password'
        )

        assert config.engine == 'sqlite'
        assert config.name == 'test.db'
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.user == 'test'
        assert config.password == 'password'

    def test_database_config_from_url(self):
        """Test database configuration from URL"""
        config = DatabaseConfig.from_url('sqlite:///test.db')
        assert config.engine == 'sqlite'
        assert config.name == 'test.db'

        config = DatabaseConfig.from_url('postgresql://user:pass@localhost:5432/testdb')
        assert config.engine == 'postgresql'
        assert config.user == 'user'
        assert config.password == 'pass'
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.name == 'testdb'

    def test_database_config_defaults(self):
        """Test database configuration defaults"""
        config = DatabaseConfig()
        assert config.engine == 'sqlite'
        assert config.name == 'db.sqlite3'
        assert config.host == 'localhost'
        assert config.port == 0  # Default port for SQLite
        assert config.pool_size == 10
