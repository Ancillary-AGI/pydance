"""
Base Forms for Pydance Framework

Provides comprehensive form handling, validation, widgets, and field definitions.
"""

from typing import Dict, Any, Optional, List, Type, Callable, Union, Tuple
import re
from datetime import datetime, date
from decimal import Decimal
import json


class ValidationError(Exception):
    """Form validation error"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


class Field:
    """Form field definition"""

    def __init__(
        self,
        field_type: Type = str,
        required: bool = False,
        default: Any = None,
        validators: Optional[List[Callable]] = None,
        widget: Optional[str] = None,
        label: Optional[str] = None,
        help_text: str = "",
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        choices: Optional[List[tuple]] = None,
        **kwargs
    ):
        self.field_type = field_type
        self.required = required
        self.default = default
        self.validators = validators or []
        self.widget = widget
        self.label = label
        self.help_text = help_text
        self.min_length = min_length
        self.max_length = max_length
        self.choices = choices
        self.kwargs = kwargs

    def validate(self, value: Any) -> Any:
        """Validate field value"""
        # Check required
        if self.required and (value is None or value == ""):
            raise ValidationError("This field is required")

        # Type conversion
        if value is not None and value != "":
            try:
                if self.field_type == int:
                    value = int(value)
                elif self.field_type == float:
                    value = float(value)
                elif self.field_type == bool:
                    value = str(value).lower() in ('true', '1', 'yes', 'on')
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid {self.field_type.__name__}")

        # Length validation
        if value and self.min_length and len(str(value)) < self.min_length:
            raise ValidationError(f"Minimum length is {self.min_length}")

        if value and self.max_length and len(str(value)) > self.max_length:
            raise ValidationError(f"Maximum length is {self.max_length}")

        # Custom validators
        for validator in self.validators:
            value = validator(value)

        return value

    def __str__(self):
        return f"Field({self.field_type.__name__})"


class BaseForm:
    """Base form class"""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.data = data or {}
        self.cleaned_data = {}
        self.errors = {}
        self.fields = {}

        # Get form fields from class attributes
        for attr_name in dir(self.__class__):
            if not attr_name.startswith('_'):
                attr = getattr(self.__class__, attr_name)
                if isinstance(attr, Field):
                    self.fields[attr_name] = attr

    def is_valid(self) -> bool:
        """Check if form is valid"""
        self.cleaned_data = {}
        self.errors = {}

        # Validate each field
        for field_name, field in self.fields.items():
            value = self.data.get(field_name)
            try:
                cleaned_value = field.validate(value)
                self.cleaned_data[field_name] = cleaned_value
            except ValidationError as e:
                self.errors[field_name] = str(e)

        # Run form-level validation
        try:
            self.clean()
        except ValidationError as e:
            self.errors['__form__'] = str(e)

        return len(self.errors) == 0

    def clean(self):
        """Form-level validation"""
        pass

    def get_value(self, field_name: str, default: Any = None) -> Any:
        """Get field value"""
        return self.data.get(field_name, default)

    def add_error(self, field_name: str, error: str):
        """Add field error"""
        if field_name not in self.errors:
            self.errors[field_name] = []
        if isinstance(self.errors[field_name], list):
            self.errors[field_name].append(error)
        else:
            self.errors[field_name] = [self.errors[field_name], error]

    def __getitem__(self, field_name: str) -> Any:
        return self.cleaned_data.get(field_name)

    def __contains__(self, field_name: str) -> bool:
        return field_name in self.cleaned_data


# Common field types
class CharField(Field):
    """Character field"""

    def __init__(self, max_length: Optional[int] = None, **kwargs):
        super().__init__(str, max_length=max_length, **kwargs)


class IntegerField(Field):
    """Integer field"""

    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)


class BooleanField(Field):
    """Boolean field"""

    def __init__(self, **kwargs):
        super().__init__(bool, **kwargs)


class EmailField(Field):
    """Email field"""

    def __init__(self, **kwargs):
        super().__init__(str, **kwargs)
        self.validators.append(self._validate_email)

    def _validate_email(self, value: str) -> str:
        """Validate email format"""
        if value:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                raise ValidationError("Invalid email format")
        return value


class URLField(Field):
    """URL field"""

    def __init__(self, **kwargs):
        super().__init__(str, **kwargs)
        self.validators.append(self._validate_url)

    def _validate_url(self, value: str) -> str:
        """Validate URL format"""
        if value:
            pattern = r'^https?://.+'
            if not re.match(pattern, value):
                raise ValidationError("Invalid URL format")
        return value


class ChoiceField(Field):
    """Choice field"""

    def __init__(self, choices: List[tuple], **kwargs):
        super().__init__(str, choices=choices, **kwargs)
        self.validators.append(self._validate_choice)

    def _validate_choice(self, value: str) -> str:
        """Validate choice"""
        if value and self.choices:
            valid_choices = [choice[0] for choice in self.choices]
            if str(value) not in valid_choices:
                raise ValidationError(f"Invalid choice: {value}")
        return value


# Advanced field types
class DateField(Field):
    """Date field with validation"""

    def __init__(self, input_formats: Optional[List[str]] = None, **kwargs):
        super().__init__(date, **kwargs)
        self.input_formats = input_formats or ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']

    def validate(self, value: Any) -> Any:
        if isinstance(value, str) and value:
            for fmt in self.input_formats:
                try:
                    value = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValidationError("Invalid date format")
        return super().validate(value)


class DateTimeField(Field):
    """DateTime field with validation"""

    def __init__(self, input_formats: Optional[List[str]] = None, **kwargs):
        super().__init__(datetime, **kwargs)
        self.input_formats = input_formats or [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%m/%d/%Y %I:%M %p'
        ]

    def validate(self, value: Any) -> Any:
        if isinstance(value, str) and value:
            for fmt in self.input_formats:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValidationError("Invalid datetime format")
        return super().validate(value)


class DecimalField(Field):
    """Decimal field with precision validation"""

    def __init__(self, max_digits: int = 10, decimal_places: int = 2, **kwargs):
        super().__init__(Decimal, **kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places

    def validate(self, value: Any) -> Any:
        if isinstance(value, str) and value:
            try:
                value = Decimal(value)
            except:
                raise ValidationError("Invalid decimal number")

        if isinstance(value, Decimal):
            if len(str(value).replace('.', '').replace('-', '')) > self.max_digits:
                raise ValidationError(f"Maximum {self.max_digits} digits")
            if len(str(value).split('.')[-1]) > self.decimal_places:
                raise ValidationError(f"Maximum {self.decimal_places} decimal places")

        return super().validate(value)


class FileField(Field):
    """File upload field"""

    def __init__(self, max_size: int = 5242880, allowed_extensions: Optional[List[str]] = None, **kwargs):
        super().__init__(dict, **kwargs)  # Store file info as dict
        self.max_size = max_size  # 5MB default
        self.allowed_extensions = allowed_extensions or []

    def validate(self, value: Any) -> Any:
        if value and isinstance(value, dict):
            # Validate file size
            if 'size' in value and value['size'] > self.max_size:
                raise ValidationError(f"File too large. Maximum size is {self.max_size} bytes")

            # Validate file extension
            if 'name' in value and self.allowed_extensions:
                extension = value['name'].split('.')[-1].lower()
                if extension not in self.allowed_extensions:
                    raise ValidationError(f"File type not allowed. Allowed: {self.allowed_extensions}")

        return super().validate(value)


class ImageField(FileField):
    """Image field with dimension validation"""

    def __init__(self, max_width: Optional[int] = None, max_height: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_width = max_width
        self.max_height = max_height
        # Add image extensions if not specified
        if not self.allowed_extensions:
            self.allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']


class PasswordField(Field):
    """Password field with strength validation"""

    def __init__(self, min_length: int = 8, require_special: bool = True,
                 require_numbers: bool = True, require_uppercase: bool = True, **kwargs):
        super().__init__(str, **kwargs)
        self.min_length = min_length
        self.require_special = require_special
        self.require_numbers = require_numbers
        self.require_uppercase = require_uppercase

    def validate(self, value: Any) -> Any:
        if value:
            if len(value) < self.min_length:
                raise ValidationError(f"Password must be at least {self.min_length} characters")

            if self.require_uppercase and not re.search(r'[A-Z]', value):
                raise ValidationError("Password must contain at least one uppercase letter")

            if self.require_numbers and not re.search(r'[0-9]', value):
                raise ValidationError("Password must contain at least one number")

            if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
                raise ValidationError("Password must contain at least one special character")

        return super().validate(value)


class JSONField(Field):
    """JSON field with validation"""

    def __init__(self, schema: Optional[Dict] = None, **kwargs):
        super().__init__(dict, **kwargs)
        self.schema = schema

    def validate(self, value: Any) -> Any:
        if isinstance(value, str) and value:
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format")

        if value and self.schema:
            # Basic schema validation
            if not isinstance(value, dict):
                raise ValidationError("JSON must be an object")

            for key, expected_type in self.schema.items():
                if key in value:
                    actual_value = value[key]
                    if expected_type == 'string' and not isinstance(actual_value, str):
                        raise ValidationError(f"Field '{key}' must be a string")
                    elif expected_type == 'number' and not isinstance(actual_value, (int, float)):
                        raise ValidationError(f"Field '{key}' must be a number")
                    elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                        raise ValidationError(f"Field '{key}' must be a boolean")
                    elif expected_type == 'array' and not isinstance(actual_value, list):
                        raise ValidationError(f"Field '{key}' must be an array")

        return super().validate(value)


class MultipleChoiceField(Field):
    """Multiple choice field"""

    def __init__(self, choices: List[tuple], **kwargs):
        super().__init__(list, choices=choices, **kwargs)

    def validate(self, value: Any) -> Any:
        if value and not isinstance(value, list):
            raise ValidationError("MultipleChoiceField must be a list")

        if value:
            valid_choices = [choice[0] for choice in self.choices]
            for item in value:
                if str(item) not in valid_choices:
                    raise ValidationError(f"Invalid choice: {item}")

        return super().validate(value)


class ModelChoiceField(Field):
    """Field that uses model instances as choices"""

    def __init__(self, model_class: Type, **kwargs):
        super().__init__(model_class, **kwargs)
        self.model_class = model_class

    def validate(self, value: Any) -> Any:
        if value:
            # Check if instance exists
            if not hasattr(value, '_pk'):
                raise ValidationError("Invalid model instance")

        return super().validate(value)


# Widget system
class Widget:
    """Base widget class"""

    def __init__(self, attrs: Optional[Dict[str, str]] = None):
        self.attrs = attrs or {}

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> str:
        """Render widget HTML"""
        raise NotImplementedError("Subclasses must implement render method")

    def build_attrs(self, base_attrs: Dict[str, str], extra_attrs: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build HTML attributes"""
        attrs = base_attrs.copy()
        if extra_attrs:
            attrs.update(extra_attrs)
        attrs.update(self.attrs)
        return attrs


class InputWidget(Widget):
    """Basic input widget"""

    input_type = 'text'

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> str:
        final_attrs = self.build_attrs({'type': self.input_type, 'name': name, 'id': name})
        if value is not None:
            final_attrs['value'] = str(value)

        attrs_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        return f'<input {attrs_str}>'


class TextInputWidget(InputWidget):
    """Text input widget"""
    pass


class EmailInputWidget(InputWidget):
    """Email input widget"""
    input_type = 'email'


class URLInputWidget(InputWidget):
    """URL input widget"""
    input_type = 'url'


class PasswordInputWidget(InputWidget):
    """Password input widget"""
    input_type = 'password'


class NumberInputWidget(InputWidget):
    """Number input widget"""
    input_type = 'number'


class DateInputWidget(InputWidget):
    """Date input widget"""
    input_type = 'date'


class DateTimeInputWidget(InputWidget):
    """DateTime input widget"""
    input_type = 'datetime-local'


class TextareaWidget(Widget):
    """Textarea widget"""

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> str:
        final_attrs = self.build_attrs({'name': name, 'id': name}, attrs)
        attrs_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        content = str(value) if value is not None else ''
        return f'<textarea {attrs_str}>{content}</textarea>'


class SelectWidget(Widget):
    """Select dropdown widget"""

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> str:
        final_attrs = self.build_attrs({'name': name, 'id': name}, attrs)
        attrs_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])

        options = []
        if hasattr(self, 'choices') and self.choices:
            for option_value, option_label in self.choices:
                selected = 'selected' if str(option_value) == str(value) else ''
                options.append(f'<option value="{option_value}" {selected}>{option_label}</option>')

        return f'<select {attrs_str}>{"".join(options)}</select>'


class CheckboxInputWidget(Widget):
    """Checkbox widget"""

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> str:
        final_attrs = self.build_attrs({'type': 'checkbox', 'name': name, 'id': name}, attrs)
        if value:
            final_attrs['checked'] = 'checked'

        attrs_str = ' '.join([f'{k}="{v}"' for k, v in final_attrs.items()])
        return f'<input {attrs_str}>'


class CheckboxSelectMultipleWidget(Widget):
    """Multiple checkbox widget"""

    def render(self, name: str, value: Any, attrs: Optional[Dict[str, str]] = None) -> str:
        if not isinstance(value, list):
            value = [value] if value else []

        options = []
        if hasattr(self, 'choices') and self.choices:
            for option_value, option_label in self.choices:
                checked = 'checked' if str(option_value) in [str(v) for v in value] else ''
                options.append(
                    f'<label><input type="checkbox" name="{name}" value="{option_value}" {checked}> {option_label}</label>'
                )

        return ''.join(options)


class FileInputWidget(InputWidget):
    """File input widget"""
    input_type = 'file'


class HiddenInputWidget(InputWidget):
    """Hidden input widget"""
    input_type = 'hidden'


# Widget registry
WIDGET_REGISTRY = {
    'text': TextInputWidget,
    'email': EmailInputWidget,
    'url': URLInputWidget,
    'password': PasswordInputWidget,
    'number': NumberInputWidget,
    'date': DateInputWidget,
    'datetime': DateTimeInputWidget,
    'textarea': TextareaWidget,
    'select': SelectWidget,
    'checkbox': CheckboxInputWidget,
    'checkbox_multiple': CheckboxSelectMultipleWidget,
    'file': FileInputWidget,
    'hidden': HiddenInputWidget,
}


# Enhanced form with widgets
class FormMeta(type):
    """Metaclass to collect form fields and set up widgets"""

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # Collect fields and set up widgets
        for field_name, field in new_class.__dict__.items():
            if isinstance(field, Field):
                # Set default widget if not specified
                if not field.widget:
                    field.widget = cls._get_default_widget(field)

                # Set default label if not specified
                if not field.label:
                    field.label = field_name.replace('_', ' ').title()

        return new_class

    def _get_default_widget(cls, field: Field) -> str:
        """Get default widget for field type"""
        widget_map = {
            str: 'text',
            int: 'number',
            float: 'number',
            bool: 'checkbox',
            date: 'date',
            datetime: 'datetime',
            list: 'checkbox_multiple',
            dict: 'textarea',
        }

        for field_type, widget in widget_map.items():
            if isinstance(field, field_type) or field.field_type == field_type:
                return widget

        return 'text'


class Form(BaseForm, metaclass=FormMeta):
    """Enhanced form with widget support"""

    def __init__(self, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None):
        super().__init__(data)
        self.files = files or {}
        self.widgets = {}

        # Set up widgets for fields
        for field_name, field in self.fields.items():
            widget_class = WIDGET_REGISTRY.get(field.widget, TextInputWidget)
            self.widgets[field_name] = widget_class()

            # Set choices on widget if applicable
            if hasattr(field, 'choices') and field.choices:
                self.widgets[field_name].choices = field.choices

    def as_p(self) -> str:
        """Render form as HTML paragraphs"""
        html_parts = []

        for field_name, field in self.fields.items():
            widget = self.widgets[field_name]
            value = self.data.get(field_name, field.default)
            error = self.errors.get(field_name, '')

            # Field HTML
            field_html = widget.render(field_name, value)

            # Label
            label = f'<label for="{field_name}">{field.label}</label>' if field.label else ''

            # Error
            error_html = f'<span class="error">{error}</span>' if error else ''

            # Help text
            help_html = f'<small class="help">{field.help_text}</small>' if field.help_text else ''

            html_parts.append(
                f'<p>{label}{field_html}{error_html}{help_html}</p>'
            )

        return '\n'.join(html_parts)

    def as_table(self) -> str:
        """Render form as HTML table"""
        rows = []

        for field_name, field in self.fields.items():
            widget = self.widgets[field_name]
            value = self.data.get(field_name, field.default)
            error = self.errors.get(field_name, '')

            field_html = widget.render(field_name, value)
            error_html = f'<td class="error">{error}</td>' if error else '<td></td>'

            rows.append(
                f'<tr><th><label for="{field_name}">{field.label}</label></th>'
                f'<td>{field_html}</td>{error_html}</tr>'
            )

        return f'<table>{"".join(rows)}</table>'


# Formsets for handling multiple forms
class BaseFormSet:
    """Base formset for handling multiple forms"""

    def __init__(self, form_class: Type[Form], data: Optional[List[Dict]] = None,
                 initial: Optional[List[Dict]] = None, prefix: str = 'form'):
        self.form_class = form_class
        self.data = data or []
        self.initial = initial or []
        self.prefix = prefix
        self.forms = []
        self.errors = []

        self._construct_forms()

    def _construct_forms(self):
        """Construct individual forms"""
        self.forms = []
        self.errors = []

        for i, form_data in enumerate(self.data):
            form_prefix = f"{self.prefix}-{i}"
            form = self.form_class(form_data, prefix=form_prefix)
            self.forms.append(form)

    def is_valid(self) -> bool:
        """Check if all forms are valid"""
        self.errors = []

        for form in self.forms:
            if not form.is_valid():
                self.errors.append(form.errors)

        return len(self.errors) == 0

    def save(self):
        """Save all forms"""
        for form in self.forms:
            if form.is_valid():
                form.save()


# Common validators
def validate_email(value: str) -> str:
    """Email validator"""
    field = EmailField()
    return field._validate_email(value)


def validate_url(value: str) -> str:
    """URL validator"""
    field = URLField()
    return field._validate_url(value)


def validate_min_length(min_len: int) -> Callable:
    """Minimum length validator"""
    def validator(value: str) -> str:
        if value and len(value) < min_len:
            raise ValidationError(f"Minimum length is {min_len}")
        return value
    return validator


def validate_max_length(max_len: int) -> Callable:
    """Maximum length validator"""
    def validator(value: str) -> str:
        if value and len(value) > max_len:
            raise ValidationError(f"Maximum length is {max_len}")
        return value
    return validator


def validate_regex(pattern: str, message: str = "Invalid format") -> Callable:
    """Regex validator"""
    def validator(value: str) -> str:
        if value and not re.match(pattern, value):
            raise ValidationError(message)
        return value
    return validator


def validate_range(min_val: Optional[Union[int, float]] = None,
                  max_val: Optional[Union[int, float]] = None) -> Callable:
    """Range validator"""
    def validator(value: Union[int, float]) -> Union[int, float]:
        if min_val is not None and value < min_val:
            raise ValidationError(f"Value must be at least {min_val}")
        if max_val is not None and value > max_val:
            raise ValidationError(f"Value must be at most {max_val}")
        return value
    return validator


__all__ = [
    # Core classes
    'Field', 'BaseForm', 'Form', 'BaseFormSet', 'ValidationError',

    # Basic field types
    'CharField', 'IntegerField', 'BooleanField', 'EmailField', 'URLField',
    'ChoiceField', 'DateField', 'DateTimeField', 'DecimalField', 'FileField',
    'ImageField', 'PasswordField', 'JSONField', 'MultipleChoiceField',
    'ModelChoiceField',

    # Widgets
    'Widget', 'InputWidget', 'TextInputWidget', 'EmailInputWidget',
    'URLInputWidget', 'PasswordInputWidget', 'NumberInputWidget',
    'DateInputWidget', 'DateTimeInputWidget', 'TextareaWidget',
    'SelectWidget', 'CheckboxInputWidget', 'CheckboxSelectMultipleWidget',
    'FileInputWidget', 'HiddenInputWidget',

    # Validators
    'validate_email', 'validate_url', 'validate_min_length',
    'validate_max_length', 'validate_regex', 'validate_range'
]
