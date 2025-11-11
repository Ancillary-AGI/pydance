"""
Advanced route parameter constraints for Pydance routing system.

Provides named constraint patterns similar to Laravel and Django, but with enhanced features.
"""

import re
from typing import Dict, Pattern, Callable, Any, Optional, Union
from functools import lru_cache


class RouteConstraints:
    """
    Advanced route parameter constraint system.

    Features:
    - Named constraint patterns (numeric, alpha, uuid, etc.)
    - Custom constraint registration
    - Validation with custom error messages
    - Performance-optimized regex compilation
    - Constraint composition and combination
    """

    def __init__(self):
        self._constraints: Dict[str, Union[str, Pattern, Callable]] = {}
        self._error_messages: Dict[str, str] = {}
        self._compiled_patterns: Dict[str, Pattern] = {}
        self._register_builtin_constraints()

    def _register_builtin_constraints(self) -> None:
        """Register built-in constraint patterns."""

        # Numeric patterns
        self._constraints['numeric'] = r'[0-9]+'
        self._constraints['integer'] = r'[0-9]+'
        self._constraints['digits'] = r'[0-9]+'
        self._constraints['digits_between'] = lambda min_digits, max_digits: f'[0-9]{{\\d,{min_digits},{max_digits}}}'

        # Alpha patterns
        self._constraints['alpha'] = r'[a-zA-Z]+'
        self._constraints['alpha_numeric'] = r'[a-zA-Z0-9]+'
        self._constraints['alpha_dash'] = r'[a-zA-Z0-9_-]+'

        # Alphanumeric with special chars
        self._constraints['slug'] = r'[a-z0-9-]+'
        self._constraints['username'] = r'[a-zA-Z0-9_-]{3,20}'

        # UUID patterns
        self._constraints['uuid'] = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        self._constraints['uuid4'] = r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'

        # Date/Time patterns
        self._constraints['date'] = r'\d{4}-\d{2}-\d{2}'
        self._constraints['time'] = r'\d{2}:\d{2}(:\d{2})?'
        self._constraints['datetime'] = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?'

        # Email and URL patterns
        self._constraints['email'] = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self._constraints['url'] = r'https?://[^\s/$.?#].[^\s]*'

        # File extension patterns
        self._constraints['image'] = r'\.(jpg|jpeg|png|gif|bmp|webp|svg)$'
        self._constraints['video'] = r'\.(mp4|avi|mkv|mov|wmv|flv|webm)$'
        self._constraints['audio'] = r'\.(mp3|wav|flac|aac|ogg)$'
        self._constraints['document'] = r'\.(pdf|doc|docx|txt|rtf)$'

        # Size constraints
        self._constraints['min'] = lambda min_val: f'.{{{min_val},}}'
        self._constraints['max'] = lambda max_val: f'.{{0,{max_val}}}'
        self._constraints['between'] = lambda min_val, max_val: f'.{{{min_val},{max_val}}}'

        # Custom patterns
        self._constraints['hex_color'] = r'#[0-9a-fA-F]{3,6}'
        self._constraints['ip'] = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        self._constraints['ipv4'] = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        self._constraints['ipv6'] = r'([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}'
        self._constraints['phone'] = r'\+?[\d\s\-\(\)]{10,}'
        self._constraints['postal_code'] = r'\d{5}(-\d{4})?'

        # Error messages
        self._error_messages.update({
            'numeric': 'Parameter must contain only numbers',
            'alpha': 'Parameter must contain only letters',
            'alpha_numeric': 'Parameter must contain only letters and numbers',
            'email': 'Parameter must be a valid email address',
            'uuid': 'Parameter must be a valid UUID',
            'url': 'Parameter must be a valid URL',
            'date': 'Parameter must be in YYYY-MM-DD format',
        })

    def register(self, name: str, pattern: Union[str, Pattern, Callable], error_message: Optional[str] = None) -> None:
        """
        Register a custom constraint pattern.

        Args:
            name: Constraint name
            pattern: Regex pattern, compiled pattern, or callable that returns a pattern
            error_message: Custom error message for validation failures
        """
        self._constraints[name] = pattern
        if error_message:
            self._error_messages[name] = error_message

        # Clear compiled pattern cache
        if name in self._compiled_patterns:
            del self._compiled_patterns[name]

    def unregister(self, name: str) -> None:
        """Remove a registered constraint."""
        if name in self._constraints:
            del self._constraints[name]
        if name in self._error_messages:
            del self._error_messages[name]
        if name in self._compiled_patterns:
            del self._compiled_patterns[name]

    @lru_cache(maxsize=128)
    def get_pattern(self, constraint_name: str, *args) -> Optional[str]:
        """
        Get the regex pattern for a constraint name.

        Args:
            constraint_name: Name of the constraint
            *args: Arguments for parameterized constraints

        Returns:
            Regex pattern string or None if constraint not found
        """
        if constraint_name not in self._constraints:
            return None

        constraint = self._constraints[constraint_name]

        if callable(constraint):
            try:
                return constraint(*args)
            except Exception:
                return None
        elif isinstance(constraint, Pattern):
            return constraint.pattern
        else:
            return str(constraint)

    def validate(self, constraint_name: str, value: str, *args) -> tuple[bool, Optional[str]]:
        """
        Validate a value against a constraint.

        Returns:
            Tuple of (is_valid, error_message)
        """
        pattern = self.get_pattern(constraint_name, *args)
        if not pattern:
            return False, f"Unknown constraint: {constraint_name}"

        try:
            compiled = re.compile(f'^{pattern}$', re.IGNORECASE)
            is_valid = bool(compiled.match(value))
            error_msg = None if is_valid else self._error_messages.get(constraint_name, f"Parameter does not match {constraint_name} constraint")
            return is_valid, error_msg
        except re.error:
            return False, f"Invalid regex pattern for constraint: {constraint_name}"

    def combine(self, *constraint_names: str) -> str:
        """
        Combine multiple constraints with OR logic.

        Example:
            constraints.combine('numeric', 'alpha') -> '(?:[0-9]+|[a-zA-Z]+)'
        """
        patterns = []
        for name in constraint_names:
            pattern = self.get_pattern(name)
            if pattern:
                patterns.append(pattern)

        if not patterns:
            return '[^/]+'  # Fallback to default

        return f'(?:{"|".join(patterns)})'

    def chain(self, *constraint_names: str) -> str:
        """
        Chain multiple constraints with AND logic (all must match).

        Example:
            constraints.chain('alpha', 'min:3', 'max:10') -> '(?=[a-zA-Z]+)(?=.{3,})(?=.{0,10})'
        """
        positive_lookaheads = []
        for name in constraint_names:
            if ':' in name:
                # Handle parameterized constraints like 'min:3'
                base_name, params = name.split(':', 1)
                param_values = params.split(',')
                pattern = self.get_pattern(base_name, *param_values)
            else:
                pattern = self.get_pattern(name)

            if pattern:
                positive_lookaheads.append(f'(?={pattern})')

        if not positive_lookaheads:
            return '[^/]+'  # Fallback to default

        return f'{"".join(positive_lookaheads)}[^/]*'

    def list_constraints(self) -> Dict[str, str]:
        """List all available constraints with descriptions."""
        descriptions = {
            'numeric': 'Only digits (0-9)',
            'alpha': 'Only letters (a-z, A-Z)',
            'alpha_numeric': 'Letters and digits',
            'alpha_dash': 'Letters, digits, underscores, and hyphens',
            'slug': 'URL-friendly slug (lowercase, digits, hyphens)',
            'uuid': 'UUID format',
            'email': 'Email address format',
            'url': 'URL format',
            'date': 'Date in YYYY-MM-DD format',
            'ip': 'IP address',
            'phone': 'Phone number',
            'postal_code': 'Postal/ZIP code',
        }

        result = {}
        for name in self._constraints.keys():
            result[name] = descriptions.get(name, 'Custom constraint')

        return result


# Global constraint registry
_global_constraints = RouteConstraints()

def get_route_constraints() -> RouteConstraints:
    """Get the global route constraints instance."""
    return _global_constraints

def register_constraint(name: str, pattern: Union[str, Pattern, Callable], error_message: Optional[str] = None) -> None:
    """Register a global constraint pattern."""
    _global_constraints.register(name, pattern, error_message)

def unregister_constraint(name: str) -> None:
    """Remove a global constraint."""
    _global_constraints.unregister(name)

__all__ = [
    'RouteConstraints',
    'get_route_constraints',
    'register_constraint',
    'unregister_constraint'
]
