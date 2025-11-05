Configuration Guide
==================

This comprehensive guide covers all aspects of configuring Pydance applications for different environments and use cases.

Configuration Architecture
--------------------------

Pydance uses a layered configuration system that allows you to:

- **Environment-specific settings** via environment variables
- **Configuration classes** for different deployment environments
- **Runtime configuration** for dynamic settings
- **Validation and type checking** for configuration values

Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **Instance configuration** (app.config['KEY'] = value)
3. **Configuration class attributes**
4. **Default values** (lowest priority)

Basic Configuration
-------------------

Application Settings
~~~~~~~~~~~~~~~~~~~~

Core application configuration:

.. code-block:: python

   from pydance import Application

   app = Application(__name__)

   # Basic settings
   app.config['SECRET_KEY'] = 'your-secret-key'
   app.config['DEBUG'] = True
   app.config['TESTING'] = False

   # Application metadata
   app.config['APP_NAME'] = 'My Pydance App'
   app.config['APP_VERSION'] = '1.0.0'
   app.config['APP_DESCRIPTION'] = 'A Pydance web application'

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Using environment variables for configuration:

.. code-block:: python

   import os
   from pydance import Application

   app = Application(__name__)

   # Environment-based configuration
   app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
   app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
   app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')

   # With validation
   app.config['PORT'] = int(os.getenv('PORT', '8000'))
   app.config['WORKERS'] = int(os.getenv('WORKERS', '4'))

Configuration Classes
~~~~~~~~~~~~~~~~~~~~~

Organizing configuration with classes:

.. code-block:: python

   from pydance.config import Config
   import os

   class BaseConfig(Config):
       """Base configuration with common settings"""

       # Application settings
       APP_NAME = 'My Pydance App'
       APP_VERSION = '1.0.0'
       SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

       # Debug settings
       DEBUG = False
       TESTING = False

       # Server settings
       HOST = '0.0.0.0'
       PORT = 8000

       # Database settings
       DATABASE_URL = 'sqlite:///app.db'

       # Cache settings
       CACHE_TYPE = 'simple'
       CACHE_DEFAULT_TIMEOUT = 300

   class DevelopmentConfig(BaseConfig):
       """Development configuration"""

       DEBUG = True
       DATABASE_URL = os.getenv('DEV_DATABASE_URL', 'sqlite:///dev.db')

       # Development-specific settings
       LOG_LEVEL = 'DEBUG'
       CACHE_TYPE = 'null'  # Disable caching in development

   class ProductionConfig(BaseConfig):
       """Production configuration"""

       DEBUG = False
       TESTING = False

       # Production database
       DATABASE_URL = os.getenv('DATABASE_URL')

       # Security settings
       SESSION_COOKIE_SECURE = True
       SESSION_COOKIE_HTTPONLY = True
       SESSION_COOKIE_SAMESITE = 'Lax'

       # Performance settings
       CACHE_TYPE = 'redis'
       CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

       # Logging
       LOG_LEVEL = 'WARNING'

   class TestingConfig(BaseConfig):
       """Testing configuration"""

       TESTING = True
       DEBUG = True

       # Use in-memory database for tests
       DATABASE_URL = 'sqlite:///:memory:'

       # Disable CSRF in tests
       WTF_CSRF_ENABLED = False

       # Use null cache for tests
       CACHE_TYPE = 'null'

       # Disable external services
       MAIL_SUPPRESS_SEND = True

   # Configuration mapping
   config = {
       'development': DevelopmentConfig,
       'production': ProductionConfig,
       'testing': TestingConfig,
       'default': DevelopmentConfig
   }

Using Configuration Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydance import Application
   from config import config
   import os

   def create_app(config_name=None):
       if config_name is None:
           config_name = os.getenv('FLASK_ENV', 'development')

       app = Application(__name__)

       # Load configuration
       config_class = config[config_name]
       app.config.from_object(config_class)

       return app

Database Configuration
----------------------

SQLAlchemy Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class Config:
       # Database connection
       SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')

       # Database engine options
       SQLALCHEMY_ENGINE_OPTIONS = {
           'pool_size': 10,
           'pool_recycle': 3600,
           'pool_pre_ping': True,
           'echo': False  # Set to True for SQL query logging
       }

       # Track modifications (disable in production for performance)
       SQLALCHEMY_TRACK_MODIFICATIONS = False

       # Database migration settings
       SQLALCHEMY_MIGRATE_REPO = 'migrations'

PostgreSQL Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class PostgreSQLConfig:
       # Connection string
       DATABASE_URL = 'postgresql://user:password@localhost:5432/dbname'

       # Advanced connection options
       SQLALCHEMY_ENGINE_OPTIONS = {
           'pool_size': 20,
           'max_overflow': 30,
           'pool_timeout': 30,
           'pool_recycle': 3600,
           'pool_pre_ping': True,
           'echo': False
       }

       # PostgreSQL-specific settings
       DB_CHARSET = 'utf8'
       DB_COLLATION = 'en_US.UTF-8'

MySQL Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MySQLConfig:
       # Connection string
       DATABASE_URL = 'mysql://user:password@localhost:3306/dbname'

       # MySQL-specific options
       SQLALCHEMY_ENGINE_OPTIONS = {
           'pool_size': 20,
           'max_overflow': 30,
           'pool_recycle': 3600,
           'pool_pre_ping': True,
           'connect_args': {
               'charset': 'utf8mb4',
               'autocommit': False,
               'init_command': 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
           }
       }

MongoDB Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MongoDBConfig:
       # MongoDB connection
       MONGODB_SETTINGS = {
           'db': 'myapp',
           'host': os.getenv('MONGODB_HOST', 'localhost'),
           'port': int(os.getenv('MONGODB_PORT', 27017)),
           'username': os.getenv('MONGODB_USERNAME'),
           'password': os.getenv('MONGODB_PASSWORD'),
           'authentication_source': 'admin'
       }

       # Connection options
       MONGODB_CONNECT = True
       MONGODB_MAX_POOL_SIZE = 10
       MONGODB_MIN_POOL_SIZE = 5
       MONGODB_MAX_IDLE_TIME_MS = 30000

Redis Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class RedisConfig:
       # Redis connection
       REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

       # Redis settings
       REDIS_DB = 0
       REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
       REDIS_SOCKET_TIMEOUT = 5
       REDIS_SOCKET_CONNECT_TIMEOUT = 5

       # Cache settings
       CACHE_TYPE = 'redis'
       CACHE_REDIS_URL = REDIS_URL
       CACHE_REDIS_DB = REDIS_DB
       CACHE_DEFAULT_TIMEOUT = 300

Security Configuration
----------------------

Session Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class SecurityConfig:
       # Session settings
       SECRET_KEY = os.getenv('SECRET_KEY')
       SESSION_TYPE = 'redis'  # or 'filesystem', 'mongodb'
       SESSION_REDIS = redis.from_url(os.getenv('REDIS_URL'))
       SESSION_PERMANENT = True
       SESSION_USE_SIGNER = True

       # Session security
       SESSION_COOKIE_SECURE = True
       SESSION_COOKIE_HTTPONLY = True
       SESSION_COOKIE_SAMESITE = 'Lax'
       SESSION_KEY_PREFIX = 'pydance:session:'

       # CSRF protection
       WTF_CSRF_ENABLED = True
       WTF_CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', SECRET_KEY)
       WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

Authentication Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class AuthConfig:
       # JWT settings
       JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
       JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
       JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
       JWT_TOKEN_LOCATION = ['headers', 'cookies']
       JWT_COOKIE_SECURE = True
       JWT_COOKIE_CSRF_PROTECT = True

       # OAuth settings
       OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID')
       OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')
       OAUTH_REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI')

       # Password settings
       PASSWORD_MIN_LENGTH = 8
       PASSWORD_REQUIRE_UPPERCASE = True
       PASSWORD_REQUIRE_LOWERCASE = True
       PASSWORD_REQUIRE_DIGITS = True
       PASSWORD_REQUIRE_SPECIAL = True

       # Rate limiting
       LOGIN_RATE_LIMIT = '5 per minute'
       API_RATE_LIMIT = '1000 per hour'

CORS Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class CORSConfig:
       # CORS settings
       CORS_ORIGINS = [
           'http://localhost:3000',
           'http://localhost:8080',
           'https://myapp.com'
       ]

       CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
       CORS_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
       CORS_EXPOSE_HEADERS = ['X-Total-Count', 'X-Page-Count']
       CORS_SUPPORTS_CREDENTIALS = True
       CORS_MAX_AGE = 86400  # 24 hours

Email Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class EmailConfig:
       # SMTP settings
       MAIL_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
       MAIL_PORT = int(os.getenv('SMTP_PORT', 587))
       MAIL_USE_TLS = True
       MAIL_USE_SSL = False
       MAIL_USERNAME = os.getenv('SMTP_USERNAME')
       MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
       MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@myapp.com')

       # Email templates
       MAIL_TEMPLATES_DIR = 'templates/email'
       MAIL_SUBJECT_PREFIX = '[MyApp] '

       # Async email
       MAIL_ASYNC = True
       MAIL_SUPPRESS_SEND = False

File Upload Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class UploadConfig:
       # Upload settings
       UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
       MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
       ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

       # Image processing
       IMAGE_MAX_SIZE = (1920, 1080)
       IMAGE_QUALITY = 85
       IMAGE_FORMATS = ['JPEG', 'PNG', 'WEBP']

       # File storage
       FILE_STORAGE_BACKEND = 'local'  # or 's3', 'gcs', 'azure'
       AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
       AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
       AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
       AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

Logging Configuration
---------------------

Basic Logging Setup
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   from pydance.utils.logging import setup_logging

   class LoggingConfig:
       # Logging level
       LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

       # Log format
       LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

       # Log handlers
       LOG_HANDLERS = ['console', 'file']
       LOG_FILE_PATH = 'logs/app.log'
       LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
       LOG_BACKUP_COUNT = 5

       # Structured logging
       LOG_STRUCTURED = True
       LOG_INCLUDE_EXTRA = True

Advanced Logging Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   LOGGING_CONFIG = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'standard': {
               'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
           },
           'detailed': {
               'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
           },
           'json': {
               'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
               'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
           }
       },
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
               'formatter': 'standard',
               'level': 'INFO'
           },
           'file': {
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': 'logs/app.log',
               'formatter': 'detailed',
               'level': 'DEBUG',
               'maxBytes': 10*1024*1024,
               'backupCount': 5
           },
           'error_file': {
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': 'logs/error.log',
               'formatter': 'detailed',
               'level': 'ERROR',
               'maxBytes': 10*1024*1024,
               'backupCount': 5
           }
       },
       'loggers': {
           'pydance': {
               'handlers': ['console', 'file'],
               'level': 'INFO',
               'propagate': False
           },
           'myapp': {
               'handlers': ['console', 'file', 'error_file'],
               'level': 'DEBUG',
               'propagate': False
           }
       },
       'root': {
           'handlers': ['console'],
           'level': 'WARNING'
       }
   }

Monitoring Configuration
------------------------

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MonitoringConfig:
       # Performance monitoring
       PERFORMANCE_MONITORING_ENABLED = True
       PERFORMANCE_SLOW_QUERY_THRESHOLD = 1.0  # seconds
       PERFORMANCE_MEMORY_THRESHOLD = 100 * 1024 * 1024  # 100MB

       # Metrics collection
       METRICS_ENABLED = True
       METRICS_BACKEND = 'prometheus'  # or 'statsd', 'datadog'
       METRICS_PREFIX = 'pydance'

       # Health checks
       HEALTH_CHECK_ENABLED = True
       HEALTH_CHECK_ENDPOINT = '/health'
       HEALTH_CHECK_DATABASE = True
       HEALTH_CHECK_REDIS = True

Sentry Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class SentryConfig:
       # Sentry error tracking
       SENTRY_DSN = os.getenv('SENTRY_DSN')
       SENTRY_ENVIRONMENT = os.getenv('FLASK_ENV', 'development')
       SENTRY_RELEASE = os.getenv('APP_VERSION', '1.0.0')

       # Sentry settings
       SENTRY_TRACES_SAMPLE_RATE = 0.1
       SENTRY_PROFILES_SAMPLE_RATE = 0.1
       SENTRY_SEND_DEFAULT_PII = False

       # Error filtering
       SENTRY_IGNORE_ERRORS = [
           'KeyboardInterrupt',
           'SystemExit'
       ]

API Configuration
-----------------

REST API Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class APIConfig:
       # API settings
       API_VERSION = 'v1'
       API_PREFIX = '/api/v1'
       API_DOCS_ENABLED = True
       API_DOCS_URL = '/api/docs'

       # Pagination
       API_DEFAULT_PAGE_SIZE = 20
       API_MAX_PAGE_SIZE = 100

       # Rate limiting
       API_RATE_LIMIT = '1000 per hour'
       API_RATE_LIMIT_STORAGE_URL = os.getenv('REDIS_URL')

       # Response formatting
       API_JSON_COMPACT = False
       API_ENVELOPE_DATA = True
       API_ENVELOPE_ERRORS = True

GraphQL Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class GraphQLConfig:
       # GraphQL settings
       GRAPHQL_ENABLED = True
       GRAPHQL_ENDPOINT = '/graphql'
       GRAPHQL_PLAYGROUND = True
       GRAPHQL_INTROSPECTION = True

       # Schema settings
       GRAPHQL_SCHEMA_MAX_DEPTH = 10
       GRAPHQL_SCHEMA_MAX_COMPLEXITY = 1000

       # Caching
       GRAPHQL_CACHE_ENABLED = True
       GRAPHQL_CACHE_TIMEOUT = 300

WebSocket Configuration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class WebSocketConfig:
       # WebSocket settings
       WEBSOCKET_ENABLED = True
       WEBSOCKET_MAX_CONNECTIONS = 1000
       WEBSOCKET_MESSAGE_SIZE_LIMIT = 64 * 1024  # 64KB
       WEBSOCKET_HEARTBEAT_INTERVAL = 30  # seconds

       # Security
       WEBSOCKET_ORIGIN_CHECK = True
       WEBSOCKET_ALLOWED_ORIGINS = ['http://localhost:3000']

       # Performance
       WEBSOCKET_COMPRESSION = True
       WEBSOCKET_BACKPRESSURE = True

Internationalization (i18n)
---------------------------

.. code-block:: python

   class I18NConfig:
       # Internationalization
       BABEL_DEFAULT_LOCALE = 'en'
       BABEL_DEFAULT_TIMEZONE = 'UTC'
       BABEL_SUPPORTED_LOCALES = ['en', 'es', 'fr', 'de', 'zh']

       # Translation settings
       BABEL_TRANSLATION_DIRECTORIES = ['translations']
       BABEL_DOMAIN = 'messages'

       # Date/time formatting
       BABEL_DATE_FORMATS = {
           'short': 'MM/dd/yyyy',
           'medium': 'MMM dd, yyyy',
           'long': 'MMMM dd, yyyy',
           'full': 'EEEE, MMMM dd, yyyy'
       }

       # Number formatting
       BABEL_NUMBER_FORMATS = {
           'decimal': '#,##0.###',
           'currency': '¤#,##0.00',
           'percent': '#,##0%'
       }

Task Queue Configuration
------------------------

.. code-block:: python

   class TaskConfig:
       # Celery settings
       CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
       CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379')

       # Task settings
       CELERY_TASK_SERIALIZER = 'json'
       CELERY_RESULT_SERIALIZER = 'json'
       CELERY_ACCEPT_CONTENT = ['json']
       CELERY_TIMEZONE = 'UTC'
       CELERY_ENABLE_UTC = True

       # Worker settings
       CELERY_WORKER_PREFETCH_MULTIPLIER = 1
       CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
       CELERY_WORKER_DISABLE_RATE_LIMITS = False

       # Task routing
       CELERY_TASK_ROUTES = {
           'myapp.tasks.heavy_task': {'queue': 'heavy'},
           'myapp.tasks.light_task': {'queue': 'light'}
       }

       # Monitoring
       CELERY_SEND_TASK_SENT_EVENT = True
       CELERY_TASK_SEND_SENT_EVENT = True

Runtime Configuration
--------------------

Dynamic Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydance.config import RuntimeConfig

   # Runtime configuration manager
   runtime_config = RuntimeConfig()

   # Set runtime values
   runtime_config.set('maintenance_mode', False)
   runtime_config.set('feature_flags.new_ui', True)

   # Get values with defaults
   maintenance_mode = runtime_config.get('maintenance_mode', False)
   new_ui_enabled = runtime_config.get('feature_flags.new_ui', False)

   # Watch for changes
   @runtime_config.on_change('maintenance_mode')
   def on_maintenance_mode_change(new_value):
       if new_value:
           # Enable maintenance mode
           app.config['MAINTENANCE_MODE'] = True
       else:
           # Disable maintenance mode
           app.config['MAINTENANCE_MODE'] = False

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydance.config import ConfigValidator
   from pydance.exceptions import ConfigurationError

   class ValidatedConfig:
       def __init__(self):
           self.validator = ConfigValidator()

           # Define validation rules
           self.validator.add_rule('SECRET_KEY', required=True, min_length=32)
           self.validator.add_rule('DATABASE_URL', required=True, url=True)
           self.validator.add_rule('PORT', type=int, min_value=1, max_value=65535)
           self.validator.add_rule('DEBUG', type=bool)

       def validate(self, config_dict):
           """Validate configuration dictionary"""
           errors = []

           for key, rules in self.validator.rules.items():
               value = config_dict.get(key)

               # Check required fields
               if rules.get('required') and value is None:
                   errors.append(f"{key} is required")
                   continue

               if value is not None:
                   # Type validation
                   expected_type = rules.get('type')
                   if expected_type and not isinstance(value, expected_type):
                       errors.append(f"{key} must be of type {expected_type.__name__}")

                   # String validations
                   if isinstance(value, str):
                       min_len = rules.get('min_length')
                       if min_len and len(value) < min_len:
                           errors.append(f"{key} must be at least {min_len} characters")

                       max_len = rules.get('max_length')
                       if max_len and len(value) > max_len:
                           errors.append(f"{key} must be at most {max_len} characters")

                   # Numeric validations
                   elif isinstance(value, (int, float)):
                       min_val = rules.get('min_value')
                       if min_val is not None and value < min_val:
                           errors.append(f"{key} must be at least {min_val}")

                       max_val = rules.get('max_value')
                       if max_val is not None and value > max_val:
                           errors.append(f"{key} must be at most {max_val}")

                   # URL validation
                   if rules.get('url') and not self._is_valid_url(value):
                       errors.append(f"{key} must be a valid URL")

           if errors:
               raise ConfigurationError(f"Configuration validation failed: {', '.join(errors)}")

           return True

       def _is_valid_url(self, url):
           """Simple URL validation"""
           import re
           url_pattern = re.compile(
               r'^https?://'  # http:// or https://
               r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
               r'localhost|'  # localhost...
               r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
               r'(?::\d+)?'  # optional port
               r'(?:/?|[/?]\S+)$', re.IGNORECASE)

           return url_pattern.match(url) is not None

Configuration Management Best Practices
---------------------------------------

Environment Separation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # config/__init__.py
   import os
   from .development import DevelopmentConfig
   from .production import ProductionConfig
   from .testing import TestingConfig

   def get_config():
       """Get configuration based on environment"""
       env = os.getenv('FLASK_ENV', 'development')

       configs = {
           'development': DevelopmentConfig,
           'production': ProductionConfig,
           'testing': TestingConfig
       }

       return configs.get(env, DevelopmentConfig)()

   # Use in application
   config = get_config()

Configuration Inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class BaseConfig:
       """Base configuration with common settings"""
       SECRET_KEY = os.getenv('SECRET_KEY')
       APP_NAME = 'MyApp'

       # Common database settings
       DB_ENGINE = 'postgresql'
       DB_HOST = 'localhost'
       DB_PORT = 5432

   class DevelopmentConfig(BaseConfig):
       """Development configuration"""
       DEBUG = True
       DB_NAME = 'myapp_dev'
       DB_USER = 'dev_user'
       DB_PASSWORD = 'dev_password'

       @property
       def DATABASE_URL(self):
           return f"{self.DB_ENGINE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

   class ProductionConfig(BaseConfig):
       """Production configuration"""
       DEBUG = False
       DB_NAME = os.getenv('DB_NAME')
       DB_USER = os.getenv('DB_USER')
       DB_PASSWORD = os.getenv('DB_PASSWORD')

       @property
       def DATABASE_URL(self):
           return f"{self.DB_ENGINE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

Configuration Testing
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from myapp.config import DevelopmentConfig, ProductionConfig

   class TestConfiguration:
       def test_development_config(self):
           config = DevelopmentConfig()
           assert config.DEBUG is True
           assert config.TESTING is False
           assert 'DATABASE_URL' in config.__dict__ or hasattr(config, 'DATABASE_URL')

       def test_production_config(self):
           config = ProductionConfig()
           assert config.DEBUG is False
           assert config.TESTING is False
           assert hasattr(config, 'DATABASE_URL')

       def test_required_environment_variables(self):
           # Test that required env vars are set
           import os
           required_vars = ['SECRET_KEY', 'DATABASE_URL']

           for var in required_vars:
               assert os.getenv(var), f"Required environment variable {var} is not set"

       def test_configuration_validation(self):
           from myapp.config import validate_config

           valid_config = {
               'SECRET_KEY': 'a' * 32,
               'DATABASE_URL': 'postgresql://user:pass@localhost/db',
               'PORT': 8000,
               'DEBUG': False
           }

           assert validate_config(valid_config)

           invalid_config = {
               'SECRET_KEY': 'short',
               'DATABASE_URL': 'invalid-url',
               'PORT': 99999
           }

           with pytest.raises(ConfigurationError):
               validate_config(invalid_config)

Configuration Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class DocumentedConfig:
       """Configuration class with documentation"""

       # Application settings
       SECRET_KEY = ConfigField(
           default=None,
           required=True,
           description="Secret key for session signing and CSRF protection",
           type=str,
           min_length=32
       )

       DEBUG = ConfigField(
           default=False,
           description="Enable debug mode",
           type=bool
       )

       DATABASE_URL = ConfigField(
           default='sqlite:///app.db',
           description="Database connection URL",
           type=str,
           validator=lambda x: x.startswith(('sqlite://', 'postgresql://', 'mysql://'))
       )

       @classmethod
       def get_documentation(cls):
           """Generate configuration documentation"""
           docs = []
           for name, field in cls.__dict__.items():
               if isinstance(field, ConfigField):
                   docs.append({
                       'name': name,
                       'description': field.description,
                       'default': field.default,
                       'required': field.required,
                       'type': field.type.__name__ if field.type else 'any'
                   })
           return docs

Configuration Migration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ConfigMigration:
       """Handle configuration migrations between versions"""

       @staticmethod
       def migrate_v1_to_v2(config):
           """Migrate from version 1 to version 2"""
           # Rename old settings
           if 'OLD_DATABASE_URI' in config:
               config['DATABASE_URL'] = config.pop('OLD_DATABASE_URI')

           # Update deprecated settings
           if 'USE_SSL' in config:
               config['SESSION_COOKIE_SECURE'] = config.pop('USE_SSL')

           # Add new required settings with defaults
           config.setdefault('SECRET_KEY', os.urandom(32).hex())
           config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')

           return config

       @staticmethod
       def get_current_version():
           """Get current configuration version"""
           return 2

       @staticmethod
       def migrate_config(config, from_version=None):
           """Migrate configuration to current version"""
           if from_version is None:
               from_version = config.get('CONFIG_VERSION', 1)

           current_version = ConfigMigration.get_current_version()

           while from_version < current_version:
               migration_method = getattr(ConfigMigration, f'migrate_v{from_version}_to_v{from_version + 1}')
               config = migration_method(config)
               from_version += 1

           config['CONFIG_VERSION'] = current_version
           return config

This comprehensive configuration guide provides everything you need to properly configure Pydance applications for any environment and use case.
