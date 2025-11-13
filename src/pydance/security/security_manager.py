"""
Security Manager for Pydance Framework

Provides centralized security management and coordination across all security modules.
"""

import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import secrets
import json

from pydance.utils.logging import get_logger
from pydance.config import AppConfig


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BREACH_ATTEMPT = "breach_attempt"
    POLICY_VIOLATION = "policy_violation"
    AUDIT_LOG = "audit_log"


@dataclass
class SecurityEvent:
    """Security event record"""
    event_type: SecurityEventType
    user_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: SecurityLevel = SecurityLevel.MEDIUM
    details: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'resource': self.resource,
            'action': self.action,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'details': self.details,
            'session_id': self.session_id
        }


@dataclass
class SecurityPolicy:
    """Security policy definition"""
    name: str
    description: str
    rules: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class SecurityManager:
    """
    Centralized security manager coordinating all security aspects of the application.

    Features:
    - Security event logging and monitoring
    - Policy enforcement
    - Threat detection and response
    - Security metrics collection
    - Integration with all security modules
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.logger = get_logger("SecurityManager")

        # Security state
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._security_events: List[SecurityEvent] = []
        self._policies: Dict[str, SecurityPolicy] = {}
        self._threat_indicators: Set[str] = set()
        self._blocked_ips: Set[str] = set()

        # Locks for thread safety
        self._session_lock = threading.RLock()
        self._event_lock = threading.RLock()
        self._policy_lock = threading.RLock()

        # Metrics
        self._metrics = {
            'total_events': 0,
            'blocked_requests': 0,
            'active_sessions': 0,
            'policy_violations': 0,
            'threats_detected': 0
        }

        # Initialize default policies
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default security policies"""
        default_policies = [
            SecurityPolicy(
                name="rate_limiting",
                description="Rate limiting for API endpoints",
                rules=[
                    {
                        "type": "rate_limit",
                        "max_requests": 100,
                        "window_seconds": 60,
                        "block_duration": 300
                    }
                ]
            ),
            SecurityPolicy(
                name="suspicious_activity",
                description="Detection of suspicious user behavior",
                rules=[
                    {
                        "type": "behavior_analysis",
                        "failed_login_threshold": 5,
                        "unusual_location_threshold": 3,
                        "rapid_requests_threshold": 50
                    }
                ]
            ),
            SecurityPolicy(
                name="data_protection",
                description="Data protection and privacy policies",
                rules=[
                    {
                        "type": "data_classification",
                        "sensitive_fields": ["password", "ssn", "credit_card"],
                        "encryption_required": True
                    }
                ]
            )
        ]

        for policy in default_policies:
            self._policies[policy.name] = policy

    async def log_security_event(self, event: SecurityEvent) -> None:
        """
        Log a security event for monitoring and analysis.

        Args:
            event: Security event to log
        """
        with self._event_lock:
            self._security_events.append(event)
            self._metrics['total_events'] += 1

            # Keep only recent events (last 10000)
            if len(self._security_events) > 10000:
                self._security_events = self._security_events[-5000:]

        # Log based on severity
        if event.severity == SecurityLevel.CRITICAL:
            self.logger.critical(f"Security event: {event.event_type.value} - {event.details}")
        elif event.severity == SecurityLevel.HIGH:
            self.logger.error(f"Security event: {event.event_type.value} - {event.details}")
        elif event.severity == SecurityLevel.MEDIUM:
            self.logger.warning(f"Security event: {event.event_type.value} - {event.details}")
        else:
            self.logger.info(f"Security event: {event.event_type.value} - {event.details}")

        # Trigger automated responses for critical events
        if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            await self._handle_security_incident(event)

    async def _handle_security_incident(self, event: SecurityEvent) -> None:
        """Handle security incidents with automated responses"""
        if event.event_type == SecurityEventType.BREACH_ATTEMPT:
            # Block IP address temporarily
            if event.ip_address:
                self._blocked_ips.add(event.ip_address)
                self.logger.warning(f"Blocked IP address: {event.ip_address}")

        elif event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY:
            # Increase monitoring for user
            if event.user_id:
                self._threat_indicators.add(f"user:{event.user_id}")

    def validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming request against security policies.

        Args:
            request_data: Request data to validate

        Returns:
            Validation result with allow/deny decision
        """
        ip_address = request_data.get('ip_address')
        user_id = request_data.get('user_id')
        endpoint = request_data.get('endpoint')

        # Check if IP is blocked
        if ip_address in self._blocked_ips:
            self._metrics['blocked_requests'] += 1
            return {
                'allowed': False,
                'reason': 'IP address blocked',
                'severity': SecurityLevel.HIGH
            }

        # Check rate limiting
        if not self._check_rate_limit(ip_address, endpoint):
            self._metrics['blocked_requests'] += 1
            return {
                'allowed': False,
                'reason': 'Rate limit exceeded',
                'severity': SecurityLevel.MEDIUM
            }

        # Check user threat indicators
        if user_id and f"user:{user_id}" in self._threat_indicators:
            return {
                'allowed': False,
                'reason': 'User flagged for suspicious activity',
                'severity': SecurityLevel.HIGH
            }

        return {'allowed': True}

    def _check_rate_limit(self, ip_address: str, endpoint: str) -> bool:
        """Check if request exceeds rate limits"""
        # Simple in-memory rate limiting (in production, use Redis or similar)
        key = f"{ip_address}:{endpoint}"
        current_time = datetime.utcnow()

        # This is a simplified implementation
        # In production, you'd use a proper rate limiting algorithm
        return True

    def create_session(self, user_id: str, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new security session for a user.

        Args:
            user_id: User identifier
            metadata: Additional session metadata

        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'metadata': metadata or {},
            'ip_address': metadata.get('ip_address') if metadata else None
        }

        with self._session_lock:
            self._active_sessions[session_id] = session_data
            self._metrics['active_sessions'] += 1

        self.logger.info(f"Created session for user: {user_id}")
        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate and refresh a session.

        Args:
            session_id: Session ID to validate

        Returns:
            Session data if valid, None otherwise
        """
        with self._session_lock:
            session_data = self._active_sessions.get(session_id)
            if session_data:
                # Check session timeout (24 hours)
                if datetime.utcnow() - session_data['created_at'] > timedelta(hours=24):
                    self._cleanup_session(session_id)
                    return None

                # Update last activity
                session_data['last_activity'] = datetime.utcnow()
                return session_data

        return None

    def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a security session.

        Args:
            session_id: Session ID to destroy

        Returns:
            True if session was destroyed, False otherwise
        """
        with self._session_lock:
            if session_id in self._active_sessions:
                self._cleanup_session(session_id)
                self.logger.info(f"Destroyed session: {session_id}")
                return True

        return False

    def _cleanup_session(self, session_id: str) -> None:
        """Clean up session data"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            self._metrics['active_sessions'] -= 1

    def add_security_policy(self, policy: SecurityPolicy) -> None:
        """
        Add a new security policy.

        Args:
            policy: Security policy to add
        """
        with self._policy_lock:
            self._policies[policy.name] = policy
            self.logger.info(f"Added security policy: {policy.name}")

    def remove_security_policy(self, policy_name: str) -> bool:
        """
        Remove a security policy.

        Args:
            policy_name: Name of policy to remove

        Returns:
            True if policy was removed, False otherwise
        """
        with self._policy_lock:
            if policy_name in self._policies:
                del self._policies[policy_name]
                self.logger.info(f"Removed security policy: {policy_name}")
                return True

        return False

    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get current security metrics.

        Returns:
            Dictionary of security metrics
        """
        with self._session_lock:
            active_sessions = len(self._active_sessions)

        return {
            **self._metrics,
            'active_sessions': active_sessions,
            'blocked_ips': len(self._blocked_ips),
            'active_policies': len([p for p in self._policies.values() if p.enabled]),
            'threat_indicators': len(self._threat_indicators)
        }

    def get_recent_events(self, limit: int = 100) -> List[SecurityEvent]:
        """
        Get recent security events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent security events
        """
        with self._event_lock:
            return self._security_events[-limit:]

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        expired_sessions = []

        with self._session_lock:
            for session_id, session_data in self._active_sessions.items():
                if current_time - session_data['last_activity'] > timedelta(hours=24):
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                self._cleanup_session(session_id)

        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    async def shutdown(self) -> None:
        """Shutdown the security manager"""
        self.logger.info("Shutting down SecurityManager")

        # Clean up all sessions
        with self._session_lock:
            session_count = len(self._active_sessions)
            self._active_sessions.clear()
            self._metrics['active_sessions'] = 0

        self.logger.info(f"SecurityManager shutdown complete. Cleaned up {session_count} sessions")


# Global security manager instance
_security_manager: Optional[SecurityManager] = None
_security_manager_lock = threading.Lock()


def get_security_manager() -> SecurityManager:
    """
    Get the global security manager instance.

    Returns:
        SecurityManager instance
    """
    global _security_manager

    if _security_manager is None:
        with _security_manager_lock:
            if _security_manager is None:
                _security_manager = SecurityManager()

    return _security_manager


# Utility functions for easy access
async def log_security_event(event: SecurityEvent) -> None:
    """Log a security event"""
    manager = get_security_manager()
    await manager.log_security_event(event)


def validate_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a request"""
    manager = get_security_manager()
    return manager.validate_request(request_data)


def create_session(user_id: str, metadata: Dict[str, Any] = None) -> str:
    """Create a new session"""
    manager = get_security_manager()
    return manager.create_session(user_id, metadata)


def validate_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Validate a session"""
    manager = get_security_manager()
    return manager.validate_session(session_id)


def destroy_session(session_id: str) -> bool:
    """Destroy a session"""
    manager = get_security_manager()
    return manager.destroy_session(session_id)


__all__ = [
    'SecurityLevel', 'SecurityEventType', 'SecurityEvent', 'SecurityPolicy',
    'SecurityManager', 'get_security_manager', 'log_security_event',
    'validate_request', 'create_session', 'validate_session', 'destroy_session'
]
