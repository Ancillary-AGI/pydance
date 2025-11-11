"""
Validation Utilities for Pydance Framework.

This module provides data validation, sanitization, and input checking utilities.
"""

import re
import string
from typing import Any, Dict, List, Optional, Callable, Union, Pattern
from decimal import Decimal, InvalidOperation
import ipaddress
import datetime
import uuid


class ValidationUtils:
    """Data validation utilities"""

    # Email validation regex (RFC 5322 compliant)
    EMAIL_REGEX = re.compile(
        r"^(?![.])[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )

    # Phone number validation regex (international format)
    PHONE_REGEX = re.compile(r'^\+?[\d\s\-\(\)\.]{10,20}$')

    # URL validation regex
    URL_REGEX = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

    # Credit card validation patterns
    CREDIT_CARD_PATTERNS = {
        'visa': re.compile(r'^4[0-9]{12}(?:[0-9]{3})?$'),
        'mastercard': re.compile(r'^5[1-5][0-9]{14}$'),
        'amex': re.compile(r'^3[47][0-9]{13}$'),
        'discover': re.compile(r'^6(?:011|5[0-9]{2})[0-9]{12}$'),
        'diners': re.compile(r'^3[0689][0-9]{11}$'),
        'jcb': re.compile(r'^(?:2131|1800|35\d{3})\d{11}$'),
    }

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address using RFC 5322 compliant regex"""
        if not isinstance(email, str) or not email:
            return False

        if len(email) > 254:  # RFC 5321 limit
            return False

        return bool(ValidationUtils.EMAIL_REGEX.match(email.strip()))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (international format)"""
        if not isinstance(phone, str) or not phone:
            return False

        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone.strip())
        return bool(ValidationUtils.PHONE_REGEX.match(phone) and 10 <= len(cleaned) <= 15)

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        if not isinstance(url, str) or not url:
            return False

        return bool(ValidationUtils.URL_REGEX.match(url.strip()))

    @staticmethod
    def validate_credit_card(number: str, card_type: Optional[str] = None) -> bool:
        """Validate credit card number using Luhn algorithm"""
        if not isinstance(number, str):
            return False

        # Remove spaces and dashes
        number = re.sub(r'[\s\-]', '', number)

        if not number.isdigit():
            return False

        # Check specific card type if provided
        if card_type and card_type.lower() in ValidationUtils.CREDIT_CARD_PATTERNS:
            pattern = ValidationUtils.CREDIT_CARD_PATTERNS[card_type.lower()]
            if not pattern.match(number):
                return False

        # Luhn algorithm
        def luhn_checksum(card_num: str) -> bool:
            digits = [int(d) for d in card_num[::-1]]
            for i in range(1, len(digits), 2):
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
            return sum(digits) % 10 == 0

        return luhn_checksum(number)

    @staticmethod
    def validate_ip_address(ip: str, version: Optional[int] = None) -> bool:
        """Validate IP address"""
        try:
            if version == 4:
                ipaddress.IPv4Address(ip)
            elif version == 6:
                ipaddress.IPv6Address(ip)
            else:
                ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_uuid(value: str, version: Optional[int] = None) -> bool:
        """Validate UUID string"""
        try:
            uuid_obj = uuid.UUID(value)
            if version and uuid_obj.version != version:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_date(date_str: str, format: str = '%Y-%m-%d') -> bool:
        """Validate date string"""
        try:
            datetime.datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_datetime(datetime_str: str, format: str = '%Y-%m-%d %H:%M:%S') -> bool:
        """Validate datetime string"""
        try:
            datetime.datetime.strptime(datetime_str, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_numeric(value: Any, min_val: Optional[Union[int, float]] = None,
                        max_val: Optional[Union[int, float]] = None,
                        allow_float: bool = True) -> bool:
        """Validate numeric value with optional range"""
        try:
            if allow_float:
                num = float(value)
            else:
                num = int(value)

            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False

            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_length(value: str, min_len: Optional[int] = None,
                       max_len: Optional[int] = None) -> bool:
        """Validate string length"""
        if not isinstance(value, str):
            return False

        length = len(value)
        if min_len is not None and length < min_len:
            return False
        if max_len is not None and length > max_len:
            return False

        return True

    @staticmethod
    def validate_regex(value: str, pattern: Union[str, Pattern]) -> bool:
        """Validate string against regex pattern"""
        if not isinstance(value, str):
            return False

        try:
            if isinstance(pattern, str):
                return bool(re.match(pattern, value))
            else:
                return bool(pattern.match(value))
        except re.error:
            return False

    @staticmethod
    def validate_in_list(value: Any, allowed_values: List[Any]) -> bool:
        """Validate that value is in allowed list"""
        return value in allowed_values

    @staticmethod
    def validate_not_empty(value: Any) -> bool:
        """Validate that value is not empty"""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict, tuple, set)):
            return bool(value)
        return True

    @staticmethod
    def validate_password_strength(password: str, min_length: int = 8,
                                 require_uppercase: bool = True,
                                 require_lowercase: bool = True,
                                 require_digits: bool = True,
                                 require_special: bool = False) -> Dict[str, bool]:
        """Validate password strength and return detailed results"""
        if not isinstance(password, str):
            return {'valid': False, 'errors': ['Password must be a string']}

        errors = []
        valid = True

        if len(password) < min_length:
            errors.append(f'Password must be at least {min_length} characters long')
            valid = False

        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
            valid = False

        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
            valid = False

        if require_digits and not re.search(r'\d', password):
            errors.append('Password must contain at least one digit')
            valid = False

        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')
            valid = False

        return {'valid': valid, 'errors': errors}


class SanitizationUtils:
    """Data sanitization utilities"""

    @staticmethod
    def sanitize_string(value: str, allow_html: bool = False,
                       max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""

        result = value.strip()

        if not allow_html:
            # Basic HTML escaping
            result = (result.replace('&', '&')
                           .replace('<', '<')
                           .replace('>', '>')
                           .replace('"', '"')
                           .replace("'", '&#x27;'))

        if max_length:
            result = result[:max_length]

        return result

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email address"""
        if not isinstance(email, str):
            return ""

        # Remove any whitespace and convert to lowercase
        return email.strip().lower()

    @staticmethod
    def sanitize_numeric(value: Any, default: Union[int, float] = 0,
                        min_val: Optional[Union[int, float]] = None,
                        max_val: Optional[Union[int, float]] = None) -> Union[int, float]:
        """Sanitize numeric value"""
        try:
            if isinstance(default, int):
                result = int(float(value))
            else:
                result = float(value)

            if min_val is not None:
                result = max(result, min_val)
            if max_val is not None:
                result = min(result, max_val)

            return result
        except (ValueError, TypeError):
            return default

    @staticmethod
    def sanitize_list(items: List[Any], item_validator: Optional[Callable] = None,
                     max_items: Optional[int] = None) -> List[Any]:
        """Sanitize list by filtering invalid items"""
        if not isinstance(items, list):
            return []

        result = []
        for item in items:
            if item_validator and not item_validator(item):
                continue
            result.append(item)

        if max_items:
            result = result[:max_items]

        return result


class ValidationChain:
    """Chain multiple validations together"""

    def __init__(self, value: Any):
        self.value = value
        self.errors = []
        self.valid = True

    def check(self, validator: Callable[[Any], bool], error_message: str) -> 'ValidationChain':
        """Add a validation check"""
        if not validator(self.value):
            self.errors.append(error_message)
            self.valid = False
        return self

    def is_valid(self) -> bool:
        """Check if all validations passed"""
        return self.valid

    def get_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.errors.copy()

    def validate(self) -> Dict[str, Any]:
        """Return validation result"""
        return {
            'valid': self.valid,
            'value': self.value,
            'errors': self.errors
        }


# Convenience functions
def validate_email(email: str) -> bool:
    """Validate email address"""
    return ValidationUtils.validate_email(email)

def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    return ValidationUtils.validate_phone(phone)

def validate_url(url: str) -> bool:
    """Validate URL"""
    return ValidationUtils.validate_url(url)

def validate_credit_card(number: str, card_type: Optional[str] = None) -> bool:
    """Validate credit card"""
    return ValidationUtils.validate_credit_card(number, card_type)

def validate_password_strength(password: str, **kwargs) -> Dict[str, Any]:
    """Validate password strength"""
    return ValidationUtils.validate_password_strength(password, **kwargs)

def sanitize_string(value: str, **kwargs) -> str:
    """Sanitize string"""
    return SanitizationUtils.sanitize_string(value, **kwargs)
