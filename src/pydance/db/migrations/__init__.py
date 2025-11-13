"""
Database Migrations Module

This module contains all database migration functionality.
Moved from src/pydance/migrations/ to src/pydance/db/migrations/ for better organization.
"""

# Re-export all migration functionality for backward compatibility
from .migrator import (
    MigrationRunner, MigrationManager, MigrationStatus,
    migration_manager, make_migrations, migrate, show_migrations,
    rollback_migration, get_migration_status
)

from .migration import (
    Migration, MigrationOperation, MigrationOperationType,
    MigrationFile, MigrationGenerator
)

from .migrator import (
    Migrator
)

__all__ = [
    # Migration runner and manager
    'MigrationRunner', 'MigrationManager', 'MigrationStatus',
    'migration_manager', 'make_migrations', 'migrate', 'show_migrations',
    'rollback_migration', 'get_migration_status',

    # Migration classes
    'Migration', 'MigrationOperation', 'MigrationOperationType',
    'MigrationFile', 'MigrationGenerator',

    # Framework integration
    'Migrator'
]
