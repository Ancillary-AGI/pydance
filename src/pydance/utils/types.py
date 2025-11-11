"""
"""
"""
Type definitions and utilities for Pydance framework.

Provides common type definitions and utilities used throughout the framework.
Note: Database-specific field types are imported from pydance.db.models.base
"""

from typing import Any, Dict, List, Optional, Union, Type, Callable


# Re-export all field types from the database models for convenience
# This avoids duplication and ensures consistency
from pydance.db.models.base import Field


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
