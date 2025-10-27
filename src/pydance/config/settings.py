"""
Django/Laravel style settings for Pydance framework.

This module provides a unified settings system that combines Django's settings
approach with Laravel's .env file configuration. All configuration comes from
settings and .env files, not from config classes.
"""

import os
import secrets
import string
import warnings
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Laravel-style env() helper function (moved before Settings so Settings can use it)
def env(key: str, default: Any = None) -> Any:
    """Laravel-style env() helper function."""
    value = os.getenv(key)
    if value is None:
        return default

    # Type casting like Laravel
    if isinstance(default, bool):
        return value.lower() in ('true', '1', 'yes', 'on')
    elif isinstance(default, int):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    elif isinstance(default, float):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    elif isinstance(default, list):
        return [item.strip() for item in value.split(',') if item.strip()]

    return value

# Django/Laravel style settings object
class Settings:
    """Global settings object combining Django and Laravel patterns."""

    def __init__(self):
        self._settings: Dict[str, Any] = {}
        self._validate_environment()
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load all settings from environment variables and .env files (Laravel style)."""
        # Load .env file first (lower priority)
        load_dotenv(override=False)  # Don't override existing environment variables

        # Load .env.local if it exists (for local overrides)
        load_dotenv('.env.local', override=False)

        # Load .env.{environment} if it exists (e.g., .env.production)
        env_name = os.getenv('APP_ENV', 'local')
        env_specific_file = f'.env.{env_name}'
        if Path(env_specific_file).exists():
            load_dotenv(env_specific_file, override=False)

        # Now load settings from environment (highest priority)
        # Core Django-style settings
        self.DEBUG = env('DEBUG', 'False').lower() == 'true'
        # CRITICAL SECURITY FIX: Generate a secure secret key if not provided
        self.SECRET_KEY = env('SECRET_KEY', self._generate_secure_secret_key())
        self.ALLOWED_HOSTS = env('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

        # Enhanced Database Configuration - supports both URL and individual settings
        self.DATABASE_URL = env('DATABASE_URL', 'sqlite:///db.sqlite3')

        # Individual database settings (Django style) - better user experience
        self.DB_ENGINE = env('DB_ENGINE', 'sqlite')
        self.DB_NAME = env('DB_NAME', 'db.sqlite3')
        self.DB_HOST = env('DB_HOST', 'localhost')
        # Keep None when DB_PORT is not set; env() will cast to int when default is int
        self.DB_PORT = env('DB_PORT', 0) if env('DB_PORT') else None
        self.DB_USER = env('DB_USER', '')
        self.DB_PASSWORD = env('DB_PASSWORD', '')

        # Pool settings
        self.DB_POOL_SIZE = env('DB_POOL_SIZE', 10)
        self.DB_MAX_OVERFLOW = env('DB_MAX_OVERFLOW', 20)
        self.DB_POOL_TIMEOUT = env('DB_POOL_TIMEOUT', 30)
        self.DB_POOL_RECYCLE = env('DB_POOL_RECYCLE', 3600)
        self.DB_ECHO = env('DB_ECHO', 'False').lower() == 'true'

        # Database-specific settings for better configuration experience
        self.DB_CHARSET = env('DB_CHARSET', 'utf8mb4')
        self.DB_COLLATION = env('DB_COLLATION', 'utf8mb4_unicode_ci')
        self.DB_AUTOCOMMIT = env('DB_AUTOCOMMIT', 'True').lower() == 'true'
        self.DB_ISOLATION_LEVEL = env('DB_ISOLATION_LEVEL', 'READ_COMMITTED')

        # Connection retry settings
        self.DB_RETRY_ATTEMPTS = env('DB_RETRY_ATTEMPTS', 3)
        self.DB_RETRY_DELAY = env('DB_RETRY_DELAY', 1.0)

        # Read replica settings (for load balancing)
        self.DB_READ_REPLICAS = env('DB_READ_REPLICAS', '').split(',') if env('DB_READ_REPLICAS') else []
        self.DB_USE_READ_REPLICAS = env('DB_USE_READ_REPLICAS', 'False').lower() == 'true'

        # Email (Laravel style)
        self.MAIL_MAILER = env('MAIL_MAILER', 'smtp')
        self.MAIL_HOST = env('MAIL_HOST', 'smtp.gmail.com')
        self.MAIL_PORT = env('MAIL_PORT', 587)
        self.MAIL_USERNAME = env('MAIL_USERNAME', '')
        self.MAIL_PASSWORD = env('MAIL_PASSWORD', '')
        self.MAIL_ENCRYPTION = env('MAIL_ENCRYPTION', 'tls')
        self.MAIL_FROM_ADDRESS = env('MAIL_FROM_ADDRESS', 'noreply@example.com')
        self.MAIL_FROM_NAME = env('MAIL_FROM_NAME', 'Pydance App')

        # Server (Laravel style)
        self.APP_NAME = env('APP_NAME', 'Pydance Application')
        self.APP_ENV = env('APP_ENV', 'local')
        self.APP_KEY = env('APP_KEY', '')
        self.APP_DEBUG = env('APP_DEBUG', 'False').lower() == 'true'
        self.APP_URL = env('APP_URL', 'http://localhost')

        # Server configuration
        self.HOST = env('HOST', '127.0.0.1')
        self.PORT = env('PORT', '8000')
        self.WORKERS = env('WORKERS', '1')

        # Cache (Laravel style)
        self.CACHE_DRIVER = env('CACHE_DRIVER', 'memory')
        self.CACHE_HOST = env('CACHE_HOST', 'localhost')
        self.CACHE_PORT = env('CACHE_PORT', '6379')
        self.CACHE_PASSWORD = env('CACHE_PASSWORD', '')
        self.CACHE_DATABASE = env('CACHE_DATABASE', '0')

        # Session (Laravel style)
        self.SESSION_DRIVER = env('SESSION_DRIVER', 'database')
        self.SESSION_LIFETIME = env('SESSION_LIFETIME', '120')
        self.SESSION_ENCRYPT = env('SESSION_ENCRYPT', 'False').lower() == 'true'
        self.SESSION_PATH = env('SESSION_PATH', '/')
        self.SESSION_DOMAIN = env('SESSION_DOMAIN', '')

        # Storage (Laravel style)
        self.FILESYSTEM_DISK = env('FILESYSTEM_DISK', 'local')
        self.AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', '')
        self.AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', '')
        self.AWS_DEFAULT_REGION = env('AWS_DEFAULT_REGION', 'us-east-1')
        self.AWS_BUCKET = env('AWS_BUCKET', '')

        # Security
        self.CSRF_PROTECTION = env('CSRF_PROTECTION', 'True').lower() == 'true'
        self.SECURITY_HEADERS = env('SECURITY_HEADERS', 'True').lower() == 'true'

        # Logging (Laravel style)
        self.LOG_CHANNEL = env('LOG_CHANNEL', 'stack')
        self.LOG_LEVEL = env('LOG_LEVEL', 'debug' if self.DEBUG else 'error')

        # Static Files (Django style)
        self.STATIC_URL = env('STATIC_URL', '/static/')
        self.STATIC_ROOT = env('STATIC_ROOT', 'staticfiles')
        self.STATICFILES_DIRS = env('STATICFILES_DIRS', 'static').split(',')

        # Template Engine Configuration
        self.TEMPLATE_ENGINE = env('TEMPLATE_ENGINE', 'pydance.templating.languages.lean.LeanTemplateEngine')
        self.TEMPLATES_DIRS = env('TEMPLATES_DIRS', 'templates').split(',')
        self.TEMPLATE_DEBUG = env('TEMPLATE_DEBUG', 'False').lower() == 'true'
        self.TEMPLATE_CACHE = env('TEMPLATE_CACHE', 'True').lower() == 'true'
        self.TEMPLATE_AUTOESCAPE = env('TEMPLATE_AUTOESCAPE', 'True').lower() == 'true'

        # Django-style template configuration (legacy support)
        self.TEMPLATES = [
            {
                'BACKEND': env('TEMPLATE_BACKEND', 'pydance.templating.languages.lean.LeanTemplateEngine'),
                'DIRS': self.TEMPLATES_DIRS,
                'APP_DIRS': env('TEMPLATE_APP_DIRS', 'True').lower() == 'true',
                'OPTIONS': {
                    'context_processors': env('TEMPLATE_CONTEXT_PROCESSORS', 'pydance.templating.context_processors.debug,pydance.templating.context_processors.request').split(','),
                    'debug': self.TEMPLATE_DEBUG,
                    'cache': self.TEMPLATE_CACHE,
                    'autoescape': self.TEMPLATE_AUTOESCAPE,
                },
            },
        ]

        # Middleware (Laravel style)
        self.MIDDLEWARE = [
            'pydance.middleware.cors.CORSMiddleware',
            'pydance.middleware.security.SecurityMiddleware',
            'pydance.middleware.csrf.CSRFMiddleware',
            'pydance.middleware.session.SessionMiddleware',
        ]

        # Custom middleware aliases - users register their middleware here
        self.MIDDLEWARE_ALIASES = {
            # Laravel-style middleware aliases
            'auth': 'pydance.contrib.auth.middleware.AuthenticationMiddleware',
            'guest': 'pydance.contrib.auth.middleware.GuestMiddleware',
            'throttle': 'pydance.middleware.throttle.ThrottleMiddleware',
            'cors': 'pydance.middleware.cors.CORSMiddleware',
            'csrf': 'pydance.middleware.csrf.CSRFMiddleware',
            'session': 'pydance.middleware.session.SessionMiddleware',
            'verify_csrf_token': 'pydance.middleware.csrf.CSRFMiddleware',
            'encrypt_cookies': 'pydance.middleware.cookies.EncryptCookiesMiddleware',
            'add_queued_cookies_to_response': 'pydance.middleware.cookies.QueueCookiesMiddleware',
            'start_session': 'pydance.middleware.session.SessionMiddleware',
            'share_errors_from_session': 'pydance.middleware.session.ShareErrorsFromSessionMiddleware',
            'verify_post_size': 'pydance.middleware.body_size.VerifyPostSizeMiddleware',
            'form_content_types': 'pydance.middleware.content_type.FormContentTypesMiddleware',
        }

        # Laravel-style middleware groups
        self.MIDDLEWARE_GROUPS = {
            'web': [
                'verify_csrf_token',
                'share_errors_from_session',
                'start_session',
                'form_content_types',
                'verify_post_size',
                'add_queued_cookies_to_response',
                'encrypt_cookies',
            ],
            'api': [
                'throttle:api',
                'auth:sanctum',
            ],
            'guest': [
                'guest',
                'throttle:guest',
            ],
            'auth': [
                'auth',
                'throttle:user',
            ],
        }

        # Installed Apps (Django style)
        self.INSTALLED_APPS = [
            'pydance.contrib.auth',
            'pydance.contrib.contenttypes',
            'pydance.contrib.sessions',
            'pydance.contrib.messages',
        ]

        # Database settings (Django style)
        self.DATABASES = {
            'default': {
                'ENGINE': 'pydance.db.backends.sqlite3',
                'NAME': self.DATABASE_URL.replace('sqlite:///', ''),
            }
        }

        # Authentication (Django style)
        self.AUTH_USER_MODEL = 'auth.User'
        self.LOGIN_URL = '/auth/login/'
        self.LOGOUT_REDIRECT_URL = '/'

        # Internationalization (Django style)
        self.LANGUAGE_CODE = env('LANGUAGE_CODE', 'en-us')
        self.TIME_ZONE = env('TIME_ZONE', 'UTC')
        self.USE_I18N = env('USE_I18N', 'True').lower() == 'true'
        self.USE_L10N = env('USE_L10N', 'True').lower() == 'true'
        self.USE_TZ = env('USE_TZ', 'True').lower() == 'true'

        # Custom settings from .env
        self._load_custom_settings()

        # Validate critical security settings after loading
        self._validate_critical_settings()

    def _validate_environment(self) -> None:
        """Validate that required environment variables are properly set."""
        # Check if .env file exists and warn if it doesn't
        env_file = Path('.env')
        if not env_file.exists():
            warnings.warn(
                "No .env file found. Using default settings. "
                "For production, create a .env file with proper SECRET_KEY and other settings.",
                UserWarning,
                stacklevel=2
            )

    def _generate_secure_secret_key(self) -> str:
        """Generate a cryptographically secure secret key."""
        # Generate a 50-character secret key using letters, digits, and symbols
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(alphabet) for _ in range(50))

    def _validate_critical_settings(self) -> None:
        """Validate critical security settings."""
        errors = []
        warnings_list = []

        # Validate SECRET_KEY strength
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            warnings_list.append(
                f"SECRET_KEY is too weak (length: {len(self.SECRET_KEY)}). "
                "Using auto-generated secure key."
            )
            self.SECRET_KEY = self._generate_secure_secret_key()

        # CRITICAL: Check for development keys in production
        dev_keys = ['your-secret-key', 'change-me', 'dev-key', 'test-key', 'example']
        if any(dev_key in self.SECRET_KEY.lower() for dev_key in dev_keys):
            errors.append(
                "SECRET_KEY contains development/insecure patterns. "
                "Set a proper SECRET_KEY environment variable."
            )
            self.SECRET_KEY = self._generate_secure_secret_key()

        # Warn about debug mode in production-like environments
        if self.DEBUG and self.APP_ENV in ['production', 'prod']:
            warnings_list.append(
                "DEBUG mode is enabled in production environment. "
                "This may expose sensitive information."
            )

        # Validate database configuration
        if not self.DATABASE_URL and not all([self.DB_ENGINE, self.DB_NAME]):
            errors.append(
                "Database configuration is incomplete. "
                "Set DATABASE_URL or configure DB_ENGINE and DB_NAME."
            )

        # Validate database credentials in production
        if self.APP_ENV in ['production', 'prod']:
            if self.DB_PASSWORD in ['password', '123456', 'admin', '']:
                errors.append(
                    "Database password is insecure. "
                    "Use a strong password for production environments."
                )

        # Validate server configuration
        if self.APP_ENV in ['production', 'prod']:
            if self.HOST in ['127.0.0.1', 'localhost']:
                warnings_list.append(
                    "Server is binding to localhost in production. "
                    "Consider binding to 0.0.0.0 or a specific interface."
                )

        # Validate email configuration for production
        if self.APP_ENV in ['production', 'prod']:
            if not self.MAIL_PASSWORD or self.MAIL_PASSWORD in ['password', '123456']:
                warnings_list.append(
                    "Email password may be insecure. "
                    "Configure proper email credentials for production."
                )

        # Show all errors (critical issues)
        for error in errors:
            print(f"CRITICAL ERROR: {error}")

        # Show warnings (non-critical but important)
        for warning in warnings_list:
            warnings.warn(warning, UserWarning, stacklevel=3)

        # Exit if critical errors found
        if errors:
            raise ValueError(f"Configuration validation failed with {len(errors)} critical errors")

    def _load_custom_settings(self) -> None:
        """Load any custom settings from .env file."""
        # Load .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    setattr(self, key, value)

    def __getattr__(self, name: str) -> Any:
        """Get setting value (Django style)."""
        if name in self._settings:
            return self._settings[name]
        raise AttributeError(f"Setting '{name}' not found")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set setting value."""
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._settings[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        """Get setting with default (Django style)."""
        return getattr(self, name, default)

    def configure(self, **kwargs) -> None:
        """Configure settings (Django style)."""
        for key, value in kwargs.items():
            setattr(self, key, value)


# Global settings instance (Django style)
# Make the settings object lazy to avoid doing heavy environment/.env work at import time.
class LazySettings:
    """Proxy that lazily creates the real Settings instance on first access."""
    def __init__(self) -> None:
        self._wrapped: Optional[Settings] = None

    def _setup(self) -> None:
        if self._wrapped is None:
            self._wrapped = Settings()

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - thin proxy
        self._setup()
        assert self._wrapped is not None
        return getattr(self._wrapped, name)

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover - thin proxy
        if name == '_wrapped':
            super().__setattr__(name, value)
            return
        self._setup()
        assert self._wrapped is not None
        setattr(self._wrapped, name, value)


# Backwards compatible module-level object. Code that imports `settings` will still
# get an object, but the heavy loading is deferred until it's actually used.
settings = LazySettings()


# Django-style configuration functions
def configure(**kwargs) -> None:
    """Configure global settings."""
    # Ensure settings object exists and delegate
    settings.configure(**kwargs)

def get_config() -> Settings:
    """Get the global settings instance."""
    # Return the (possibly-not-yet-instantiated) settings proxy. Callers that
    # need the real Settings object may access attributes or use the proxy as before.
    return settings

# Database configuration helpers
def get_database_config() -> Dict[str, Any]:
    """Get database configuration in a user-friendly format."""
    return {
        'engine': settings.DB_ENGINE,
        'name': settings.DB_NAME,
        'host': settings.DB_HOST,
        'port': settings.DB_PORT,
        'user': settings.DB_USER,
        'password': settings.DB_PASSWORD,
        'charset': settings.DB_CHARSET,
        'collation': settings.DB_COLLATION,
        'autocommit': settings.DB_AUTOCOMMIT,
        'isolation_level': settings.DB_ISOLATION_LEVEL,
        'pool_size': settings.DB_POOL_SIZE,
        'max_overflow': settings.DB_MAX_OVERFLOW,
        'pool_timeout': settings.DB_POOL_TIMEOUT,
        'pool_recycle': settings.DB_POOL_RECYCLE,
        'echo': settings.DB_ECHO,
        'retry_attempts': settings.DB_RETRY_ATTEMPTS,
        'retry_delay': settings.DB_RETRY_DELAY,
        'read_replicas': settings.DB_READ_REPLICAS,
        'use_read_replicas': settings.DB_USE_READ_REPLICAS,
    }

def get_database_url() -> str:
    """Get database URL (backward compatibility)."""
    return settings.DATABASE_URL

def get_db_url() -> str:
    """Get database URL (new naming)."""
    return settings.DATABASE_URL

def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return settings.DEBUG

def is_testing() -> bool:
    """Check if testing mode is enabled."""
    return settings.APP_ENV == 'testing'

def get_secret_key() -> str:
    """Get secret key."""
    return settings.SECRET_KEY

def get_host() -> str:
    """Get server host."""
    return settings.HOST

def get_port() -> int:
    """Get server port."""
    return settings.PORT

def get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    return env(key, default)

def get_int_env(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    return env(key, default)

def get_list_env(key: str, default: List[str] = None) -> List[str]:
    """Get list environment variable."""
    return env(key, default or [])

__all__ = [
    'Settings', 'settings', 'env', 'configure', 'get_config',
    'get_database_config', 'get_database_url', 'get_db_url',
    'is_debug', 'is_testing', 'get_secret_key', 'get_host', 'get_port',
    'get_bool_env', 'get_int_env', 'get_list_env'
]
