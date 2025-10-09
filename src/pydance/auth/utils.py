"""
Authentication Utilities for Pydance Framework

Utility functions for password hashing, token generation, and security.
"""

import hashlib
import hmac
import secrets
import base64
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Hash password with salt using SHA3"""
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2 with SHA3 for key derivation
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA3_256(),
        length=32,
        salt=salt.encode('utf-8'),
        iterations=100000,
        backend=default_backend()
    )

    key = kdf.derive(password.encode('utf-8'))

    return {
        'hash': base64.b64encode(key).decode('utf-8'),
        'salt': salt,
        'algorithm': 'sha3_256',
        'iterations': 100000
    }


def verify_password(password: str, stored_hash: Dict[str, str]) -> bool:
    """Verify password against stored hash"""
    try:
        salt = stored_hash['salt']
        algorithm = stored_hash.get('algorithm', 'sha3_256')
        iterations = stored_hash.get('iterations', 100000)

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend

        kdf = PBKDF2HMAC(
            algorithm=getattr(hashes, algorithm.upper())(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=iterations,
            backend=default_backend()
        )

        key = kdf.derive(password.encode('utf-8'))
        stored_key = base64.b64decode(stored_hash['hash'])

        return hmac.compare_digest(key, stored_key)
    except Exception:
        return False


def generate_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_hex(length)


def generate_api_key() -> str:
    """Generate API key"""
    return f"pk_{secrets.token_hex(16)}"


def generate_session_id() -> str:
    """Generate session ID"""
    return secrets.token_hex(32)


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_hex(32)


def constant_time_compare(a: str, b: str) -> bool:
    """Constant time string comparison to prevent timing attacks"""
    return hmac.compare_digest(a.encode(), b.encode())


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """Validate username format"""
    import re
    if len(username) < 3 or len(username) > 150:
        return False
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, username) is not None


def validate_password_strength(password: str) -> Tuple[bool, list]:
    """Validate password strength"""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if len(password) > 128:
        errors.append("Password is too long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
    sanitized = input_string

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    return sanitized


def generate_secure_password(length: int = 16) -> str:
    """Generate secure random password"""
    import string
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))


def create_jwt_token(payload: Dict[str, Any], secret: str, expiry: int = 3600) -> str:
    """Create JWT token"""
    try:
        import jwt
        payload['exp'] = datetime.utcnow() + timedelta(seconds=expiry)
        payload['iat'] = datetime.utcnow()
        return jwt.encode(payload, secret, algorithm='HS256')
    except ImportError:
        # Fallback if PyJWT is not installed
        return generate_token(32)


def verify_jwt_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token"""
    try:
        import jwt
        return jwt.decode(token, secret, algorithms=['HS256'])
    except ImportError:
        # Fallback if PyJWT is not installed
        return None
    except:
        return None


def get_client_ip(request) -> str:
    """Get client IP address from request"""
    # Try various headers
    for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
        ip = request.headers.get(header)
        if ip:
            return ip.split(',')[0].strip()

    return getattr(request, 'client_ip', None) or 'unknown'


def is_safe_url(url: str, allowed_hosts: Optional[list] = None) -> bool:
    """Check if URL is safe for redirection"""
    if not url:
        return False

    if '://' not in url:
        return True  # Relative URL

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)

        if not parsed.netloc:
            return True

        if allowed_hosts is None:
            return False

        return parsed.netloc in allowed_hosts
    except:
        return False


def rate_limit_check(client_id: str, requests: Dict[str, list], limit: int, window: int) -> bool:
    """Check rate limit for client"""
    now = datetime.utcnow()

    if client_id not in requests:
        requests[client_id] = []

    # Clean old requests
    cutoff = now - timedelta(seconds=window)
    requests[client_id] = [t for t in requests[client_id] if t > cutoff]

    # Check limit
    if len(requests[client_id]) >= limit:
        return False

    requests[client_id].append(now)
    return True


def generate_otp(length: int = 6) -> str:
    """Generate one-time password"""
    import random
    return ''.join(random.choices('0123456789', k=length))


def hash_otp(otp: str, secret: str) -> str:
    """Hash OTP for storage"""
    return hashlib.sha3_256((otp + secret).encode()).hexdigest()


def verify_otp(otp: str, hashed_otp: str, secret: str) -> bool:
    """Verify OTP against hash"""
    return constant_time_compare(hash_otp(otp, secret), hashed_otp)


def create_password_reset_token(user_id: int, secret: str) -> str:
    """Create password reset token"""
    payload = {
        'user_id': user_id,
        'type': 'password_reset',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return create_jwt_token(payload, secret, 3600)


def verify_password_reset_token(token: str, secret: str) -> Optional[int]:
    """Verify password reset token and return user ID"""
    payload = verify_jwt_token(token, secret)
    if payload and payload.get('type') == 'password_reset':
        return payload.get('user_id')
    return None


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data in logs"""
    sensitive_fields = ['password', 'password_hash', 'token', 'secret', 'key']
    masked = {}

    for key, value in data.items():
        if any(field in key.lower() for field in sensitive_fields):
            masked[key] = '***MASKED***'
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)
        else:
            masked[key] = value

    return masked


def audit_log(action: str, user_id: Optional[int] = None, details: Optional[Dict] = None):
    """Log authentication/authorization events"""
    log_entry = {
        'timestamp': datetime.utcnow(),
        'action': action,
        'user_id': user_id,
        'details': details or {}
    }

    # In real implementation, this would write to audit log
    print(f"AUDIT: {log_entry}")


# Security utilities
def check_password_breach(password: str) -> bool:
    """Check if password has been breached (mock implementation)"""
    # In real implementation, this would check against HaveIBeenPwned API
    # For now, just return False
    return False


def generate_device_fingerprint(request) -> str:
    """Generate device fingerprint from request"""
    components = [
        request.headers.get('User-Agent', ''),
        request.headers.get('Accept-Language', ''),
        get_client_ip(request),
        str(request.headers.get('Accept', ''))
    ]

    fingerprint = '|'.join(components)
    return hashlib.sha3_256(fingerprint.encode()).hexdigest()


def validate_device_trust(device_fingerprint: str, stored_fingerprints: list) -> bool:
    """Validate if device is trusted"""
    return device_fingerprint in stored_fingerprints


def encrypt_sensitive_data(data: str, key: str) -> str:
    """Encrypt sensitive data"""
    # Simple XOR encryption for demo - use proper encryption in production
    encrypted = ""
    key_len = len(key)
    for i, char in enumerate(data):
        encrypted += chr(ord(char) ^ ord(key[i % key_len]))

    return base64.b64encode(encrypted.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
    """Decrypt sensitive data"""
    try:
        encrypted = base64.b64decode(encrypted_data).decode()
        decrypted = ""

        key_len = len(key)
        for i, char in enumerate(encrypted):
            decrypted += chr(ord(char) ^ ord(key[i % key_len]))

        return decrypted
    except:
        raise ValueError("Decryption failed")


# Export utility functions
__all__ = [
    'hash_password',
    'verify_password',
    'generate_token',
    'generate_api_key',
    'generate_session_id',
    'generate_csrf_token',
    'constant_time_compare',
    'validate_email',
    'validate_username',
    'validate_password_strength',
    'sanitize_input',
    'generate_secure_password',
    'create_jwt_token',
    'verify_jwt_token',
    'get_client_ip',
    'is_safe_url',
    'rate_limit_check',
    'generate_otp',
    'hash_otp',
    'verify_otp',
    'create_password_reset_token',
    'verify_password_reset_token',
    'mask_sensitive_data',
    'audit_log',
    'check_password_breach',
    'generate_device_fingerprint',
    'validate_device_trust',
    'encrypt_sensitive_data',
    'decrypt_sensitive_data'
]

