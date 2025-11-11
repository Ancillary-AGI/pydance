# Advanced Regex Routing in Pydance

Pydance provides powerful regex-based route parameter constraints that go beyond Laravel and Django, offering more flexibility and advanced features.

## Features

- **Named Constraints**: Pre-defined patterns like `numeric`, `alpha`, `uuid`, `email`, etc.
- **Inline Constraints**: Define constraints directly in route paths
- **Custom Constraints**: Register your own reusable constraint patterns
- **Parameterized Constraints**: Constraints with parameters like `min:3`, `max:10`
- **Constraint Composition**: Combine constraints with OR/AND logic
- **Advanced Patterns**: Support for complex regex patterns

## Basic Usage

### Named Constraints

```python
from pydance.routing import Router

router = Router()

# Using named constraints
@router.route('/users/{id}', methods=['GET'])
def get_user(request, id):
    return f"User {id}"

# Add constraint after route definition
router.routes[-1].where('id', 'numeric')

# Or define constraint inline
@router.route('/users/{id:numeric}', methods=['GET'])
def get_user_inline(request, id):
    return f"User {id}"
```

### Available Named Constraints

| Constraint | Pattern | Example |
|------------|---------|---------|
| `numeric` | `[0-9]+` | `123`, `456789` |
| `alpha` | `[a-zA-Z]+` | `hello`, `WORLD` |
| `alpha_numeric` | `[a-zA-Z0-9]+` | `user123`, `ABCdef` |
| `alpha_dash` | `[a-zA-Z0-9_-]+` | `user-name_123` |
| `slug` | `[a-z0-9-]+` | `my-awesome-post` |
| `uuid` | UUID v4 format | `550e8400-e29b-41d4-a716-446655440000` |
| `email` | Email format | `user@example.com` |
| `url` | URL format | `https://example.com` |
| `date` | YYYY-MM-DD | `2023-12-25` |
| `time` | HH:MM(:SS) | `14:30:00` |
| `phone` | Phone number | `+1-555-123-4567` |
| `postal_code` | ZIP/Postal | `12345` or `12345-6789` |
| `ip` | IP address | `192.168.1.1` |
| `hex_color` | Hex color | `#ff0000`, `#f00` |

### Parameterized Constraints

```python
# Length constraints
route.where('name', 'min:3')      # Minimum 3 characters
route.where('code', 'max:10')     # Maximum 10 characters
route.where('zip', 'between:5,9') # Between 5 and 9 characters

# Custom parameterized constraints
route.where('digits', 'digits_between:3,5')  # 3-5 digits
```

### Custom Constraints

```python
from pydance.routing.constraints import register_constraint

# Register a custom constraint
register_constraint('hex_color_short', r'#[0-9a-fA-F]{3}', 'Invalid short hex color')

# Use it in routes
@router.route('/colors/{color:hex_color_short}')
def get_color(request, color):
    return f"Color: {color}"
```

### Multiple Constraints

```python
# Multiple parameters with different constraints
@router.route('/api/v1/users/{id}/posts/{slug}')
def get_post(request, id, slug):
    pass

# Add constraints
router.routes[-1].where({
    'id': 'numeric',
    'slug': 'slug'
})

# Or inline
@router.route('/api/v1/users/{id:numeric}/posts/{slug:slug}')
def get_post_inline(request, id, slug):
    pass
```

### Advanced Constraint Composition

```python
from pydance.routing.constraints import get_route_constraints

constraints = get_route_constraints()

# Combine constraints with OR logic
combined = constraints.combine('numeric', 'alpha')  # Either numeric OR alpha

# Chain constraints with AND logic
chained = constraints.chain('alpha', 'min:3', 'max:10')  # Alpha AND min:3 AND max:10

# Use in routes
route.where('code', combined)
route.where('name', chained)
```

## Complex Examples

### E-commerce Routes

```python
router = Router()

# Product routes with various constraints
@router.route('/products/{category:slug}/{id:numeric}')
def get_product(request, category, id):
    return f"Product {id} in category {category}"

# Search with flexible parameters
@router.route('/search/{query:alpha_numeric}/{page:numeric}')
def search(request, query, page=1):
    return f"Search: {query}, page: {page}"

# User profile with UUID
@router.route('/users/{uuid:uuid}/profile')
def get_profile(request, uuid):
    return f"Profile for user {uuid}"
```

### API Versioning

```python
# API routes with version constraints
@router.route('/api/v{version:numeric}/users/{id:numeric}')
def api_user(request, version, id):
    return f"API v{version} - User {id}"

# Date-based routes
@router.route('/reports/{date:date}/export')
def export_report(request, date):
    return f"Report for {date}"
```

### File Upload Routes

```python
# File routes with extension constraints
@router.route('/files/images/{filename:image}')
def get_image(request, filename):
    return f"Image: {filename}"

@router.route('/files/videos/{filename:video}')
def get_video(request, filename):
    return f"Video: {filename}"
```

## Custom Constraint Registration

```python
from pydance.routing.constraints import register_constraint

# Register business-specific constraints
register_constraint('product_code', r'PRD-[0-9]{6}', 'Invalid product code format')
register_constraint('order_number', r'ORD-[0-9]{8}', 'Invalid order number format')
register_constraint('username', r'[a-zA-Z0-9_-]{3,20}', 'Invalid username format')

# Use in routes
@router.route('/products/{code:product_code}')
def get_product(request, code):
    return f"Product: {code}"

@router.route('/orders/{number:order_number}')
def get_order(request, number):
    return f"Order: {number}"

@router.route('/users/{username:username}')
def get_user(request, username):
    return f"User: {username}"
```

## Constraint Validation

```python
from pydance.routing.constraints import get_route_constraints

constraints = get_route_constraints()

# Validate values against constraints
is_valid, error = constraints.validate('email', 'user@example.com')
# is_valid = True, error = None

is_valid, error = constraints.validate('numeric', 'abc')
# is_valid = False, error = 'Parameter does not match numeric constraint'

# List all available constraints
available = constraints.list_constraints()
print(available)
# {'numeric': 'Only digits (0-9)', 'alpha': 'Only letters (a-z, A-Z)', ...}
```

## Protected Routes

Pydance provides middleware-based route protection similar to Laravel's middleware.

### Authentication Middleware

```python
from pydance.auth.middleware import AuthMiddleware, AdminAuthMiddleware

router = Router()
auth_middleware = AuthMiddleware()
admin_middleware = AdminAuthMiddleware()

# Protected route - requires authentication
@router.route('/dashboard', middleware=[auth_middleware])
def dashboard(request):
    return f"Welcome {request.user['name']}!"

# Admin-only route
@router.route('/admin/users', middleware=[admin_middleware])
def admin_users(request):
    return "Admin user list"

# Public route - no middleware needed
@router.route('/public')
def public_page(request):
    return "This is public"
```

### Route Groups with Middleware

```python
# Create authenticated route group
auth_group = router.group('/api', middleware=[auth_middleware])

@auth_group.route('/users')
def api_users(request):
    return "User list"

@auth_group.route('/profile')
def api_profile(request):
    return f"Profile for {request.user['id']}"

# Admin route group
admin_group = router.group('/admin', middleware=[admin_middleware])

@admin_group.route('/stats')
def admin_stats(request):
    return "Admin statistics"
```

### Custom Middleware

```python
from pydance.middleware.base import HTTPMiddleware

class RoleMiddleware(HTTPMiddleware):
    def __init__(self, required_role: str):
        self.required_role = required_role

    async def process_request(self, request):
        user = getattr(request, 'user', None)
        if not user:
            raise Unauthorized("Authentication required")

        user_roles = user.get('roles', [])
        if self.required_role not in user_roles:
            raise Forbidden(f"Role '{self.required_role}' required")

        return request

# Use custom middleware
editor_middleware = RoleMiddleware('editor')

@router.route('/articles/{id:numeric}/edit', middleware=[auth_middleware, editor_middleware])
def edit_article(request, id):
    return f"Editing article {id}"
```

## Performance Considerations

- Constraints are compiled to regex patterns and cached for performance
- Named constraints are resolved once during route registration
- Complex constraints may impact routing performance for high-traffic applications
- Consider using simple constraints for frequently accessed routes

## Migration from Basic Routing

### Before (Basic)
```python
@router.route('/users/{id}')
def get_user(request, id):
    # Manual validation
    if not id.isdigit():
        return "Invalid ID", 400
    return f"User {id}"
```

### After (Advanced)
```python
@router.route('/users/{id:numeric}')
def get_user(request, id):
    # Automatic validation by routing system
    return f"User {id}"
```

## Best Practices

1. **Use Named Constraints**: Prefer named constraints over custom regex for maintainability
2. **Validate Early**: Let the routing system handle parameter validation
3. **Group Related Routes**: Use route groups for consistent middleware application
4. **Custom Constraints**: Register reusable constraints for business logic
5. **Test Constraints**: Always test your custom constraints with various inputs
6. **Performance**: Use simple constraints for high-traffic routes

## Comparison with Laravel/Django

| Feature | Laravel | Django | Pydance |
|---------|---------|--------|---------|
| Named Constraints | ✓ | ✗ | ✓ |
| Inline Constraints | ✓ | ✗ | ✓ |
| Custom Constraints | ✓ | ✗ | ✓ |
| Parameterized Constraints | ✓ | ✗ | ✓ |
| Constraint Composition | ✗ | ✗ | ✓ |
| Middleware Integration | ✓ | ✓ | ✓ |
| UUID Support | ✓ | ✗ | ✓ |
| Email Validation | ✓ | ✗ | ✓ |
| File Extension Constraints | ✗ | ✗ | ✓ |

Pydance provides all the features of Laravel's routing constraints plus additional advanced capabilities like constraint composition and more built-in constraint types.
