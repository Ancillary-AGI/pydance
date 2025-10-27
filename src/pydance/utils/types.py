"""
Type definitions and utilities for Pydance framework.

Provides common type definitions, field types, and type utilities
used throughout the framework.
"""

from typing import Any, Dict, List, Optional, Union, Type, Callable
from enum import Enum
from dataclasses import dataclass


class FieldType(Enum):
    """Field type enumeration for database fields"""
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    BIGINT = "bigint"
    FLOAT = "float"
    DOUBLE = "double"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    TIME = "time"
    JSON = "json"
    UUID = "uuid"
    BINARY = "binary"
    BLOB = "blob"
    BYTEA = "bytea"
    TIMESTAMPTZ = "timestamptz"


@dataclass
class Field:
    """Base field class for database models"""
    field_type: FieldType = FieldType.STRING
    nullable: bool = True
    default: Any = None
    primary_key: bool = False
    unique: bool = False
    index: bool = False
    max_length: Optional[int] = None
    autoincrement: bool = False

    def __post_init__(self):
        if self.primary_key:
            self.nullable = False


class StringField(Field):
    """String field for database models"""
    def __init__(self, max_length: int = 255, **kwargs):
        super().__init__(field_type=FieldType.STRING, **kwargs)
        self.max_length = max_length


class IntegerField(Field):
    """Integer field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.INTEGER, **kwargs)


class BooleanField(Field):
    """Boolean field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.BOOLEAN, **kwargs)


class DateTimeField(Field):
    """DateTime field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.DATETIME, **kwargs)


class TextField(Field):
    """Text field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.TEXT, **kwargs)


class JSONField(Field):
    """JSON field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.JSON, **kwargs)


class UUIDField(Field):
    """UUID field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.UUID, **kwargs)


class FloatField(Field):
    """Float field for database models"""
    def __init__(self, **kwargs):
        super().__init__(field_type=FieldType.FLOAT, **kwargs)


class DecimalField(Field):
    """Decimal field for database models"""
    def __init__(self, max_digits: int = 10, decimal_places: int = 2, **kwargs):
        super().__init__(field_type=FieldType.DECIMAL, **kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places


# Type aliases for better code readability
ModelClass = Type[Any]
FieldDefinition = Union[Field, Dict[str, Any]]
QueryFilter = Dict[str, Any]
QuerySort = List[tuple]  # List of (field, direction) tuples
QueryParams = Dict[str, Any]

# Common type patterns
OptionalString = Optional[str]
OptionalInt = Optional[int]
OptionalBool = Optional[bool]
StringOrInt = Union[str, int]
StringList = List[str]
IntList = List[int]
AnyDict = Dict[str, Any]
StringDict = Dict[str, str]

# Database-related types
ConnectionConfig = Dict[str, Any]
MigrationOperation = Dict[str, Any]
MigrationResult = Dict[str, Any]

# HTTP-related types
HTTPHeaders = Dict[str, str]
HTTPQueryParams = Dict[str, str]
HTTPFormData = Dict[str, Any]
HTTPMethod = str

# Service-related types
ServiceConfig = Dict[str, Any]
ServiceStatus = str
ServiceHealth = Dict[str, Any]

# Cache-related types
CacheKey = str
CacheValue = Any
CacheTTL = int
CacheConfig = Dict[str, Any]

# Event-related types
EventData = Dict[str, Any]
EventHandler = Callable[[EventData], Any]
EventListener = Callable[[str, EventData], None]

# Validation types
ValidationRule = Callable[[Any], bool]
ValidationError = Dict[str, str]
ValidationResult = Dict[str, Any]

# Common utility types
Timestamp = float
Duration = float
SizeBytes = int
Percentage = float

__all__ = [
    # Field types
    'FieldType',
    'Field',
    'StringField',
    'IntegerField',
    'BooleanField',
    'DateTimeField',
    'TextField',
    'JSONField',
    'UUIDField',
    'FloatField',
    'DecimalField',

    # Type aliases
    'ModelClass',
    'FieldDefinition',
    'QueryFilter',
    'QuerySort',
    'QueryParams',
    'OptionalString',
    'OptionalInt',
    'OptionalBool',
    'StringOrInt',
    'StringList',
    'IntList',
    'AnyDict',
    'StringDict',

    # Database types
    'ConnectionConfig',
    'MigrationOperation',
    'MigrationResult',

    # HTTP types
    'HTTPHeaders',
    'HTTPQueryParams',
    'HTTPFormData',
    'HTTPMethod',

    # Service types
    'ServiceConfig',
    'ServiceStatus',
    'ServiceHealth',

    # Cache types
    'CacheKey',
    'CacheValue',
    'CacheTTL',
    'CacheConfig',

    # Event types
    'EventData',
    'EventHandler',
    'EventListener',

    # Validation types
    'ValidationRule',
    'ValidationError',
    'ValidationResult',

    # Utility types
    'Timestamp',
    'Duration',
    'SizeBytes',
    'Percentage'
]
