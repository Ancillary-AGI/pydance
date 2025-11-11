"""
Complete Server-Side Rendering system for Pydance Framework.

This module provides comprehensive SSR capabilities for pydance-client including:
- Template rendering with data hydration
- Client-side bridge for seamless integration
- Caching and performance optimization
- Prerendering capabilities
- SEO optimization
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional

from pydance.ssr.renderer import SSRRenderer
from pydance.ssr.bridge import SSRBridge
from pydance.ssr.cache import SSRCache
from pydance.ssr.prerenderer import Prerenderer

# Main SSR components
__all__ = [
    'SSRRenderer',
    'DataHydrator',
    'SSRBridge',
    'SSRCache',
    'Prerenderer',
    'render_to_string',
    'prerender_app',
    'create_ssr_bridge',
    'get_ssr_renderer',
    'get_ssr_bridge',
    'get_ssr_cache',
]

# Global SSR instances
_ssr_renderer: Optional[SSRRenderer] = None
_ssr_bridge: Optional[SSRBridge] = None
_ssr_cache: Optional[SSRCache] = None

def get_ssr_renderer() -> SSRRenderer:
    """Get or create the global SSR renderer instance."""
    global _ssr_renderer
    if _ssr_renderer is None:
        _ssr_renderer = SSRRenderer()
    return _ssr_renderer

def get_ssr_bridge() -> SSRBridge:
    """Get or create the global SSR bridge instance."""
    global _ssr_bridge
    if _ssr_bridge is None:
        _ssr_bridge = SSRBridge()
    return _ssr_bridge

def get_ssr_cache() -> SSRCache:
    """Get or create the global SSR cache instance."""
    global _ssr_cache
    if _ssr_cache is None:
        _ssr_cache = SSRCache()
    return _ssr_cache

async def render_to_string(template_path: str, data: Dict[str, Any] = None, context: Dict[str, Any] = None) -> str:
    """
    Render a template to string with SSR support.

    Args:
        template_path: Path to the template file
        data: Data to pass to the template
        context: Additional context for rendering

    Returns:
        Rendered HTML string
    """
    renderer = get_ssr_renderer()
    return await renderer.render_template(template_path, data or {}, context or {})

async def prerender_app(app_path: str, routes: List[str] = None, output_dir: str = 'dist') -> Dict[str, Any]:
    """
    Prerender the entire application for static hosting.

    Args:
        app_path: Path to the application entry point
        routes: List of routes to prerender
        output_dir: Output directory for prerendered files

    Returns:
        Dictionary with prerendering results
    """
    prerenderer = Prerenderer()
    return await prerenderer.prerender_app(app_path, routes or [], output_dir)

def create_ssr_bridge(client_entry: str = 'pydance-client/src/index.js') -> SSRBridge:
    """
    Create an SSR bridge for client-server communication.

    Args:
        client_entry: Path to the client entry point

    Returns:
        Configured SSR bridge instance
    """
    return SSRBridge(client_entry)
