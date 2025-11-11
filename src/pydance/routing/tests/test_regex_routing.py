"""
Tests for advanced regex routing functionality in Pydance.

Tests the enhanced route parameter constraints that go beyond Laravel/Django.
"""

import pytest
from pydance.routing.route import Route
from pydance.routing.constraints import get_route_constraints, register_constraint
from pydance.routing.router import Router


class TestAdvancedRegexRouting:
    """Test advanced regex routing features."""

    def test_basic_regex_constraints(self):
        """Test basic regex constraints like Laravel/Django."""
        route = Route('/users/{id}', lambda: None)
        route.where('id', r'[0-9]+')

        # Should match numeric IDs
        assert route.match('/users/123', 'GET') == {'id': '123'}
        assert route.match('/users/abc', 'GET') is None

    def test_named_constraints(self):
        """Test named constraints like 'numeric', 'alpha', etc."""
        route = Route('/users/{id}', lambda: None)
        route.where('id', 'numeric')

        # Should match numeric IDs
        assert route.match('/users/123', 'GET') == {'id': '123'}
        assert route.match('/users/abc', 'GET') is None

    def test_inline_named_constraints(self):
        """Test inline named constraints in route path."""
        route = Route('/users/{id:numeric}', lambda: None)

        # Should match numeric IDs
        assert route.match('/users/123', 'GET') == {'id': '123'}
        assert route.match('/users/abc', 'GET') is None

    def test_multiple_named_constraints(self):
        """Test multiple named constraints on different parameters."""
        route = Route('/users/{id}/posts/{slug}', lambda: None)
        route.where({'id': 'numeric', 'slug': 'slug'})

        # Should match valid patterns
        assert route.match('/users/123/posts/my-post-title', 'GET') == {
            'id': '123',
            'slug': 'my-post-title'
        }
        assert route.match('/users/abc/posts/my-post-title', 'GET') is None
        assert route.match('/users/123/posts/My Post Title', 'GET') is None

    def test_uuid_constraint(self):
        """Test UUID constraint."""
        route = Route('/users/{uuid}', lambda: None)
        route.where('uuid', 'uuid')

        valid_uuid = '550e8400-e29b-41d4-a716-446655440000'
        assert route.match(f'/users/{valid_uuid}', 'GET') == {'uuid': valid_uuid}
        assert route.match('/users/invalid-uuid', 'GET') is None

    def test_email_constraint(self):
        """Test email constraint."""
        route = Route('/users/{email}', lambda: None)
        route.where('email', 'email')

        assert route.match('/users/user@example.com', 'GET') == {'email': 'user@example.com'}
        assert route.match('/users/invalid-email', 'GET') is None

    def test_alpha_numeric_constraint(self):
        """Test alpha_numeric constraint."""
        route = Route('/users/{username}', lambda: None)
        route.where('username', 'alpha_numeric')

        assert route.match('/users/user123', 'GET') == {'username': 'user123'}
        assert route.match('/users/user-123', 'GET') is None  # Contains dash

    def test_parameterized_constraints(self):
        """Test parameterized constraints like min:3, max:10."""
        route = Route('/users/{name}', lambda: None)
        route.where('name', 'min:3')

        assert route.match('/users/john', 'GET') == {'name': 'john'}
        assert route.match('/users/ab', 'GET') is None  # Too short

    def test_between_constraint(self):
        """Test between constraint for length limits."""
        route = Route('/users/{name}', lambda: None)
        route.where('name', 'between:2,5')

        assert route.match('/users/john', 'GET') == {'name': 'john'}
        assert route.match('/users/a', 'GET') is None  # Too short
        assert route.match('/users/alexander', 'GET') is None  # Too long

    def test_custom_constraint_registration(self):
        """Test registering custom constraints."""
        # Register a custom constraint
        register_constraint('hex_color_short', r'#[0-9a-fA-F]{3}', 'Invalid hex color')

        route = Route('/colors/{color}', lambda: None)
        route.where('color', 'hex_color_short')

        assert route.match('/colors/#f00', 'GET') == {'color': '#f00'}
        assert route.match('/colors/#ff0000', 'GET') is None  # Too long for short format

    def test_constraint_combination_or(self):
        """Test combining constraints with OR logic."""
        constraints = get_route_constraints()
        combined = constraints.combine('numeric', 'alpha')

        route = Route('/items/{code}', lambda: None)
        route.where('code', combined)

        assert route.match('/items/123', 'GET') == {'code': '123'}
        assert route.match('/items/abc', 'GET') == {'code': 'abc'}
        assert route.match('/items/abc123', 'GET') is None  # Doesn't match either

    def test_constraint_chaining_and(self):
        """Test chaining constraints with AND logic."""
        constraints = get_route_constraints()
        chained = constraints.chain('alpha', 'min:3', 'max:10')

        route = Route('/names/{name}', lambda: None)
        route.where('name', chained)

        assert route.match('/names/john', 'GET') == {'name': 'john'}
        assert route.match('/names/ab', 'GET') is None  # Too short
        assert route.match('/names/alexanderlongname', 'GET') is None  # Too long
        assert route.match('/names/john123', 'GET') is None  # Contains numbers

    def test_file_extension_constraints(self):
        """Test file extension constraints."""
        route = Route('/files/{filename}', lambda: None)
        route.where('filename', 'image')

        assert route.match('/files/photo.jpg', 'GET') == {'filename': 'photo.jpg'}
        assert route.match('/files/document.pdf', 'GET') is None

    def test_phone_constraint(self):
        """Test phone number constraint."""
        route = Route('/contacts/{phone}', lambda: None)
        route.where('phone', 'phone')

        assert route.match('/contacts/+1234567890', 'GET') == {'phone': '+1234567890'}
        assert route.match('/contacts/123-456-7890', 'GET') == {'phone': '123-456-7890'}
        assert route.match('/contacts/invalid', 'GET') is None

    def test_postal_code_constraint(self):
        """Test postal code constraint."""
        route = Route('/addresses/{zip}', lambda: None)
        route.where('zip', 'postal_code')

        assert route.match('/addresses/12345', 'GET') == {'zip': '12345'}
        assert route.match('/addresses/12345-6789', 'GET') == {'zip': '12345-6789'}
        assert route.match('/addresses/abcde', 'GET') is None

    def test_date_constraint(self):
        """Test date constraint."""
        route = Route('/events/{date}', lambda: None)
        route.where('date', 'date')

        assert route.match('/events/2023-12-25', 'GET') == {'date': '2023-12-25'}
        assert route.match('/events/2023/12/25', 'GET') is None

    def test_url_constraint(self):
        """Test URL constraint."""
        route = Route('/links/{url}', lambda: None)
        route.where('url', 'url')

        assert route.match('/links/https://example.com', 'GET') == {'url': 'https://example.com'}
        assert route.match('/links/ftp://example.com', 'GET') is None

    def test_inline_regex_patterns(self):
        """Test inline regex patterns in route definitions."""
        route = Route('/users/{id:[0-9]+}', lambda: None)

        assert route.match('/users/123', 'GET') == {'id': '123'}
        assert route.match('/users/abc', 'GET') is None

    def test_complex_route_patterns(self):
        """Test complex route patterns with multiple constraints."""
        route = Route('/api/v1/users/{id:numeric}/posts/{slug:slug}/comments/{comment_id:numeric}', lambda: None)

        assert route.match('/api/v1/users/123/posts/my-awesome-post/comments/456', 'GET') == {
            'id': '123',
            'slug': 'my-awesome-post',
            'comment_id': '456'
        }

        # Test invalid patterns
        assert route.match('/api/v1/users/abc/posts/my-awesome-post/comments/456', 'GET') is None
        assert route.match('/api/v1/users/123/posts/My Awesome Post/comments/456', 'GET') is None
        assert route.match('/api/v1/users/123/posts/my-awesome-post/comments/abc', 'GET') is None

    def test_router_integration(self):
        """Test that advanced constraints work with the router."""
        router = Router()

        def handler(): pass

        # Add route with named constraints
        route = router.add_route('/users/{id:numeric}/posts/{slug:slug}', handler)

        # Test matching
        match = router.match('GET', '/users/123/posts/my-post')
        assert match is not None
        assert match.params == {'id': '123', 'slug': 'my-post'}

        # Test non-matching
        no_match = router.match('GET', '/users/abc/posts/my-post')
        assert no_match is None

    def test_constraint_validation(self):
        """Test constraint validation with error messages."""
        constraints = get_route_constraints()

        # Test valid constraints
        is_valid, error = constraints.validate('numeric', '123')
        assert is_valid is True
        assert error is None

        # Test invalid constraints
        is_valid, error = constraints.validate('numeric', 'abc')
        assert is_valid is False
        assert error == 'Parameter does not match numeric constraint'

        # Test unknown constraint
        is_valid, error = constraints.validate('unknown_constraint', 'value')
        assert is_valid is False
        assert error == 'Unknown constraint: unknown_constraint'

    def test_list_available_constraints(self):
        """Test listing available constraints."""
        constraints = get_route_constraints()
        available = constraints.list_constraints()

        assert 'numeric' in available
        assert 'alpha' in available
        assert 'email' in available
        assert 'uuid' in available

        assert available['numeric'] == 'Only digits (0-9)'
        assert available['email'] == 'Email address format'


class TestTypedParameters:
    """Test existing typed parameter functionality is preserved."""

    def test_int_type_parameters(self):
        """Test that {id:int} syntax still works for type conversion."""
        route = Route('/users/{id:int}', lambda: None)

        # Should match and convert to int
        result = route.match('/users/123', 'GET')
        assert result == {'id': 123}
        assert isinstance(result['id'], int)

        # Should not match non-numeric
        assert route.match('/users/abc', 'GET') is None

    def test_float_type_parameters(self):
        """Test that {price:float} syntax works for type conversion."""
        route = Route('/products/{price:float}', lambda: None)

        # Should match and convert to float
        result = route.match('/products/29.99', 'GET')
        assert result == {'price': 29.99}
        assert isinstance(result['price'], float)

        # Should not match non-numeric
        assert route.match('/products/abc', 'GET') is None

    def test_bool_type_parameters(self):
        """Test that {active:bool} syntax works for type conversion."""
        route = Route('/users/{id:int}/active/{active:bool}', lambda: None)

        # Should match and convert to bool
        result = route.match('/users/123/active/true', 'GET')
        assert result == {'id': 123, 'active': True}
        assert isinstance(result['id'], int)
        assert isinstance(result['active'], bool)

        # Test different boolean representations
        result2 = route.match('/users/456/active/1', 'GET')
        assert result2 == {'id': 456, 'active': True}

        result3 = route.match('/users/789/active/false', 'GET')
        assert result3 == {'id': 789, 'active': False}

    def test_mixed_typed_and_named_constraints(self):
        """Test mixing typed parameters with named constraints."""
        route = Route('/api/v1/users/{id:int}/posts/{slug:slug}', lambda: None)

        # Should work with both type conversion and constraints
        result = route.match('/api/v1/users/123/posts/my-awesome-post', 'GET')
        assert result == {'id': 123, 'slug': 'my-awesome-post'}
        assert isinstance(result['id'], int)
        assert isinstance(result['slug'], str)

        # Should fail if constraints not met
        assert route.match('/api/v1/users/123/posts/My Invalid Slug', 'GET') is None
        assert route.match('/api/v1/users/abc/posts/my-awesome-post', 'GET') is None


class TestProtectedRoutes:
    """Test protected routes functionality."""

    def test_auth_middleware_protection(self):
        """Test that auth middleware protects routes."""
        from pydance.auth.middleware import AuthMiddleware

        router = Router()
        middleware = AuthMiddleware()

        def protected_handler(): pass
        def public_handler(): pass

        # Add protected route with auth middleware
        router.add_route('/protected', protected_handler, middleware=[middleware])

        # Add public route without middleware
        router.add_route('/public', public_handler)

        # Both routes should be registered
        protected_match = router.match('GET', '/protected')
        public_match = router.match('GET', '/public')

        assert protected_match is not None
        assert public_match is not None

        # The middleware would be executed during request processing
        # (this is tested in integration tests)

    def test_admin_middleware_protection(self):
        """Test admin middleware protection."""
        from pydance.auth.middleware import AdminAuthMiddleware

        router = Router()
        middleware = AdminAuthMiddleware()

        def admin_handler(): pass

        # Add admin-only route
        router.add_route('/admin', admin_handler, middleware=[middleware])

        # Route should be registered
        match = router.match('GET', '/admin')
        assert match is not None

    def test_route_groups_with_middleware(self):
        """Test route groups with middleware."""
        from pydance.auth.middleware import AuthMiddleware

        router = Router()
        auth_middleware = AuthMiddleware()

        def user_handler(): pass
        def profile_handler(): pass

        # Create route group with auth middleware
        group = router.group('/api', middleware=[auth_middleware])

        group.add_route('/users', user_handler)
        group.add_route('/profile', profile_handler)

        # Routes should be registered with middleware
        users_match = router.match('GET', '/api/users')
        profile_match = router.match('GET', '/api/profile')

        assert users_match is not None
        assert profile_match is not None

        # Middleware should be applied
        assert len(users_match.middleware) > 0
        assert len(profile_match.middleware) > 0
