"""
Email sending functionality for Pydance  framework.
"""

from .mail import Mail, EmailMessage, EmailTemplate
from .backends import SMTPBackend, ConsoleBackend, FileBackend

__all__ = [
    'Mail',
    'EmailMessage',
    'EmailTemplate',
    'SMTPBackend',
    'ConsoleBackend',
    'FileBackend',
    'EmailTemplateEngine',
]




