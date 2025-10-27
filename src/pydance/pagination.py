"""
Pagination utilities for Pydance API framework.
Provides various pagination strategies for API responses.
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class Pagination:
    """Base pagination class"""

    def __init__(self, page_size: int = 10):
        self.page_size = page_size

    def paginate_queryset(self, queryset, request) -> List[Any]:
        """Paginate a queryset"""
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', self.page_size))

        if isinstance(queryset, list):
            start = (page - 1) * page_size
            end = start + page_size
            return queryset[start:end]

        return []


class PageNumberPagination(Pagination):
    """Page number-based pagination"""

    def __init__(self, page_size: int = 10):
        super().__init__(page_size)

    def paginate_queryset(self, queryset, request) -> List[Any]:
        """Paginate using page numbers"""
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', self.page_size))

        if isinstance(queryset, list):
            start = (page - 1) * page_size
            end = start + page_size
            return queryset[start:end]

        return []

    def get_paginated_response(self, data: List[Any], request) -> Dict[str, Any]:
        """Get paginated response data"""
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', self.page_size))

        if isinstance(data, list):
            total_count = len(data) * (page // len(data) + 1) if data else 0
        else:
            total_count = 0

        return {
            'results': data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }


class LimitOffsetPagination(Pagination):
    """Limit-offset pagination"""

    def __init__(self, default_limit: int = 10, max_limit: int = 100):
        super().__init__(default_limit)
        self.max_limit = max_limit

    def paginate_queryset(self, queryset, request) -> List[Any]:
        """Paginate using limit and offset"""
        limit = int(request.query_params.get('limit', self.page_size))
        offset = int(request.query_params.get('offset', 0))

        # Enforce maximum limit
        limit = min(limit, self.max_limit)

        if isinstance(queryset, list):
            return queryset[offset:offset + limit]

        return []

    def get_paginated_response(self, data: List[Any], request) -> Dict[str, Any]:
        """Get paginated response data"""
        limit = int(request.query_params.get('limit', self.page_size))
        offset = int(request.query_params.get('offset', 0))

        if isinstance(data, list):
            total_count = len(data) + offset
        else:
            total_count = 0

        return {
            'results': data,
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'next_offset': offset + limit if offset + limit < total_count else None,
            'previous_offset': offset - limit if offset > 0 else None
        }


class CursorPagination(Pagination):
    """Cursor-based pagination"""

    def __init__(self, page_size: int = 10, ordering: str = '-id'):
        super().__init__(page_size)
        self.ordering = ordering

    def paginate_queryset(self, queryset, request) -> List[Any]:
        """Paginate using cursors"""
        cursor = request.query_params.get('cursor')

        if isinstance(queryset, list):
            # Simple cursor implementation - in practice, this would use
            # database cursors or encoded position markers
            if cursor:
                try:
                    cursor_index = int(cursor)
                    start = cursor_index
                    end = start + self.page_size
                    return queryset[start:end]
                except ValueError:
                    pass

            # Default to first page
            return queryset[:self.page_size]

        return []

    def get_paginated_response(self, data: List[Any], request) -> Dict[str, Any]:
        """Get paginated response data"""
        cursor = request.query_params.get('cursor')

        if isinstance(data, list):
            total_count = len(data) * 2  # Estimate for demo purposes

            # Generate next cursor
            next_cursor = None
            if cursor:
                try:
                    current_index = int(cursor)
                    next_cursor = str(current_index + len(data))
                except ValueError:
                    next_cursor = str(len(data))
            else:
                next_cursor = str(len(data))

            return {
                'results': data,
                'cursor': cursor or '0',
                'next_cursor': next_cursor,
                'previous_cursor': cursor if cursor and int(cursor) > 0 else None,
                'count': len(data)
            }

        return {'results': data}


# Global pagination instances
page_number_pagination = PageNumberPagination()
limit_offset_pagination = LimitOffsetPagination()
cursor_pagination = CursorPagination()

__all__ = [
    'Pagination', 'PageNumberPagination', 'LimitOffsetPagination', 'CursorPagination',
    'page_number_pagination', 'limit_offset_pagination', 'cursor_pagination'
]
