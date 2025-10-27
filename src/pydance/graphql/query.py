"""
GraphQL Query and Mutation handling for Pydance framework.
"""

from typing import Dict, Any, Optional, Callable
from .schema import GraphQLType, Field, ObjectType


class GraphQLQuery:
    """GraphQL query handler"""

    def __init__(self, query_type: ObjectType):
        self.query_type = query_type

    def resolve(self, field_name: str, **kwargs) -> Any:
        """Resolve a query field"""
        field = self.query_type.get_field(field_name)
        if field and field.resolver:
            return field.resolver(**kwargs)
        return None


class GraphQLMutation:
    """GraphQL mutation handler"""

    def __init__(self, mutation_type: ObjectType):
        self.mutation_type = mutation_type

    def resolve(self, field_name: str, **kwargs) -> Any:
        """Resolve a mutation field"""
        field = self.mutation_type.get_field(field_name)
        if field and field.resolver:
            return field.resolver(**kwargs)
        return None


class GraphQLSubscription:
    """GraphQL subscription handler"""

    def __init__(self, subscription_type: ObjectType):
        self.subscription_type = subscription_type

    def resolve(self, field_name: str, **kwargs) -> Any:
        """Resolve a subscription field"""
        field = self.subscription_type.get_field(field_name)
        if field and field.resolver:
            return field.resolver(**kwargs)
        return None


__all__ = [
    'GraphQLQuery',
    'GraphQLMutation',
    'GraphQLSubscription'
]
