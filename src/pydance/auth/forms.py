"""
Authentication Forms for Pydance Framework

Forms for user authentication, registration, and password management.
"""

from typing import Dict, Any, Optional, List
from pydance.http.request import Request
from pydance.forms.base import BaseForm, Field, ValidationError


class LoginForm(BaseForm):
    """Login form for user authentication"""

    username = Field(str, required=True, min_length=3, max_length=150)
    password = Field(str, required=True, min_length=6, max_length=128)
    remember_me = Field(bool, required=False, default=False)

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        super().__init__(data)
        self.user = None

    def clean_username(self, value: str) -> str:
        """Clean and validate username"""
        if not value:
            raise ValidationError("Username is required")

        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters")

        if len(value) > 150:
            raise ValidationError("Username is too long")

        return value.strip()

    def clean_password(self, value: str) -> str:
        """Clean and validate password"""
        if not value:
            raise ValidationError("Password is required")

        if len(value) < 6:
            raise ValidationError("Password must be at least 6 characters")

        return value

    def clean(self) -> Dict[str, Any]:
        """Validate form data and authenticate user"""
        cleaned_data = super().clean()

        if not self.errors:
            from .core import auth_manager
            username = cleaned_data.get('username')
            password = cleaned_data.get('password')

            user = auth_manager.authenticate_user(username, password)
            if user:
                self.user = user
            else:
                raise ValidationError("Invalid username or password")

        return cleaned_data

    async def save(self) -> Dict[str, Any]:
        """Save form and create session"""
        if self.user:
            from .core import auth_manager
            session_id = auth_manager.create_session(self.user['id'])
            return {
                'user': self.user,
                'session_id': session_id
            }
        return {}


class RegistrationForm(BaseForm):
    """Registration form for new user creation"""

    username = Field(str, required=True, min_length=3, max_length=150)
    email = Field(str, required=True, max_length=254)
    password = Field(str, required=True, min_length=8, max_length=128)
    password_confirm = Field(str, required=True)
    first_name = Field(str, required=False, max_length=150)
    last_name = Field(str, required=False, max_length=150)
    accept_terms = Field(bool, required=True)

    def clean_username(self, value: str) -> str:
        """Clean and validate username"""
        if not value:
            raise ValidationError("Username is required")

        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters")

        if len(value) > 150:
            raise ValidationError("Username is too long")

        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError("Username contains invalid characters")

        return value.strip()

    def clean_email(self, value: str) -> str:
        """Clean and validate email"""
        if not value:
            raise ValidationError("Email is required")

        if len(value) > 254:
            raise ValidationError("Email is too long")

        # Basic email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise ValidationError("Invalid email format")

        return value.lower().strip()

    def clean_password(self, value: str) -> str:
        """Clean and validate password"""
        if not value:
            raise ValidationError("Password is required")

        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters")

        if len(value) > 128:
            raise ValidationError("Password is too long")

        # Check password strength
        if not any(c.isupper() for c in value):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in value):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in value):
            raise ValidationError("Password must contain at least one number")

        return value

    def clean_password_confirm(self, value: str) -> str:
        """Validate password confirmation"""
        if not value:
            raise ValidationError("Password confirmation is required")

        password = self.data.get('password')
        if password and value != password:
            raise ValidationError("Passwords do not match")

        return value

    def clean_accept_terms(self, value: bool) -> bool:
        """Validate terms acceptance"""
        if not value:
            raise ValidationError("You must accept the terms and conditions")
        return value

    def clean(self) -> Dict[str, Any]:
        """Validate form data and check for existing users"""
        cleaned_data = super().clean()

        if not self.errors:
            from .core import auth_manager
            username = cleaned_data.get('username')
            email = cleaned_data.get('email')

            # Check if user already exists
            # Note: In a real implementation, you'd check the database
            # For now, we'll just validate the format

        return cleaned_data

    async def save(self) -> Dict[str, Any]:
        """Save form and create user"""
        if not self.errors:
            from .core import auth_manager
            username = self.cleaned_data.get('username')
            email = self.cleaned_data.get('email')
            password = self.cleaned_data.get('password')

            user = auth_manager.create_user(username, email, password)
            return {
                'user': user,
                'created': True
            }
        return {}


class PasswordChangeForm(BaseForm):
    """Form for changing user password"""

    old_password = Field(str, required=True)
    new_password = Field(str, required=True, min_length=8, max_length=128)
    new_password_confirm = Field(str, required=True)

    def __init__(self, user: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(data)
        self.user = user

    def clean_old_password(self, value: str) -> str:
        """Validate old password"""
        if not value:
            raise ValidationError("Old password is required")

        if not self.user:
            raise ValidationError("User not authenticated")

        from .core import auth_manager
        if not auth_manager.verify_password(value, self.user.get('password_hash', '')):
            raise ValidationError("Old password is incorrect")

        return value

    def clean_new_password(self, value: str) -> str:
        """Validate new password"""
        if not value:
            raise ValidationError("New password is required")

        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters")

        # Check that new password is different from old
        old_password = self.data.get('old_password')
        if old_password and value == old_password:
            raise ValidationError("New password must be different from old password")

        return value

    def clean_new_password_confirm(self, value: str) -> str:
        """Validate password confirmation"""
        if not value:
            raise ValidationError("Password confirmation is required")

        new_password = self.data.get('new_password')
        if new_password and value != new_password:
            raise ValidationError("Passwords do not match")

        return value


class PasswordResetForm(BaseForm):
    """Form for password reset request"""

    email = Field(str, required=True, max_length=254)

    def clean_email(self, value: str) -> str:
        """Clean and validate email"""
        if not value:
            raise ValidationError("Email is required")

        if len(value) > 254:
            raise ValidationError("Email is too long")

        # Basic email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise ValidationError("Invalid email format")

        return value.lower().strip()


class PasswordResetConfirmForm(BaseForm):
    """Form for confirming password reset"""

    new_password = Field(str, required=True, min_length=8, max_length=128)
    new_password_confirm = Field(str, required=True)

    def clean_new_password(self, value: str) -> str:
        """Validate new password"""
        if not value:
            raise ValidationError("New password is required")

        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters")

        if len(value) > 128:
            raise ValidationError("Password is too long")

        # Check password strength
        if not any(c.isupper() for c in value):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in value):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in value):
            raise ValidationError("Password must contain at least one number")

        return value

    def clean_new_password_confirm(self, value: str) -> str:
        """Validate password confirmation"""
        if not value:
            raise ValidationError("Password confirmation is required")

        new_password = self.data.get('new_password')
        if new_password and value != new_password:
            raise ValidationError("Passwords do not match")

        return value


class ProfileUpdateForm(BaseForm):
    """Form for updating user profile"""

    first_name = Field(str, required=False, max_length=150)
    last_name = Field(str, required=False, max_length=150)
    email = Field(str, required=True, max_length=254)

    def __init__(self, user: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(data)
        self.user = user

    def clean_email(self, value: str) -> str:
        """Clean and validate email"""
        if not value:
            raise ValidationError("Email is required")

        if len(value) > 254:
            raise ValidationError("Email is too long")

        # Basic email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise ValidationError("Invalid email format")

        # Check if email is already taken by another user
        if self.user and value.lower() != self.user.get('email', '').lower():
            # In real implementation, check database
            pass

        return value.lower().strip()


# Convenience form instances
login_form = LoginForm()
registration_form = RegistrationForm()
password_change_form = PasswordChangeForm()
password_reset_form = PasswordResetForm()
password_reset_confirm_form = PasswordResetConfirmForm()
profile_update_form = ProfileUpdateForm()


__all__ = [
    'LoginForm',
    'RegistrationForm',
    'PasswordChangeForm',
    'PasswordResetForm',
    'PasswordResetConfirmForm',
    'ProfileUpdateForm',
    'login_form',
    'registration_form',
    'password_change_form',
    'password_reset_form',
    'password_reset_confirm_form',
    'profile_update_form'
]

