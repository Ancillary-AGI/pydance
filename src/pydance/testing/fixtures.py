"""
Universal Test Fixtures and Factories

Provides framework-agnostic test data factories and fixtures that can be used
with any web framework or application. Completely detached from specific
framework structures.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from abc import ABC, abstractmethod

T = TypeVar('T')


class BaseFactory(ABC, Generic[T]):
    """Abstract base factory class for generating test data."""

    @classmethod
    @abstractmethod
    def _defaults(cls) -> Dict[str, Any]:
        """Return default values for the factory."""
        pass

    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build a single instance."""
        defaults = cls._defaults()
        # Merge defaults with overrides
        return {**defaults, **kwargs}

    @classmethod
    def build_batch(cls, count: int, **kwargs) -> list[Dict[str, Any]]:
        """Build multiple instances."""
        return [cls.build(**kwargs) for _ in range(count)]

    @classmethod
    def create(cls, **kwargs) -> T:
        """
        Create an actual model instance if the framework supports it.
        This is a hook for framework-specific implementations.
        """
        return cls.build(**kwargs)  # Default implementation returns dict


class UserFactory(BaseFactory[Dict[str, Any]]):
    """Generic factory for user test data."""

    @classmethod
    def _defaults(cls) -> Dict[str, Any]:
        return {
            'id': str(uuid.uuid4()),
            'username': f"user_{uuid.uuid4().hex[:8]}",
            'email': f"user_{uuid.uuid4().hex[:8]}@example.com",
            'password': f"password_{uuid.uuid4().hex[:8]}",
            'is_active': True,
            'is_admin': False,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }


class PostFactory(BaseFactory[Dict[str, Any]]):
    """Generic factory for post/blog test data."""

    @classmethod
    def _defaults(cls) -> Dict[str, Any]:
        return {
            'id': str(uuid.uuid4()),
            'title': f"Test Post {uuid.uuid4().hex[:8]}",
            'content': f"This is test content {uuid.uuid4().hex[:20]}",
            'author_id': str(uuid.uuid4()),
            'published': True,
            'tags': ['test', 'sample'],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }


class CommentFactory(BaseFactory[Dict[str, Any]]):
    """Generic factory for comment test data."""

    @classmethod
    def _defaults(cls) -> Dict[str, Any]:
        return {
            'id': str(uuid.uuid4()),
            'content': f"Test comment {uuid.uuid4().hex[:10]}",
            'post_id': str(uuid.uuid4()),
            'author_id': str(uuid.uuid4()),
            'parent_id': None,
            'likes': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }


class ProductFactory(BaseFactory[Dict[str, Any]]):
    """Generic factory for product test data."""

    @classmethod
    def _defaults(cls) -> Dict[str, Any]:
        return {
            'id': str(uuid.uuid4()),
            'name': f"Product {uuid.uuid4().hex[:8]}",
            'description': f"Description for product {uuid.uuid4().hex[:12]}",
            'price': round(uuid.uuid4().int % 1000 + 10, 2),
            'category': 'general',
            'in_stock': True,
            'stock_quantity': uuid.uuid4().int % 100,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }


class OrderFactory(BaseFactory[Dict[str, Any]]):
    """Generic factory for order test data."""

    @classmethod
    def _defaults(cls) -> Dict[str, Any]:
        return {
            'id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4()),
            'total_amount': round(uuid.uuid4().int % 500 + 50, 2),
            'status': 'pending',
            'items': [],
            'shipping_address': {
                'street': f"{uuid.uuid4().int % 1000} Main St",
                'city': 'Test City',
                'state': 'Test State',
                'zip_code': f"{10000 + uuid.uuid4().int % 90000}",
                'country': 'Test Country'
            },
            'created_at': datetime.now(timezone.utc).isoformat(),
        }


# Convenience functions for common entities
def create_user(**kwargs) -> Dict[str, Any]:
    """Create a user instance."""
    return UserFactory.build(**kwargs)


def create_users(count: int, **kwargs) -> list[Dict[str, Any]]:
    """Create multiple user instances."""
    return UserFactory.build_batch(count, **kwargs)


def create_post(**kwargs) -> Dict[str, Any]:
    """Create a post instance."""
    return PostFactory.build(**kwargs)


def create_posts(count: int, **kwargs) -> list[Dict[str, Any]]:
    """Create multiple post instances."""
    return PostFactory.build_batch(count, **kwargs)


def create_comment(**kwargs) -> Dict[str, Any]:
    """Create a comment instance."""
    return CommentFactory.build(**kwargs)


def create_comments(count: int, **kwargs) -> list[Dict[str, Any]]:
    """Create multiple comment instances."""
    return CommentFactory.build_batch(count, **kwargs)


def create_product(**kwargs) -> Dict[str, Any]:
    """Create a product instance."""
    return ProductFactory.build(**kwargs)


def create_products(count: int, **kwargs) -> list[Dict[str, Any]]:
    """Create multiple product instances."""
    return ProductFactory.build_batch(count, **kwargs)


def create_order(**kwargs) -> Dict[str, Any]:
    """Create an order instance."""
    return OrderFactory.build(**kwargs)


def create_orders(count: int, **kwargs) -> list[Dict[str, Any]]:
    """Create multiple order instances."""
    return OrderFactory.build_batch(count, **kwargs)


def create_app(app_factory: Optional[Callable] = None, **kwargs):
    """
    Create a test application instance.

    Args:
        app_factory: Optional factory function to create the app
        **kwargs: Application configuration options

    Returns:
        Application instance
    """
    if app_factory:
        return app_factory(**kwargs)

    # Generic fallback - return a mock app
    mock_app = Mock(name='test_app')

    # Add common ASGI app methods
    async def mock_callable(scope, receive, send):
        # Basic ASGI response
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'application/json']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"message": "Hello from test app"}',
        })

    mock_app.__call__ = mock_callable
    return mock_app


def database_session(session_factory: Optional[Callable] = None):
    """
    Create a test database session.

    Args:
        session_factory: Optional factory function to create the session

    Returns:
        Database session instance
    """
    if session_factory:
        return session_factory()

    # Generic fallback - return a mock session
    return Mock(name='database_session')


def create_factory(model_name: str, defaults: Dict[str, Any]) -> type:
    """
    Dynamically create a factory class for any model.

    Args:
        model_name: Name of the model (used for class name)
        defaults: Default values for the factory

    Returns:
        Factory class
    """
    class DynamicFactory(BaseFactory[Dict[str, Any]]):
        _model_defaults = defaults.copy()

        @classmethod
        def _defaults(cls) -> Dict[str, Any]:
            return cls._model_defaults.copy()

    DynamicFactory.__name__ = f"{model_name}Factory"
    return DynamicFactory


__all__ = [
    'BaseFactory',
    'UserFactory',
    'PostFactory',
    'CommentFactory',
    'ProductFactory',
    'OrderFactory',
    'create_user',
    'create_users',
    'create_post',
    'create_posts',
    'create_comment',
    'create_comments',
    'create_product',
    'create_products',
    'create_order',
    'create_orders',
    'create_app',
    'database_session',
    'create_factory',
]
