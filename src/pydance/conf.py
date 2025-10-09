"""
Configuration module for Pydance framework.

This module provides backward compatibility imports for configuration functionality.
For new code, consider using pydance.conf directly.
"""

from pydance.config.settings import Settings, settings, configure, get_settings, setup_settings, override_settings, get_config, is_debug, is_testing, get_database_url, get_secret_key, get_host, get_port, get_bool_env, get_int_env, get_list_env
from pydance.conf import AppConfig, DatabaseConfig, EmailConfig, StorageConfig, CacheConfig, CDNConfig, SecurityConfig, ServerConfig, I18nConfig, LoggingConfig, TestingConfig, StaticFilesConfig, ConfigPresets, get_config_from_environment, default_config, EmailProvider, StorageProvider, CacheBackend

__all__ = [
    'AppConfig', 'DatabaseConfig', 'EmailConfig', 'StorageConfig',
    'CacheConfig', 'CDNConfig', 'SecurityConfig', 'ServerConfig',
    'I18nConfig', 'LoggingConfig', 'TestingConfig', 'StaticFilesConfig',
    'ConfigPresets', 'get_config_from_environment', 'default_config',
    'EmailProvider', 'StorageProvider', 'CacheBackend'
]

