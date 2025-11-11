#!/usr/bin/env python3
"""
Example demonstrating advanced regex routing in Pydance.

This example shows how to use regex constraints in route parameters,
similar to Laravel and Django but with enhanced features.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from pydance.routing.route import Route
from pydance.routing.constraints import register_constraint
from pydance.routing.router import Router


def main():
    print("🔥 Pydance Advanced Regex Routing Demo")
    print("=" * 50)

    # Example 1: Basic regex constraints
    print("\n1. Basic Regex Constraints (Laravel/Django style)")
    route1 = Route('/users/{id}', lambda: None)
    route1.where('id', r'[0-9]+')  # Only digits

    print("Route: /users/{id} with constraint [0-9]+")
    print("✓ Matches: /users/123 ->", route1.match('/users/123', 'GET'))
    print("✗ No match: /users/abc ->", route1.match('/users/abc', 'GET'))

    # Example 2: Named constraints
    print("\n2. Named Constraints")
    route2 = Route('/users/{id}', lambda: None)
    route2.where('id', 'numeric')

    print("Route: /users/{id} with 'numeric' constraint")
    print("✓ Matches: /users/123 ->", route2.match('/users/123', 'GET'))
    print("✗ No match: /users/abc ->", route2.match('/users/abc', 'GET'))

    # Example 3: Inline named constraints
    print("\n3. Inline Named Constraints")
    route3 = Route('/users/{id:numeric}', lambda: None)

    print("Route: /users/{id:numeric}")
    print("✓ Matches: /users/123 ->", route3.match('/users/123', 'GET'))
    print("✗ No match: /users/abc ->", route3.match('/users/abc', 'GET'))

    # Example 4: Multiple constraints
    print("\n4. Multiple Constraints")
    route4 = Route('/users/{id}/posts/{slug}', lambda: None)
    route4.where({'id': 'numeric', 'slug': 'slug'})

    print("Route: /users/{id:numeric}/posts/{slug:slug}")
    print("✓ Matches: /users/123/posts/my-post-title ->",
          route4.match('/users/123/posts/my-post-title', 'GET'))
    print("✗ No match: /users/abc/posts/my-post-title ->",
          route4.match('/users/abc/posts/my-post-title', 'GET'))

    # Example 5: UUID constraint
    print("\n5. UUID Constraint")
    route5 = Route('/users/{uuid}', lambda: None)
    route5.where('uuid', 'uuid')

    uuid_example = '550e8400-e29b-41d4-a716-446655440000'
    print(f"Route: /users/{{uuid}} with 'uuid' constraint")
    print(f"✓ Matches: /users/{uuid_example} ->",
          route5.match(f'/users/{uuid_example}', 'GET'))
    print("✗ No match: /users/invalid-uuid ->",
          route5.match('/users/invalid-uuid', 'GET'))

    # Example 6: Email constraint
    print("\n6. Email Constraint")
    route6 = Route('/users/{email}', lambda: None)
    route6.where('email', 'email')

    print("Route: /users/{email} with 'email' constraint")
    print("✓ Matches: /users/user@example.com ->",
          route6.match('/users/user@example.com', 'GET'))
    print("✗ No match: /users/invalid-email ->",
          route6.match('/users/invalid-email', 'GET'))

    # Example 7: Parameterized constraints
    print("\n7. Parameterized Constraints")
    route7 = Route('/users/{name}', lambda: None)
    route7.where('name', 'min:3')

    print("Route: /users/{name} with 'min:3' constraint")
    print("✓ Matches: /users/john ->", route7.match('/users/john', 'GET'))
    print("✗ No match: /users/ab ->", route7.match('/users/ab', 'GET'))

    # Example 8: Between constraint
    print("\n8. Between Constraint")
    route8 = Route('/users/{name}', lambda: None)
    route8.where('name', 'between:2,5')

    print("Route: /users/{name} with 'between:2,5' constraint")
    print("✓ Matches: /users/john ->", route8.match('/users/john', 'GET'))
    print("✗ No match: /users/a ->", route8.match('/users/a', 'GET'))
    print("✗ No match: /users/alexander ->", route8.match('/users/alexander', 'GET'))

    # Example 9: Custom constraint registration
    print("\n9. Custom Constraint Registration")
    register_constraint('hex_color_short', r'#[0-9a-fA-F]{3}', 'Invalid hex color')

    route9 = Route('/colors/{color}', lambda: None)
    route9.where('color', 'hex_color_short')

    print("Custom constraint: hex_color_short = #[0-9a-fA-F]{3}")
    print("Route: /colors/{color} with 'hex_color_short' constraint")
    print("✓ Matches: /colors/#f00 ->", route9.match('/colors/#f00', 'GET'))
    print("✗ No match: /colors/#ff0000 ->", route9.match('/colors/#ff0000', 'GET'))

    # Example 10: Complex route with multiple constraints
    print("\n10. Complex Route with Multiple Constraints")
    route10 = Route('/api/v1/users/{id:numeric}/posts/{slug:slug}/comments/{comment_id:numeric}', lambda: None)

    print("Route: /api/v1/users/{id:numeric}/posts/{slug:slug}/comments/{comment_id:numeric}")
    result = route10.match('/api/v1/users/123/posts/my-awesome-post/comments/456', 'GET')
    print("✓ Matches: /api/v1/users/123/posts/my-awesome-post/comments/456 ->", result)

    # Example 11: Router integration
    print("\n11. Router Integration")
    router = Router()

    def user_posts_handler(): pass

    router.add_route('/users/{id:numeric}/posts/{slug:slug}', user_posts_handler)

    print("Router with route: /users/{id:numeric}/posts/{slug:slug}")
    match = router.match('GET', '/users/123/posts/my-post')
    print("✓ Router matches: /users/123/posts/my-post ->", match.params if match else None)

    no_match = router.match('GET', '/users/abc/posts/my-post')
    print("✗ Router no match: /users/abc/posts/my-post ->", no_match)

    print("\n" + "=" * 50)
    print("🎉 Advanced regex routing demo completed!")
    print("\nKey features demonstrated:")
    print("• Named constraints (numeric, alpha, email, uuid, slug, etc.)")
    print("• Parameterized constraints (min:3, max:10, between:2,5)")
    print("• Custom constraint registration")
    print("• Inline constraint syntax ({param:constraint})")
    print("• Multiple constraints per route")
    print("• Router integration")
    print("• Type conversion preservation (int, float, bool)")
    print("• Enhanced validation with custom error messages")


if __name__ == '__main__':
    main()
