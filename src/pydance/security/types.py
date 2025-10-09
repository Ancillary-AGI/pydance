"""Security-related type definitions."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Permission:
    """Permission definition."""
    name: str
    description: str
    resource: str
    actions: List[str]


@dataclass
class Role:
    """Role definition."""
    name: str
    description: str
    permissions: List[Permission]
    inherits_from: List[str] = field(default_factory=list)


@dataclass
class Policy:
    """Policy definition."""
    name: str
    description: str
    effect: str  # "allow" or "deny"
    principals: List[str]
    actions: List[str]
    resources: List[str]
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IAMUser:
    """IAM user."""
    id: str
    username: str
    roles: List[str]
    permissions: List[str]
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityEvent:
    """Security event."""
    id: str
    type: str
    severity: str
    timestamp: datetime
    source: str
    details: Dict[str, Any]


@dataclass
class AuditLogEntry:
    """Audit log entry."""
    id: str
    timestamp: datetime
    user_id: str | None
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: str | None = None


@dataclass
class DeviceFingerprint:
    """Device fingerprint for zero-trust."""
    device_id: str
    fingerprint: str
    last_seen: datetime
    trust_score: float


@dataclass
class TrustContext:
    """Trust context for zero-trust architecture."""
    user_id: str | None = None
    device_id: str | None = None
    session_id: str | None = None
    risk_level: str = "low"

class RateLimitAlgorithm(str, Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

@dataclass
class RateLimitConfig:
    requests: int
    window: int
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.FIXED_WINDOW

@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None

__all__ = [
    'Permission', 'Role', 'Policy', 'IAMUser',
    'SecurityEvent', 'AuditLogEntry',
    'DeviceFingerprint', 'TrustContext'
]
