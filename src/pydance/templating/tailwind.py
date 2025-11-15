"""
Tailwind CSS Integration for Pydance Templates

Provides optional Tailwind CSS support for templates, views, and components.
Includes utility classes, component styles, and responsive design helpers.

Features:
- Automatic CSS class generation for components
- Responsive design utilities
- Dark mode support
- Theme-aware styling
- Integration with Pydance widgets and views
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import json
import re


class TailwindConfig:
    """Configuration for Tailwind CSS integration"""

    def __init__(self,
                 enabled: bool = False,
                 cdn_url: str = "https://cdn.tailwindcss.com",
                 version: str = "3.4.0",
                 custom_css: Optional[str] = None,
                 dark_mode: str = "media",  # 'media', 'class', or False
                 content_paths: Optional[List[str]] = None,
                 theme: Optional[Dict[str, Any]] = None):
        self.enabled = enabled
        self.cdn_url = cdn_url
        self.version = version
        self.custom_css = custom_css or ""
        self.dark_mode = dark_mode
        self.content_paths = content_paths or ["templates/**/*.{html,js}", "static/**/*.js"]
        self.theme = theme or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "enabled": self.enabled,
            "cdn_url": self.cdn_url,
            "version": self.version,
            "custom_css": self.custom_css,
            "dark_mode": self.dark_mode,
            "content_paths": self.content_paths,
            "theme": self.theme
        }


class TailwindCSS:
    """Tailwind CSS integration manager"""

    def __init__(self, config: TailwindConfig):
        self.config = config
        self._css_cache: Optional[str] = None

    def is_enabled(self) -> bool:
        """Check if Tailwind CSS is enabled"""
        return self.config.enabled

    def get_cdn_link(self) -> str:
        """Get CDN link for Tailwind CSS"""
        if not self.is_enabled():
            return ""

        script = f'<script src="{self.config.cdn_url}"></script>'
        if self.config.custom_css:
            script += f'\n<style>{self.config.custom_css}</style>'

        return script

    def get_css_classes(self, component: str, variant: str = "default") -> str:
        """Get Tailwind CSS classes for a component"""
        if not self.is_enabled():
            return ""

        # Component class mappings
        component_classes = {
            "button": {
                "default": "inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                "secondary": "inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                "danger": "inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            },
            "input": {
                "default": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "error": "block w-full px-3 py-2 border border-red-300 rounded-md shadow-sm placeholder-red-300 focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm text-red-900"
            },
            "card": {
                "default": "bg-white overflow-hidden shadow rounded-lg",
                "bordered": "bg-white overflow-hidden shadow rounded-lg border border-gray-200"
            },
            "alert": {
                "success": "bg-green-50 border border-green-200 rounded-md p-4",
                "error": "bg-red-50 border border-red-200 rounded-md p-4",
                "warning": "bg-yellow-50 border border-yellow-200 rounded-md p-4",
                "info": "bg-blue-50 border border-blue-200 rounded-md p-4"
            },
            "badge": {
                "default": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800",
                "success": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800",
                "error": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
            }
        }

        return component_classes.get(component, {}).get(variant, "")

    def get_responsive_classes(self, base_classes: str, breakpoints: Optional[Dict[str, str]] = None) -> str:
        """Generate responsive classes"""
        if not self.is_enabled() or not breakpoints:
            return base_classes

        responsive_parts = [base_classes]

        # Add responsive prefixes
        prefix_map = {
            "sm": "sm:",
            "md": "md:",
            "lg": "lg:",
            "xl": "xl:",
            "2xl": "2xl:"
        }

        for bp, classes in breakpoints.items():
            if bp in prefix_map:
                responsive_parts.append(f"{prefix_map[bp]}{classes}")

        return " ".join(responsive_parts)

    def get_dark_mode_classes(self, light_classes: str, dark_classes: Optional[str] = None) -> str:
        """Generate dark mode classes"""
        if not self.is_enabled() or self.config.dark_mode != "class":
            return light_classes

        if dark_classes:
            return f"{light_classes} dark:{dark_classes}"

        # Auto-generate dark variants for common classes
        dark_variants = []
        for cls in light_classes.split():
            if cls.startswith("bg-white"):
                dark_variants.append("dark:bg-gray-800")
            elif cls.startswith("text-gray-"):
                dark_variants.append(f"dark:text-gray-{900 if '900' in cls else 100}")
            elif cls.startswith("border-gray-"):
                dark_variants.append(f"dark:border-gray-{700 if '200' in cls else 600}")
            else:
                dark_variants.append(cls)

        return f"{light_classes} {' '.join(dark_variants)}"


# Global Tailwind CSS instance
_tailwind_instance: Optional[TailwindCSS] = None


def get_tailwind() -> TailwindCSS:
    """Get global Tailwind CSS instance"""
    global _tailwind_instance
    if _tailwind_instance is None:
        # Default config - disabled by default
        config = TailwindConfig(enabled=False)
        _tailwind_instance = TailwindCSS(config)
    return _tailwind_instance


def configure_tailwind(config: TailwindConfig) -> None:
    """Configure global Tailwind CSS instance"""
    global _tailwind_instance
    _tailwind_instance = TailwindCSS(config)


def enable_tailwind(cdn_url: str = "https://cdn.tailwindcss.com",
                   custom_css: str = "",
                   dark_mode: str = "media") -> None:
    """Enable Tailwind CSS with default configuration"""
    config = TailwindConfig(
        enabled=True,
        cdn_url=cdn_url,
        custom_css=custom_css,
        dark_mode=dark_mode
    )
    configure_tailwind(config)


def disable_tailwind() -> None:
    """Disable Tailwind CSS"""
    config = TailwindConfig(enabled=False)
    configure_tailwind(config)


# Template helper functions
def tw_classes(component: str, variant: str = "default") -> str:
    """Template helper for component classes"""
    return get_tailwind().get_css_classes(component, variant)


def tw_responsive(base_classes: str, breakpoints: Optional[Dict[str, str]] = None) -> str:
    """Template helper for responsive classes"""
    return get_tailwind().get_responsive_classes(base_classes, breakpoints)


def tw_dark(light_classes: str, dark_classes: Optional[str] = None) -> str:
    """Template helper for dark mode classes"""
    return get_tailwind().get_dark_mode_classes(light_classes, dark_classes)


# Built-in component templates with Tailwind CSS
BUTTON_TEMPLATE = """
<button class="{{ classes|default(tw_classes('button', variant), true) }}"
        {% if disabled %}disabled{% endif %}
        {% if type %}type="{{ type }}"{% endif %}>
    {{ text }}
</button>
"""

INPUT_TEMPLATE = """
<input class="{{ classes|default(tw_classes('input', variant), true) }}"
       {% if type %}type="{{ type }}"{% endif %}
       {% if name %}name="{{ name }}"{% endif %}
       {% if value %}value="{{ value }}"{% endif %}
       {% if placeholder %}placeholder="{{ placeholder }}"{% endif %}
       {% if required %}required{% endif %}
       {% if disabled %}disabled{% endif %}>
"""

CARD_TEMPLATE = """
<div class="{{ classes|default(tw_classes('card', variant), true) }}">
    {% if header %}
    <div class="px-4 py-5 sm:px-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900">{{ header }}</h3>
    </div>
    {% endif %}
    <div class="px-4 py-5 sm:p-6">
        {{ content }}
    </div>
</div>
"""

ALERT_TEMPLATE = """
<div class="{{ classes|default(tw_classes('alert', variant), true) }}">
    <div class="flex">
        <div class="flex-shrink-0">
            {% if variant == 'success' %}
            <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            {% elif variant == 'error' %}
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            {% endif %}
        </div>
        <div class="ml-3">
            <p class="text-sm font-medium text-gray-800">{{ message }}</p>
        </div>
    </div>
</div>
"""


__all__ = [
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
