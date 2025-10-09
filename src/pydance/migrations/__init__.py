"""
Migration system for Pydance framework.
Supports both database-stored and file-based migrations.
"""

from pydance.db.migrations.migrator import MigrationRunner, MigrationGenerator, MigrationManager, MigrationStatus, Migrator
from pydance.db.migrations.migration import Migration, MigrationOperation, MigrationOperationType, MigrationFile, LegacyMigration
from pydance.db.migrations.framework import MigrationFramework, migrate_app, check_migration_status, discover_models, analyze_model_changes

__all__ = [
    'MigrationRunner', 'MigrationGenerator', 'MigrationManager', 'MigrationStatus',
    'Migration', 'MigrationOperation', 'MigrationOperationType', 'MigrationFile',
    'MigrationFramework', 'migrate_app', 'check_migration_status',
    'discover_models', 'analyze_model_changes'
]
