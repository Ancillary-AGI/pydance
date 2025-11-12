from typing import List, Dict, Any, AsyncGenerator, Type, Optional, Tuple
from pymongo import ASCENDING, DESCENDING


class MongoDBConnection(DatabaseConnection):
    """MongoDB database backend implementation."""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.client = None
        self.db = None

    async def connect(self) -> None:
        """Connect to the database"""
        params = self.config.get_connection_params()
        self.client = AsyncIOMotorClient(
            host=params['host'],
            port=params['port'],
            username=params['username'],
            password=params['password'],
            authSource=params['authSource']
        )
        self.db = self.client[self.config.database]

    async def disconnect(self) -> None:
        """Disconnect from the database"""
        if self.client:
            self.client.close()

    async def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute a query (not applicable for MongoDB - placeholder)"""
        # MongoDB doesn't use SQL queries, so this is a no-op
        return None

    async def execute_raw(self, query: str, params: tuple = None) -> Any:
        """Execute a raw MongoDB command and return results for advanced usage."""
        # For MongoDB, we can execute raw commands or return collection cursor
        if hasattr(self, 'db') and self.db:
            if params and isinstance(params, dict):
                return await self.db.command(query, **params)
            else:
                return await self.db.command(query)
        return None

    async def begin_transaction(self) -> Any:
        """Begin MongoDB transaction."""
        if hasattr(self, 'client') and self.client:
            return await self.client.start_session()

    async def commit_transaction(self, transaction: Any) -> None:
        """Commit MongoDB transaction."""
        await transaction.commit_transaction()

    async def rollback_transaction(self, transaction: Any) -> None:
        """Rollback MongoDB transaction."""
        await transaction.abort_transaction()

    async def execute_in_transaction(self, query: str, params: tuple = None) -> Any:
        """Execute MongoDB command within transaction context."""
        if hasattr(self, 'client') and self.client:
            async with await self.client.start_session() as session:
                async with session.start_transaction():
                    try:
                        if params and isinstance(params, dict):
                            result = await self.db.command(query, **params, session=session)
                        else:
                            result = await self.db.command(query, session=session)
                        return result
                    except Exception as e:
                        await session.abort_transaction()
                        raise e

    async def create_table(self, model_class: Type) -> None:
        """Create indexes for the model (MongoDB collections are created automatically)"""
        collection = self.db[model_class.get_table_name()]

        # Create indexes based on field definitions
        indexes = []
        for name, field in model_class._fields.items():
            if field.index or field.primary_key:
                indexes.append((name, ASCENDING))
            if field.unique and not field.primary_key:
                await collection.create_index([(name, ASCENDING)], unique=True)

        # Create compound index for primary keys if multiple
        if indexes:
            await collection.create_index(indexes)

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Any, None]:
        """Get a database connection context manager"""
        if not self.db:
            await self.connect()
        try:
            yield self.db
        finally:
            pass

    async def get_param_placeholder(self, index: int) -> str:
        """Get parameter placeholder (not applicable for MongoDB)"""
        return ""

    def get_sql_type(self, field: Field) -> str:
        """Get SQL type (not applicable for MongoDB)"""
        return ""

    async def insert_one(self, model_class: Type, data: Dict[str, Any]) -> Any:
        """Insert a single document"""
        collection = self.db[model_class.get_table_name()]

        # Convert data to MongoDB format
        mongo_data = self._convert_to_mongo(data)

        result = await collection.insert_one(mongo_data)
        return str(result.inserted_id)

    async def update_one(self, model_class: Type, filters: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update a single document"""
        collection = self.db[model_class.get_table_name()]

        # Convert filters and data to MongoDB format
        mongo_filters = self._convert_to_mongo(filters)
        mongo_data = self._convert_to_mongo(data)

        result = await collection.update_one(mongo_filters, {"$set": mongo_data})
        return result.modified_count > 0

    async def delete_one(self, model_class: Type, filters: Dict[str, Any]) -> bool:
        """Delete a single document"""
        collection = self.db[model_class.get_table_name()]

        # Convert filters to MongoDB format
        mongo_filters = self._convert_to_mongo(filters)

        result = await collection.delete_one(mongo_filters)
        return result.deleted_count > 0

    async def find_one(self, model_class: Type, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        collection = self.db[model_class.get_table_name()]

        # Convert filters to MongoDB format
        mongo_filters = self._convert_to_mongo(filters)

        result = await collection.find_one(mongo_filters)
        if result:
            # Convert ObjectId to string and return
            result['_id'] = str(result['_id'])
            return result
        return None

    async def find_many(self, model_class: Type, filters: Dict[str, Any], limit: Optional[int] = None,
                       offset: Optional[int] = None, sort: Optional[List[Tuple[str, int]]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        collection = self.db[model_class.get_table_name()]

        # Convert filters to MongoDB format
        mongo_filters = self._convert_to_mongo(filters)

        # Build query
        query = collection.find(mongo_filters)

        # Add sorting
        if sort:
            mongo_sort = [(field, ASCENDING if direction == 1 else DESCENDING) for field, direction in sort]
            query = query.sort(mongo_sort)

        # Add pagination
        if offset:
            query = query.skip(offset)
        if limit:
            query = query.limit(limit)

        results = await query.to_list(length=None)

        # Convert ObjectIds to strings
        for result in results:
            if '_id' in result:
                result['_id'] = str(result['_id'])

        return results

    async def count(self, model_class: Type, filters: Dict[str, Any]) -> int:
        """Count documents matching filters"""
        collection = self.db[model_class.get_table_name()]

        # Convert filters to MongoDB format
        mongo_filters = self._convert_to_mongo(filters)

        return await collection.count_documents(mongo_filters)

    async def aggregate(self, model_class: Type, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform aggregation operations using MongoDB"""
        collection = self.db[model_class.get_table_name()]

        # MongoDB aggregation pipeline can be used directly
        results = await collection.aggregate(pipeline).to_list(length=None)

        # Convert ObjectIds to strings
        for result in results:
            if '_id' in result and isinstance(result['_id'], ObjectId):
                result['_id'] = str(result['_id'])

        return results

    def _convert_to_mongo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data to MongoDB format"""
        mongo_data = {}

        for key, value in data.items():
            if key == 'id' and isinstance(value, str):
                # Convert string ID to ObjectId for MongoDB
                try:
                    mongo_data['_id'] = ObjectId(value)
                except:
                    mongo_data['_id'] = value
            elif key == 'id':
                mongo_data['_id'] = value
            else:
                mongo_data[key] = value

        return mongo_data

    async def _create_connection(self) -> Any:
        """Create a new MongoDB connection for pooling"""
        params = self.config.get_connection_params()
        return AsyncIOMotorClient(
            host=params['host'],
            port=params['port'],
            username=params['username'],
            password=params['password'],
            authSource=params['authSource']
        )

    async def get_collection(self, model_class: Type) -> Any:
        """Get the collection for a model"""
        return self.db[model_class.get_table_name()]

    async def create_index(self, model_class: Type) -> None:
        """Create indexes for the model"""
        collection = await self.get_collection(model_class)
        indexes = []
        for name, field in model_class._fields.items():
            if field.primary_key:
                indexes.append((name, ASCENDING))

        for field_name, direction in indexes:
            await collection.create_index([(field_name, direction)])

    async def create_migrations_table(self) -> None:
        """Create the migrations tracking collection for MongoDB"""
        # MongoDB creates collections automatically on first insert
        # We can create an index for efficient querying
        migrations_collection = self.db.migrations
        await migrations_collection.create_index([("model_name", 1), ("version", 1)], unique=True)

    async def insert_migration_record(self, model_name: str, version: int, schema_definition: dict, operations: dict, migration_id: str = None) -> None:
        """Insert a migration record for MongoDB"""
        migrations_collection = self.db.migrations
        migration_doc = {
            'model_name': model_name,
            'version': version,
            'schema_definition': schema_definition,
            'operations': operations,
            'applied_at': datetime.now()
        }
        if migration_id:
            migration_doc['migration_id'] = migration_id
        await migrations_collection.insert_one(migration_doc)

    async def get_applied_migrations(self) -> Dict[str, int]:
        """Get all applied migrations for MongoDB"""
        migrations_collection = self.db.migrations
        migrations = {}

        async for doc in migrations_collection.find({}):
            migrations[doc['model_name']] = doc['version']

        return migrations

    async def delete_migration_record(self, model_name: str, version: int) -> None:
        """Delete a migration record for MongoDB"""
        migrations_collection = self.db.migrations
        await migrations_collection.delete_one({"model_name": model_name, "version": version})

    async def drop_table(self, table_name: str) -> None:
        """Drop a collection for MongoDB"""
        await self.db[table_name].drop()

    async def add_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        """Add a field to documents for MongoDB (no-op - MongoDB is schemaless)"""
        # MongoDB is schemaless, so adding a column is a no-op
        # Fields are added dynamically when documents are inserted
        pass

    async def drop_column(self, table_name: str, column_name: str) -> None:
        """Remove a field from all documents for MongoDB"""
        collection = self.db[table_name]
        # Use $unset to remove the field from all documents
        await collection.update_many({}, {"$unset": {column_name: ""}})

    async def modify_column(self, table_name: str, column_name: str, column_definition: str) -> None:
        """Modify a field in documents for MongoDB"""
        collection = self.db[table_name]

        # Parse the column definition to understand the new field type
        # This is a basic implementation - in practice, you'd need more sophisticated parsing
        try:
            # Extract field type from definition (simplified parsing)
            parts = column_definition.strip().split()
            if len(parts) >= 2:
                field_type = parts[1].upper()

                # Handle common type conversions
                if field_type in ['VARCHAR', 'TEXT', 'CHAR']:
                    # Convert to string
                    await collection.update_many(
                        {column_name: {"$exists": True}},
                        [{"$set": {column_name: {"$toString": f"${column_name}"}}}]
                    )
                elif field_type in ['INT', 'INTEGER', 'BIGINT']:
                    # Convert to integer
                    await collection.update_many(
                        {column_name: {"$exists": True}},
                        [{"$set": {column_name: {"$toInt": f"${column_name}"}}}]
                    )
                elif field_type in ['FLOAT', 'DOUBLE', 'DECIMAL']:
                    # Convert to double
                    await collection.update_many(
                        {column_name: {"$exists": True}},
                        [{"$set": {column_name: {"$toDouble": f"${column_name}"}}}]
                    )
                elif field_type == 'BOOLEAN':
                    # Convert to boolean
                    await collection.update_many(
                        {column_name: {"$exists": True}},
                        [{"$set": {column_name: {"$toBool": f"${column_name}"}}}]
                    )
                elif field_type == 'DATE':
                    # Convert to date
                    await collection.update_many(
                        {column_name: {"$exists": True}},
                        [{"$set": {column_name: {"$toDate": f"${column_name}"}}}]
                    )

        except Exception as e:
            # If conversion fails, log warning but don't fail the operation
            print(f"Warning: Field modification partially failed for {table_name}.{column_name}: {e}")

    async def create_index(self, table_name: str, index_name: str, columns: List[str]) -> None:
        """Create an index on a collection for MongoDB"""
        collection = self.db[table_name]
        # MongoDB doesn't use named indexes in the same way, but we can create compound indexes
        index_spec = [(col, ASCENDING) for col in columns]
        await collection.create_index(index_spec, name=index_name)

    async def drop_index(self, table_name: str, index_name: str) -> None:
        """Drop an index from a collection for MongoDB"""
        collection = self.db[table_name]
        await collection.drop_index(index_name)

    async def execute_query_builder(self, model_class: Type, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a complex query built by QueryBuilder for MongoDB"""
        collection = self.db[model_class.get_table_name()]

        # Extract query parameters
        select_fields = query_params.get('select_fields', [])
        distinct = query_params.get('distinct', False)
        filters = query_params.get('filters', {})
        limit = query_params.get('limit')
        offset = query_params.get('offset')
        order_by = query_params.get('order_by', [])
        group_by = query_params.get('group_by', [])
        having = query_params.get('having', [])

        # Convert filters to MongoDB format
        mongo_filters = self._convert_filters_to_mongo(filters)

        # Build projection (SELECT fields)
        projection = None
        if select_fields:
            projection = {field: 1 for field in select_fields}
            # Add _id if not explicitly excluded
            if '_id' not in projection and '_id' not in [f for f in select_fields if f.startswith('-')]:
                projection['_id'] = 1

        # Build sort specification
        sort_spec = None
        if order_by:
            sort_spec = [(field, ASCENDING if direction == 1 else DESCENDING) for field, direction in order_by]

        # Build aggregation pipeline if needed
        if group_by or having or distinct:
            pipeline = []

            # Add $match stage for filters
            if mongo_filters:
                pipeline.append({"$match": mongo_filters})

            # Add $group stage for GROUP BY
            if group_by:
                group_spec = {"_id": {field: f"${field}" for field in group_by}}
                # Add accumulators for HAVING-like conditions
                if having:
                    # Parse HAVING conditions and add appropriate accumulators
                    for condition in having:
                        self._add_having_accumulators(group_spec, condition)
                pipeline.append({"$group": group_spec})

            # Add $sort stage
            if sort_spec:
                sort_dict = {field: direction for field, direction in sort_spec}
                pipeline.append({"$sort": sort_dict})

            # Add $skip and $limit stages
            if offset:
                pipeline.append({"$skip": offset})
            if limit:
                pipeline.append({"$limit": limit})

            # Execute aggregation
            results = await collection.aggregate(pipeline).to_list(length=None)

        else:
            # Simple find query
            query = collection.find(mongo_filters, projection)

            if sort_spec:
                query = query.sort(sort_spec)

            if offset:
                query = query.skip(offset)

            if limit:
                query = query.limit(limit)

            results = await query.to_list(length=None)

        # Convert ObjectIds to strings
        for result in results:
            if '_id' in result and isinstance(result['_id'], ObjectId):
                result['_id'] = str(result['_id'])

        return results

    def _convert_filters_to_mongo(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert query filters to MongoDB format"""
        mongo_filters = {}

        for key, value in filters.items():
            if isinstance(value, dict):
                # Handle MongoDB-style operators
                mongo_filters[key] = value
            else:
                mongo_filters[key] = value

        return mongo_filters

    async def add_field(self, model_name: str, field_name: str, field: Field) -> None:
        """Add a field to documents for MongoDB (no-op - MongoDB is schemaless)"""
        # MongoDB is schemaless, so adding a field is a no-op
        # Fields are added dynamically when documents are inserted
        pass

    async def remove_field(self, model_name: str, field_name: str) -> None:
        """Remove a field from all documents for MongoDB"""
        collection = self.db[model_name.lower() + 's']  # Follow convention
        # Use $unset to remove the field from all documents
        await collection.update_many({}, {"$unset": {field_name: ""}})

    async def alter_field(self, model_name: str, field_name: str, field: Field) -> None:
        """Alter a field in documents for MongoDB"""
        collection = self.db[model_name.lower() + 's']  # Follow convention

        # For MongoDB, field alterations are limited but we can handle some cases
        # This is a basic implementation - in practice, you'd need more sophisticated parsing
        try:
            # Get field type information
            field_type = getattr(field, 'field_type', 'string')

            # Handle common field type changes
            if field_type == 'string':
                # Convert to string
                await collection.update_many(
                    {field_name: {"$exists": True}},
                    [{"$set": {field_name: {"$toString": f"${field_name}"}}}]
                )
            elif field_type == 'integer':
                # Convert to integer
                await collection.update_many(
                    {field_name: {"$exists": True}},
                    [{"$set": {field_name: {"$toInt": f"${field_name}"}}}]
                )
            elif field_type == 'float':
                # Convert to double
                await collection.update_many(
                    {field_name: {"$exists": True}},
                    [{"$set": {field_name: {"$toDouble": f"${field_name}"}}}]
                )
            elif field_type == 'boolean':
                # Convert to boolean
                await collection.update_many(
                    {field_name: {"$exists": True}},
                    [{"$set": {field_name: {"$toBool": f"${field_name}"}}}]
                )

        except Exception as e:
            # If conversion fails, log warning but don't fail the operation
            print(f"Warning: Field alteration partially failed for {model_name}.{field_name}: {e}")

    async def test_connection(self) -> bool:
        """Test if MongoDB connection is working."""
        try:
            # Ping the database
            ping_result = await self.db.command('ping')
            return ping_result.get('ok') == 1
        except Exception as e:
            self.logger.error(f"MongoDB connection test failed: {e}")
            return False

    async def execute_many(self, query: str, parameters_list: List[Tuple]) -> Any:
        """Execute a query multiple times (not applicable for MongoDB)."""
        # MongoDB doesn't use SQL queries, so this is a no-op
        return None

    async def table_exists(self, table_name: str) -> bool:
        """Check if collection exists in MongoDB."""
        collections = await self.db.list_collection_names()
        return table_name in collections

    async def get_table_columns(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get collection field information for MongoDB (MongoDB is schemaless)."""
        # MongoDB is schemaless, so we return an empty dict
        # In practice, you might analyze a sample document to infer schema
        return {}

    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a MongoDB collection."""
        collection = self.db[table_name]
        indexes = await collection.list_indexes().to_list(length=None)

        result = []
        for index in indexes:
            index_info = {
                'name': index.get('name', ''),
                'key': index.get('key', {}),
                'unique': index.get('unique', False)
            }
            result.append(index_info)
        return result

    def get_column_sql_definition(self, field_name: str, field) -> str:
        """Generate SQL for column definition (not applicable for MongoDB)."""
        # MongoDB is schemaless, so this returns empty string
        return ""

    def get_field_type_mapping(self) -> Dict[str, str]:
        """Get MongoDB field type mapping (not applicable for MongoDB)."""
        # MongoDB is schemaless, so we return empty dict
        return {}

    def _add_having_accumulators(self, group_spec: Dict[str, Any], condition: str) -> None:
        """Add accumulators for HAVING conditions in MongoDB aggregation"""
        # Parse simple HAVING conditions and add appropriate accumulators
        # This is a simplified implementation - in practice, you'd need more sophisticated parsing

        # Handle common patterns like "SUM(amount) > 100" or "COUNT(*) > 5"
        import re

        # Pattern for SUM(field) > value
        sum_pattern = r'SUM\((\w+)\)\s*([><=]+)\s*(\d+)'
        match = re.search(sum_pattern, condition)
        if match:
            field, operator, value = match.groups()
            accumulator_name = f"{field}_sum"
            group_spec[accumulator_name] = {"$sum": f"${field}"}

            # Add a $match stage after $group to filter by the condition
            # This would need to be handled in the calling method

        # Pattern for COUNT(*) > value
        count_pattern = r'COUNT\(\*\)\s*([><=]+)\s*(\d+)'
        match = re.search(count_pattern, condition)
        if match:
            operator, value = match.groups()
            group_spec['count'] = {"$sum": 1}

        # Pattern for AVG(field) > value
        avg_pattern = r'AVG\((\w+)\)\s*([><=]+)\s*([\d.]+)'
        match = re.search(avg_pattern, condition)
        if match:
            field, operator, value = match.groups()
            accumulator_name = f"{field}_avg"
            group_spec[accumulator_name] = {"$avg": f"${field}"}
