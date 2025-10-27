"""
Pydance Widgets Forms

Form-related widgets for building dynamic web interfaces.
"""

from pydance.widgets.core import Widget, WidgetConfig, WidgetType


class FormWidget(Widget):
    """Base form widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)

    @property
    def widget_type(self) -> WidgetType:
        return WidgetType.FORM


class FieldWidget(FormWidget):
    """Base field widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)


class ButtonWidget(FormWidget):
    """Button widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)
        self.text = kwargs.get('text', 'Button')
        self.type = kwargs.get('type', 'button')

    def render(self) -> str:
        attrs = self.get_attributes()
        attrs.update({
            'type': self.type,
        })
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<button {attr_str}>{self.text}</button>'


class InputWidget(FieldWidget):
    """Input widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)
        self.input_type = kwargs.get('type', 'text')

    def render(self) -> str:
        attrs = self.get_attributes()
        attrs.update({
            'type': self.input_type,
        })
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<input {attr_str}>'


class TextareaWidget(FieldWidget):
    """Textarea widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)
        self.rows = kwargs.get('rows', 4)
        self.cols = kwargs.get('cols', 50)

    def render(self) -> str:
        attrs = self.get_attributes()
        attrs.update({
            'rows': str(self.rows),
            'cols': str(self.cols),
        })
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<textarea {attr_str}></textarea>'


class SelectWidget(FieldWidget):
    """Select widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)
        self.options = kwargs.get('options', [])

    def render(self) -> str:
        attrs = self.get_attributes()
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        options_html = '\n'.join(f'<option value="{opt[0]}">{opt[1]}</option>' for opt in self.options)
        return f'<select {attr_str}>{options_html}</select>'


class CheckboxWidget(FieldWidget):
    """Checkbox widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)
        self.checked = kwargs.get('checked', False)

    def render(self) -> str:
        attrs = self.get_attributes()
        if self.checked:
            attrs['checked'] = 'checked'
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<input type="checkbox" {attr_str}>'


class RadioWidget(FieldWidget):
    """Radio widget"""

    def __init__(self, name: str, config: WidgetConfig = None, **kwargs):
        super().__init__(name, config, **kwargs)
        self.value = kwargs.get('value', '')
        self.checked = kwargs.get('checked', False)

    def render(self) -> str:
        attrs = self.get_attributes()
        attrs.update({
            'type': 'radio',
            'value': self.value,
        })
        if self.checked:
            attrs['checked'] = 'checked'
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<input {attr_str}>'


__all__ = [
    'FormWidget',
    'FieldWidget',
    'ButtonWidget',
    'InputWidget',
    'TextareaWidget',
    'SelectWidget',
    'CheckboxWidget',
    'RadioWidget',
]
