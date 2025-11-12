"""
Modern Python Template Engine
A high-performance, pure Python template rendering system with async support.
"""

import asyncio
from typing import Dict, Any, Optional, Union, List, Callable
from abc import ABC, abstractmethod


@dataclass
class TemplateConfig:
    """Configuration for template engine"""
    cache_enabled: bool = True
    cache_dir: Optional[Path] = None
    auto_escape: bool = True
    trim_blocks: bool = True
    lstrip_blocks: bool = False
    keep_trailing_newline: bool = False


class TemplateError(Exception):
    """Base exception for template errors"""
    pass


class TemplateSyntaxError(TemplateError):
    """Exception for template syntax errors"""
    pass


class AbstractTemplateEngine(ABC):
    """Abstract base class for all template engines"""

    def __init__(self, template_dir: Path, **options):
        self.template_dir = Path(template_dir)
        self.options = options

    @abstractmethod
    async def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template file"""
        pass

    @abstractmethod
    async def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string"""
        pass


def get_template_engine(engine_type: str = "lean", template_dir: str = "templates") -> AbstractTemplateEngine:
    """Get template engine instance"""
    template_path = Path(template_dir)

    if engine_type == "lean":
        return LeanTemplateEngine(template_path)
    elif engine_type == "jinja":
        return JinjaTemplateEngine(template_path)
    else:
        raise ValueError(f"Unknown template engine: {engine_type}")


def render_template_string(source: str, engine_type: str = "lean", **context) -> str:
    """Render template string"""
    engine = get_template_engine(engine_type)
    try:
        # Try to get current event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, create a task
        task = loop.create_task(engine.render_string(source, context))
        return loop.run_until_complete(task)
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(engine.render_string(source, context))


def render_template_file(path: Union[str, Path], engine_type: str = "lean", **context) -> str:
    """Render template file"""
    engine = get_template_engine(engine_type)
    return asyncio.run(engine.render(str(path), context))


async def render_template_string_async(source: str, engine_type: str = "lean", **context) -> str:
    """Async render template string"""
    engine = get_template_engine(engine_type)
    return await engine.render_string(source, context)


async def render_template_file_async(path: Union[str, Path], engine_type: str = "lean", **context) -> str:
    """Async render template file"""
    engine = get_template_engine(engine_type)
    return await engine.render(str(path), context)


# Alias for backward compatibility
TemplateEngine = lambda template_dir="templates": get_template_engine("lean", template_dir)
