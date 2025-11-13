"""
Pydance Utilities
Consolidated utility functions for the Pydance framework.

All utilities are now centralized in pydance.core.utilities for better organization
and to eliminate code duplication. This module provides convenient access to all
utility classes and functions.
"""

# Import collections utilities
from .collections import Collection, LazyCollection, CachedCollection, SortedList, PriorityQueue, LRUCache

# Import performance utilities
from .performance_utilities import PerformanceMonitor, PerformanceMetrics, PerformanceProfiler

# Import locale support
from .locale_support import (
    LocaleManager, TranslationManager, LocalizedFormatter,
    get_locale_manager, get_translation_manager, get_localized_formatter,
    set_locale, get_locale, _, ngettext,
    format_date, format_datetime, format_number, format_currency, format_percent,
    format_address, format_measurement, format_list
)

# Import function utilities
from .function_utilities import FunctionUtils

# Import async utilities
from .async_utilities import AsyncUtils

# Import data utilities
from .data_utilities import DataUtils

# Import validation utilities
from .validation_utilities import ValidationUtils

# Import math operations
from .math_operations import MathOperations

__all__ = [
    # Collections utilities
    'Collection', 'LazyCollection', 'CachedCollection', 'SortedList', 'PriorityQueue', 'LRUCache',

    # Performance utilities
    'PerformanceMonitor', 'PerformanceMetrics', 'PerformanceProfiler',

    # Locale and internationalization support
    'LocaleManager', 'TranslationManager', 'LocalizedFormatter',
    'get_locale_manager', 'get_translation_manager', 'get_localized_formatter',
    'set_locale', 'get_locale', '_', 'ngettext',
    'format_date', 'format_datetime', 'format_number', 'format_currency', 'format_percent',
    'format_address', 'format_measurement', 'format_list',

    # Function utilities
    'FunctionUtils',

    # Async utilities
    'AsyncUtils',

    # Data utilities
    'DataUtils',

    # Validation utilities
    'ValidationUtils',

    # Math operations
    'MathOperations',
]
