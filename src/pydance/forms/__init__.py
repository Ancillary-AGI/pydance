from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
import re


class ValidationError(Exception):
    """Form validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


@dataclass
class Field:
    """Base form field."""

    required: bool = True
    label: Optional[str] = None
    initial: Any = None
    help_text: Optional[str] = None
    error_messages: Dict[str, str] = field(default_factory=dict)
    validators: List[Callable] = field(default_factory=list)

    def __post_init__(self):
        if not self.label:
            self.label = self.__class__.__name__

    def clean(self, value: Any) -> Any:
        """Clean and validate field value."""
        if value is None or value == '':
            if self.required:
                raise ValidationError(self.error_messages.get('required', 'This field is required'))
            return None

        # Run custom validators
        for validator in self.validators:
            validator(value)

        return self.to_python(value)

    def to_python(self, value: Any) -> Any:
        """Convert value to Python type."""
        return value

    def validate(self, value: Any):
        """Validate field value."""
        pass


class CharField(Field):
    """Character field for text input."""

    def __init__(self, max_length: Optional[int] = None, min_length: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length

    def to_python(self, value: Any) -> str:
        """Convert to string."""
        if value is None:
            return ''
        return str(value)

    def validate(self, value: Any):
        """Validate string length."""
        if value:
            if self.max_length and len(value) > self.max_length:
                raise ValidationError(f'Ensure this value has at most {self.max_length} characters')
            if self.min_length and len(value) < self.min_length:
                raise ValidationError(f'Ensure this value has at least {self.min_length} characters')


class EmailField(CharField):
    """Email field with validation."""

    def validate(self, value: Any):
        """Validate email format."""
        super().validate(value)

        if value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValidationError('Enter a valid email address')


class IntegerField(Field):
    """Integer field."""

    def to_python(self, value: Any) -> Optional[int]:
        """Convert to integer."""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValidationError('Enter a valid integer')


class BooleanField(Field):
    """Boolean field."""

    def to_python(self, value: Any) -> bool:
        """Convert to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)


@dataclass
class Form:
    """Base form class."""

    data: Dict[str, Any] = field(default_factory=dict)
    files: Dict[str, Any] = field(default_factory=dict)
    initial: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.fields: Dict[str, Field] = {}
        self.errors: Dict[str, List[str]] = {}
        self.cleaned_data: Dict[str, Any] = {}
        self.is_bound = bool(self.data)

        self.declare_fields()

    def declare_fields(self):
        """Declare form fields. Override in subclasses."""
        pass

    def is_valid(self) -> bool:
        """Check if form is valid."""
        self.errors = {}
        self.cleaned_data = {}

        if not self.is_bound:
            return False

        for name, field in self.fields.items():
            value = self.data.get(name)
            try:
                cleaned_value = field.clean(value)
                self.cleaned_data[name] = cleaned_value
            except ValidationError as e:
                self.errors.setdefault(name, []).append(str(e))

        return not self.errors

    def clean(self):
        """Clean form data. Override for custom validation."""
        pass

    def full_clean(self):
        """Full form cleaning and validation."""
        self.is_valid()
        if not self.errors:
            self.clean()


class ModelForm(Form):
    """Form based on a model."""

    model: Optional[Type] = None

    def __init__(self, data: Dict[str, Any] = None, instance: Any = None, **kwargs):
        self.instance = instance
        super().__init__(data=data, **kwargs)

    def declare_fields(self):
        """Declare fields based on model."""
        if not self.model:
            return

        # This would introspect the model and create fields
        # For now, just pass
        pass

    def save(self) -> Any:
        """Save the model instance."""
        if not self.is_valid():
            raise ValidationError("Form is not valid")

        if self.instance:
            # Update existing instance
            for key, value in self.cleaned_data.items():
                if hasattr(self.instance, key):
                    setattr(self.instance, key, value)
            return self.instance
        else:
            # Create new instance
            return self.model(**self.cleaned_data)


# Utility functions
def field_error_messages(field_name: str, errors: List[str]) -> Dict[str, List[str]]:
    """Format field errors."""
    return {field_name: errors}


def form_errors(form: Form) -> Dict[str, List[str]]:
    """Get all form errors."""
    return form.errors


__all__ = [
    'ValidationError',
    'Field',
    'CharField',
    'EmailField',
    'IntegerField',
    'BooleanField',
    'Form',
    'ModelForm',
    'field_error_messages',
    'form_errors'
]
