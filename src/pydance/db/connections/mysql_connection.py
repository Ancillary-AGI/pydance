from typing import List, Dict, Any, AsyncGenerator, Type, Optional, Tuple
import aiomysql
from contextlib import asynccontextmanager
from pydance.db.config import DatabaseConfig
from pydance.db.models.base import Field, StringField, IntegerField, BooleanField, DateTimeField, FieldType
from .base_connection import DatabaseConnection


class MySQLConnection(DatabaseConnection):
    """MySQL database connection"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None

    async def connect(self) -> None:
        """Connect to the database"""
        params = self.config.get_connection_params()
        self.pool = await aiomysql.create_pool(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            db=params['database'],
            autocommit=True
        )

    async def disconnect(self) -> None:
        """Disconnect from the database"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute a SQL query"""
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                return cursor

    async def execute_raw(self, query: str, params: tuple = None) -> Any:
        """Execute a raw query and return cursor for advanced usage (Django-like cursor API)."""
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                return cursor

    async def begin_transaction(self) -> Any:
        """Begin MySQL transaction."""
        async with self.pool.acquire() as connection:
            await connection.begin()
            return connection

    async def commit_transaction(self, transaction: Any) -> None:
        """Commit MySQL transaction."""
        await transaction.commit()

    async def rollback_transaction(self, transaction: Any) -> None:
        """Rollback MySQL transaction."""
        await transaction.rollback()

    async def execute_in_transaction(self, query: str, params: tuple = None) -> Any:
        """Execute MySQL query within transaction context."""
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await connection.begin()
                    if params:
                        await cursor.execute(query, params)
                    else:
                        await cursor.execute(query)
                    await connection.commit()
                    return cursor
                except Exception as e:
                    await connection.rollback()
                    raise e

    async def create_table(self, model_class: Type) -> None:
        """Create a table for the model"""
        fields = []
        for name, field in model_class._fields.items():
            field_def = f"{name} {self.get_sql_type(field)}"
            if field.primary_key:
                field_def += " PRIMARY KEY"
                if field.autoincrement:
                    field_def += " AUTO_INCREMENT"
            if not field.nullable:
                field_def += " NOT NULL"
            if field.default is not None:
                field_def += f" DEFAULT {self._format_default(field.default)}"
            fields.append(field_def)

        query = f"CREATE TABLE IF NOT EXISTS {model_class.get_table_name()} ({', '.join(fields)}) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        await self.execute_query(query)

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Any, None]:
        """Get a database connection context manager"""
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                yield cursor

    async def get_param_placeholder(self, index: int) -> str:
        """Get parameter placeholder for MySQL"""
        return "%s"

    def get_sql_type(self, field: Field) -> str:
        """Get SQL type for a field"""
        if isinstance(field, StringField):
            if field.max_length:
                return f"VARCHAR({field.max_length})"
            return "TEXT"
        elif isinstance(field, IntegerField):
            return "INT"
        elif isinstance(field, BooleanField):
            return "TINYINT(1)"
        elif isinstance(field, DateTimeField):
            return "DATETIME"
        elif field.field_type == FieldType.UUID:
            return "CHAR(36)"
        elif field.field_type == FieldType.JSON:
            return "JSON"
        elif field.field_type == FieldType.FLOAT:
            return "FLOAT"
        return "TEXT"

    async def insert_one(self, model_class: Type, data: Dict[str, Any]) -> Any:
        """Insert a single record"""
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join([self.get_param_placeholder(i+1) for i in range(len(fields))])
        query = f"INSERT INTO {model_class.get_table_name()} ({', '.join(fields)}) VALUES ({placeholders})"

        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, values)
                await connection.commit()
                return cursor.lastrowid

    async def update_one(self, model_class: Type, filters: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update a single record"""
        set_clause = ', '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(data.keys())])
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(len(data) + i + 1)}" for i, k in enumerate(filters.keys())])
        query = f"UPDATE {model_class.get_table_name()} SET {set_clause} WHERE {where_clause}"

        params = tuple(list(data.values()) + list(filters.values()))
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                result = await cursor.execute(query, params)
                await connection.commit()
                return cursor.rowcount > 0

    async def delete_one(self, model_class: Type, filters: Dict[str, Any]) -> bool:
        """Delete a single record"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())])
        query = f"DELETE FROM {model_class.get_table_name()} WHERE {where_clause}"

        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(filters.values()))
                await connection.commit()
                return cursor.rowcount > 0

    async def find_one(self, model_class: Type, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single record"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())])
        query = f"SELECT * FROM {model_class.get_table_name()} WHERE {where_clause} LIMIT 1"

        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(filters.values()))
                result = await cursor.fetchone()
                return dict(result) if result else None

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

        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(filters.values()) if filters else None)
                results = await cursor.fetchall()
                return [dict(row) for row in results]

    async def _create_connection(self) -> Any:
        """Create a new MySQL connection for pooling"""
        import aiomysql
        params = self.config.get_connection_params()
        return await aiomysql.connect(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            db=params['database'],
            autocommit=True
        )

    async def count(self, model_class: Type, filters: Dict[str, Any]) -> int:
        """Count records matching filters"""
        where_clause = ' AND '.join([f"{k} = {self.get_param_placeholder(i+1)}" for i, k in enumerate(filters.keys())]) if filters else ""
        query = f"SELECT COUNT(*) as count FROM {model_class.get_table_name()}"
        if where_clause:
            query += f" WHERE {where_clause}"

        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(filters.values()) if filters else None)
                result = await cursor.fetchone()
                return result['count'] if result else 0

    async def aggregate(self, model_class: Type, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform aggregation operations using MySQL"""
        if not pipeline:
            return []

        results = []
        for stage in pipeline:
            if '$group' in stage:
                results = await self._handle_group_stage(model_class, stage)
            elif '$match' in stage:
                results = await self._handle_match_stage(model_class, stage, results)
            elif '$sort' in stage:
                results = await self._handle_sort_stage(model_class, stage, results)
            elif '$limit' in stage:
                results = await self._handle_limit_stage(model_class, stage, results)
            elif '$skip' in stage:
                results = await self._handle_skip_stage(model_class, stage, results)
            elif '$project' in stage:
                results = await self._handle_project_stage(model_class, stage, results)

        return results

    async def _handle_group_stage(self, model_class: Type, stage: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle $group aggregation stage"""
        group_fields = stage['$group']

        # Build GROUP BY clause
        group_columns = []
        select_parts = []

        for field, expression in group_fields.items():
            if field == '_id':
                # Handle _id field (grouping key)
                if isinstance(expression, str):
                    group_columns.append(expression)
                    select_parts.append(f"{expression} as _id")
                elif isinstance(expression, dict) and '$field' in expression:
                    group_field = expression['$field']
                    group_columns.append(group_field)
                    select_parts.append(f"{group_field} as _id")
                else:
                    # No grouping, aggregate all records
                    select_parts.append("NULL as _id")
            else:
                # Handle aggregation functions
                if isinstance(expression, dict):
                    for agg_func, field_name in expression.items():
                        if agg_func == '$sum':
                            select_parts.append(f"SUM({field_name}) as {field}")
                        elif agg_func == '$avg':
                            select_parts.append(f"AVG({field_name}) as {field}")
                        elif agg_func == '$min':
                            select_parts.append(f"MIN({field_name}) as {field}")
                        elif agg_func == '$max':
                            select_parts.append(f"MAX({field_name}) as {field}")
                        elif agg_func == '$count':
                            select_parts.append(f"COUNT(*) as {field}")
                        elif agg_func == '$first':
                            select_parts.append(f"FIRST_VALUE({field_name}) as {field}")
                        elif agg_func == '$last':
                            select_parts.append(f"LAST_VALUE({field_name}) as {field}")
                        elif agg_func == '$stdDevPop':
                            select_parts.append(f"STDDEV_POP({field_name}) as {field}")
                        elif agg_func == '$stdDevSamp':
                            select_parts.append(f"STDDEV_SAMP({field_name}) as {field}")
                        elif agg_func == '$varPop':
                            select_parts.append(f"VAR_POP({field_name}) as {field}")
                        elif agg_func == '$varSamp':
                            select_parts.append(f"VAR_SAMP({field_name}) as {field}")

        if not select_parts:
            return []

        # Build GROUP BY clause
        group_clause = f"GROUP BY {', '.join(group_columns)}" if group_columns else ""

        # Build complete query
        query = f"SELECT {', '.join(select_parts)} FROM {model_class.get_table_name()} {group_clause}"

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            # Fallback for complex aggregations
            return await self._handle_group_stage_fallback(model_class, stage)

    async def _handle_group_stage_fallback(self, model_class: Type, stage: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback implementation for complex group operations"""
        group_fields = stage['$group']

        # Simple implementation for basic cases
        select_parts = []
        for field, expression in group_fields.items():
            if field == '_id':
                continue
            if isinstance(expression, dict):
                for agg_func, field_name in expression.items():
                    if agg_func == '$sum':
                        select_parts.append(f"SUM({field_name}) as {field}")
                    elif agg_func == '$count':
                        select_parts.append(f"COUNT(*) as {field}")
                    elif agg_func == '$avg':
                        select_parts.append(f"AVG({field_name}) as {field}")

        if select_parts:
            query = f"SELECT {', '.join(select_parts)} FROM {model_class.get_table_name()}"
            async with self.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        return []

    async def _handle_match_stage(self, model_class: Type, stage: Dict[str, Any], current_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle $match aggregation stage"""
        match_conditions = stage['$match']

        # For simplicity, filter in Python if we have current results
        if current_results:
            return self._filter_results(current_results, match_conditions)

        # Otherwise, build SQL WHERE clause
        where_parts = []
        params = []

        for field, condition in match_conditions.items():
            if isinstance(condition, dict):
                for op, value in condition.items():
                    if op == '$eq':
                        where_parts.append(f"{field} = %s")
                        params.append(value)
                    elif op == '$ne':
                        where_parts.append(f"{field} != %s")
                        params.append(value)
                    elif op == '$gt':
                        where_parts.append(f"{field} > %s")
                        params.append(value)
                    elif op == '$gte':
                        where_parts.append(f"{field} >= %s")
                        params.append(value)
                    elif op == '$lt':
                        where_parts.append(f"{field} < %s")
                        params.append(value)
                    elif op == '$lte':
                        where_parts.append(f"{field} <= %s")
                        params.append(value)
                    elif op == '$in':
                        placeholders = ', '.join(['%s'] * len(value))
                        where_parts.append(f"{field} IN ({placeholders})")
                        params.extend(value)
                    elif op == '$regex':
                        where_parts.append(f"{field} LIKE %s")
                        params.append(value.replace('.*', '%'))
            else:
                where_parts.append(f"{field} = %s")
                params.append(condition)

        if where_parts:
            query = f"SELECT * FROM {model_class.get_table_name()} WHERE {' AND '.join(where_parts)}"
            async with self.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        return []

    async def _handle_sort_stage(self, model_class: Type, stage: Dict[str, Any], current_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle $sort aggregation stage"""
        sort_spec = stage['$sort']

        # Sort in Python if we have current results
        if current_results:
            def sort_key(item):
                keys = []
                for field, direction in sort_spec.items():
                    value = item.get(field, 0)
                    keys.append((value, direction))
                return keys

            current_results.sort(key=sort_key)
            return current_results

        # Otherwise, this would need to be handled in the query building
        return current_results

    async def _handle_limit_stage(self, model_class: Type, stage: Dict[str, Any], current_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle $limit aggregation stage"""
        limit = stage['$limit']
        return current_results[:limit] if current_results else []

    async def _handle_skip_stage(self, model_class: Type, stage: Dict[str, Any], current_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle $skip aggregation stage"""
        skip = stage['$skip']
        return current_results[skip:] if current_results else []

    async def _handle_project_stage(self, model_class: Type, stage: Dict[str, Any], current_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle $project aggregation stage"""
        projection = stage['$project']

        if not current_results:
            return []

        result = []
        for item in current_results:
            projected_item = {}
            for field, expression in projection.items():
                if expression == 1 or expression is True:
                    # Include field
                    if field in item:
                        projected_item[field] = item[field]
                elif expression == 0 or expression is False:
                    # Exclude field (already handled by not including)
                    continue
                elif isinstance(expression, dict):
                    # Handle expressions like {'$add': ['$field1', '$field2']}
                    if '$add' in expression:
                        fields = expression['$add']
                        if isinstance(fields, list) and len(fields) == 2:
                            val1 = item.get(fields[0], 0)
                            val2 = item.get(fields[1], 0)
                            projected_item[field] = val1 + val2
                    elif '$subtract' in expression:
                        fields = expression['$subtract']
                        if isinstance(fields, list) and len(fields) == 2:
                            val1 = item.get(fields[0], 0)
                            val2 = item.get(fields[1], 0)
                            projected_item[field] = val1 - val2
                    elif '$multiply' in expression:
                        fields = expression['$multiply']
                        if isinstance(fields, list) and len(fields) == 2:
                            val1 = item.get(fields[0], 0)
                            val2 = item.get(fields[1], 0)
                            projected_item[field] = val1 * val2
                    elif '$divide' in expression:
                        fields = expression['$divide']
                        if isinstance(fields, list) and len(fields) == 2:
                            val1 = item.get(fields[0], 0)
                            val2 = item.get(fields[1], 1)
                            projected_item[field] = val1 / val2 if val2 != 0 else 0
                else:
                    # Literal value
                    projected_item[field] = expression

            result.append(projected_item)

        return result

    def _filter_results(self, results: List[Dict[str, Any]], conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter results in Python"""
        filtered = []
        for item in results:
            match = True
            for field, condition in conditions.items():
                if field not in item:
                    match = False
                    break

                if isinstance(condition, dict):
                    for op, value in condition.items():
                        item_value = item[field]
                        if op == '$eq' and item_value != value:
                            match = False
                            break
                        elif op == '$ne' and item_value == value:
                            match = False
                            break
                        elif op == '$gt' and item_value <= value:
                            match = False
                            break
                        elif op == '$gte' and item_value < value:
                            match = False
                            break
                        elif op == '$lt' and item_value >= value:
                            match = False
                            break
                        elif op == '$lte' and item_value > value:
                            match = False
                            break
                        elif op == '$in' and item_value not in value:
                            match = False
                            break
                        elif op == '$regex':
                            import re
                            if not re.search(value, str(item_value)):
                                match = False
                                break
                else:
                    if item[field] != condition:
                        match = False
                        break

            if match:
                filtered.append(item)

        return filtered

    def _format_default(self, default: Any) -> str:
        """Format default value for MySQL"""
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
        """Create the migrations tracking table for MySQL"""
        query = '''
            CREATE TABLE IF NOT EXISTS migrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                migration_id VARCHAR(255) UNIQUE,
                model_name VARCHAR(255) NOT NULL,
                version INT NOT NULL,
                schema_definition TEXT NOT NULL,
                operations TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, version)
            ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        '''
        await self.execute_query(query)

    async def insert_migration_record(self, model_name: str, version: int, schema_definition: dict, operations: dict, migration_id: str = None) -> None:
        """Insert a migration record for MySQL"""
        import json
        if migration_id:
            query = '''
                INSERT INTO migrations (migration_id, model_name, version, schema_definition, operations)
                VALUES (%s, %s, %s, %s, %s)
            '''
            params = (migration_id, model_name, version, json.dumps(schema_definition), json.dumps(operations))
        else:
            query = '''
                INSERT INTO migrations (model_name, version, schema_definition, operations)
                VALUES (%s, %s, %s, %s)
            '''
            params = (model_name, version, json.dumps(schema_definition), json.dumps(operations))
        await self.execute_query(query, params)

    async def get_applied_migrations(self) -> Dict[str, int]:
        """Get all applied migrations for MySQL"""
        import json
        query = "SELECT model_name, version, schema_definition FROM migrations"
        cursor = await self.execute_query(query)

        migrations = {}
        if hasattr(cursor, 'fetchall'):
            rows = await cursor.fetchall()
        else:
            rows = cursor

        for row in rows:
            migrations[row['model_name']] = row['version']
        return migrations

    async def delete_migration_record(self, model_name: str, version: int) -> None:
        """Delete a migration record for MySQL"""
        query = "DELETE FROM migrations WHERE model_name = %s AND version = %s"
        await self.execute_query(query, (model_name, version))

    async def drop_table(self, table_name: str) -> None:
        """Drop a table for MySQL"""
        query = f"DROP TABLE IF EXISTS {table_name}"
        await self.execute_query(query)

    async def add_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        """Add a column to a table for MySQL"""
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        await self.execute_query(query)

    async def drop_column(self, table_name: str, column_name: str) -> None:
        """Drop a column from a table for MySQL"""
        query = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
        await self.execute_query(query)

    async def modify_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        """Modify a column in a table for MySQL"""
        query = f"ALTER TABLE {table_name} MODIFY COLUMN {column_name} {column_definition}"
        await self.execute_query(query)

    async def create_index(self, table_name: str, index_name: str, columns: List[str]) -> None:
        """Create an index on a table for MySQL"""
        column_list = ', '.join(columns)
        query = f"CREATE INDEX {index_name} ON {table_name} ({column_list}) USING BTREE"
        await self.execute_query(query)

    async def drop_index(self, table_name: str, index_name: str) -> None:
        """Drop an index from a table for MySQL"""
        query = f"DROP INDEX {index_name} ON {table_name}"
        await self.execute_query(query)

    async def add_field(self, model_name: str, field_name: str, field: Field) -> None:
        """Add a field to an existing model/table for MySQL"""
        table_name = model_name.lower() + 's'  # Follow convention
        column_definition = f"{field_name} {self.get_sql_type(field)}"

        if field.primary_key:
            column_definition += " PRIMARY KEY"
            if field.autoincrement:
                column_definition += " AUTO_INCREMENT"

        if not field.nullable:
            column_definition += " NOT NULL"

        if field.default is not None:
            column_definition += f" DEFAULT {self._format_default(field.default)}"

        query = f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"
        await self.execute_query(query)

    async def remove_field(self, model_name: str, field_name: str) -> None:
        """Remove a field from an existing model/table for MySQL"""
        table_name = model_name.lower() + 's'  # Follow convention
        query = f"ALTER TABLE {table_name} DROP COLUMN {field_name}"
        await self.execute_query(query)

    async def alter_field(self, model_name: str, field_name: str, field: Field) -> None:
        """Alter an existing field in a model/table for MySQL"""
        table_name = model_name.lower() + 's'  # Follow convention
        column_definition = self.get_sql_type(field)

        if field.primary_key:
            column_definition += " PRIMARY KEY"
            if field.autoincrement:
                column_definition += " AUTO_INCREMENT"

        if not field.nullable:
            column_definition += " NOT NULL"

        if field.default is not None:
            column_definition += f" DEFAULT {self._format_default(field.default)}"

        query = f"ALTER TABLE {table_name} MODIFY COLUMN {field_name} {column_definition}"
        await self.execute_query(query)

    async def execute_query_builder(self, model_class: Type, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a complex query built by QueryBuilder for MySQL"""
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
                            conditions.append(f"{key} > %s")
                            params.append(val)
                        elif op == '$lt':
                            conditions.append(f"{key} < %s")
                            params.append(val)
                        elif op == '$gte':
                            conditions.append(f"{key} >= %s")
                            params.append(val)
                        elif op == '$lte':
                            conditions.append(f"{key} <= %s")
                            params.append(val)
                        elif op == '$ne':
                            conditions.append(f"{key} != %s")
                            params.append(val)
                        elif op == '$in':
                            placeholders = ', '.join(['%s' for _ in val])
                            conditions.append(f"{key} IN ({placeholders})")
                            params.extend(val)
                        elif op == '$regex':
                            conditions.append(f"{key} LIKE %s")
                            params.append(val.replace('.*', '%'))
                else:
                    conditions.append(f"{key} = %s")
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
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(params))
                results = await cursor.fetchall()
                return [dict(row) for row in results]

    async def test_connection(self) -> bool:
        """Test if MySQL connection is working."""
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"MySQL connection test failed: {e}")
            return False

    async def execute_many(self, query: str, parameters_list: List[Tuple]) -> Any:
        """Execute a query multiple times with different parameters."""
        async with self.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                return await cursor.executemany(query, parameters_list)

    async def table_exists(self, table_name: str) -> bool:
        """Check if table exists in MySQL."""
        query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s)"
        cursor = await self.execute_query(query, (table_name,))
        if hasattr(cursor, 'fetchone'):
            row = await cursor.fetchone()
            return row[0] == 1 if row else False
        return False

    async def get_table_columns(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get table column information for MySQL."""
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        cursor = await self.execute_query(query, (table_name,))
        if hasattr(cursor, 'fetchall'):
            rows = await cursor.fetchall()
        else:
            rows = cursor

        columns = {}
        for row in rows:
            columns[row['column_name']] = {
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES',
                'default': row['column_default']
            }
        return columns

    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a MySQL table."""
        query = """
            SELECT index_name, column_name, non_unique
            FROM information_schema.statistics
            WHERE table_name = %s
            ORDER BY index_name, seq_in_index
        """
        cursor = await self.execute_query(query, (table_name,))
        if hasattr(cursor, 'fetchall'):
            rows = await cursor.fetchall()
        else:
            rows = cursor

        indexes = {}
        for row in rows:
            index_name = row['index_name']
            if index_name not in indexes:
                indexes[index_name] = {
                    'name': index_name,
                    'unique': row['non_unique'] == 0,
                    'columns': []
                }
            indexes[index_name]['columns'].append(row['column_name'])

        return list(indexes.values())

    def get_column_sql_definition(self, field_name: str, field) -> str:
        """Generate SQL for MySQL column definition."""
        field_type = getattr(field, 'field_type', 'string')
        db_type = self.get_field_type_mapping().get(field_type, 'VARCHAR(255)')

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
        """Get MySQL field type mapping."""
        from pydance.db.connections.base import COMMON_FIELD_TYPE_MAPPINGS
        return COMMON_FIELD_TYPE_MAPPINGS['mysql']
