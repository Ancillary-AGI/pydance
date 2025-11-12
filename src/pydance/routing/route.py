"""
Route classes for Pydance routing system with advanced regex parameter support.
"""

import re
import asyncio
from typing import Callable, Dict, List, Optional, Tuple, Any, Union, Set, Pattern
from enum import Enum
from dataclasses import dataclass
from pydance.routing.types import HandlerType


class Route:
    """
    Enhanced route with advanced pattern matching and middleware support.

    Features:
    - Regex pattern compilation with parameter extraction
    - Type conversion for path parameters
    - Middleware pipeline per route
    - Caching support
    - Priority-based matching
    """

    def __init__(
        self,
        path: str,
        handler: Callable,
        methods: Optional[Union[List[str], Set[str]]] = None,
        name: Optional[str] = None,
        middleware: Optional[List[Callable]] = None,
        route_type: HandlerType = HandlerType.HTTP,
        redirect_to: Optional[str] = None,
        redirect_code: int = 302,
        view_class: Optional[Any] = None,
        view_kwargs: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Union[str, Pattern]]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        host: Optional[str] = None,
        schemes: Optional[List[str]] = None,
        **kwargs
    ):
        self.path = path
        self.handler = handler
        self.name = name or f"{handler.__module__}.{handler.__name__}"
        self.methods = set(methods or ["GET"])
        self.middleware = self._resolve_middleware(middleware or [])
        self.route_type = route_type
        self.redirect_to = redirect_to
        self.redirect_code = redirect_code
        self.view_class = view_class
        self.view_kwargs = view_kwargs or {}
        self.constraints = constraints or {}
        self.defaults = defaults or {}
        self.host = host
        self.schemes = schemes or []
        # Simple config dict instead of RouteConfig class
        self.config = {
            'methods': self.methods,
            'name': name,
            'middleware': self.middleware,
            **kwargs
        }

        # Pattern compilation
        self.pattern: Optional[Pattern] = None
        self.param_names: List[str] = []
        self.param_types: Dict[str, type] = {}
        self._compile_pattern()

    def _resolve_middleware(self, middleware_specs: List[Any]) -> List[Callable]:
        """Resolve middleware specifications to callable instances."""
        resolved = []
        for spec in middleware_specs:
            middleware = middleware_resolver.resolve(spec)
            if middleware:
                resolved.append(middleware)
        return resolved

    def _compile_pattern(self) -> None:
        """Compile regex pattern with enhanced parameter handling and constraints."""
        constraints_registry = get_route_constraints()
        pattern = self.path

        # First, handle parameters with inline constraints like {id:[0-9]+}, {id:numeric}, or {id:int}
        regex_param_pattern = r'\{([^:}]+):(\[[^\]]+\]|[^}]+)\}'
        def regex_param_replacer(match):
            param_name = match.group(1)
            constraint = match.group(2)

            if param_name not in self.param_names:  # Avoid duplicates
                self.param_names.append(param_name)
                self.param_types[param_name] = str  # Default to string

                # If constraint is a regex pattern (starts with [), store it as constraint
                if constraint.startswith('[') and constraint.endswith(']'):
                    regex_pattern = constraint[1:-1]  # Remove brackets
                    self.constraints[param_name] = regex_pattern
                    return f'(?P<{param_name}>{regex_pattern})'
                else:
                    # Check if it's a type hint (int, float, bool, uuid)
                    param_type = self._get_type_from_string(constraint)
                    if param_type != str:  # It's a type hint
                        self.param_types[param_name] = param_type
                        return f'(?P<{param_name}>[^/]+)'
                    else:
                        # Check if it's a named constraint
                        named_pattern = constraints_registry.get_pattern(constraint)
                        if named_pattern:
                            self.constraints[param_name] = named_pattern
                            return f'(?P<{param_name}>{named_pattern})'
                        else:
                            # It's a custom regex pattern or unknown constraint
                            self.constraints[param_name] = constraint
                            return f'(?P<{param_name}>[^/]+)'

            return f'(?P<{param_name}>[^/]+)'

        pattern = re.sub(regex_param_pattern, regex_param_replacer, pattern)

        # Then handle simple parameters like {id}
        simple_param_pattern = r'\{([^}]+)\}'
        def simple_param_replacer(match):
            param_name = match.group(1)
            if param_name not in self.param_names:  # Avoid overwriting
                self.param_names.append(param_name)
                self.param_types[param_name] = str  # Default to string
            return f'(?P<{param_name}>[^/]+)'

        pattern = re.sub(simple_param_pattern, simple_param_replacer, pattern)

        # Apply additional constraints from self.constraints (set via where() method)
        for param_name, constraint in self.constraints.items():
            if isinstance(constraint, str) and not constraint.startswith('(?P<'):
                # Replace the parameter group with constrained version
                param_group = f'(?P<{param_name}>[^/]+)'

                # Check if it's a named constraint first
                if ':' in constraint:
                    # Handle parameterized constraints like 'min:3'
                    base_name, params = constraint.split(':', 1)
                    param_values = params.split(',')
                    named_pattern = constraints_registry.get_pattern(base_name, *param_values)
                    if named_pattern:
                        constrained_group = f'(?P<{param_name}>{named_pattern})'
                    else:
                        constrained_group = f'(?P<{param_name}>[^/]+)'
                else:
                    # Check for named constraint
                    named_pattern = constraints_registry.get_pattern(constraint)
                    if named_pattern:
                        constrained_group = f'(?P<{param_name}>{named_pattern})'
                    elif constraint.startswith('[') and constraint.endswith(']'):
                        # It's already a regex pattern
                        constrained_group = f'(?P<{param_name}>{constraint[1:-1]})'
                    else:
                        # It's a regex pattern
                        constrained_group = f'(?P<{param_name}>{constraint})'

                pattern = pattern.replace(param_group, constrained_group)

        # Escape special regex characters, but not within the parameter groups we created
        # Split the pattern by our added groups and escape each part separately
        parts = re.split(r'(\(\?P<\w+>[^)]+\))', pattern)
        escaped_parts = []

        for part in parts:
            if part.startswith('(?P<') and part.endswith(')'):
                # This is one of our parameter groups, don't escape it
                escaped_parts.append(part)
            else:
                # Escape special regex chars in non-parameter parts
                escaped_part = re.sub(r'([.+^$*()\\[\]{}|])', r'\\\1', part)
                escaped_parts.append(escaped_part)

        # Join back together and add anchors
        final_pattern = f'^{"".join(escaped_parts)}$'

        self.pattern = re.compile(final_pattern)

    def _get_type_from_string(self, type_str: str) -> type:
        """Convert string type representation to actual type."""
        type_map = {
            'int': int,
            'str': str,
            'float': float,
            'bool': bool,
            'uuid': str,  # UUID as string for simplicity
        }
        return type_map.get(type_str.lower(), str)

    def match(self, path: str, method: str, host: str = None, scheme: str = None) -> Optional[Dict[str, Any]]:
        """
        Match path against route pattern with type conversion and constraints.

        Returns:
            Dictionary of converted parameters or None if no match
        """
        if method not in self.methods:
            return None

        # Check host constraint
        if self.host and host != self.host:
            return None

        # Check scheme constraint
        if self.schemes and scheme not in self.schemes:
            return None

        match = self.pattern.match(unquote(path))
        if not match:
            return None

        params = match.groupdict()

        # Apply defaults for missing parameters
        for key, default_value in self.defaults.items():
            if key not in params:
                params[key] = default_value

        # Type conversion
        converted_params = {}
        for param_name, param_value in params.items():
            param_type = self.param_types.get(param_name, str)
            try:
                if param_type == bool:
                    converted_params[param_name] = param_value.lower() in ('true', '1', 'yes', 'on')
                elif param_type == int:
                    converted_params[param_name] = int(param_value)
                elif param_type == float:
                    converted_params[param_name] = float(param_value)
                else:
                    converted_params[param_name] = param_value
            except (ValueError, TypeError):
                return None  # Type conversion failed

        return converted_params

    def get_redirect_url(self, params: Dict[str, str] = None) -> Optional[str]:
        """Get the redirect URL for redirect routes"""
        if not self.redirect_to:
            return None

        if not params:
            return self.redirect_to

        # Replace parameters in redirect URL
        redirect_url = self.redirect_to
        for key, value in params.items():
            redirect_url = redirect_url.replace(f'{{{key}}}', str(value))

        return redirect_url

    async def execute_middleware(self, request: Any, call_next: Callable) -> Any:
        """Execute route-specific middleware pipeline."""
        if not self.middleware:
            return await call_next(request)

        async def dispatch(index: int, req: Any) -> Any:
            if index >= len(self.middleware):
                return await call_next(req)

            middleware = self.middleware[index]

            async def next_middleware(next_req: Any) -> Any:
                return await dispatch(index + 1, next_req)

            if asyncio.iscoroutinefunction(middleware):
                return await middleware(req, next_middleware)
            else:
                return middleware(req, next_middleware)

        return await dispatch(0, request)

    def where(self, param: Union[str, Dict[str, Union[str, Pattern]]], constraint: Optional[Union[str, Pattern]] = None) -> 'Route':
        """
        Add regex constraints to route parameters.

        Examples:
            # Single constraint
            route.where('id', '[0-9]+')

            # Multiple constraints
            route.where({'id': '[0-9]+', 'slug': '[a-z0-9-]+'})

            # Using constraint names
            route.where('id', 'numeric')
        """
        if isinstance(param, dict):
            # Multiple constraints
            for param_name, param_constraint in param.items():
                self.constraints[param_name] = param_constraint
        else:
            # Single constraint
            if constraint is not None:
                self.constraints[param] = constraint

        # Recompile pattern with new constraints
        self._compile_pattern()
        return self


@dataclass
class WebSocketRoute:
    path: str
    handler: Callable
    pattern: re.Pattern

    def __init__(self, path: str, handler: Callable):
        self.path = path
        self.handler = handler
        self.pattern = self._compile_pattern(path)

    def _compile_pattern(self, path: str) -> re.Pattern:
        # Convert route path to regex pattern
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', path)
        return re.compile(f'^{pattern}$')

    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Check if this route matches the given path"""
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None
