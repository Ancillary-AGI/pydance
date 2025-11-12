"""
Alert management system for Pydance monitoring.
Provides alerting capabilities for metrics and system events.
"""

from typing import Dict, Any, List, Callable, Optional
import time
from enum import Enum
from dataclasses import dataclass


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    description: str
    metric_name: str
    condition: str  # e.g., "value > 90"
    severity: AlertSeverity
    threshold: float
    duration: int = 60  # seconds
    cooldown: int = 300  # seconds
    enabled: bool = True

    def evaluate(self, value: float) -> bool:
        """Evaluate if the alert condition is met"""
        if not self.enabled:
            return False

        # Simple condition evaluation
        if self.condition == "value > threshold":
            return value > self.threshold
        elif self.condition == "value < threshold":
            return value < self.threshold
        elif self.condition == "value >= threshold":
            return value >= self.threshold
        elif self.condition == "value <= threshold":
            return value <= self.threshold

        return False


@dataclass
class Alert:
    """Alert instance"""

    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: float
    status: AlertStatus = AlertStatus.ACTIVE
    resolved_at: Optional[float] = None

    def resolve(self):
        """Mark alert as resolved"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = time.time()

    def acknowledge(self):
        """Mark alert as acknowledged"""
        self.status = AlertStatus.ACKNOWLEDGED


class AlertManager:
    """Central alert management system"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []

    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]

    def evaluate_metric(self, metric_name: str, value: float):
        """Evaluate metric against all rules"""
        for rule in self.rules.values():
            if rule.metric_name == metric_name:
                if rule.evaluate(value):
                    self._trigger_alert(rule, value)

    def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert"""
        alert_id = f"{rule.name}_{int(time.time())}"

        # Check if alert is already active and within cooldown
        if alert_id in self.active_alerts:
            existing_alert = self.active_alerts[alert_id]
            if time.time() - existing_alert.timestamp < rule.cooldown:
                return

        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"{rule.description}: {value} {rule.condition.replace('value', '').replace('threshold', str(rule.threshold))}",
            value=value,
            threshold=rule.threshold,
            timestamp=time.time()
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Notify handlers
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Alert notification failed: {e}")

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolve()
            del self.active_alerts[alert_id]

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]

    def add_notification_handler(self, handler: Callable):
        """Add a notification handler"""
        self.notification_handlers.append(handler)

    def clear_all_alerts(self):
        """Clear all active alerts"""
        self.active_alerts.clear()
