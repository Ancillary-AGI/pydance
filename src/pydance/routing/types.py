"""Routing-related type definitions."""

from typing import Dict, Any, Callable, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum


class RouteType(Enum):
    """Types of routes."""
    NORMAL = "normal"
    REDIRECT = "redirect"
    VIEW = "view"
    FALLBACK = "fallback"
    INTENDED = "intended"


@dataclass
class RouteMatch:
    """Route match result with enhanced metadata."""
    handler: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    route: Optional['Route'] = None
    middleware: List[Callable] = field(default_factory=list)


@dataclass
class RouteConfig:
    """Configuration for route behavior."""
    methods: Set[str] = field(default_factory=lambda: {"GET"})
    name: Optional[str] = None
    middleware: List[Callable] = field(default_factory=list)
    cache_timeout: Optional[int] = None
    priority: int = 0


# Type aliases
RouteMethods = List[str]
RouteParams = Dict[str, Any]

__all__ = [
    'RouteType', 'RouteMatch', 'RouteConfig',
    'RouteMethods', 'RouteParams'
]
