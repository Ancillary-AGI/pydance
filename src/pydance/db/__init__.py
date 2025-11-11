"""
Database package - Unified database access layer.

Provides DatabaseConfig, DatabaseConnection, models, migrations, and type definitions.
"""


# Types and fields
from pydance.db.models.base import (
    FieldType, RelationshipType, OrderDirection, PoolConfig, ConnectionStats,
    DistributedCacheConfig, PaginationParams, PaginationMetadata, PaginationLink,
    PaginatedResponse, AggregationResult, LazyLoad, Field, StringField,
    IntegerField, BigIntegerField, BooleanField, DateTimeField, DateField,
    TimeField, FloatField, DecimalField, UUIDField, JSONField, TextField,
    BlobField, ByteaField, TimestampTZField, EmailField, PhoneField, URLField,
    IPAddressField, PasswordField, ArrayField, EnumField, ForeignKeyField,
    FileField, ImageField, Relationship, validate_email, validate_url,
    validate_phone, validate_ip, get_field_from_type
)

# Models

# Migrations
from pydance.db.migrations import (
    Migration, MigrationOperation, MigrationOperationType,
    MigrationFile, MigrationGenerator, MigrationRunner, MigrationManager,
    MigrationFramework, migration_manager, make_migrations, migrate,
    show_migrations, rollback_migration, get_migration_status
)

__all__ = [
    # Core database
    'DatabaseConfig', 'DatabaseConnection',

    # Types and fields
    'FieldType', 'RelationshipType', 'OrderDirection', 'PoolConfig', 'ConnectionStats',
    'DistributedCacheConfig', 'PaginationParams', 'PaginationMetadata', 'PaginationLink',
    'PaginatedResponse', 'AggregationResult', 'LazyLoad', 'Field', 'StringField',
    'IntegerField', 'BigIntegerField', 'BooleanField', 'DateTimeField', 'DateField',
    'TimeField', 'FloatField', 'DecimalField', 'UUIDField', 'JSONField', 'TextField',
    'BlobField', 'ByteaField', 'TimestampTZField', 'EmailField', 'PhoneField', 'URLField',
    'IPAddressField', 'PasswordField', 'ArrayField', 'EnumField', 'ForeignKeyField',
    'FileField', 'ImageField', 'Relationship', 'validate_email', 'validate_url',
    'validate_phone', 'validate_ip', 'get_field_from_type',

    # Models
    'BaseModel', 'QueryBuilder',

    # Migrations
    'Migration', 'MigrationOperation', 'MigrationOperationType',
    'MigrationFile', 'MigrationGenerator', 'MigrationRunner', 'MigrationManager',
    'MigrationFramework', 'migration_manager', 'make_migrations', 'migrate',
    'show_migrations', 'rollback_migration', 'get_migration_status'
]
