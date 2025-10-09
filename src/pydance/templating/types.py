"""
Template types for Pydance.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any

class TemplateEngine(str, Enum):
    JINJA2 = "jinja2"
    LEAN = "lean"
    DJANGO = "django"

@dataclass
class TemplateConfig:
    engine: TemplateEngine = TemplateEngine.JINJA2
    cache_templates: bool = True
    auto_reload: bool = False
    options: Dict[str, Any] = field(default_factory=dict)
