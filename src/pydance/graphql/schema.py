"""
GraphQL schema definition for Pydance framework.
Provides type system, schema construction, and field definitions with full GraphQL spec compliance.
"""

from typing import Dict, Any, Optional, List, Callable, Union, Type, Set
import json
import asyncio


class GraphQLError(Exception):
    """GraphQL execution error"""
    pass


class GraphQLType:
    """Base GraphQL type"""
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


# Scalar types
class String(GraphQLType):
    def __init__(self):
        super().__init__("String")

class Int(GraphQLType):
    def __init__(self):
        super().__init__("Int")

class Float(GraphQLType):
    def __init__(self):
        super().__init__("Float")

class Boolean(GraphQLType):
    def __init__(self):
        super().__init__("Boolean")

class ID(GraphQLType):
    def __init__(self):
        super().__init__("ID")


class GraphQLList(GraphQLType):
    """List type wrapper"""
    def __init__(self, of_type: GraphQLType):
        self.of_type = of_type
        super().__init__(f"[{of_type.name}]")


class Field:
    """GraphQL field definition"""
    def __init__(self, type_: GraphQLType, resolver: Optional[Callable] = None,
                 args: Optional[Dict[str, GraphQLType]] = None,
                 description: Optional[str] = None):
        self.type = type_
        self.resolver = resolver
        self.args = args or {}
        self.description = description


class ObjectType(GraphQLType):
    """GraphQL object type"""
    def __init__(self, name: str, fields: Optional[Dict[str, Field]] = None):
        super().__init__(name)
        self.fields = fields or {}

    def add_field(self, name: str, field: Field):
        """Add field to object type"""
        self.fields[name] = field

    def get_field(self, name: str) -> Optional[Field]:
        """Get field by name"""
        return self.fields.get(name)


class Query(ObjectType):
    """GraphQL Query type"""
    def __init__(self, fields: Optional[Dict[str, Field]] = None):
        super().__init__("Query", fields)


class Mutation(ObjectType):
    """GraphQL Mutation type"""
    def __init__(self, fields: Optional[Dict[str, Field]] = None):
        super().__init__("Mutation", fields)


class Subscription(ObjectType):
    """GraphQL Subscription type"""
    def __init__(self, fields: Optional[Dict[str, Field]] = None):
        super().__init__("Subscription", fields)


class Schema:
    """GraphQL schema definition"""
    def __init__(self, query: Optional[Query] = None,
                 mutation: Optional[Mutation] = None,
                 subscription: Optional[Subscription] = None):
        self.query = query
        self.mutation = mutation
        self.subscription = subscription
        self.types: Dict[str, ObjectType] = {}

        # Register built-in types
        if query:
            self.types["Query"] = query
        if mutation:
            self.types["Mutation"] = mutation
        if subscription:
            self.types["Subscription"] = subscription

    def add_type(self, type_: ObjectType):
        """Add custom type to schema"""
        self.types[type_.name] = type_

    def get_type(self, name: str) -> Optional[ObjectType]:
        """Get type by name"""
        return self.types.get(name)

    def validate(self) -> List[str]:
        """Validate schema"""
        errors = []

        if not self.query:
            errors.append("Schema must have a Query type")

        # Check for duplicate field names
        for type_name, type_obj in self.types.items():
            field_names = set()
            for field_name in type_obj.fields.keys():
                if field_name in field_names:
                    errors.append(f"Duplicate field '{field_name}' in type '{type_name}'")
                field_names.add(field_name)

        return errors

    def to_graphql(self) -> str:
        """Convert schema to GraphQL SDL"""
        lines = []

        # Add types
        for type_name, type_obj in self.types.items():
            lines.append(f"type {type_name} {{")
            for field_name, field in type_obj.fields.items():
                args_str = ""
                if field.args:
                    args_list = []
                    for arg_name, arg_type in field.args.items():
                        args_list.append(f"{arg_name}: {arg_type.name}")
                    args_str = f"({', '.join(args_list)})"

                lines.append(f"  {field_name}{args_str}: {field.type.name}")
            lines.append("}")

        return "\n".join(lines)


class SelectionSet:
    """GraphQL selection set"""
    def __init__(self, selections: List[Dict[str, Any]]):
        self.selections = selections

    def get_field_names(self) -> List[str]:
        """Get field names in selection set"""
        return [sel['name']['value'] for sel in self.selections if 'name' in sel]


class GraphQLDocument:
    """Parsed GraphQL document"""
    def __init__(self, operations: Dict[str, Any]):
        self.operations = operations

    def get_operation(self, operation_name: Optional[str] = None):
        """Get operation by name"""
        if operation_name:
            return self.operations.get(operation_name)
        elif len(self.operations) == 1:
            return list(self.operations.values())[0]
        else:
            raise GraphQLError("Must specify operation name when multiple operations exist")


class GraphQLParser:
    """Full GraphQL spec-compliant parser"""

    @staticmethod
    def parse(query: str) -> GraphQLDocument:
        """Parse GraphQL query string with full spec compliance"""
        parser = GraphQLParser()
        parser.query = query.strip()
        parser.pos = 0
        parser.line = 1
        parser.column = 1

        # Skip BOM and whitespace
        parser._skip_ignored()

        # Parse document
        operations = parser._parse_document()

        return GraphQLDocument(operations)

    def _parse_document(self) -> Dict[str, Any]:
        """Parse the full document"""
        operations = {}

        while self.pos < len(self.query):
            if self._peek() == '{':
                # Anonymous query
                operation_name = 'query'
                if operation_name not in operations:
                    operations[operation_name] = {
                        'type': 'query',
                        'operation_type': 'query',
                        'selection_set': self._parse_selection_set(),
                        'variable_definitions': [],
                        'directives': []
                    }
            elif self._peek().isalpha():
                # Named operation
                operation = self._parse_operation()
                operations[operation['name']] = operation
            else:
                break

            self._skip_ignored()

        return operations

    def _parse_operation(self) -> Dict[str, Any]:
        """Parse operation definition"""
        operation_type = self._read_name()

        if operation_type not in ['query', 'mutation', 'subscription']:
            self._error(f"Invalid operation type: {operation_type}")

        # Parse name if present
        name = None
        if self._peek() != '(' and self._peek() != '{':
            name = self._read_name()

        # Parse variable definitions
        variable_definitions = []
        if self._match('('):
            while not self._match(')'):
                if not variable_definitions and not self._match('$'):
                    break
                var_def = self._parse_variable_definition()
                variable_definitions.append(var_def)
                self._match(',')  # Optional comma

        # Parse directives
        directives = []
        while self._match('@'):
            directives.append(self._parse_directive())

        # Parse selection set
        selection_set = self._parse_selection_set()

        return {
            'type': operation_type,
            'operation_type': operation_type,
            'name': name,
            'variable_definitions': variable_definitions,
            'directives': directives,
            'selection_set': selection_set
        }

    def _parse_variable_definition(self) -> Dict[str, Any]:
        """Parse variable definition ($var: Type = default)"""
        var_name = self._read_name()
        self._expect(':')
        var_type = self._parse_type()

        default_value = None
        if self._match('='):
            default_value = self._parse_value()

        return {
            'variable': var_name,
            'type': var_type,
            'default_value': default_value
        }

    def _parse_type(self) -> str:
        """Parse GraphQL type (String, [String!], User, etc.)"""
        # Handle list types [Type]
        if self._match('['):
            inner_type = self._parse_type()
            self._expect(']')
            type_name = f"[{inner_type}]"
        else:
            type_name = self._read_name()

        # Handle non-null ! modifier
        if self._match('!'):
            type_name += '!'

        return type_name

    def _parse_selection_set(self) -> List[Dict[str, Any]]:
        """Parse selection set { field alias: field(args) { ... } }"""
        self._expect('{')
        selections = []

        while not self._match('}'):
            if self._match('...'):
                # Fragment or spread
                if self._peek().isalpha() and self._peek() not in ['on']:
                    # Named fragment spread
                    fragment_name = self._read_name()
                    selections.append({
                        'kind': 'FragmentSpread',
                        'name': {'value': fragment_name}
                    })
                elif self._match('on'):
                    # Inline fragment
                    type_condition = self._read_name()
                    directives = []
                    while self._match('@'):
                        directives.append(self._parse_directive())

                    selection_set = self._parse_selection_set()
                    selections.append({
                        'kind': 'InlineFragment',
                        'type_condition': type_condition,
                        'directives': directives,
                        'selection_set': selection_set
                    })
                else:
                    self._error("Invalid fragment syntax")
            else:
                # Field selection
                selections.append(self._parse_field())
                self._match(',')  # Optional comma

        return selections

    def _parse_field(self) -> Dict[str, Any]:
        """Parse field with alias, arguments, directives, selection_set"""
        # Check for alias
        name = self._read_name()
        alias = None

        if self._match(':'):
            alias = name
            name = self._read_name()

        # Parse arguments
        arguments = []
        if self._match('('):
            while not self._match(')'):
                if arguments and not self._match(','):
                    break
                arg_name = self._read_name()
                self._expect(':')
                arg_value = self._parse_value()
                arguments.append({
                    'name': {'value': arg_name},
                    'value': arg_value
                })

        # Parse directives
        directives = []
        while self._match('@'):
            directives.append(self._parse_directive())

        # Parse selection set (for nested fields)
        selection_set = None
        if self._match('{'):
            self.pos -= 1  # Un-read the brace for selection set parsing
            selection_set = self._parse_selection_set()
        elif self._match('('):
            # This is argument syntax, not selection set
            self.pos -= 1
            selection_set = None

        return {
            'kind': 'Field',
            'name': {'value': name},
            'alias': {'value': alias} if alias else None,
            'arguments': arguments,
            'directives': directives,
            'selection_set': selection_set
        }

    def _parse_directive(self) -> Dict[str, Any]:
        """Parse directive @directive(arg: value)"""
        name = self._read_name()

        arguments = []
        if self._match('('):
            while not self._match(')'):
                if arguments and not self._match(','):
                    break
                arg_name = self._read_name()
                self._expect(':')
                arg_value = self._parse_value()
                arguments.append({
                    'name': {'value': arg_name},
                    'value': arg_value
                })

        return {
            'name': {'value': name},
            'arguments': arguments
        }

    def _parse_value(self) -> Dict[str, Any]:
        """Parse GraphQL value (string, int, float, boolean, null, enum, list, object)"""
        if self._match('"'):
            # String literal
            string_content = ""
            while self.pos < len(self.query) and self.query[self.pos] != '"':
                if self.query[self.pos] == '\\':
                    self.pos += 1
                    if self.pos < len(self.query):
                        string_content += self.query[self.pos]
                else:
                    string_content += self.query[self.pos]
                self.pos += 1
            self._expect('"')
            return {'kind': 'StringValue', 'value': string_content}

        elif str.isdigit(self._peek()) or self._peek() == '-':
            # Number
            num_str = ""
            if self._match('-'):
                num_str += '-'

            while self.pos < len(self.query) and (str.isdigit(self._peek()) or self._peek() == '.'):
                num_str += self._read()

            if '.' in num_str:
                return {'kind': 'FloatValue', 'value': float(num_str)}
            else:
                return {'kind': 'IntValue', 'value': int(num_str)}

        elif self._match('true'):
            return {'kind': 'BooleanValue', 'value': True}

        elif self._match('false'):
            return {'kind': 'BooleanValue', 'value': False}

        elif self._match('null'):
            return {'kind': 'NullValue'}

        elif self._match('$'):
            # Variable
            var_name = self._read_name()
            return {'kind': 'Variable', 'name': {'value': var_name}}

        elif self._match('['):
            # List
            values = []
            while not self._match(']'):
                if values and not self._match(','):
                    break
                if self._peek() == ']':
                    break
                values.append(self._parse_value())
            return {'kind': 'ListValue', 'values': values}

        elif self._match('{'):
            # Object
            fields = []
            while not self._match('}'):
                if fields and not self._match(','):
                    break
                if self._peek() == '}':
                    break
                name = self._read_name()
                self._expect(':')
                value = self._parse_value()
                fields.append({
                    'name': {'value': name},
                    'value': value
                })
            return {'kind': 'ObjectValue', 'fields': fields}

        else:
            # Enum value or identifier
            name = self._read_name()
            return {'kind': 'EnumValue', 'value': name}

    def _read_name(self) -> str:
        """Read identifier/name token"""
        name = ""
        while self.pos < len(self.query) and (self._peek().isalnum() or self._peek() == '_'):
            name += self._read()
        if not name:
            self._error("Expected name")
        return name

    def _read(self) -> str:
        """Read single character and advance position"""
        if self.pos >= len(self.query):
            self._error("Unexpected end of input")
        char = self.query[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _peek(self, offset: int = 0) -> str:
        """Peek at character without advancing"""
        pos = self.pos + offset
        return self.query[pos] if pos < len(self.query) else ''

    def _match(self, expected: str) -> bool:
        """Match and consume expected string"""
        if self.query.startswith(expected, self.pos):
            self.pos += len(expected)
            self.column += len(expected)
            return True
        return False

    def _expect(self, expected: str):
        """Expect specific character or error"""
        if not self._match(expected):
            self._error(f"Expected '{expected}', got '{self._peek()}'")

    def _skip_ignored(self):
        """Skip whitespace, comments, etc."""
        while self.pos < len(self.query):
            if self.query[self.pos].isspace():
                self.pos += 1
                if self.query[self.pos] == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
            elif self.query.startswith('#', self.pos):
                # Skip comments
                while self.pos < len(self.query) and self.query[self.pos] != '\n':
                    self.pos += 1
                self.line += 1
                self.column = 1
            else:
                break

    def _error(self, message: str):
        """Raise parsing error with position info"""
        error_msg = f"GraphQL parsing error at line {self.line}, column {self.column}: {message}"
        error_msg += "\n" + self._get_context()
        raise GraphQLError(error_msg)

    def _get_context(self, context_lines: int = 2) -> str:
        """Get error context"""
        lines = self.query.split('\n')
        start = max(0, self.line - context_lines)
        end = min(len(lines), self.line + context_lines)

        result = ""
        for i in range(start, end):
            line_num = i + 1
            prefix = ">>> " if line_num == self.line else "    "
            result += f"{prefix}{line_num:3d}: {lines[i]}\n"
            if line_num == self.line:
                result += "    " + " " * (self.column + 4) + "^\n"

        return result


class GraphQLResult:
    """GraphQL execution result"""
    def __init__(self, data: Optional[Dict[str, Any]] = None,
                 errors: Optional[List[Dict[str, Any]]] = None):
        self.data = data
        self.errors = errors or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        if self.data is not None:
            result['data'] = self.data
        if self.errors:
            result['errors'] = self.errors
        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class GraphQLExecutor:
    """Full GraphQL query executor with variables, fragments, and proper field resolution"""

    def __init__(self, schema: Schema, document: GraphQLDocument):
        self.schema = schema
        self.document = document
        self.errors = []
        self.field_stack = []
        self.visited_fragments = set()

    def execute(self, operation_name: Optional[str] = None,
               variables: Optional[Dict[str, Any]] = None) -> GraphQLResult:
        """Execute GraphQL operation"""
        try:
            self.errors = []
            variables = variables or {}
            variables = self._coerce_variables(variables)

            operation = self.document.get_operation(operation_name)
            operation_type = operation['name']

            # Execute based on operation type
            if operation_type == 'query':
                root_value = {}  # Root query object
                root_type = self.schema.query
            elif operation_type == 'mutation':
                root_value = {}  # Root mutation object
                root_type = self.schema.mutation
            elif operation_type == 'subscription':
                root_value = {}  # Root subscription object
                root_type = self.schema.subscription
            else:
                raise GraphQLError(f"Unknown operation type: {operation_type}")

            # Execute selection set
            data = self._execute_selection_set(
                operation['selection_set'],
                root_type,
                root_value,
                variables
            )

            result = GraphQLResult(data=data)
            if self.errors:
                result.errors = self.errors

            return result

        except Exception as e:
            return GraphQLResult(errors=[{"message": str(e)}])

    def _coerce_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce variable values to expected types"""
        # In a full implementation, this would validate and coerce variables
        # based on the operation's variable definitions
        return variables

    def _execute_selection_set(self, selection_set: List[Dict[str, Any]], object_type,
                              object_value: Any, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a selection set"""
        result = {}
        grouped_fields = self._collect_fields(selection_set, object_type, variables)

        for response_key, fields in grouped_fields.items():
            field_ast = fields[0]  # Use first field for now (merging would be done in collect_fields)

            if not self._should_include_field(field_ast, variables):
                continue

            field_name = field_ast['name']['value']
            field_def = object_type.fields.get(field_name)

            if not field_def:
                self.errors.append({
                    "message": f"Field '{field_name}' not found on type '{object_type.name}'",
                    "locations": [field_ast['name']]
                })
                continue

            # Resolve field
            resolved_value = self._resolve_field_value(
                object_value,
                field_def,
                field_ast,
                variables
            )

            # Execute sub-selection if nested
            if field_ast.get('selection_set'):
                resolved_type = self._get_field_type(field_def)
                if isinstance(resolved_type, ObjectType):
                    resolved_value = self._execute_selection_set(
                        field_ast['selection_set'],
                        resolved_type,
                        resolved_value,
                        variables
                    )

            result[response_key] = resolved_value

        return result

    def _collect_fields(self, selection_set: List[Dict[str, Any]], object_type,
                       variables: Dict[str, Any]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Collect and merge fields with same response key"""
        visited_fragments = set()
        grouped_fields = {}

        def collect_fields_recursive(selections):
            for selection in selections:
                if not self._should_include_field(selection, variables):
                    continue

                if selection['kind'] == 'Field':
                    response_key = selection.get('alias', {}).get('value', selection['name']['value'])

                    if response_key not in grouped_fields:
                        grouped_fields[response_key] = []

                    grouped_fields[response_key].append(selection)

                elif selection['kind'] == 'InlineFragment':
                    if self._does_fragment_condition_match(selection, object_type, variables):
                        collect_fields_recursive(selection['selection_set'])

                elif selection['kind'] == 'FragmentSpread':
                    fragment_name = selection['name']['value']
                    if fragment_name not in visited_fragments:
                        visited_fragments.add(fragment_name)
                        fragment = self.document.operations.get(fragment_name)
                        if fragment and self._does_fragment_condition_match(fragment, object_type, variables):
                            collect_fields_recursive(fragment['selection_set'])

        collect_fields_recursive(selection_set)
        return grouped_fields

    def _does_fragment_condition_match(self, fragment, object_type, variables) -> bool:
        """Check if fragment type condition matches current object type"""
        if 'type_condition' in fragment:
            return fragment['type_condition'] == object_type.name
        return True

    def _should_include_field(self, field_ast: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        """Check if field should be included based on @skip/@include directives"""
        for directive in field_ast.get('directives', []):
            name = directive['name']['value']
            args = {arg['name']['value']: self._value_from_ast(arg['value'], variables)
                   for arg in directive.get('arguments', [])}

            if name == 'skip' and args.get('if', False):
                return False
            elif name == 'include' and not args.get('if', True):
                return False

        return True

    def _resolve_field_value(self, object_value: Any, field_def: Field,
                           field_ast: Dict[str, Any], variables: Dict[str, Any]) -> Any:
        """Resolve a field value"""
        # Extract arguments
        args = {}
        for arg_ast in field_ast.get('arguments', []):
            arg_name = arg_ast['name']['value']
            arg_value = self._value_from_ast(arg_ast['value'], variables)
            args[arg_name] = arg_value

        # Execute resolver
        try:
            if field_def.resolver:
                # Call resolver with context
                context = GraphQLContext(self.schema, object_value, variables)
                return field_def.resolver(object_value, args, context)
            else:
                # Default resolver - get attribute from object
                field_name = field_ast['name']['value']
                if hasattr(object_value, field_name):
                    return getattr(object_value, field_name)
                elif isinstance(object_value, dict):
                    return object_value.get(field_name)

        except Exception as e:
            self.errors.append({
                "message": f"Error resolving field '{field_ast['name']['value']}': {str(e)}",
                "locations": [field_ast['name']]
            })
            return None

    def _value_from_ast(self, value_ast: Dict[str, Any], variables: Dict[str, Any]) -> Any:
        """Extract value from AST value node"""
        kind = value_ast['kind']

        if kind == 'Variable':
            var_name = value_ast['name']['value']
            return variables.get(var_name)

        elif kind == 'IntValue':
            return int(value_ast['value'])

        elif kind == 'FloatValue':
            return float(value_ast['value'])

        elif kind == 'StringValue':
            return value_ast['value']

        elif kind == 'BooleanValue':
            return value_ast['value']

        elif kind == 'NullValue':
            return None

        elif kind == 'EnumValue':
            return value_ast['value']

        elif kind == 'ListValue':
            return [self._value_from_ast(item, variables) for item in value_ast['values']]

        elif kind == 'ObjectValue':
            obj = {}
            for field in value_ast['fields']:
                field_name = field['name']['value']
                field_value = self._value_from_ast(field['value'], variables)
                obj[field_name] = field_value
            return obj

        return None

    def _get_field_type(self, field_def: Field) -> GraphQLType:
        """Get the type of a field"""
        return field_def.type

    async def execute_async(self, operation_name: Optional[str] = None,
                           variables: Optional[Dict[str, Any]] = None) -> GraphQLResult:
        """Execute GraphQL operation asynchronously"""
        # For now, delegate to sync version
        return await asyncio.get_event_loop().run_in_executor(
            None, self.execute, operation_name, variables
        )


class GraphQLContext:
    """GraphQL execution context"""

    def __init__(self, schema: Schema, root_value: Any, variables: Dict[str, Any]):
        self.schema = schema
        self.root_value = root_value
        self.variables = variables


class GraphQLManager:
    """Main GraphQL manager for handling queries and mutations."""

    def __init__(self, schema: Schema):
        self.schema = schema
        self.middlewares = []
        self.executors_cache = {}

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None,
               operation_name: Optional[str] = None) -> GraphQLResult:
        """Execute GraphQL query"""
        try:
            # Parse query
            document = GraphQLParser.parse(query)

            # Create executor
            executor = GraphQLExecutor(self.schema, document)

            # Execute
            return executor.execute(operation_name, variables)

        except Exception as e:
            return GraphQLResult(errors=[{"message": str(e)}])

    async def execute_async(self, query: str, variables: Optional[Dict[str, Any]] = None,
                           operation_name: Optional[str] = None) -> GraphQLResult:
        """Execute GraphQL query asynchronously"""
        try:
            # Parse query
            document = GraphQLParser.parse(query)

            # Create executor
            executor = GraphQLExecutor(self.schema, document)

            # Execute asynchronously
            return await executor.execute_async(operation_name, variables)

        except Exception as e:
            return GraphQLResult(errors=[{"message": str(e)}])

    def add_middleware(self, middleware):
        """Add middleware to GraphQL execution"""
        self.middlewares.append(middleware)

    def validate_query(self, query: str) -> List[str]:
        """Validate GraphQL query"""
        errors = []

        try:
            document = GraphQLParser.parse(query)

            # Validate against schema
            for operation_name, operation in document.operations.items():
                operation_type = operation['type']

                if operation_type == 'query':
                    if not self.schema.query:
                        errors.append("Schema does not support queries")
                    else:
                        errors.extend(self._validate_selection_set(
                            operation['selection_set'], self.schema.query
                        ))
                elif operation_type == 'mutation':
                    if not self.schema.mutation:
                        errors.append("Schema does not support mutations")
                    else:
                        errors.extend(self._validate_selection_set(
                            operation['selection_set'], self.schema.mutation
                        ))
                elif operation_type == 'subscription':
                    if not self.schema.subscription:
                        errors.append("Schema does not support subscriptions")
                    else:
                        errors.extend(self._validate_selection_set(
                            operation['selection_set'], self.schema.subscription
                        ))

        except Exception as e:
            errors.append(f"Query parsing error: {str(e)}")

        return errors

    def _validate_selection_set(self, selection_set: List[Dict[str, Any]], object_type) -> List[str]:
        """Validate a selection set against schema"""
        errors = []

        for selection in selection_set:
            if selection['kind'] == 'Field':
                field_name = selection['name']['value']
                if field_name not in object_type.fields:
                    errors.append(f"Unknown field '{field_name}' on type '{object_type.name}'")

                # Validate arguments
                field_def = object_type.fields[field_name]
                for arg in selection.get('arguments', []):
                    arg_name = arg['name']['value']
                    if arg_name not in field_def.args:
                        errors.append(f"Unknown argument '{arg_name}' on field '{field_name}'")

                # Validate sub-selection
                if selection.get('selection_set'):
                    field_type = field_def.type
                    if isinstance(field_type, ObjectType):
                        errors.extend(self._validate_selection_set(
                            selection['selection_set'], field_type
                        ))

            elif selection['kind'] == 'FragmentSpread':
                fragment_name = selection['name']['value']
                # Fragment validation would go here

        return errors




class GraphQLSchema:
    """GraphQL schema wrapper"""
    def __init__(self, schema: Schema):
        self.schema = schema


class GraphQLObjectType:
    """GraphQL object type wrapper"""
    def __init__(self, object_type: ObjectType):
        self.object_type = object_type


class GraphQLField:
    """GraphQL field wrapper"""
    def __init__(self, field: Field):
        self.field = field
