"""
GraphQL middleware for Pydance framework.
"""

from typing import Dict, Any, Optional


class GraphQLMiddleware(HTTPMiddleware):
    """GraphQL middleware for handling GraphQL requests"""

    def __init__(self, graphql_manager, endpoint: str = "/graphql"):
        super().__init__("GraphQLMiddleware")
        self.graphql_manager = graphql_manager
        self.endpoint = endpoint

    async def process_request(self, request: Request) -> Request:
        """Process GraphQL requests"""
        if request.path == self.endpoint and request.method == "POST":
            # Mark request as GraphQL
            request.is_graphql = True
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process GraphQL responses"""
        return response


__all__ = ['GraphQLMiddleware']
