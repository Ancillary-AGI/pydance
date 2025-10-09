"""
Database package - Unified database access layer.

Provides DatabaseConfig, DatabaseConnection, models, migrations, and type definitions.
"""

from pydance.db.config import DatabaseConfig
from pydance.db.connections import DatabaseConnection

# Models
from pydance.db.models import (
    BaseModel, Field, StringField, IntegerField, BooleanField, EmailField,
    DateTimeField, DateField, TimeField, UUIDField, DecimalField, JSONField,
    ModelFactory, QueryBuilder, BaseUser, UserRole, UserStatus
)

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
    'FieldType', 'RelationshipType', 'OrderDirection',
    'PoolConfig', 'ConnectionStats',

    # Models
    'BaseModel', 'Field', 'StringField', 'IntegerField', 'BooleanField', 'EmailField',
    'DateTimeField', 'DateField', 'TimeField', 'UUIDField', 'DecimalField', 'JSONField',
    'ModelFactory', 'QueryBuilder', 'BaseUser', 'UserRole', 'UserStatus',

    # Migrations
    'Migration', 'MigrationOperation', 'MigrationOperationType',
    'MigrationFile', 'MigrationGenerator', 'MigrationRunner', 'MigrationManager',
    'MigrationFramework', 'migration_manager', 'make_migrations', 'migrate',
    'show_migrations', 'rollback_migration', 'get_migration_status'
]
