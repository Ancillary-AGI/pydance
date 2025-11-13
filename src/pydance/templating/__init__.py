"""
Modern Python Template Engine
A high-performance, pure Python template rendering system with async support.
"""

from .engine import (
    TemplateConfig,
    TemplateError,
    TemplateSyntaxError,
    AbstractTemplateEngine,
    TemplateEngine,
    get_template_engine,
    render_template_string,
    render_template_file,
    render_template_string_async,
    render_template_file_async,
)

from .languages import LeanTemplateEngine, JinjaTemplateEngine

from .tailwind import (
    TailwindConfig,
    TailwindCSS,
    get_tailwind,
    configure_tailwind,
    enable_tailwind,
    disable_tailwind,
    tw_classes,
    tw_responsive,
    tw_dark,
    BUTTON_TEMPLATE,
    INPUT_TEMPLATE,
    CARD_TEMPLATE,
    ALERT_TEMPLATE
)

__all__ = [
    'TemplateConfig',
    'TemplateError',
    'TemplateSyntaxError',
    'AbstractTemplateEngine',
    'LeanTemplateEngine',
    'JinjaTemplateEngine',
    'TemplateEngine',
    'get_template_engine',
    'render_template_string',
    'render_template_file',
    'render_template_string_async',
    'render_template_file_async',
    # Tailwind CSS support (optional)
    'TailwindConfig',
    'TailwindCSS',
    'get_tailwind',
    'configure_tailwind',
    'enable_tailwind',
    'disable_tailwind',
    'tw_classes',
    'tw_responsive',
    'tw_dark',
    'BUTTON_TEMPLATE',
    'INPUT_TEMPLATE',
    'CARD_TEMPLATE',
    'ALERT_TEMPLATE'
]
