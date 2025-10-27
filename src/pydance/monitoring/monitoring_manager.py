"""
Monitoring manager for Pydance framework.
Coordinates monitoring, metrics collection, and alerting.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
import asyncio


@dataclass
class MonitoringConfig:
    """Configuration for monitoring system"""

    enabled: bool = True
    metrics_enabled: bool = True
    alerting_enabled: bool = True
    logging_enabled: bool = True
    dashboard_enabled: bool = False

    # Metrics settings
    metrics_interval: int = 60  # seconds
    metrics_retention: int = 3600  # 1 hour

    # Alerting settings
    alert_check_interval: int = 30  # seconds
    alert_cooldown: int = 300  # 5 minutes

    # Dashboard settings
    dashboard_port: int = 8080
    dashboard_host: str = "localhost"


class MonitoringManager:
    """Central monitoring management system"""

    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.metrics_collector = None
        self.alert_manager = None
        self.log_aggregator = None
        self.trace_manager = None
        self.dashboard_generator = None

        self._monitoring_task: Optional[asyncio.Task] = None
        self._alerting_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the monitoring system"""
        if not self.config.enabled:
            return

        # Initialize components
        await self._initialize_components()

        # Start monitoring tasks
        if self.config.metrics_enabled:
            self._monitoring_task = asyncio.create_task(self._run_metrics_collection())

        if self.config.alerting_enabled:
            self._alerting_task = asyncio.create_task(self._run_alert_checking())

    async def stop(self):
        """Stop the monitoring system"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self._alerting_task:
            self._alerting_task.cancel()
            try:
                await self._alerting_task
            except asyncio.CancelledError:
                pass

    async def _initialize_components(self):
        """Initialize monitoring components"""
        if self.config.metrics_enabled:
            try:
                from .metrics import MetricsCollector
                self.metrics_collector = MetricsCollector()
            except ImportError:
                pass

        if self.config.alerting_enabled:
            try:
                from .alert_manager import AlertManager
                self.alert_manager = AlertManager()
            except ImportError:
                pass

        if self.config.logging_enabled:
            try:
                from .log_aggregator import LogAggregator
                self.log_aggregator = LogAggregator()
            except ImportError:
                pass

        if self.config.dashboard_enabled:
            try:
                from .dashboard_generator import DashboardGenerator
                self.dashboard_generator = DashboardGenerator()
            except ImportError:
                pass

    async def _run_metrics_collection(self):
        """Run periodic metrics collection"""
        while True:
            try:
                if self.metrics_collector:
                    await self.metrics_collector.collect_all()
                await asyncio.sleep(self.config.metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Metrics collection error: {e}")
                await asyncio.sleep(self.config.metrics_interval)

    async def _run_alert_checking(self):
        """Run periodic alert checking"""
        while True:
            try:
                if self.alert_manager and self.metrics_collector:
                    # Check metrics against alert rules
                    all_values = await self.metrics_collector.collect_all()
                    for value in all_values:
                        self.alert_manager.evaluate_metric(value.name, value.value)

                await asyncio.sleep(self.config.alert_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Alert checking error: {e}")
                await asyncio.sleep(self.config.alert_check_interval)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        if not self.metrics_collector:
            return {}

        try:
            # Get basic metrics summary
            return {
                "total_metrics": len(self.metrics_collector._metrics),
                "active_collectors": len(self.metrics_collector._collectors),
                "timestamp": time.time()
            }
        except Exception:
            return {}

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get a summary of current alerts"""
        if not self.alert_manager:
            return {}

        try:
            active_alerts = self.alert_manager.get_active_alerts()
            return {
                "active_alerts": len(active_alerts),
                "total_rules": len(self.alert_manager.rules),
                "alert_history_count": len(self.alert_manager.alert_history)
            }
        except Exception:
            return {}

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        health = {
            "monitoring_enabled": self.config.enabled,
            "metrics_healthy": self.metrics_collector is not None,
            "alerting_healthy": self.alert_manager is not None,
            "logging_healthy": self.log_aggregator is not None,
            "dashboard_healthy": self.dashboard_generator is not None,
            "timestamp": time.time()
        }

        # Add component health details
        if self.metrics_collector:
            try:
                health["metrics_status"] = "healthy"
                health["metrics_count"] = len(self.metrics_collector._metrics)
            except Exception:
                health["metrics_status"] = "error"

        if self.alert_manager:
            try:
                health["alerting_status"] = "healthy"
                health["active_alerts"] = len(self.alert_manager.get_active_alerts())
            except Exception:
                health["alerting_status"] = "error"

        return health

    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        health = await self._check_component_health()

        # Check database connections
        db_health = await self._check_database_health()
        health.update(db_health)

        # Check cache health
        cache_health = await self._check_cache_health()
        health.update(cache_health)

        # Check external services
        external_health = await self._check_external_services()
        health.update(external_health)

        return health

    async def _check_component_health(self) -> Dict[str, Any]:
        """Check health of monitoring components"""
        component_health = {}

        # Check metrics collector
        if self.metrics_collector:
            try:
                metrics = await self.metrics_collector.collect_all()
                component_health["metrics_collector"] = {
                    "status": "healthy",
                    "metrics_count": len(metrics)
                }
            except Exception as e:
                component_health["metrics_collector"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            component_health["metrics_collector"] = {"status": "disabled"}

        # Check alert manager
        if self.alert_manager:
            try:
                active_alerts = self.alert_manager.get_active_alerts()
                component_health["alert_manager"] = {
                    "status": "healthy",
                    "active_alerts": len(active_alerts)
                }
            except Exception as e:
                component_health["alert_manager"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            component_health["alert_manager"] = {"status": "disabled"}

        return component_health

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connection health"""
        db_health = {"databases": {}}

        try:
            from pydance.db import DatabaseConnection
            db = DatabaseConnection.get_instance()
            if db:
                # Test connection
                await db.test_connection()
                db_health["databases"]["main"] = {"status": "healthy"}
            else:
                db_health["databases"]["main"] = {"status": "disconnected"}
        except Exception as e:
            db_health["databases"]["main"] = {"status": "error", "error": str(e)}

        return db_health

    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache system health"""
        cache_health = {"caches": {}}

        try:
            from pydance.caching import get_cache_manager
            cache_manager = get_cache_manager()
            if cache_manager:
                metrics = cache_manager.get_metrics()
                cache_health["caches"]["main"] = {
                    "status": "healthy",
                    "hit_rate": metrics.get("hit_rate", 0),
                    "total_hits": metrics.get("total_hits", 0)
                }
            else:
                cache_health["caches"]["main"] = {"status": "disabled"}
        except Exception as e:
            cache_health["caches"]["main"] = {"status": "error", "error": str(e)}

        return cache_health

    async def _check_external_services(self) -> Dict[str, Any]:
        """Check external service health"""
        external_health = {"external_services": {}}

        # Check Redis if configured
        try:
            from pydance.caching.cache_manager import RedisCache
            redis_cache = RedisCache(None)
            await redis_cache.initialize()
            await redis_cache.close()
            external_health["external_services"]["redis"] = {"status": "healthy"}
        except Exception as e:
            external_health["external_services"]["redis"] = {"status": "error", "error": str(e)}

        return external_health
