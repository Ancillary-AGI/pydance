"""
Enhanced microservices support for Pydance  framework.

This module provides comprehensive microservices architecture with:
- Service discovery and registration
- Distributed consensus (Raft algorithm)
- Event sourcing and CQRS patterns
- API design with HATEOAS and rate limiting
- Data-intensive processing patterns
"""

# Core service architecture
from .service import (
    Service, ServiceStatus, ServiceDiscovery, ServiceInstance,
    InMemoryServiceDiscovery
)

# Distributed consensus
from .consensus import (
    ConsensusManager, LogEntry, DistributedLock, RaftConsensus, ConsensusState
)

# Event sourcing and CQRS
from .event_sourcing import (
    Event, EventStore, Aggregate, Command, CommandHandler,
    Repository, EventPublisher
)

# API design patterns
# from .api_design import (
#     HttpMethod, Link, APIResponse, APIError, RateLimiter,
#     DistributedRateLimiter, PaginationParams, Paginator,
#     APIResource, ValidationError, NotFoundError,
#     UnauthorizedError, ForbiddenError
# )

# Legacy service discovery (for backward compatibility)
from .service_discovery import ConsulDiscovery, ZookeeperDiscovery

__all__ = [
    # Service architecture
    'Service', 'ServiceStatus', 'ServiceDiscovery', 'ServiceInstance',
    'InMemoryServiceDiscovery',

    # Distributed consensus
    'ConsensusManager', 'LogEntry', 'DistributedLock', 'RaftConsensus', 'ConsensusState',

    # Event sourcing and CQRS
    'Event', 'EventStore', 'Aggregate', 'Command', 'CommandHandler',
    'Repository', 'EventPublisher',

    # API design patterns (commented out - module not available)
    # 'HttpMethod', 'Link', 'APIResponse', 'APIError', 'RateLimiter',
    # 'DistributedRateLimiter', 'PaginationParams', 'Paginator',
    # 'APIResource', 'ValidationError', 'NotFoundError',
    # 'UnauthorizedError', 'ForbiddenError',

    # Legacy (backward compatibility)
    'LegacyServiceDiscovery', 'ConsulDiscovery', 'ZookeeperDiscovery'
]
