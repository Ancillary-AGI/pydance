"""
Internationalization (i18n) module for Pydance  framework
"""

from .translations import gettext, ngettext, pgettext, lazy_gettext, Translations
    format_date, format_time, format_datetime,
    format_number, format_currency, format_percent, format_scientific
)
    get_locale, set_locale, get_timezone, set_timezone,
    get_current_time, to_timezone, to_utc
)
from .manager import I18n, _, set_locale as set_locale_func, get_locale as get_locale_func, LocaleContext

__all__ = [
    # Translation functions
    'gettext', 'ngettext', 'pgettext', 'lazy_gettext', 'Translations',
    # Formatting functions
    'format_date', 'format_time', 'format_datetime',
    'format_number', 'format_currency', 'format_percent', 'format_scientific',
    # Utilities
    'get_locale', 'set_locale', 'get_timezone', 'set_timezone',
    'get_current_time', 'to_timezone', 'to_utc',
    # Manager
    'I18n', '_', 'set_locale_func', 'get_locale_func', 'LocaleContext'
]

