"""
Migration classes and operations for Pydance framework.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Type
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pydance.db.connections import DatabaseConnection
from pydance.db.config import DatabaseConfig
from .base import BaseModel
from pydance.utils.types import Field


class MigrationOperationType(str, Enum):
    """Types of migration operations"""
    CREATE_MODEL = "create_model"
    DELETE_MODEL = "delete_model"
    RENAME_MODEL = "rename_model"
    ADD_FIELD = "add_field"
    REMOVE_FIELD = "remove_field"
    ALTER_FIELD = "alter_field"
    RENAME_FIELD = "rename_field"
    CREATE_INDEX = "create_index"
    DELETE_INDEX = "delete_index"
    CREATE_RELATIONSHIP = "create_relationship"
    DELETE_RELATIONSHIP = "delete_relationship"
    RUN_SQL = "run_sql"
    RUN_PYTHON = "run_python"


@dataclass
class MigrationOperation:
    """Represents a single migration operation"""
    operation_type: MigrationOperationType
    model_name: Optional[str] = None
    field_name: Optional[str] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    field_type: Optional[str] = None
    field_options: Dict[str, Any] = field(default_factory=dict)
    index_name: Optional[str] = None
    index_fields: List[str] = field(default_factory=list)
    index_options: Dict[str, Any] = field(default_factory=dict)
    relationship_type: Optional[str] = None
    related_model: Optional[str] = None
    sql: Optional[str] = None
    python_code: Optional[str] = None
    reverse_code: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    atomic: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary"""
        return {
            'operation_type': self.operation_type.value,
            'model_name': self.model_name,
            'field_name': self.field_name,
            'old_name': self.old_name,
            'new_name': self.new_name,
            'field_type': self.field_type,
            'field_options': self.field_options,
            'index_name': self.index_name,
            'index_fields': self.index_fields,
            'index_options': self.index_options,
            'relationship_type': self.relationship_type,
            'related_model': self.related_model,
            'sql': self.sql,
            'python_code': self.python_code,
            'reverse_code': self.reverse_code,
            'dependencies': self.dependencies,
            'atomic': self.atomic
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MigrationOperation':
        """Create operation from dictionary"""
        return cls(
            operation_type=MigrationOperationType(data['operation_type']),
            model_name=data.get('model_name'),
            field_name=data.get('field_name'),
            old_name=data.get('old_name'),
            new_name=data.get('new_name'),
            field_type=data.get('field_type'),
            field_options=data.get('field_options', {}),
            index_name=data.get('index_name'),
            index_fields=data.get('index_fields', []),
            index_options=data.get('index_options', {}),
            relationship_type=data.get('relationship_type'),
            related_model=data.get('related_model'),
            sql=data.get('sql'),
            python_code=data.get('python_code'),
            reverse_code=data.get('reverse_code'),
            dependencies=data.get('dependencies', []),
            atomic=data.get('atomic', True)
        )


@dataclass
class Migration:
    """Represents a database migration"""
    id: str
    name: str
    description: str
    version: int
    operations: List[MigrationOperation] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    checksum: Optional[str] = None
    rollback_sql: Optional[str] = None
    migration_file: Optional[str] = None
    migration_type: str = "auto"  # auto, manual, data

    def to_dict(self) -> Dict[str, Any]:
        """Convert migration to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'operations': [op.to_dict() for op in self.operations],
            'dependencies': self.dependencies,
            'created_at': self.created_at.isoformat(),
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'checksum': self.checksum,
            'rollback_sql': self.rollback_sql,
            'migration_file': self.migration_file,
            'migration_type': self.migration_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Migration':
        """Create migration from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            version=data['version'],
            operations=[MigrationOperation.from_dict(op) for op in data.get('operations', [])],
            dependencies=data.get('dependencies', []),
            created_at=datetime.fromisoformat(data['created_at']),
            applied_at=datetime.fromisoformat(data['applied_at']) if data.get('applied_at') else None,
            checksum=data.get('checksum'),
            rollback_sql=data.get('rollback_sql'),
            migration_file=data.get('migration_file'),
            migration_type=data.get('migration_type', 'auto')
        )

    def calculate_checksum(self) -> str:
        """Calculate checksum for migration integrity"""
        import hashlib

        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def validate(self) -> List[str]:
        """Validate migration for potential issues"""
        errors = []

        if not self.operations:
            errors.append("Migration has no operations")

        for i, op in enumerate(self.operations):
            if op.operation_type == MigrationOperationType.CREATE_MODEL and not op.model_name:
                errors.append(f"Operation {i}: CREATE_MODEL requires model_name")

            if op.operation_type == MigrationOperationType.ADD_FIELD and not op.field_name:
                errors.append(f"Operation {i}: ADD_FIELD requires field_name")

            if op.operation_type == MigrationOperationType.REMOVE_FIELD and not op.field_name:
                errors.append(f"Operation {i}: REMOVE_FIELD requires field_name")

        return errors

    async def execute(self, db_connection: DatabaseConnection) -> bool:
        """Execute migration operations"""
        logger = logging.getLogger("migration_executor")

        try:
            logger.info(f"Executing migration {self.id}: {self.name}")

            for operation in self.operations:
                await self._execute_operation(operation, db_connection)

            # Mark as applied
            self.applied_at = datetime.now()
            self.checksum = self.calculate_checksum()

            logger.info(f"Migration {self.id} executed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration {self.id} failed: {e}")
            raise

    async def _execute_operation(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Execute a single migration operation"""
        if operation.operation_type == MigrationOperationType.CREATE_MODEL:
            await self._create_model(operation, db_connection)
        elif operation.operation_type == MigrationOperationType.ADD_FIELD:
            await self._add_field(operation, db_connection)
        elif operation.operation_type == MigrationOperationType.REMOVE_FIELD:
            await self._remove_field(operation, db_connection)
        elif operation.operation_type == MigrationOperationType.ALTER_FIELD:
            await self._alter_field(operation, db_connection)
        elif operation.operation_type == MigrationOperationType.CREATE_INDEX:
            await self._create_index(operation, db_connection)
        elif operation.operation_type == MigrationOperationType.RUN_SQL:
            await self._run_sql(operation, db_connection)
        elif operation.operation_type == MigrationOperationType.RUN_PYTHON:
            await self._run_python(operation, db_connection)
        else:
            raise ValueError(f"Unsupported operation type: {operation.operation_type}")

    async def _create_model(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Create a new model/table"""
        from .base import BaseModel
        from pydance.utils.types import Field

        # Find the model class
        model_class = None
        for cls in BaseModel.__subclasses__():
            if cls.__name__ == operation.model_name:
                model_class = cls
                break

        if not model_class:
            raise ValueError(f"Model class {operation.model_name} not found")

        # Create table using the database backend
        await db_connection.backend.create_table(model_class)

    async def _add_field(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Add a field to an existing model"""
        from pydance.utils.types import Field

        # Create field object from operation data
        field = Field(
            field_type=operation.field_type,
            primary_key=operation.field_options.get('primary_key', False),
            nullable=operation.field_options.get('nullable', True),
            default=operation.field_options.get('default', None),
            max_length=operation.field_options.get('max_length', None),
            autoincrement=operation.field_options.get('autoincrement', False)
        )

        # Add field using database backend
        await db_connection.backend.add_field(
            operation.model_name,
            operation.field_name,
            field
        )

    async def _remove_field(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Remove a field from an existing model"""
        # Remove field using database backend
        await db_connection.backend.remove_field(
            operation.model_name,
            operation.field_name
        )

    async def _alter_field(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Alter an existing field"""
        from pydance.utils.types import Field

        # Create field object from operation data
        field = Field(
            field_type=operation.field_type,
            primary_key=operation.field_options.get('primary_key', False),
            nullable=operation.field_options.get('nullable', True),
            default=operation.field_options.get('default', None),
            max_length=operation.field_options.get('max_length', None),
            autoincrement=operation.field_options.get('autoincrement', False)
        )

        # Alter field using database backend
        await db_connection.backend.alter_field(
            operation.model_name,
            operation.field_name,
            field
        )

    async def _create_index(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Create an index"""
        # Create index using database backend
        await db_connection.backend.create_index(
            operation.model_name,
            operation.index_name,
            operation.index_fields,
            operation.index_options
        )

    async def _run_sql(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Run raw SQL"""
        if operation.sql:
            await db_connection.execute_query(operation.sql)

    async def _run_python(self, operation: MigrationOperation, db_connection: DatabaseConnection):
        """Run Python code"""
        if operation.python_code:
            # Execute Python code in a safe context
            exec_globals = {'db': db_connection, 'datetime': datetime}
            exec(operation.python_code, exec_globals)


class MigrationFile:
    """Represents a migration file on disk"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.migration = None
        self._load_migration()

    def _load_migration(self):
        """Load migration from file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse migration file
            # This would parse the migration file format
            # For now, create a basic migration
            self.migration = Migration(
                id=self.file_path.stem,
                name=self.file_path.stem,
                description=f"Migration from {self.file_path.name}",
                version=1
            )

        except Exception as e:
            logging.error(f"Failed to load migration file {self.file_path}: {e}")

    def save(self):
        """Save migration to file"""
        if not self.migration:
            return

        try:
            # Generate migration file content
            content = self._generate_file_content()

            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            logging.error(f"Failed to save migration file {self.file_path}: {e}")

    def _generate_file_content(self) -> str:
        """Generate file content for migration"""
        if not self.migration:
            return ""

        # Generate Python migration file
        content = f'''"""
Migration: {self.migration.name}
Generated: {datetime.now().isoformat()}
"""

import asyncio
from pydance.db.migrations.migration import Migration, MigrationOperation, MigrationOperationType
from pydance.db.connections import DatabaseConnection

# Migration operations
operations = [
'''

        for op in self.migration.operations:
            content += f'''    MigrationOperation(
        operation_type=MigrationOperationType.{op.operation_type.value.upper()},
        model_name="{op.model_name}",
        field_name="{op.field_name}",
        field_type="{op.field_type}",
        field_options={op.field_options}
    ),
'''

        content += f''']

# Create migration
migration = Migration(
    id="{self.migration.id}",
    name="{self.migration.name}",
    description="{self.migration.description}",
    version={self.migration.version},
    operations=operations
)

async def upgrade(db_connection: DatabaseConnection):
    """Run migration upgrade"""
    await migration.execute(db_connection)

async def downgrade(db_connection: DatabaseConnection):
    """Run migration downgrade"""
    # Reverse operations would go here
    pass

if __name__ == "__main__":
    # Run migration directly
    async def main():
        db = DatabaseConnection.get_instance()
        await upgrade(db)

    asyncio.run(main())
'''

        return content


class MigrationGenerator:
    """Generates migrations from model changes"""

    def __init__(self, migrations_dir: Path = None):
        self.migrations_dir = migrations_dir or Path("migrations")
        self.migrations_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("migration_generator")

    def generate_migration_id(self) -> str:
        """Generate unique migration ID"""
        timestamp = int(datetime.now().timestamp())
        return f"{timestamp:010d}"

    def generate_migration_name(self, changes: Dict[str, Any]) -> str:
        """Generate migration name from changes"""
        if not changes:
            return "auto_migration"

        # Analyze changes to create descriptive name
        model_changes = changes.get('models', {})

        if len(model_changes) == 1:
            model_name = list(model_changes.keys())[0]
            operations = list(model_changes[model_name].keys())
            if 'create' in operations:
                return f"create_{model_name}_model"
            elif 'fields' in operations:
                return f"alter_{model_name}_fields"
            else:
                return f"modify_{model_name}"

        return "auto_migration"

    def detect_model_changes(self, models: List[type]) -> Dict[str, Any]:
        """Detect changes in models compared to current database schema"""
        # This would compare models with database schema
        # For now, return empty changes
        return {}

    def create_migration_from_changes(self, changes: Dict[str, Any], name: str = None) -> Migration:
        """Create migration from detected changes"""
        migration_id = self.generate_migration_id()
        migration_name = name or self.generate_migration_name(changes)

        operations = []

        # Convert changes to operations
        for model_name, model_changes in changes.get('models', {}).items():
            if 'create' in model_changes:
                operations.append(MigrationOperation(
                    operation_type=MigrationOperationType.CREATE_MODEL,
                    model_name=model_name
                ))

            if 'fields' in model_changes:
                for field_name, field_changes in model_changes['fields'].items():
                    if field_changes.get('added'):
                        operations.append(MigrationOperation(
                            operation_type=MigrationOperationType.ADD_FIELD,
                            model_name=model_name,
                            field_name=field_name
                        ))

        migration = Migration(
            id=migration_id,
            name=migration_name,
            description=f"Auto-generated migration: {migration_name}",
            version=1,
            operations=operations
        )

        return migration

    def save_migration_file(self, migration: Migration):
        """Save migration to file"""
        filename = f"{migration.id}_{migration.name}.py"
        file_path = self.migrations_dir / filename

        migration_file = MigrationFile(file_path)
        migration_file.migration = migration
        migration_file.save()

        migration.migration_file = str(file_path)
        return file_path

    def generate_migration(self, models: List[type], name: str = None) -> Migration:
        """Generate migration from models"""
        changes = self.detect_model_changes(models)
        migration = self.create_migration_from_changes(changes, name)
        self.save_migration_file(migration)
        return migration
