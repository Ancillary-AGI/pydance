"""
Middleware Resolver for Pydance Framework.

This module provides Laravel-style middleware resolution, allowing middleware
to be specified as strings and resolved to actual middleware instances.
"""

from typing import Dict, Any, List, Union, Callable, Optional, Type
from pydance.middleware.throttle import ThrottleMiddleware


class MiddlewareResolver:
    """
    Resolves middleware from strings to instances.

    String-based middleware resolution:
    - 'throttle:100,10' -> ThrottleMiddleware with capacity=100, refill_rate=10
    - 'auth' -> Authentication middleware (when implemented)
    - 'cors' -> CORS middleware (when implemented)
    """

    def __init__(self):
        self._middleware_map: Dict[str, Callable] = {
            'throttle': self._resolve_throttle,
        }
        self._instances: Dict[str, Any] = {}
        self._aliases_registered = False

    def register(self, name: str, resolver: Callable):
        """Register a custom middleware resolver"""
        self._middleware_map[name] = resolver

    def register_alias(self, alias: str, middleware_class: Type, **default_kwargs):
        """Register a middleware alias with default parameters"""
        def alias_resolver(params: str = ''):
            """Resolve middleware alias to actual middleware"""
            try:
                # Parse parameters if provided
                kwargs = default_kwargs.copy()
                if params:
                    # Parse parameters like "key1=value1,key2=value2"
                    for param in params.split(','):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            kwargs[key.strip()] = value.strip()

                return middleware_class(**kwargs)
            except Exception as e:
                raise ValueError(f"Failed to resolve middleware alias '{alias}': {e}")

        self.register(alias, alias_resolver)

    def resolve(self, middleware_spec: Union[str, Callable, type]) -> Optional[Callable]:
        """
        Resolve middleware specification to middleware instance.

        Args:
            middleware_spec: String like 'throttle:100,10' or middleware class/instance

        Returns:
            Middleware instance or None if resolution fails
        """
        if callable(middleware_spec):
            return middleware_spec

        if isinstance(middleware_spec, str):
            return self._resolve_string(middleware_spec)

        return None

    def _resolve_string(self, middleware_string: str) -> Optional[Callable]:
        """Resolve string-based middleware specification"""
        # Check cache first
        if middleware_string in self._instances:
            return self._instances[middleware_string]

        # Parse middleware string
        if ':' in middleware_string:
            name, params = middleware_string.split(':', 1)
            name = name.strip()
        else:
            name = middleware_string.strip()
            params = ''

        # Find resolver
        resolver = self._middleware_map.get(name)
        if not resolver:
            return None

        # Resolve and cache
        try:
            instance = resolver(params)
            self._instances[middleware_string] = instance
            return instance
        except Exception:
            return None

    def _resolve_throttle(self, params: str) -> ThrottleMiddleware:
        """Resolve throttle middleware from parameters"""
        return ThrottleMiddleware.from_string(f"throttle:{params}")

    def _register_middleware_aliases(self):
        """Register middleware aliases from settings and built-in middleware"""
        try:
            # Register built-in aliases from middleware module
            for alias, middleware_path in MIDDLEWARE_ALIASES.items():
                self._register_alias_resolver(alias, middleware_path)

            # Register custom aliases from settings
            if hasattr(settings, 'MIDDLEWARE_ALIASES'):
                for alias, middleware_path in settings.MIDDLEWARE_ALIASES.items():
                    self._register_alias_resolver(alias, middleware_path)

        except ImportError:
            # MIDDLEWARE_ALIASES not available yet
            pass

    def _register_alias_resolver(self, alias: str, middleware_path: str):
        """Register a resolver for a middleware alias"""
        def alias_resolver(params: str = ''):
            """Resolve middleware alias to actual middleware"""
            try:
                # Import the middleware class
                module_path, class_name = middleware_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                middleware_class = getattr(module, class_name)

                # Parse parameters if provided
                if params:
                    # Parse parameters like "key1=value1,key2=value2"
                    param_dict = {}
                    for param in params.split(','):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            param_dict[key.strip()] = value.strip()

                    return middleware_class(**param_dict)
                else:
                    return middleware_class()

            except Exception as e:
                raise ValueError(f"Failed to resolve middleware alias '{alias}': {e}")

        self.register(alias, alias_resolver)

    def resolve_list(self, middleware_specs: List[Union[str, Callable, type]]) -> List[Callable]:
        """Resolve a list of middleware specifications"""
        resolved = []
        for spec in middleware_specs:
            middleware = self.resolve(spec)
            if middleware:
                resolved.append(middleware)
        return resolved

    def clear_cache(self):
        """Clear the middleware instance cache"""
        self._instances.clear()


# Global middleware resolver instance
middleware_resolver = MiddlewareResolver()

# Register common middleware resolvers
def register_builtin_middleware():
    """Register built-in middleware resolvers"""
    # Throttle middleware is already registered
    pass

# Initialize built-in middleware
register_builtin_middleware()


__all__ = [
    'MiddlewareResolver',
    'middleware_resolver'
]
