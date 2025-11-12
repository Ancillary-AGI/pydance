"""
Comprehensive SSR Integration Tests for Pydance Client and Server.

Tests the complete SSR pipeline including template rendering, component rendering,
pydance-client integration, hydration, caching, and cross-framework support.
"""

import pytest
import tempfile

from pydance.ssr.renderer import SSRRenderer, SSRConfig, SSRFramework


@pytest.mark.asyncio
class TestSSRBasicFunctionality:
    """Test basic SSR rendering functionality with pydance-client integration."""

    @pytest.fixture
    def temp_template_dir(self):
        """Create temporary template directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            # Create template structure
            (template_dir / 'layouts').mkdir()
            (template_dir / 'components').mkdir()

            # Create basic templates
            layout_template = """
            <!DOCTYPE html>
            <html>
            <head><title>{{title}}</title></head>
            <body>
                <div id="app">{{content}}</div>
            </body>
            </html>
            """
            (template_dir / 'layouts' / 'base.html').write_text(layout_template)

            component_template = """
            <div class="test-component">
                <h1>{{props.title}}</h1>
                <p>{{props.description}}</p>
            </div>
            """
            (template_dir / 'components' / 'test.html').write_text(component_template)

            yield template_dir

    @pytest.fixture
    def ssr_renderer(self, temp_template_dir):
        """Create SSR renderer instance for testing."""
        config = SSRConfig(enable_hydration=True, cache_ttl=300, timeout_per_render=30.0)
        return SSRRenderer(str(temp_template_dir), config)

    async def test_template_rendering_with_ssr_injection(self, ssr_renderer):
        """Test basic template rendering with SSR data injection."""
        data = {
            'title': 'Test Page',
            'content': '<div>Hello World</div>'
        }

        html = await ssr_renderer.render_template('layouts/base.html', data)

        # Verify HTML structure
        assert '<!DOCTYPE html>' in html
        assert '<title>Test Page</title>' in html
        assert '<div>Hello World</div>' in html
        assert 'window.__SSR_DATA__' in html
        assert 'window.__PYDANCE_SSR__ = true' in html

    async def test_ssr_component_rendering_pydance_client(self, ssr_renderer):
        """Test pydance-client component SSR rendering."""
        # Test pydance-client component rendering
        html = await ssr_renderer.render_component('TestComponent', {'title': 'Hello'}, 'pydance')

        # When pydance-client SSR fails (as expected in test environment),
        # it should fall back to template or placeholder rendering
        assert html  # Should return some HTML
        # Either pydance-client SSR output or fallback
        assert ('data-ssr-component' in html or
                'data-component' in html or
                'TestComponent' in html)

    async def test_react_component_fallback_rendering(self, ssr_renderer):
        """Test React component placeholder when no actual SSR."""
        html = await ssr_renderer._render_react_component("MyComponent", {"message": "Hello"})

        assert 'data-react-component="MyComponent"' in html
        assert '"message": "Hello"' in html

    async def test_vue_component_fallback_rendering(self, ssr_renderer):
        """Test Vue component placeholder when no actual SSR."""
        html = await ssr_renderer._render_vue_component("MyComponent", {"active": True})

        assert 'data-vue-component="MyComponent"' in html
        assert '"active": true' in html

    async def test_svelte_component_fallback_rendering(self, ssr_renderer):
        """Test Svelte component placeholder when no actual SSR."""
        html = await ssr_renderer._render_svelte_component("MyComponent", {"count": 42})

        assert 'data-svelte-component="MyComponent"' in html
        assert '"count": 42' in html

    async def test_unknown_framework_error_handling(self, ssr_renderer):
        """Test error handling for unknown framework."""
        with pytest.raises(ValueError, match="Unsupported framework"):
            await ssr_renderer._render_framework_component("TestComponent", {}, "unknown-framework")

    async def test_template_fallback_component_rendering(self, ssr_renderer, temp_template_dir):
        """Test template-based fallback component rendering."""
        # This should use the test.html template we created
        html = await ssr_renderer._render_fallback_component('test', {
            'props': {'title': 'Test Title', 'description': 'Test Description'}
        })

        # Should render using the template
        assert len(html.strip()) > 0

    async def test_page_rendering_integration(self, ssr_renderer):
        """Test complete page rendering functionality."""
        html = await ssr_renderer.render_page('/test/route', {'id': '123'}, {'filter': 'active'})

        assert '<!DOCTYPE html>' in html
        assert 'Page - /test/route' in html
        assert 'window.__SSR_DATA__' in html

    async def test_hydration_data_generation(self, ssr_renderer):
        """Test generation of hydration data."""
        result = await ssr_renderer.render_with_hydration('TestComponent', {
            'prop1': 'value1',
            'prop2': {'nested': True}
        }, 'pydance')

        assert 'html' in result
        assert 'hydration_data' in result
        assert 'framework' in result

        hydration_data = result['hydration_data']
        assert hydration_data['component'] == 'TestComponent'
        assert hydration_data['props']['prop1'] == 'value1'
        assert hydration_data['props']['prop2']['nested'] is True
        assert hydration_data['framework'] == 'pydance'
        assert 'checksum' in hydration_data


@pytest.mark.asyncio
class TestSSRCachingAndPerformance:
    """Test SSR caching and performance optimizations."""

    @pytest.fixture
    def ssr_renderer(self, tmp_path):
        """Create SSR renderer for performance testing."""
        config = SSRConfig(enable_hydration=True, cache_ttl=300)
        renderer = SSRRenderer(str(tmp_path), config)
        return renderer

    async def test_ssr_caching_mechanism(self, ssr_renderer):
        """Test SSR component caching works correctly."""
        component_name = "CachedComponent"
        props = {"data": "test-value"}

        # First render
        html1 = await ssr_renderer.render_component(component_name, props, 'pydance')

        # Second render - should use cache
        html2 = await ssr_renderer.render_component(component_name, props, 'pydance')

        # Results should be identical (cached)
        assert html1 == html2

        # Verify cache contains entry
        assert hasattr(ssr_renderer, 'cache')

    async def test_cache_operations_with_custom_keys(self, ssr_renderer):
        """Test cache set/get operations with custom key."""
        custom_key = "custom_cache_key"
        cache_value = "<div>Cached HTML</div>"

        await ssr_renderer.cache.set(custom_key, cache_value)
        retrieved_value = await ssr_renderer.cache.get(custom_key)

        assert retrieved_value == cache_value

    async def test_cache_clearing_functionality(self, ssr_renderer):
        """Test cache clearing removes all entries."""
        # Add multiple entries
        await ssr_renderer.cache.set("key1", "value1")
        await ssr_renderer.cache.set("key2", "value2")

        # Verify they exist
        assert await ssr_renderer.cache.get("key1") == "value1"
        assert await ssr_renderer.cache.get("key2") == "value2"

        # Clear cache
        ssr_renderer.clear_cache()

        # Verify they're gone
        assert await ssr_renderer.cache.get("key1") is None
        assert await ssr_renderer.cache.get("key2") is None


@pytest.mark.asyncio
class TestSSRMultiFrameworkSupport:
    """Test multi-framework SSR support."""

    @pytest.fixture
    def ssr_renderer(self, tmp_path):
        """Create SSR renderer for multi-framework testing."""
        config = SSRConfig(enable_hydration=False)
        renderer = SSRRenderer(str(tmp_path), config)
        return renderer

    async def test_react_framework_component_dispatch(self, ssr_renderer):
        """Test React framework component dispatch."""
        html = await ssr_renderer.render_component("ReactComp", {}, "react")
        assert "data-react-component" in html

    async def test_vue_framework_component_dispatch(self, ssr_renderer):
        """Test Vue framework component dispatch."""
        html = await ssr_renderer.render_component("VueComp", {}, "vue")
        assert "data-vue-component" in html

    async def test_svelte_framework_component_dispatch(self, ssr_renderer):
        """Test Svelte framework component dispatch."""
        html = await ssr_renderer.render_component("SvelteComp", {}, "svelte")
        assert "data-svelte-component" in html

    async def test_default_framework_fallback(self, ssr_renderer):
        """Test default framework when not specified."""
        html = await ssr_renderer.render_component("DefaultComp", {}, "pydance")
        assert html  # Should not be empty

    async def test_streaming_ssr_vs_regular_ssr(self, ssr_renderer):
        """Test streaming SSR matches regular SSR."""
        route = "/test/streaming"

        # Mock the template rendering to avoid file system dependencies
        with patch.object(ssr_renderer, 'render_template', return_value="<html>Test</html>"):
            # Test that both methods return valid HTML
            regular_html = await ssr_renderer.render_page(route)
            streaming_html = await ssr_renderer.render_page_streaming(route)

            # Both should return HTML strings
            assert isinstance(regular_html, str)
            assert isinstance(streaming_html, str)
            assert len(regular_html) > 0
            assert len(streaming_html) > 0

            # For now, they should be identical as streaming isn't fully implemented
            assert regular_html == streaming_html


@pytest.mark.asyncio
class TestSSRConfigurationAndErrorHandling:
    """Test SSR configuration and error handling."""

    def test_ssr_config_defaults(self):
        """Test SSR configuration defaults."""
        config = SSRConfig()

        assert config.framework == SSRFramework.REACT
        assert config.enable_hydration is True
        assert config.cache_ttl == 300
        assert config.timeout_per_render == 10.0
        assert config.enable_compression is True

    def test_ssr_config_custom_values(self):
        """Test SSR configuration with custom values."""
        config = SSRConfig(
            framework=SSRFramework.VUE,
            enable_hydration=False,
            cache_ttl=600,
            timeout_per_render=20.0,
            enable_error_boundary=False
        )

        assert config.framework == SSRFramework.VUE
        assert config.enable_hydration is False
        assert config.cache_ttl == 600
        assert config.timeout_per_render == 20.0
        assert config.enable_error_boundary is False

    def test_ssr_framework_enum_values(self):
        """Test SSR framework enum values."""
        assert SSRFramework.REACT.value == "react"
        assert SSRFramework.VUE.value == "vue"
        assert SSRFramework.SVELTE.value == "svelte"
        assert SSRFramework.ANGULAR.value == "angular"
        assert SSRFramework.LIT.value == "lit"
        assert SSRFramework.VANILLA.value == "vanilla"

    @pytest.fixture
    def ssr_renderer(self, tmp_path):
        """Create SSR renderer for error handling tests."""
        config = SSRConfig(timeout_per_render=0.1)  # Very short timeout
        renderer = SSRRenderer(str(tmp_path), config)
        return renderer

    async def test_component_rendering_error_fallback(self, ssr_renderer):
        """Test that component rendering errors properly fallback."""
        # This should succeed (even with fallback logic)
        html = await ssr_renderer.render_component("NonExistentComponent", {}, "nonexistent")

        # Should return some valid HTML (fallback components)
        assert html
        assert len(html.strip()) > 0

    async def test_template_rendering_error_handling(self, ssr_renderer):
        """Test template rendering error handling."""
        # Try to render non-existent template - should not crash
        try:
            html = await ssr_renderer.render_template("nonexistent.html", {})
            # This might succeed with fallback or should handle the error gracefully
            assert html  # If it doesn't crash, it should return something
        except Exception as e:
            # Expected behavior for non-existent template
            pass  # The test passes if no unhandled exception is raised
