"""
Database connections module for Pydance Framework (new pydance.db namespace).

This file is a copy/adaptation of the previous `pydance.db.connections`
implementation but imports the configuration from `pydance.db.config` so the
new `pydance.db` package is self-contained.
"""

import asyncio
import logging
import time
from typing import Any, Dict, AsyncGenerator, Optional, List
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from pydance.db.config import DatabaseConfig
from .base_connection import (
    DatabaseConnection,
    ConnectionState,
    ConnectionStats,
    ManagedConnection,
    DatabaseBackend,
    DatabaseUtils,
    COMMON_FIELD_TYPE_MAPPINGS
)

# Import concrete implementations - all backends are required for full functionality
from .sqlite_connection import SQLiteConnection
from .postgres_connection import PostgreSQLConnection
from .mysql_connection import MySQLConnection
from .mongodb_connection import MongoDBConnection


@dataclass
class PoolConfig:
    """Configuration for database connection pool"""
    min_size: int = 5
    max_size: int = 20
    max_idle_time: int = 300  # seconds
    max_lifetime: int = 3600  # seconds
    acquire_timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 0.1  # seconds
    health_check_interval: int = 60  # seconds
    prepared_statement_cache_size: int = 100


@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    pending_acquires: int = 0
    total_acquires: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    total_errors: int = 0
    created_at: float = field(default_factory=time.time)


class PoolConnection:
    """Wrapper for pooled database connections"""

    def __init__(self, connection: Any, pool: 'DatabaseConnection', created_at: float):
        self.connection = connection
        self.pool = pool
        self.created_at = created_at
        self.last_used = created_at
        self.in_use = False
        self.prepared_statements: Dict[str, Any] = {}

    async def execute(self, query: str, params: tuple = None) -> Any:
        """Execute query with connection"""
        self.last_used = time.time()
        try:
            if hasattr(self.connection, 'execute'):
                return await self.connection.execute(query, params or ())
            else:
                # MongoDB style
                return await self.connection.command(query, params or {})
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def execute_raw(self, query: str, params: tuple = None) -> Any:
        """Execute raw query with cursor access"""
        self.last_used = time.time()
        try:
            if hasattr(self.connection, 'execute_raw'):
                return await self.connection.execute_raw(query, params or ())
            else:
                # Fallback to regular execute for backends without raw support
                return await self.execute(query, params)
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def get_cursor(self) -> Any:
        """Get raw database cursor (Django-style API)"""
        self.last_used = time.time()
        try:
            if hasattr(self.connection, 'cursor'):
                return self.connection.cursor()
            else:
                # For backends without direct cursor access
                raise NotImplementedError("Direct cursor access not available for this backend")
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def begin_transaction(self) -> Any:
        """Begin transaction with connection"""
        self.last_used = time.time()
        try:
            if hasattr(self.connection, 'begin_transaction'):
                return await self.connection.begin_transaction()
            else:
                raise NotImplementedError("Transaction support not available for this backend")
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def commit_transaction(self, transaction: Any) -> None:
        """Commit transaction"""
        try:
            if hasattr(self.connection, 'commit_transaction'):
                await self.connection.commit_transaction(transaction)
            else:
                raise NotImplementedError("Transaction support not available for this backend")
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def rollback_transaction(self, transaction: Any) -> None:
        """Rollback transaction"""
        try:
            if hasattr(self.connection, 'rollback_transaction'):
                await self.connection.rollback_transaction(transaction)
            else:
                raise NotImplementedError("Transaction support not available for this backend")
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def execute_in_transaction(self, query: str, params: tuple = None) -> Any:
        """Execute query within transaction context"""
        self.last_used = time.time()
        try:
            if hasattr(self.connection, 'execute_in_transaction'):
                return await self.connection.execute_in_transaction(query, params or ())
            else:
                # Fallback to manual transaction handling
                transaction = await self.begin_transaction()
                try:
                    result = await self.execute(query, params)
                    await self.commit_transaction(transaction)
                    return result
                except Exception:
                    await self.rollback_transaction(transaction)
                    raise
        except Exception as e:
            self.pool._stats.total_errors += 1
            raise e

    async def close(self):
        """Close the connection"""
        if hasattr(self.connection, 'close'):
            await self.connection.close()

    def is_expired(self, max_lifetime: int) -> bool:
        """Check if connection has expired"""
        return (time.time() - self.created_at) > max_lifetime

    def is_idle_timeout(self, max_idle_time: int) -> bool:
        """Check if connection has been idle too long"""
        return (time.time() - self.last_used) > max_idle_time





# Import concrete implementations lazily in get_instance to avoid circular imports

__all__ = [
    'DatabaseConnection',
    'SQLiteConnection',
    'PostgreSQLConnection',
    'MySQLConnection',
    'MongoDBConnection',
    'PoolConfig',
    'ConnectionStats',
    'PoolConnection'
]
