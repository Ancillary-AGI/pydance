"""
Database-specific type definitions for Pydance framework.
"""

from typing import Dict, List, Any, Callable, Awaitable, Union, Optional, Set, Type
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date, time
import uuid
import re
from decimal import Decimal

# Database field types
class FieldType(str, Enum):
    # Basic types
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    TEXT = "TEXT"
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    JSON = "JSON"
    JSONB = "JSONB"
    DATE = "DATE"
    TIME = "TIME"
    UUID = "UUID"
    BLOB = "BLOB"
    BYTEA = "BYTEA"

    # Specialized types
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    URL = "URL"
    IP_ADDRESS = "IP_ADDRESS"
    MAC_ADDRESS = "MAC_ADDRESS"
    ENUM = "ENUM"
    ARRAY = "ARRAY"
    RANGE = "RANGE"
    GEOMETRY = "GEOMETRY"
    GEOGRAPHY = "GEOGRAPHY"
    HSTORE = "HSTORE"
    INET = "INET"
    MONEY = "MONEY"

class RelationshipType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"

class OrderDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

# Database pool types
@dataclass
class PoolConfig:
    """Database connection pool configuration"""
    min_size: int = 1
    max_size: int = 10
    max_idle_time: int = 300
    max_lifetime: int = 3600
    acquire_timeout: int = 30

@dataclass
class ConnectionStats:
    """Database connection statistics"""
    active: int
    idle: int
    created: int
    destroyed: int
    borrowed: int
    returned: int

# Distributed cache types
@dataclass
class DistributedCacheConfig:
    """Distributed cache configuration"""
    nodes: List[str]
    replication_factor: int = 1
    consistency_level: str = "quorum"
    ttl: int = 300

# Pagination types
@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: OrderDirection = OrderDirection.ASC

@dataclass
class PaginationMetadata:
    """Pagination metadata"""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

@dataclass
class PaginationLink:
    """Pagination link"""
    rel: str
    href: str
    method: str = "GET"

__all__ = [
    'FieldType', 'RelationshipType', 'OrderDirection',
    'PoolConfig', 'ConnectionStats', 'DistributedCacheConfig',
    'PaginationParams', 'PaginationMetadata', 'PaginationLink'
]
