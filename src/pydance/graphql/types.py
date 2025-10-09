"""
GraphQL types for Pydance.
"""
class GraphQLType:
    def __init__(self, nullable: bool = True):
        self.nullable = nullable

class String(GraphQLType):
    def __init__(self, nullable: bool = True):
        super().__init__(nullable)

class Int(GraphQLType):
    def __init__(self, nullable: bool = True):
        super().__init__(nullable)

class Float(GraphQLType):
    def __init__(self, nullable: bool = True):
        super().__init__(nullable)

class Boolean(GraphQLType):
    def __init__(self, nullable: bool = True):
        super().__init__(nullable)

class ID(GraphQLType):
    def __init__(self, nullable: bool = True):
        super().__init__(nullable)

class GraphQLList(GraphQLType):
    def __init__(self, of_type: GraphQLType, nullable: bool = True):
        super().__init__(nullable)
        self.of_type = of_type

class ObjectType(GraphQLType):
    def __init__(self, name: str, fields: dict, nullable: bool = True):
        super().__init__(nullable)
        self.name = name
        self.fields = fields

class Query(ObjectType):
    def __init__(self, fields: dict):
        super().__init__("Query", fields)

class Mutation(ObjectType):
    def __init__(self, fields: dict):
        super().__init__("Mutation", fields)

class Subscription(ObjectType):
    def __init__(self, fields: dict):
        super().__init__("Subscription", fields)
