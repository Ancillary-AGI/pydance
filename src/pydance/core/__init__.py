"""
Core service layer for Pydance framework.

Provides service layer architecture for better code organization,
separation of concerns, and maintainability.
"""

from .service_base import ServiceBase, ServiceConfig
from .di import (
    Container, ServiceLifetime, ServiceDescriptor, ServiceScope,
    container, inject, service, singleton_service, transient_service, scoped_service,
    service_scope, get_service_health, is_service_healthy, get_service_metadata,
    get_container_stats, register_service
)

__all__ = [
    'ServiceBase', 'ServiceConfig',
    # DI exports
    'Container', 'ServiceLifetime', 'ServiceDescriptor', 'ServiceScope',
    'container', 'inject', 'service', 'singleton_service', 'transient_service', 'scoped_service',
    'service_scope', 'get_service_health', 'is_service_healthy', 'get_service_metadata',
    'get_container_stats', 'register_service'
]
