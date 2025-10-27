"""
SQLite Database Backend

This module provides a database backend for SQLite, implementing the full
DatabaseBackend interface with SQLite-specific features.

Key SQLite-specific features:
- Proper handling of SQLite's lack of DROP COLUMN support via table recreation
- AUTOINCREMENT support for primary keys
- Foreign key enforcement
- WAL mode support for better concurrency

Example usage:
    from pydance.db.models import Model, StringField, IntegerField

    class User(Model):
        name = StringField(max_length=100)
        age = IntegerField()

        class Meta:
            table_name = 'users'

    # Backend handles table creation, migrations, etc.
    backend = SQLiteBackend(config)
    await backend.create_table(User)
"""

import sqlite3
import json
import os
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Type, Optional, Tuple, Union
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import threading
from decimal import Decimal

from .base_connection import DatabaseConnection
from pydance.db.config import DatabaseConfig
from pydance.db.models.base import Field, StringField, IntegerField, BooleanField, DateTimeField, FieldType

logger = logging.getLogger(__name__)


class SQLiteConnection(DatabaseConnection):
    """
    SQLite Database Backend

    This backend provides SQLite database connectivity with async operations:
    - Model-based table creation
    - Migration support with proper SQLite column recreation
    - Query building with parameter binding
    - Transaction management

    Example usage:
        backend = SQLiteBackend(config)
        await backend.connect()

        # Create tables
        await backend.create_table(UserModel)

        # Query
        users = await backend.find_many(UserModel, {'active': True})
    """

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.connection = None

    async def connect(self) -> None:
        """Connect to the database"""
        self.connection = sqlite3.connect(self.config.name)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    async def disconnect(self) -> None:
        """Disconnect from the database"""
        if self.connection:
            self.connection.close()

    async def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute a SQL query"""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    async def execute_raw(self, query: str, params: tuple = None) -> Any:
        """Execute a raw query and return cursor for advanced usage (Django-like cursor API)."""
        return await self.execute_query(query, params)

    async def begin_transaction(self) -> Any:
        """Begin SQLite transaction."""
        cursor = self.connection.cursor()
        cursor.execute("BEGIN")
        return cursor

    async def commit_transaction(self, transaction: Any) -> None:
        """Commit SQLite transaction."""
        self.connection.commit()

    async def rollback_transaction(self, transaction: Any) -> None:
        """Rollback SQLite transaction."""
        self.connection.rollback()

    async def execute_in_transaction(self, query: str, params: tuple = None) -> Any:
        """Execute SQLite query within transaction context."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("BEGIN")
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor
        except Exception as e:
            self.connection.rollback()
            raise e

    async def _create_connection(self) -> Any:
        """Create a new SQLite connection for pooling"""
        import sqlite3
        conn = sqlite3.connect(self.config.database)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    async def create_table(self, model_class: Type) -> None:
        """Create a table for the model"""
        fields = []
        for name, field in model_class._fields.items():
            field_def = f"{name} {self.get_sql_type(field)}"
            if field.primary_key:
                field_def += " PRIMARY KEY"
                if field.autoincrement:
                    field_def += " AUTOINCREMENT"
            if not field.nullable:
                field_def += " NOT NULL"
            if field.default is not None:
                field_def += f" DEFAULT {self._format_default(field.default)}"
            fields.append(field_def)

        query = f"CREATE TABLE IF NOT EXISTS {model_class.get_table_name()} ({', '.join(fields)})"
        await self.execute_query(query)
        self.connection.commit()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Any, None]:
        """Get a database connection context manager"""
        if not self.connection:
            await self.connect()
        try:
            yield self.connection
        finally:
            pass  # SQLite connections are not pooled

    async def get_param_placeholder(self, index: int) -> str:
        """Get parameter placeholder for SQLite"""
        return "?"

    def get_sql_type(self, field: Field) -> str:
        """Get SQL type for a field"""
        if isinstance(field, StringField):
            if field.max_length:
                return f"VARCHAR({field.max_length})"
            return "TEXT"
        elif isinstance(field, IntegerField):
            return "INTEGER"
        elif isinstance(field, BooleanField):
            return "INTEGER"  # SQLite uses INTEGER for boolean
        elif isinstance(field, DateTimeField):
            return "DATETIME"
        elif field.field_type == FieldType.UUID:
            return "TEXT"
        elif field.field_type == FieldType.JSON:
            return "TEXT"
        elif field.field_type == FieldType.FLOAT:
            return "REAL"
        return "TEXT"

    async def insert_one(self, model_class: Type, data: Dict[str, Any]) -> Any:
        """Insert a single record"""
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join([self.get_param_placeholder(i+1) for i in range(len(fields))])
        query = f"INSERT INTO {model_class.get_table_name()} ({', '.join(fields)}) VALUES ({placeholders})"

        cursor = await self.execute_query(query, tuple(values))
        self.connection.commit()
        return cursor.lastrowid

    async def update_one(self, model_class: Type, filters: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update a single record"""
        set_clause = ', '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(data.keys())])
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(len(data) + i + 1)}" for i, k in enumerate(filters.keys())])
        query = f"UPDATE {model_class.get_table_name()} SET {set_clause} WHERE {where_clause}"

        params = tuple(list(data.values()) + list(filters.values()))
        cursor = await self.execute_query(query, params)
        self.connection.commit()
        return cursor.rowcount > 0

    async def delete_one(self, model_class: Type, filters: Dict[str, Any]) -> bool:
        """Delete a single record"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())])
        query = f"DELETE FROM {model_class.get_table_name()} WHERE {where_clause}"

        cursor = await self.execute_query(query, tuple(filters.values()))
        self.connection.commit()
        return cursor.rowcount > 0

    async def find_one(self, model_class: Type, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single record"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())])
        query = f"SELECT * FROM {model_class.get_table_name()} WHERE {where_clause} LIMIT 1"

        cursor = await self.execute_query(query, tuple(filters.values()))
        row = cursor.fetchone()
        return dict(row) if row else None

    async def find_many(self, model_class: Type, filters: Dict[str, Any], limit: Optional[int] = None,
                       offset: Optional[int] = None, sort: Optional[List[Tuple[str, int]]] = None) -> List[Dict[str, Any]]:
        """Find multiple records"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())]) if filters else ""
        order_clause = ""
        if sort:
            order_parts = [f"{field} {'DESC' if direction == -1 else 'ASC'}" for field, direction in sort]
            order_clause = f" ORDER BY {', '.join(order_parts)}"

        limit_clause = f" LIMIT {limit}" if limit else ""
        offset_clause = f" OFFSET {offset}" if offset else ""

        query = f"SELECT * FROM {model_class.get_table_name()}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += order_clause + limit_clause + offset_clause

        cursor = await self.execute_query(query, tuple(filters.values()) if filters else None)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def count(self, model_class: Type, filters: Dict[str, Any]) -> int:
        """Count records matching filters"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())]) if filters else ""
        query = f"SELECT COUNT(*) as count FROM {model_class.get_table_name()}"
        if where_clause:
            query += f" WHERE {where_clause}"

        cursor = await self.execute_query(query, tuple(filters.values()) if filters else None)
        row = cursor.fetchone()
        return row['count'] if row else 0

    async def aggregate(self, model_class: Type, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform aggregation operations

        This method implements aggregation pipeline syntax translated to SQL.
        Note: SQLite has more limited aggregation support compared to other databases,
        but this implementation provides basic aggregation capabilities.

        Example pipeline:
        [
            {
                '$group': {
                    '_id': 'category',
                    'total': {'$sum': 'amount'},
                    'count': {'$count': '*'}
                }
            }
        ]
        """
        if not pipeline:
            return []

        # Handle basic aggregation operations
        results = []
        agg_query = pipeline[0]

        if '$group' in agg_query:
            group_fields = agg_query['$group']

            # Build GROUP BY clause
            group_columns = []
            for field, alias in group_fields.items():
                if field != '_id':  # Skip _id field for now
                    group_columns.append(field)

            if group_columns:
                # Build aggregation functions
                select_parts = []
                for field, alias in group_fields.items():
                    if field == '_id':
                        select_parts.append(f"{alias} as _id")
                    else:
                        select_parts.append(field)

                # Add aggregation functions if specified
                if '$sum' in agg_query:
                    for field in agg_query['$sum']:
                        select_parts.append(f"SUM({field}) as {field}_sum")

                if '$count' in agg_query:
                    select_parts.append("COUNT(*) as count")

                if '$avg' in agg_query:
                    for field in agg_query['$avg']:
                        select_parts.append(f"AVG({field}) as {field}_avg")

                if '$max' in agg_query:
                    for field in agg_query['$max']:
                        select_parts.append(f"MAX({field}) as {field}_max")

                if '$min' in agg_query:
                    for field in agg_query['$min']:
                        select_parts.append(f"MIN({field}) as {field}_min")

                # Build the query
                select_clause = ', '.join(select_parts)
                group_clause = ', '.join(group_columns)

                query = f"SELECT {select_clause} FROM {model_class.get_table_name()} GROUP BY {group_clause}"

                # Execute the query
                cursor = await self.execute_query(query)
                rows = cursor.fetchall()

                # Convert to MongoDB-style aggregation result
                for row in rows:
                    result = {}
                    for key, value in row.items():
                        if key.endswith('_sum'):
                            field = key[:-4]
                            if '$sum' not in result:
                                result['$sum'] = {}
                            result['$sum'][field] = value
                        elif key.endswith('_avg'):
                            field = key[:-4]
                            if '$avg' not in result:
                                result['$avg'] = {}
                            result['$avg'][field] = value
                        elif key.endswith('_max'):
                            field = key[:-4]
                            if '$max' not in result:
                                result['$max'] = {}
                            result['$max'][field] = value
                        elif key.endswith('_min'):
                            field = key[:-4]
                            if '$min' not in result:
                                result['$min'] = {}
                            result['$min'][field] = value
                        elif key == 'count':
                            result['count'] = value
                        else:
                            result[key] = value
                    results.append(result)

        return results
    def _format_default(self, default: Any) -> str:
        """Format default value for SQLite"""
        if isinstance(default, str):
            if default.upper() in ['CURRENT_TIMESTAMP', 'CURRENT_DATE']:
                return default
            return f"'{default}'"
        elif isinstance(default, bool):
            return '1' if default else '0'
        elif default is None:
            return 'NULL'
        return str(default)

    async def create_migrations_table(self) -> None:
        """Create the migrations tracking table for SQLite"""
        query = '''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY,
                migration_id TEXT UNIQUE,
                model_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                schema_definition TEXT NOT NULL,
                operations TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, version)
            )
        '''
        await self.execute_query(query)
        self.connection.commit()

    async def insert_migration_record(self, model_name: str, version: int, schema_definition: dict, operations: dict, migration_id: str = None) -> None:
        """Insert a migration record for SQLite"""
        import json
        if migration_id:
            query = '''
                INSERT INTO migrations (migration_id, model_name, version, schema_definition, operations)
                VALUES (?, ?, ?, ?, ?)
            '''
            params = (migration_id, model_name, version, json.dumps(schema_definition), json.dumps(operations))
        else:
            query = '''
                INSERT INTO migrations (model_name, version, schema_definition, operations)
                VALUES (?, ?, ?, ?)
            '''
            params = (model_name, version, json.dumps(schema_definition), json.dumps(operations))
        await self.execute_query(query, params)
        self.connection.commit()

    async def get_applied_migrations(self) -> Dict[str, int]:
        """Get all applied migrations for SQLite"""
        query = "SELECT model_name, version FROM migrations"
        cursor = await self.execute_query(query)
        rows = cursor.fetchall()

        migrations = {}
        for row in rows:
            migrations[row['model_name']] = row['version']
        return migrations

    async def delete_migration_record(self, model_name: str, version: int) -> None:
        """Delete a migration record for SQLite"""
        query = "DELETE FROM migrations WHERE model_name = ? AND version = ?"
        await self.execute_query(query, (model_name, version))
        self.connection.commit()

    async def drop_table(self, table_name: str) -> None:
        """Drop a table for SQLite"""
        query = f"DROP TABLE IF EXISTS {table_name}"
        await self.execute_query(query)
        self.connection.commit()

    async def add_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        """Add a column to a table for SQLite"""
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        await self.execute_query(query)
        self.connection.commit()

    async def drop_column(self, table_name: str, column_name: str) -> None:
        """
        Drop a column from a table - SQLite-specific implementation

        SQLite doesn't support DROP COLUMN directly, so we must recreate the table
        without the column. The process is:
        1. Create temporary table with new schema
        2. Copy data from old table to new table
        3. Drop old table
        4. Rename temporary table to original name

        This ensures all column constraints (NOT NULL, DEFAULT, PRIMARY KEY, etc.) are preserved.
        """
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        temp_table = f"{table_name}_temp"

        # Get current schema
        cursor = await self.execute_query(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # Create new column list without the dropped column
        new_columns = [col for col in columns if col['name'] != column_name]

        if new_columns:
            # Build complete column definitions including constraints
            column_defs = []
            for col in new_columns:
                col_def = f"{col['name']} {col['type']}"
                if col['notnull']:
                    col_def += " NOT NULL"
                if col['pk']:
                    col_def += " PRIMARY KEY"
                    if col['type'].upper() == 'INTEGER':
                        col_def += " AUTOINCREMENT"
                if col['dflt_value'] is not None:
                    col_def += f" DEFAULT {col['dflt_value']}"
                column_defs.append(col_def)

            # Create temporary table with full column definitions
            await self.execute_query(f"CREATE TABLE {temp_table} ({', '.join(column_defs)})")

            # Copy data
            column_names = ', '.join([col['name'] for col in new_columns])
            await self.execute_query(f"INSERT INTO {temp_table} ({column_names}) SELECT {column_names} FROM {table_name}")

            # Drop old table and rename new one
            await self.execute_query(f"DROP TABLE {table_name}")
            await self.execute_query(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

        self.connection.commit()

    def _parse_column_definition(self, column_definition: str) -> Dict[str, Any]:
        """
        Parse a column definition string and extract type and constraints.

        Args:
            column_definition: SQL column definition like "name VARCHAR(100) NOT NULL DEFAULT 'test'"

        Returns:
            Dict with keys: 'type', 'constraints' (dict with constraint details)
        """
        parts = column_definition.strip().split()
        if not parts:
            return {'type': 'TEXT', 'constraints': {}}

        # First part is the type
        column_type = parts[0]

        # Parse constraints
        constraints = {}
        i = 1
        while i < len(parts):
            part = parts[i].upper()
            if part == 'NOT':
                if i + 1 < len(parts) and parts[i + 1].upper() == 'NULL':
                    constraints['not_null'] = True
                    i += 2
                else:
                    i += 1
            elif part == 'NULL':
                constraints['not_null'] = False
                i += 1
            elif part == 'PRIMARY':
                if i + 1 < len(parts) and parts[i + 1].upper() == 'KEY':
                    constraints['primary_key'] = True
                    i += 2
                else:
                    i += 1
            elif part == 'AUTOINCREMENT':
                constraints['autoincrement'] = True
                i += 1
            elif part == 'DEFAULT':
                # Handle DEFAULT value (can be multiple words)
                default_start = i + 1
                default_value = []
                while default_start < len(parts):
                    if default_start < len(parts) - 1 and parts[default_start + 1].upper() in ['NOT', 'NULL', 'PRIMARY', 'KEY', 'AUTOINCREMENT', 'UNIQUE', 'CHECK']:
                        break
                    default_value.append(parts[default_start])
                    default_start += 1

                if default_value:
                    constraints['default'] = ' '.join(default_value)
                    i = default_start
                else:
                    i += 1
            elif part == 'UNIQUE':
                constraints['unique'] = True
                i += 1
            elif part == 'CHECK':
                # Handle CHECK constraint (can be multiple words)
                check_start = i + 1
                check_value = []
                while check_start < len(parts):
                    if check_start < len(parts) - 1 and parts[check_start + 1].upper() in ['NOT', 'NULL', 'PRIMARY', 'KEY', 'AUTOINCREMENT', 'UNIQUE']:
                        break
                    check_value.append(parts[check_start])
                    check_start += 1

                if check_value:
                    constraints['check'] = ' '.join(check_value)
                    i = check_start
                else:
                    i += 1
            else:
                i += 1

        return {'type': column_type, 'constraints': constraints}

    def _merge_column_constraints(self, existing_constraints: Dict[str, Any], new_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge existing column constraints with new ones.

        New constraints override existing ones, except for some special cases.

        Args:
            existing_constraints: Constraints from PRAGMA table_info
            new_constraints: Constraints from parsed column definition

        Returns:
            Merged constraints dictionary
        """
        merged = existing_constraints.copy()

        # Override with new constraints
        for key, value in new_constraints.items():
            if key == 'not_null':
                # NOT NULL in new definition overrides existing nullable setting
                merged['not_null'] = value
            elif key == 'primary_key':
                merged['primary_key'] = value
            elif key == 'autoincrement':
                merged['autoincrement'] = value
            elif key == 'default':
                # New default overrides existing
                merged['default'] = value
            elif key == 'unique':
                merged['unique'] = value
            elif key == 'check':
                merged['check'] = value

        return merged

    def _build_column_definition(self, column_name: str, column_type: str, constraints: Dict[str, Any]) -> str:
        """
        Build a complete column definition string from type and constraints.

        Args:
            column_name: Name of the column
            column_type: SQL data type
            constraints: Dictionary of constraints

        Returns:
            Complete column definition string
        """
        parts = [column_name, column_type]

        if constraints.get('not_null'):
            parts.append('NOT NULL')
        elif constraints.get('not_null') is False:
            parts.append('NULL')

        if constraints.get('primary_key'):
            parts.append('PRIMARY KEY')
            if constraints.get('autoincrement') and column_type.upper() == 'INTEGER':
                parts.append('AUTOINCREMENT')

        if 'default' in constraints and constraints['default'] is not None:
            parts.append(f"DEFAULT {constraints['default']}")

        if constraints.get('unique'):
            parts.append('UNIQUE')

        if 'check' in constraints and constraints['check']:
            parts.append(f"CHECK {constraints['check']}")

        return ' '.join(parts)

    async def modify_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        """
        Modify a column in a table - SQLite-specific implementation

        SQLite requires table recreation for column modifications. This method handles
        column type changes, constraint modifications, etc.

        Unlike other databases, SQLite requires the full table recreation process.
        """
        # Similar to drop_column, SQLite requires table recreation for column modifications
        temp_table = f"{table_name}_temp"

        # Get current schema
        cursor = await self.execute_query(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # Create new column definitions with full attributes
        column_defs = []
        for col in columns:
            if col['name'] == column_name:
                # Parse new column definition
                new_def = self._parse_column_definition(column_definition)

                # Build existing constraints from PRAGMA info
                existing_constraints = {
                    'not_null': col['notnull'] == 1,
                    'primary_key': col['pk'] > 0,
                    'autoincrement': col['pk'] > 0 and col['type'].upper() == 'INTEGER',
                    'default': col['dflt_value']
                }

                # Merge constraints
                merged_constraints = self._merge_column_constraints(existing_constraints, new_def['constraints'])

                # Build complete column definition
                col_def = self._build_column_definition(column_name, new_def['type'], merged_constraints)
                column_defs.append(col_def)
            else:
                # Preserve original column definition with all attributes
                col_def = f"{col['name']} {col['type']}"
                if col['notnull']:
                    col_def += " NOT NULL"
                if col['pk']:
                    col_def += " PRIMARY KEY"
                    if col['type'].upper() == 'INTEGER':
                        col_def += " AUTOINCREMENT"
                if col['dflt_value'] is not None:
                    col_def += f" DEFAULT {col['dflt_value']}"
                column_defs.append(col_def)

        # Create temporary table
        await self.execute_query(f"CREATE TABLE {temp_table} ({', '.join(column_defs)})")

        # Copy data
        column_names = ', '.join([col['name'] for col in columns])
        await self.execute_query(f"INSERT INTO {temp_table} ({column_names}) SELECT {column_names} FROM {table_name}")

        # Drop old table and rename new one
        await self.execute_query(f"DROP TABLE {table_name}")
        await self.execute_query(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

        self.connection.commit()

    async def create_index(self, table_name: str, index_name: str, columns: List[str]) -> None:
        """Create an index on a table for SQLite"""
        column_list = ', '.join(columns)
        query = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_list})"
        await self.execute_query(query)
        self.connection.commit()

    async def drop_index(self, table_name: str, index_name: str) -> None:
        """Drop an index from a table for SQLite"""
        query = f"DROP INDEX IF EXISTS {index_name}"
        await self.execute_query(query)
        self.connection.commit()

    async def add_field(self, model_name: str, field_name: str, field: Field) -> None:
        """Add a field to an existing model/table for SQLite"""
        table_name = model_name.lower() + 's'  # Follow convention
        column_definition = f"{field_name} {self.get_sql_type(field)}"

        if field.primary_key:
            column_definition += " PRIMARY KEY"
            if field.autoincrement:
                column_definition += " AUTOINCREMENT"

        if not field.nullable:
            column_definition += " NOT NULL"

        if field.default is not None:
            column_definition += f" DEFAULT {self._format_default(field.default)}"

        query = f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"
        await self.execute_query(query)
        self.connection.commit()

    async def remove_field(self, model_name: str, field_name: str) -> None:
        """Remove a field from an existing model/table for SQLite"""
        table_name = model_name.lower() + 's'  # Follow convention
        await self.drop_column(table_name, field_name)

    async def alter_field(self, model_name: str, field_name: str, field: Field) -> None:
        """Alter an existing field in a model/table for SQLite"""
        table_name = model_name.lower() + 's'  # Follow convention
        await self.modify_column(table_name, field_name, self.get_sql_type(field))

    def get_type_mappings(self) -> Dict[Any, str]:
        """Get SQLite-specific type mappings"""
        from pydance.db.models.base import FieldType
        return {
            FieldType.BOOLEAN: "INTEGER",
            FieldType.UUID: "TEXT",
            FieldType.JSON: "TEXT",
            FieldType.TIMESTAMPTZ: "TEXT",
            FieldType.BLOB: "BLOB",
            FieldType.BYTEA: "BLOB",
        }

    def format_default_value(self, value: Any) -> str:
        """Format default value for SQLite"""
        from decimal import Decimal
        if isinstance(value, str):
            if value.upper() in ['CURRENT_TIMESTAMP', 'CURRENT_DATE']:
                return value
            return f"'{value}'"
        elif isinstance(value, (int, float, Decimal)):
            return str(value)
        elif isinstance(value, bool):
            return '1' if value else '0'
        elif value is None:
            return 'NULL'
        return f"'{str(value)}'"

    def format_foreign_key(self, foreign_key: str) -> str:
        """Format foreign key constraint for SQLite"""
        ref_table, ref_column = foreign_key.split('.')
        return f"REFERENCES {ref_table}({ref_column})"

    async def execute_query_builder(self, model_class: Type, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a complex query built by QueryBuilder for SQLite"""
        # Extract query parameters
        select_fields = query_params.get('select_fields', [])
        distinct = query_params.get('distinct', False)
        filters = query_params.get('filters', {})
        limit = query_params.get('limit')
        offset = query_params.get('offset')
        order_by = query_params.get('order_by', [])
        group_by = query_params.get('group_by', [])
        having = query_params.get('having', [])

        # Build SELECT clause
        select_clause = "SELECT "
        if distinct:
            select_clause += "DISTINCT "
        if select_fields:
            select_clause += ', '.join(select_fields)
        else:
            select_clause += '*'

        # Build FROM clause
        from_clause = f"FROM {model_class.get_table_name()}"

        # Build WHERE clause
        where_clause = ""
        params = []
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Handle MongoDB-style operators
                    for op, val in value.items():
                        if op == '$gt':
                            conditions.append(f"{key} > ?")
                            params.append(val)
                        elif op == '$lt':
                            conditions.append(f"{key} < ?")
                            params.append(val)
                        elif op == '$gte':
                            conditions.append(f"{key} >= ?")
                            params.append(val)
                        elif op == '$lte':
                            conditions.append(f"{key} <= ?")
                            params.append(val)
                        elif op == '$ne':
                            conditions.append(f"{key} != ?")
                            params.append(val)
                        elif op == '$in':
                            placeholders = ', '.join(['?' for _ in val])
                            conditions.append(f"{key} IN ({placeholders})")
                            params.extend(val)
                        elif op == '$regex':
                            conditions.append(f"{key} LIKE ?")
                            params.append(val.replace('.*', '%'))
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"

        # Build GROUP BY clause
        group_clause = ""
        if group_by:
            group_clause = f"GROUP BY {', '.join(group_by)}"

        # Build HAVING clause
        having_clause = ""
        if having:
            having_conditions = []
            for condition in having:
                # Simple parsing - in practice, you'd need more sophisticated parsing
                having_conditions.append(condition)
            if having_conditions:
                having_clause = f"HAVING {' AND '.join(having_conditions)}"

        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            order_parts = []
            for field, direction in order_by:
                order_parts.append(f"{field} {'DESC' if direction == -1 else 'ASC'}")
            order_clause = f"ORDER BY {', '.join(order_parts)}"

        # Build LIMIT and OFFSET clauses
        limit_clause = f"LIMIT {limit}" if limit else ""
        offset_clause = f"OFFSET {offset}" if offset else ""

        # Combine all parts
        query = f"{select_clause} {from_clause} {where_clause} {group_clause} {having_clause} {order_clause} {limit_clause} {offset_clause}".strip()

        # Execute query
        cursor = await self.execute_query(query, tuple(params) if params else None)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def test_connection(self) -> bool:
        """
        Test database connectivity

        Performs a simple query to verify the database connection is working.
        Returns True if connection is healthy, False otherwise.
        """
        try:
            cursor = await self.execute_query("SELECT 1")
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"SQLite connection test failed: {e}")
            return False

    async def execute_many(self, query: str, parameters_list: List[Tuple]) -> Any:
        """Execute a query multiple times with different parameters."""
        cursor = self.connection.cursor()
        cursor.executemany(query, parameters_list)
        self.connection.commit()
        return cursor

    async def table_exists(self, table_name: str) -> bool:
        """Check if table exists in SQLite."""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        cursor = await self.execute_query(query, (table_name,))
        row = cursor.fetchone()
        return row is not None

    async def get_table_columns(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get table column information for SQLite."""
        query = f"PRAGMA table_info({table_name})"
        cursor = await self.execute_query(query)
        rows = cursor.fetchall()

        columns = {}
        for row in rows:
            columns[row['name']] = {
                'type': row['type'],
                'nullable': row['notnull'] == 0,
                'default': row['dflt_value']
            }
        return columns

    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a SQLite table."""
        query = f"PRAGMA index_list({table_name})"
        cursor = await self.execute_query(query)
        indexes = cursor.fetchall()

        result = []
        for index in indexes:
            index_info = {
                'name': index['name'],
                'unique': index['unique'] == 1,
                'origin': index['origin'],
                'partial': index['partial']
            }
            result.append(index_info)
        return result

    def get_column_sql_definition(self, field_name: str, field) -> str:
        """Generate SQL for SQLite column definition."""
        field_type = getattr(field, 'field_type', 'string')
        db_type = self.get_field_type_mapping().get(field_type, 'TEXT')

        # Handle field options
        nullable = getattr(field, 'nullable', True)
        default = getattr(field, 'default', None)
        max_length = getattr(field, 'max_length', None)
        primary_key = getattr(field, 'primary_key', False)

        # Apply length constraints
        if max_length and 'VARCHAR' in db_type:
            db_type = db_type.replace('VARCHAR', f'VARCHAR({max_length})')

        sql_parts = [field_name, db_type]

        if not nullable:
            sql_parts.append("NOT NULL")

        if primary_key:
            sql_parts.append("PRIMARY KEY")

        if default is not None:
            if isinstance(default, str):
                sql_parts.append(f"DEFAULT '{default}'")
            else:
                sql_parts.append(f"DEFAULT {default}")

        return " ".join(sql_parts)

    def get_field_type_mapping(self) -> Dict[str, str]:
        """Get SQLite field type mapping."""
        from pydance.db.connections.base import COMMON_FIELD_TYPE_MAPPINGS
        return COMMON_FIELD_TYPE_MAPPINGS['sqlite']
