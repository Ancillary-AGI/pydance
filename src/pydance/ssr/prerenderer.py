"""
Prerenderer for Pydance SSR Framework.

This module provides static site generation capabilities by pre-rendering
pages at build time for improved performance and SEO.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class PrerenderConfig:
    """Configuration for prerendering."""
    output_dir: str = 'dist'
    routes: List[str] = None
    crawl: bool = True
    follow_external_links: bool = False
    max_depth: int = 3
    concurrency: int = 5
    timeout: int = 30
    user_agent: str = 'Pydance-Prerenderer/1.0'


@dataclass
class PrerenderResult:
    """Result of prerendering operation."""
    url: str
    status: str  # 'success', 'error', 'timeout', 'skipped'
    output_path: str
    error_message: Optional[str] = None
    render_time: float = 0.0
    file_size: int = 0


class Prerenderer:
    """
    Static site prerenderer for SSR applications.

    Pre-renders pages at build time for static hosting,
    improving performance and SEO.
    """

    def __init__(self, config: PrerenderConfig = None):
        self.config = config or PrerenderConfig()
        self.visited_urls: Set[str] = set()
        self.results: List[PrerenderResult] = []

    async def prerender_app(
        self,
        app_path: str,
        routes: List[str] = None,
        output_dir: str = 'dist'
    ) -> Dict[str, Any]:
        """
        Prerender the entire application.

        Args:
            app_path: Path to the application entry point
            routes: Specific routes to prerender
            output_dir: Output directory for prerendered files

        Returns:
            Prerendering results summary
        """
        self.config.output_dir = output_dir
        self.config.routes = routes or await self._discover_routes(app_path)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Prerender routes
        await self._prerender_routes()

        # Generate sitemap and metadata
        await self._generate_metadata()

        return self._get_summary()

    async def _discover_routes(self, app_path: str) -> List[str]:
        """Discover all routes in the application."""
        routes = []

        # Common routes to prerender
        default_routes = [
            '/',
            '/about',
            '/contact',
            '/blog',
            '/api/docs',
            '/404'
        ]

        # Try to extract routes from application
        try:
            # This would integrate with the actual routing system
            # For now, return default routes
            routes = default_routes
        except Exception as e:
            print(f"Error discovering routes: {e}")
            routes = default_routes

        return routes

    async def _prerender_routes(self) -> None:
        """Prerender all configured routes."""
        semaphore = asyncio.Semaphore(self.config.concurrency)

        async def prerender_with_semaphore(route: str) -> None:
            async with semaphore:
                await self._prerender_route(route)

        # Create tasks for all routes
        tasks = [
            prerender_with_semaphore(route)
            for route in self.config.routes
        ]

        # Execute with concurrency control
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _prerender_route(self, route: str) -> None:
        """Prerender a single route."""
        if route in self.visited_urls:
            return

        self.visited_urls.add(route)

        try:
            # Simulate prerendering process
            result = await self._render_route_to_html(route)

            # Write to file
            output_path = self._get_output_path(route)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.html)

            # Record result
            prerender_result = PrerenderResult(
                url=route,
                status='success',
                output_path=str(output_path),
                render_time=result.render_time,
                file_size=len(result.html.encode('utf-8'))
            )

            self.results.append(prerender_result)

        except asyncio.TimeoutError:
            self.results.append(PrerenderResult(
                url=route,
                status='timeout',
                output_path=self._get_output_path(route)
            ))
        except Exception as e:
            self.results.append(PrerenderResult(
                url=route,
                status='error',
                output_path=self._get_output_path(route),
                error_message=str(e)
            ))

    async def _render_route_to_html(self, route: str) -> 'RenderResult':
        """Render a route to HTML."""
        import time

        start_time = time.time()

        # This would integrate with the actual SSR renderer
        # For now, return a basic HTML structure
        html_content = await self._generate_basic_html(route)

        render_time = time.time() - start_time

        # Mock result object
        class RenderResult:
            def __init__(self, html, render_time):
                self.html = html
                self.render_time = render_time

        return RenderResult(html_content, render_time)

    async def _generate_basic_html(self, route: str) -> str:
        """Generate basic HTML for a route."""
        title = f"Pydance App - {route}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="Pydance SSR Application">
    <meta name="generator" content="Pydance-Prerenderer">
</head>
<body>
    <div id="app">
        <h1>{title}</h1>
        <p>This page was pre-rendered at build time.</p>
        <p>Route: {route}</p>
    </div>

    <!-- SSR Data -->
    <script>
        window.__PRERENDERED__ = true;
        window.__ROUTE__ = "{route}";
        window.__BUILD_TIME__ = "{asyncio.get_event_loop().time()}";
    </script>

    <!-- Client-side hydration script would go here -->
</body>
</html>"""

        return html

    def _get_output_path(self, route: str) -> Path:
        """Get output file path for a route."""
        output_path = Path(self.config.output_dir)

        if route == '/':
            return output_path / 'index.html'
        else:
            # Convert route to file path
            path_parts = route.strip('/').split('/')
            return output_path / '/'.join(path_parts) / 'index.html'

    async def _generate_metadata(self) -> None:
        """Generate sitemap and other metadata files."""
        output_path = Path(self.config.output_dir)

        # Generate sitemap.xml
        await self._generate_sitemap(output_path)

        # Generate prerender metadata
        await self._generate_prerender_metadata(output_path)

    async def _generate_sitemap(self, output_path: Path) -> None:
        """Generate XML sitemap."""
        sitemap_path = output_path / 'sitemap.xml'

        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

        for result in self.results:
            if result.status == 'success':
                sitemap_content += f"""    <url>
        <loc>https://example.com{result.url}</loc>
        <lastmod>{asyncio.get_event_loop().time()}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
"""

        sitemap_content += "</urlset>"

        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_content)

    async def _generate_prerender_metadata(self, output_path: Path) -> None:
        """Generate prerender metadata file."""
        metadata_path = output_path / 'prerender-metadata.json'

        metadata = {
            'generated_at': asyncio.get_event_loop().time(),
            'total_pages': len(self.results),
            'successful_pages': len([r for r in self.results if r.status == 'success']),
            'failed_pages': len([r for r in self.results if r.status == 'error']),
            'routes': [
                {
                    'url': result.url,
                    'status': result.status,
                    'output_path': result.output_path,
                    'render_time': result.render_time,
                    'file_size': result.file_size,
                    'error_message': result.error_message
                }
                for result in self.results
            ]
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def _get_summary(self) -> Dict[str, Any]:
        """Get prerendering summary."""
        total_pages = len(self.results)
        successful = len([r for r in self.results if r.status == 'success'])
        failed = len([r for r in self.results if r.status == 'error'])
        total_time = sum(r.render_time for r in self.results if r.render_time)

        return {
            'total_pages': total_pages,
            'successful_pages': successful,
            'failed_pages': failed,
            'success_rate': successful / total_pages if total_pages > 0 else 0,
            'total_render_time': total_time,
            'average_render_time': total_time / successful if successful > 0 else 0,
            'output_directory': self.config.output_dir,
            'routes_prerendered': [r.url for r in self.results if r.status == 'success']
        }

    async def prerender_single_route(self, route: str) -> PrerenderResult:
        """Prerender a single route."""
        await self._prerender_route(route)
        return [r for r in self.results if r.url == route][0]

    def get_prerendered_routes(self) -> List[str]:
        """Get list of successfully prerendered routes."""
        return [r.url for r in self.results if r.status == 'success']

    def clear_results(self) -> None:
        """Clear prerendering results."""
        self.results.clear()
        self.visited_urls.clear()

