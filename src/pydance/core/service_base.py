"""
Base service class for Pydance framework.

Provides the foundation for implementing business logic services
with proper dependency injection, lifecycle management, and error handling.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

from pydance.exceptions import BaseFrameworkException

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceConfig:
    """Configuration for service instances"""
    name: str
    auto_start: bool = True
    health_check_interval: int = 30  # seconds
    max_concurrent_requests: int = 100
    timeout: float = 30.0  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # Service-specific settings
    settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.settings is None:
            self.settings = {}


class ServiceError(BaseFrameworkException):
    """Base exception for service-related errors"""

    def __init__(self, message: str, service_name: str = None, **kwargs):
        super().__init__(message, error_code="service_error", **kwargs)
        self.service_name = service_name


class ServiceNotFoundError(ServiceError):
    """Exception raised when a requested service is not found"""

    def __init__(self, service_name: str, **kwargs):
        message = f"Service not found: {service_name}"
        super().__init__(message, service_name, error_code="service_not_found", **kwargs)


class ServiceLifecycleError(ServiceError):
    """Exception raised during service lifecycle operations"""

    def __init__(self, message: str, service_name: str = None, **kwargs):
        super().__init__(message, service_name, error_code="service_lifecycle_error", **kwargs)


class ServiceBase(ABC):
    """
    Base class for all Pydance services.

    Provides common functionality for service lifecycle management,
    health checking, dependency injection, and error handling.
    """

    def __init__(self, config: ServiceConfig = None):
        self.config = config or ServiceConfig(name=self.__class__.__name__)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._dependencies: Dict[str, 'ServiceBase'] = {}
        self._is_initialized = False
        self._is_started = False
        self._is_healthy = False
        self._health_check_task = None
        self._start_time = None

    @property
    def name(self) -> str:
        """Service name"""
        return self.config.name

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._is_initialized

    @property
    def is_started(self) -> bool:
        """Check if service is started"""
        return self._is_started

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        return self._is_healthy

    @property
    def uptime(self) -> Optional[float]:
        """Get service uptime in seconds"""
        if self._start_time:
            return datetime.now().timestamp() - self._start_time
        return None

    async def initialize(self) -> None:
        """Initialize the service"""
        if self._is_initialized:
            self.logger.warning(f"Service {self.name} is already initialized")
            return

        try:
            self.logger.info(f"Initializing service: {self.name}")

            # Initialize dependencies first
            for dependency in self._dependencies.values():
                if not dependency.is_initialized:
                    await dependency.initialize()

            # Perform service-specific initialization
            await self._do_initialize()

            self._is_initialized = True
            self.logger.info(f"Service {self.name} initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize service {self.name}: {e}")
            raise ServiceLifecycleError(f"Initialization failed: {str(e)}", self.name)

    async def start(self) -> None:
        """Start the service"""
        if not self._is_initialized:
            await self.initialize()

        if self._is_started:
            self.logger.warning(f"Service {self.name} is already started")
            return

        try:
            self.logger.info(f"Starting service: {self.name}")

            # Start dependencies first
            for dependency in self._dependencies.values():
                if not dependency.is_started:
                    await dependency.start()

            # Perform service-specific startup
            await self._do_start()

            self._start_time = datetime.now().timestamp()
            self._is_started = True

            # Start health checking if configured
            if self.config.health_check_interval > 0:
                self._start_health_checking()

            self.logger.info(f"Service {self.name} started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start service {self.name}: {e}")
            raise ServiceLifecycleError(f"Startup failed: {str(e)}", self.name)

    async def stop(self) -> None:
        """Stop the service"""
        if not self._is_started:
            self.logger.warning(f"Service {self.name} is not started")
            return

        try:
            self.logger.info(f"Stopping service: {self.name}")

            # Stop health checking
            if self._health_check_task:
                self._health_check_task.cancel()
                self._health_check_task = None

            # Perform service-specific shutdown
            await self._do_stop()

            self._is_started = False
            self.logger.info(f"Service {self.name} stopped successfully")

        except Exception as e:
            self.logger.error(f"Failed to stop service {self.name}: {e}")
            raise ServiceLifecycleError(f"Shutdown failed: {str(e)}", self.name)

    async def restart(self) -> None:
        """Restart the service"""
        await self.stop()
        await self.start()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Basic health metrics
            health_data = {
                "service_name": self.name,
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": self.uptime,
                "is_initialized": self._is_initialized,
                "is_started": self._is_started
            }

            # Perform service-specific health checks
            service_health = await self._do_health_check()

            # Merge service-specific health data
            if service_health:
                health_data.update(service_health)

            # Check dependencies
            dependency_health = await self._check_dependencies_health()
            health_data["dependencies"] = dependency_health

            # Overall health determination
            if not all(dep["status"] == "healthy" for dep in dependency_health.values()):
                health_data["status"] = "degraded"

            self._is_healthy = health_data["status"] == "healthy"
            return health_data

        except Exception as e:
            self.logger.error(f"Health check failed for service {self.name}: {e}")
            return {
                "service_name": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def add_dependency(self, service: 'ServiceBase'):
        """Add a service dependency"""
        self._dependencies[service.name] = service

    def get_dependency(self, name: str) -> Optional['ServiceBase']:
        """Get a service dependency by name"""
        return self._dependencies.get(name)

    def get_dependencies(self) -> Dict[str, 'ServiceBase']:
        """Get all service dependencies"""
        return self._dependencies.copy()

    # Abstract methods that subclasses must implement

    @abstractmethod
    async def _do_initialize(self) -> None:
        """Perform service-specific initialization"""
        pass

    @abstractmethod
    async def _do_start(self) -> None:
        """Perform service-specific startup"""
        pass

    @abstractmethod
    async def _do_stop(self) -> None:
        """Perform service-specific shutdown"""
        pass

    @abstractmethod
    async def _do_health_check(self) -> Dict[str, Any]:
        """Perform service-specific health checks"""
        pass

    # Protected methods for subclasses

    def _start_health_checking(self):
        """Start periodic health checking"""
        async def health_check_loop():
            while self._is_started:
                try:
                    await asyncio.sleep(self.config.health_check_interval)
                    await self.health_check()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Health check error: {e}")

        self._health_check_task = asyncio.create_task(health_check_loop())

    async def _check_dependencies_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all dependencies"""
        health_results = {}

        for name, service in self._dependencies.items():
            try:
                health_results[name] = await service.health_check()
            except Exception as e:
                health_results[name] = {
                    "service_name": name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        return health_results


class DatabaseService(ServiceBase):
    """
    Base class for database-related services.

    Provides common database functionality and transaction management.
    """

    def __init__(self, config: ServiceConfig = None, db_connection = None):
        super().__init__(config)
        self.db_connection = db_connection

    async def _do_initialize(self) -> None:
        """Initialize database service"""
        if self.db_connection:
            await self.db_connection.connect()

    async def _do_start(self) -> None:
        """Start database service"""
        # Perform any startup tasks like warming up connections
        pass

    async def _do_stop(self) -> None:
        """Stop database service"""
        if self.db_connection:
            await self.db_connection.disconnect()

    async def _do_health_check(self) -> Dict[str, Any]:
        """Check database service health"""
        if not self.db_connection:
            return {"database_status": "not_configured"}

        try:
            health = await self.db_connection.health_check()
            return {"database_status": health.get("status", "unknown")}
        except Exception as e:
            return {"database_status": "error", "error": str(e)}


class CacheService(ServiceBase):
    """
    Base class for cache-related services.

    Provides common caching functionality and cache management.
    """

    def __init__(self, config: ServiceConfig = None, cache_manager = None):
        super().__init__(config)
        self.cache_manager = cache_manager

    async def _do_initialize(self) -> None:
        """Initialize cache service"""
        if self.cache_manager:
            await self.cache_manager.initialize()

    async def _do_start(self) -> None:
        """Start cache service"""
        # Cache warmup or other startup tasks
        pass

    async def _do_stop(self) -> None:
        """Stop cache service"""
        if self.cache_manager:
            await self.cache_manager.clear()

    async def _do_health_check(self) -> Dict[str, Any]:
        """Check cache service health"""
        if not self.cache_manager:
            return {"cache_status": "not_configured"}

        try:
            metrics = self.cache_manager.get_metrics()
            return {
                "cache_status": "healthy",
                "hit_rate": metrics.get("hit_rate", 0),
                "total_hits": metrics.get("total_hits", 0),
                "total_misses": metrics.get("total_misses", 0)
            }
        except Exception as e:
            return {"cache_status": "error", "error": str(e)}


__all__ = [
    'ServiceBase',
    'ServiceConfig',
    'ServiceError',
    'ServiceNotFoundError',
    'ServiceLifecycleError',
    'DatabaseService',
    'CacheService'
]
