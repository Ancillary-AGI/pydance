"""
Enhanced Security Framework for Pydance
Provides enterprise-grade security features for mission-critical applications.
"""

# Authentication moved to auth module - use from pydance.auth import AuthManager
from .file_validation import (
    FileValidator, BasicFileValidator, ClamAVValidator,
    AWSGuardDutyValidator, CompositeValidator, SecurityManager,
    get_security_manager
)

__all__ = [
    'EncryptionService',
    'AuditLogger',
    'RoleBasedAccessControl',
    'RateLimiter',
    'CSRFProtection',
    'SecurityHeaders',
    'FileValidator',
    'BasicFileValidator', 
    'ClamAVValidator',
    'AWSGuardDutyValidator',
    'CompositeValidator',
    'SecurityManager',
    'get_security_manager'
]

