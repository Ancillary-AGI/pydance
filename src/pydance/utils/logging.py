"""
Advanced logging system for Pydance framework.
Provides comprehensive logging capabilities with multiple handlers, formatters,
filters, and configuration options similar to Django/Laravel logging systems.
"""

import logging
import logging.handlers
import logging.config
import sys
import json
import threading
from typing import Dict, Any, Optional, List, Callable, Union
import traceback
import inspect
from enum import Enum
from datetime import datetime
from pathlib import Path
from pydance.config import default_config as settings


class LogLevel(Enum):
    """Log levels enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Log format presets"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    COLORED = "colored"


class LogHandler(Enum):
    """Available log handlers"""
    CONSOLE = "console"
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    TIMED_ROTATING_FILE = "timed_rotating_file"
    SYSLOG = "syslog"
    EMAIL = "email"
    HTTP = "http"


class PydanceFormatter(logging.Formatter):
    """Custom formatter for Pydance logs"""

    def __init__(self, format_type: LogFormat = LogFormat.DETAILED, colors: bool = True):
        self.format_type = format_type
        self.colors = colors

        # Color codes for different log levels
        self.colors_map = {
            logging.DEBUG: '\033[36m',  # Cyan
            logging.INFO: '\033[32m',   # Green
            logging.WARNING: '\033[33m', # Yellow
            logging.ERROR: '\033[31m',   # Red
            logging.CRITICAL: '\033[35m', # Magenta
        }
        self.reset_color = '\033[0m'

        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record"""
        if self.format_type == LogFormat.JSON:
            return self._format_json(record)
        elif self.format_type == LogFormat.SIMPLE:
            return self._format_simple(record)
        elif self.format_type == LogFormat.COLORED:
            return self._format_colored(record)
        else:  # DETAILED
            return self._format_detailed(record)

    def _format_simple(self, record: logging.LogRecord) -> str:
        """Simple format: LEVEL: message"""
        return f"{record.levelname}: {record.getMessage()}"

    def _format_detailed(self, record: logging.LogRecord) -> str:
        """Detailed format with timestamp, logger name, etc."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        module = record.module
        func = record.funcName
        line = record.lineno

        return f"[{timestamp}] {record.levelname} {record.name} {module}.{func}:{line} - {record.getMessage()}"

    def _format_colored(self, record: logging.LogRecord) -> str:
        """Colored format for console output"""
        if not self.colors or not sys.stdout.isatty():
            return self._format_detailed(record)

        color = self.colors_map.get(record.levelno, '')
        reset = self.reset_color

        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = f"{color}{record.levelname}{reset}"
        module = record.module
        func = record.funcName
        line = record.lineno

        return f"[{timestamp}] {level} {record.name} {module}.{func}:{line} - {record.getMessage()}"

    def _format_json(self, record: logging.LogRecord) -> str:
        """JSON format for structured logging"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process': record.process,
            'thread': record.thread,
            'thread_name': record.threadName,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }

        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                             'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                             'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                             'thread', 'threadName', 'processName', 'process', 'message']:
                    log_entry[f'extra_{key}'] = value

        return json.dumps(log_entry, default=str)


class PydanceFilter(logging.Filter):
    """Custom filter for Pydance logs"""

    def __init__(self, level: LogLevel = None, modules: List[str] = None,
                 exclude_modules: List[str] = None):
        super().__init__()
        self.level = level
        self.modules = modules or []
        self.exclude_modules = exclude_modules or []

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records"""
        # Check level
        if self.level and record.levelno < self.level.value:
            return False

        # Check included modules
        if self.modules and record.name not in self.modules:
            return False

        # Check excluded modules
        if self.exclude_modules and record.name in self.exclude_modules:
            return False

        return True


class LogConfig:
    """Configuration for a single logger"""

    def __init__(self,
                 level: LogLevel = LogLevel.INFO,
                 handlers: List[str] = None,
                 propagate: bool = True,
                 filters: List[Dict[str, Any]] = None):
        self.level = level
        self.handlers = handlers or ['console']
        self.propagate = propagate
        self.filters = filters or []


class HandlerConfig:
    """Configuration for a log handler"""

    def __init__(self,
                 handler_type: LogHandler,
                 level: LogLevel = LogLevel.DEBUG,
                 format: LogFormat = LogFormat.DETAILED,
                 filters: List[Dict[str, Any]] = None,
                 **kwargs):
        self.handler_type = handler_type
        self.level = level
        self.format = format
        self.filters = filters or []
        self.kwargs = kwargs


class PydanceLogger:
    """Main logger class for Pydance"""

    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(name)
        self._context = {}
        # Initialize the logger with proper configuration
        self._setup_logger()

    def _setup_logger(self):
        """Setup logger configuration"""
        # Ensure the logger has at least one handler
        if not self._logger.handlers:
            # Add a default handler if none exists
            handler = logging.StreamHandler()
            formatter = PydanceFormatter(LogFormat.COLORED)
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, args, kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, args, kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, args, kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self._log(LogLevel.ERROR, message, args, kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, args, kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        kwargs['exc_info'] = True
        self._log(LogLevel.ERROR, message, args, kwargs)

    def _log(self, level: LogLevel, message: str, args, kwargs):
        """Internal logging method"""
        # Add context to extra
        extra = kwargs.get('extra', {})
        extra.update(self._context)

        # Add caller info
        frame = inspect.currentframe().f_back.f_back
        if frame:
            extra.update({
                'caller_file': frame.f_code.co_filename,
                'caller_line': frame.f_lineno,
                'caller_function': frame.f_code.co_name
            })

        kwargs['extra'] = extra

        self._logger.log(level.value, message, *args, **kwargs)

    def set_context(self, **context):
        """Set context for all subsequent logs"""
        self._context.update(context)

    def clear_context(self):
        """Clear logging context"""
        self._context.clear()

    def is_enabled_for(self, level: LogLevel) -> bool:
        """Check if logger is enabled for level"""
        return self._logger.isEnabledFor(level.value)

    def setLevel(self, level):
        """Set the logging level (compatibility with standard logging)"""
        if isinstance(level, LogLevel):
            self._logger.setLevel(level.value)
        else:
            self._logger.setLevel(level)

    def addHandler(self, handler):
        """Add a handler (compatibility with standard logging)"""
        self._logger.addHandler(handler)

    def removeHandler(self, handler):
        """Remove a handler (compatibility with standard logging)"""
        self._logger.removeHandler(handler)

    def addFilter(self, filter):
        """Add a filter (compatibility with standard logging)"""
        self._logger.addFilter(filter)

    def removeFilter(self, filter):
        """Remove a filter (compatibility with standard logging)"""
        self._logger.removeFilter(filter)

    def getEffectiveLevel(self):
        """Get the effective logging level"""
        return self._logger.getEffectiveLevel()

    def hasHandlers(self):
        """Check if logger has handlers"""
        return self._logger.hasHandlers()


class LoggerManager:
    """Central manager for all loggers and handlers"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._loggers = {}
            self._handlers = {}
            self._config = self._get_default_config()
            self._setup_logging()

    def configure_from_settings(self):
        """Configure logging from Pydance settings"""
        try:

            # Build configuration from settings
            config = {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {},
                'handlers': {},
                'loggers': {},
                'root': {
                    'level': 'WARNING',
                    'handlers': ['console'] if settings.LOG_HANDLERS.get('console', {}).get('enabled', True) else []
                }
            }

            # Configure formatters
            for fmt_name, fmt_config in settings.LOG_FORMATTERS.items():
                config['formatters'][fmt_name] = fmt_config.copy()

            # Configure handlers
            for handler_name, handler_config in settings.LOG_HANDLERS.items():
                if handler_config.get('enabled', True):
                    handler_dict = {
                        'level': handler_config['level'].upper(),
                        'formatter': handler_config['formatter'],
                    }

                    # Add handler-specific configuration
                    if handler_name == 'console':
                        handler_dict.update({
                            'class': 'logging.StreamHandler',
                            'stream': 'ext://sys.stdout' if handler_config.get('stream', 'stdout') == 'stdout' else 'ext://sys.stderr'
                        })
                    elif handler_name == 'file':
                        handler_dict.update({
                            'class': 'logging.FileHandler',
                            'filename': handler_config['filename'],
                            'encoding': handler_config.get('encoding', 'utf-8'),
                        })
                    elif handler_name == 'error_file':
                        handler_dict.update({
                            'class': 'logging.FileHandler',
                            'filename': handler_config['filename'],
                            'encoding': handler_config.get('encoding', 'utf-8'),
                        })
                    elif handler_name == 'json_file':
                        handler_dict.update({
                            'class': 'logging.FileHandler',
                            'filename': handler_config['filename'],
                            'encoding': handler_config.get('encoding', 'utf-8'),
                        })

                    config['handlers'][handler_name] = handler_dict

            # Configure loggers
            for logger_name, logger_config in settings.LOG_LOGGERS.items():
                config['loggers'][logger_name] = {
                    'level': logger_config['level'].upper(),
                    'handlers': logger_config['handlers'],
                    'propagate': logger_config.get('propagate', False),
                }

            # Apply configuration
            self._config = config
            self._setup_logging()

        except (ImportError, AttributeError):
            # Settings not available, use defaults
            pass

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {
                    'format': '%(levelname)s: %(message)s'
                },
                'detailed': {
                    'format': '[%(asctime)s] %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d - %(message)s'
                },
                'colored': {
                    'format': '[%(asctime)s] %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'json': {
                    'format': '%(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'colored',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': 'logs/pydance.log',
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                'pydance': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                'pydance.db': {
                    'level': 'INFO',
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                'pydance.auth': {
                    'level': 'INFO',
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                'pydance.graphql': {
                    'level': 'INFO',
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            },
            'root': {
                'level': 'WARNING',
                'handlers': ['console']
            }
        }

    def _setup_logging(self):
        """Set up logging configuration"""
        # Create logs directory
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.config.dictConfig(self._config)

    def get_logger(self, name: str) -> PydanceLogger:
        """Get or create a logger"""
        if name not in self._loggers:
            self._loggers[name] = PydanceLogger(name)
        return self._loggers[name]

    def configure(self, config: Dict[str, Any]):
        """Configure logging with custom config"""
        self._config.update(config)
        self._setup_logging()

    def add_handler(self, name: str, handler_config: HandlerConfig):
        """Add a custom handler"""
        self._handlers[name] = handler_config

        # Create handler configuration
        handler_dict = {
            'level': handler_config.level.name,
            'formatter': handler_config.format.value,
            'filters': []
        }

        # Add handler-specific configuration
        if handler_config.handler_type == LogHandler.CONSOLE:
            handler_dict.update({
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            })
        elif handler_config.handler_type == LogHandler.FILE:
            handler_dict.update({
                'class': 'logging.FileHandler',
                'filename': handler_config.kwargs.get('filename', f'logs/{name}.log'),
                'encoding': 'utf-8'
            })
        elif handler_config.handler_type == LogHandler.ROTATING_FILE:
            handler_dict.update({
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': handler_config.kwargs.get('filename', f'logs/{name}.log'),
                'maxBytes': handler_config.kwargs.get('maxBytes', 10*1024*1024),
                'backupCount': handler_config.kwargs.get('backupCount', 5),
                'encoding': 'utf-8'
            })
        elif handler_config.handler_type == LogHandler.TIMED_ROTATING_FILE:
            handler_dict.update({
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': handler_config.kwargs.get('filename', f'logs/{name}.log'),
                'when': handler_config.kwargs.get('when', 'midnight'),
                'interval': handler_config.kwargs.get('interval', 1),
                'backupCount': handler_config.kwargs.get('backupCount', 30),
                'encoding': 'utf-8'
            })

        # Add filters
        for filter_config in handler_config.filters:
            filter_dict = {
                '()': 'pydance.utils.logging.PydanceFilter'
            }
            filter_dict.update(filter_config)
            handler_dict['filters'].append(filter_dict)

        self._config['handlers'][name] = handler_dict
        self._setup_logging()

    def set_level(self, logger_name: str, level: LogLevel):
        """Set log level for a logger"""
        logger = get_logger(logger_name)
        logger.setLevel(level.value)

    def add_filter(self, logger_name: str, filter_config: Dict[str, Any]):
        """Add filter to a logger"""
        logger = get_logger(logger_name)
        filter_obj = PydanceFilter(**filter_config)
        logger.addFilter(filter_obj)


# Global logger manager instance
logger_manager = LoggerManager()


def get_logger(name: str) -> PydanceLogger:
    """Get a logger instance"""
    return logger_manager.get_logger(name)


def configure_logging(config: Dict[str, Any]):
    """Configure logging system"""
    logger_manager.configure(config)


def setup_request_logging(request_id: str = None):
    """Set up request-specific logging context"""
    if request_id is None:
        import uuid
        request_id = str(uuid.uuid4())

    # Set context for current thread
    logger = get_logger('pydance.request')
    logger.set_context(request_id=request_id, timestamp=datetime.now().isoformat())

    return request_id


def log_request_start(request, logger=None):
    """Log request start"""
    if logger is None:
        logger = get_logger('pydance.request')

    logger.info(f"Request started: {request.method} {request.path}", extra={
        'method': request.method,
        'path': request.path,
        'user_agent': getattr(request, 'headers', {}).get('User-Agent'),
        'remote_addr': getattr(request, 'remote_addr', None)
    })


def log_request_end(request, response, duration: float, logger=None):
    """Log request end"""
    if logger is None:
        logger = get_logger('pydance.request')

    level = LogLevel.INFO
    if hasattr(response, 'status_code') and response.status_code >= 400:
        level = LogLevel.WARNING if response.status_code < 500 else LogLevel.ERROR

    logger.log(level, f"Request completed: {request.method} {request.path} -> {getattr(response, 'status_code', 'unknown')} ({duration:.2f}s)",
               extra={
                   'method': request.method,
                   'path': request.path,
                   'status_code': getattr(response, 'status_code', None),
                   'duration': duration,
                   'response_size': getattr(response, 'content_length', None)
               })


def log_database_query(query: str, params: tuple = None, duration: float = None, logger=None):
    """Log database query"""
    if logger is None:
        logger = get_logger('pydance.db')

    message = f"Database query executed"
    if duration:
        message += f" in {duration:.3f}s"

    logger.debug(message, extra={
        'query': query,
        'params': params,
        'duration': duration
    })


def log_auth_event(event: str, user_id: str = None, details: Dict[str, Any] = None, logger=None):
    """Log authentication event"""
    if logger is None:
        logger = get_logger('pydance.auth')

    logger.info(f"Auth event: {event}", extra={
        'event': event,
        'user_id': user_id,
        'details': details or {}
    })


def log_error(error: Exception, context: Dict[str, Any] = None, logger=None):
    """Log error with full context"""
    if logger is None:
        logger = get_logger('pydance.error')

    logger.error(f"Error occurred: {error.__class__.__name__}: {str(error)}",
                 extra={
                     'error_type': error.__class__.__name__,
                     'error_message': str(error),
                     'traceback': ''.join(traceback.format_exception(type(error), error, error.__traceback__)),
                     'context': context or {}
                 })


# Convenience functions for common loggers
def db_logger():
    """Get database logger"""
    return get_logger('pydance.db')


def auth_logger():
    """Get authentication logger"""
    return get_logger('pydance.auth')


def request_logger():
    """Get request logger"""
    return get_logger('pydance.request')


def error_logger():
    """Get error logger"""
    return get_logger('pydance.error')


def graphql_logger():
    """Get GraphQL logger"""
    return get_logger('pydance.graphql')


def cache_logger():
    """Get cache logger"""
    return get_logger('pydance.cache')


# Initialize default loggers
_db_logger = db_logger()
_auth_logger = auth_logger()
_request_logger = request_logger()
_error_logger = error_logger()
_graphql_logger = graphql_logger()
_cache_logger = cache_logger()

# Note: Pydance logging system is available via get_logger() function
# Standard logging.getLogger() will use default Python logging for non-pydance modules
# Pydance modules should use get_logger() for enhanced features

__all__ = [
    'LogLevel', 'LogFormat', 'LogHandler', 'PydanceFormatter', 'PydanceFilter',
    'LogConfig', 'HandlerConfig', 'PydanceLogger', 'LoggerManager',
    'get_logger', 'configure_logging', 'setup_request_logging',
    'log_request_start', 'log_request_end', 'log_database_query',
    'log_auth_event', 'log_error', 'db_logger', 'auth_logger',
    'request_logger', 'error_logger', 'graphql_logger', 'cache_logger'
]
