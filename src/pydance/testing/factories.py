"""
Model factories for testing.

Provides factory classes for creating test data with realistic values.
"""

from typing import Dict, Any, Optional, Type, List
from datetime import datetime, timedelta
import random


class ModelFactory:
    """
    Base factory class for creating test model instances.

    Provides common functionality for generating test data with
    realistic values and relationships.
    """

    def __init__(self, model_class: Type = None):
        self.model_class = model_class
        self._sequences = {}
        self._defaults = {}

    def set_defaults(self, **defaults):
        """Set default values for factory"""
        self._defaults.update(defaults)
        return self

    def get_next_sequence(self, name: str) -> int:
        """Get next value in a sequence"""
        if name not in self._sequences:
            self._sequences[name] = 1
        value = self._sequences[name]
        self._sequences[name] += 1
        return value

    def reset_sequences(self):
        """Reset all sequences"""
        self._sequences.clear()

    def build(self, **overrides) -> Dict[str, Any]:
        """
        Build a model instance dictionary without saving.

        Args:
            **overrides: Field values to override defaults

        Returns:
            Dictionary representing the model instance
        """
        data = {**self._defaults}

        # Apply field generators
        for field_name, field_config in self._fields.items():
            if field_name not in data:
                if callable(field_config):
                    data[field_name] = field_config()
                else:
                    data[field_name] = field_config

        # Apply overrides
        data.update(overrides)

        return data

    def create(self, **overrides) -> Any:
        """
        Create and save a model instance.

        Args:
            **overrides: Field values to override defaults

        Returns:
            Created model instance
        """
        data = self.build(**overrides)

        if self.model_class:
            # Create actual model instance
            return self.model_class(**data)
        else:
            # Return dictionary for mock testing
            return data


class UserFactory(ModelFactory):
    """
    Factory for creating test users.

    Provides realistic user data generation with proper email formats,
    usernames, and profile information.
    """

    def __init__(self):
        super().__init__()
        self._fields = {
            'username': lambda: f"user{self.get_next_sequence('username')}",
            'email': lambda: f"user{self.get_next_sequence('email')}@example.com",
            'first_name': lambda: self._random_first_name(),
            'last_name': lambda: self._random_last_name(),
            'password': 'password123',
            'is_active': True,
            'created_at': lambda: datetime.now(),
            'updated_at': lambda: datetime.now()
        }

    def _random_first_name(self) -> str:
        """Generate random first name"""
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma',
            'James', 'Lisa', 'Robert', 'Mary', 'William', 'Jennifer',
            'Richard', 'Patricia', 'Charles', 'Linda', 'Thomas', 'Barbara'
        ]
        return random.choice(first_names)

    def _random_last_name(self) -> str:
        """Generate random last name"""
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez',
            'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore'
        ]
        return random.choice(last_names)

    def with_admin_role(self) -> 'UserFactory':
        """Create user with admin role"""
        self._defaults['roles'] = ['admin']
        return self

    def inactive(self) -> 'UserFactory':
        """Create inactive user"""
        self._defaults['is_active'] = False
        return self

    def with_custom_email(self, domain: str = 'test.com') -> 'UserFactory':
        """Create user with custom email domain"""
        def custom_email():
            return f"user{self.get_next_sequence('email')}@{domain}"
        self._fields['email'] = custom_email
        return self


class PostFactory(ModelFactory):
    """
    Factory for creating test posts/blog entries.

    Generates realistic post content with titles, bodies, and metadata.
    """

    def __init__(self):
        super().__init__()
        self._fields = {
            'title': lambda: f"Test Post {self.get_next_sequence('post')}",
            'content': lambda: self._random_content(),
            'author_id': lambda: random.randint(1, 100),
            'published': True,
            'published_at': lambda: datetime.now(),
            'created_at': lambda: datetime.now(),
            'updated_at': lambda: datetime.now()
        }

    def _random_content(self) -> str:
        """Generate random post content"""
        contents = [
            "This is a test post with some content.",
            "Another post with different content for testing purposes.",
            "Yet another post to ensure variety in our test data.",
            "Testing post creation and data generation functionality."
        ]
        return random.choice(contents)

    def draft(self) -> 'PostFactory':
        """Create draft post"""
        self._defaults['published'] = False
        return self

    def with_author(self, author_id: int) -> 'PostFactory':
        """Create post with specific author"""
        self._defaults['author_id'] = author_id
        return self


class CommentFactory(ModelFactory):
    """
    Factory for creating test comments.

    Generates realistic comments for posts with proper relationships.
    """

    def __init__(self):
        super().__init__()
        self._fields = {
            'content': lambda: self._random_comment(),
            'post_id': lambda: random.randint(1, 50),
            'author_id': lambda: random.randint(1, 100),
            'created_at': lambda: datetime.now(),
            'updated_at': lambda: datetime.now()
        }

    def _random_comment(self) -> str:
        """Generate random comment content"""
        comments = [
            "Great post! Thanks for sharing.",
            "This is very helpful information.",
            "I have a question about this topic.",
            "Nice work on this implementation.",
            "This solves a problem I've been having."
        ]
        return random.choice(comments)

    def for_post(self, post_id: int) -> 'CommentFactory':
        """Create comment for specific post"""
        self._defaults['post_id'] = post_id
        return self

    def by_user(self, user_id: int) -> 'CommentFactory':
        """Create comment by specific user"""
        self._defaults['author_id'] = user_id
        return self


class ProductFactory(ModelFactory):
    """
    Factory for creating test products/e-commerce items.

    Generates realistic product data with pricing and categories.
    """

    def __init__(self):
        super().__init__()
        self._fields = {
            'name': lambda: f"Product {self.get_next_sequence('product')}",
            'description': lambda: "A test product for e-commerce testing.",
            'price': lambda: round(random.uniform(10.0, 1000.0), 2),
            'category': lambda: self._random_category(),
            'in_stock': lambda: random.choice([True, False]),
            'stock_quantity': lambda: random.randint(0, 100),
            'created_at': lambda: datetime.now(),
            'updated_at': lambda: datetime.now()
        }

    def _random_category(self) -> str:
        """Generate random product category"""
        categories = [
            'Electronics', 'Clothing', 'Books', 'Home & Garden',
            'Sports & Outdoors', 'Health & Beauty', 'Toys & Games'
        ]
        return random.choice(categories)

    def in_category(self, category: str) -> 'ProductFactory':
        """Create product in specific category"""
        self._defaults['category'] = category
        return self

    def with_price(self, min_price: float, max_price: float) -> 'ProductFactory':
        """Create product with price in range"""
        def price_range():
            return round(random.uniform(min_price, max_price), 2)
        self._fields['price'] = price_range
        return self


# Convenience factory instances
user_factory = UserFactory()
post_factory = PostFactory()
comment_factory = CommentFactory()
product_factory = ProductFactory()


__all__ = [
    'ModelFactory',
    'UserFactory',
    'PostFactory',
    'CommentFactory',
    'ProductFactory',
    'user_factory',
    'post_factory',
    'comment_factory',
    'product_factory'
]
