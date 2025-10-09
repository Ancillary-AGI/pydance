/**
 * @fileoverview SSR Integration - Server-Side Rendering for Pydance Client
 * Provides full-stack SSR capabilities with Pydance backend integration
 *
 * @description
 * This module implements Pydance Client's SSR integration, which provides:
 * - Server-side component rendering with Pydance
 * - Hydration strategies for client-side interactivity
 * - State synchronization between server and client
 * - SEO optimization with meta tag management
 * - Universal components that work on both sides
 * - Data fetching strategies for SSR
 * - Error boundaries for SSR error handling
 * - Performance monitoring for SSR metrics
 *
 * The SSR system enables:
 * - Universal applications that run on both server and client
 * - SEO-friendly server-side rendering
 * - Improved initial page load performance
 * - Better user experience with instant navigation
 * - Full-stack data flow and state management
 * - Progressive enhancement and graceful degradation
 *
 * @example
 * ```javascript
 * // Server-side rendering
 * import { renderToString } from '~/core/SSRIntegration.js';
 *
 * const html = await renderToString(MyApp, {
 *   initialData: { user: currentUser },
 *   metaTags: { title: 'My App' }
 * });
 *
 * // Client-side hydration
 * import { hydrate } from '~/core/SSRIntegration.js';
 *
 * hydrate(MyApp, document.getElementById('root'), {
 *   initialData: window.__INITIAL_DATA__
 * });
 * ```
 *
 * @author Pydance Framework Team
 * @version 3.0.0
 * @license MIT
 */

// SSR Context for server-side rendering
export class SSRContext {
  constructor(options = {}) {
    this.isServer = true;
    this.isClient = false;
    this.requests = new Map();
    this.components = new Set();
    this.metaTags = new Map();
    this.scripts = new Set();
    this.styles = new Set();
    this.initialData = options.initialData || {};
    this.routes = options.routes || [];
    this.currentRoute = options.currentRoute || {};

    // Server-side state
    this.serverState = {};
    this.renderedComponents = new Set();
  }

  // Register component for SSR
  registerComponent(componentName, component) {
    this.components.add({ name: componentName, component });
  }

  // Set meta tag for SEO
  setMetaTag(name, content) {
    this.metaTags.set(name, content);
  }

  // Add script for hydration
  addScript(src) {
    this.scripts.add(src);
  }

  // Add stylesheet
  addStyle(href) {
    this.styles.add(href);
  }

  // Set server state for hydration
  setServerState(key, value) {
    this.serverState[key] = value;
  }

  // Generate HTML shell for SSR
  generateHTMLShell(content, options = {}) {
    const {
      title = 'Pydance Application',
      lang = 'en',
      charset = 'utf-8'
    } = options;

    return `
<!DOCTYPE html>
<html lang="${lang}">
<head>
  <meta charset="${charset}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>

  <!-- Meta tags for SEO -->
  ${Array.from(this.metaTags.entries())
    .map(([name, content]) => `<meta name="${name}" content="${content}">`)
    .join('\n  ')}

  <!-- Stylesheets -->
  ${Array.from(this.styles)
    .map(href => `<link rel="stylesheet" href="${href}">`)
    .join('\n  ')}

  <!-- Preload critical resources -->
  <link rel="preload" href="/client.js" as="script">
</head>
<body>
  <div id="root">${content}</div>

  <!-- Initial data for hydration -->
  <script>
    window.__INITIAL_DATA__ = ${JSON.stringify(this.initialData).replace(/</g, '\\u003c')};
    window.__SERVER_STATE__ = ${JSON.stringify(this.serverState).replace(/</g, '\\u003c')};
    window.__ROUTES__ = ${JSON.stringify(this.routes).replace(/</g, '\\u003c')};
  </script>

  <!-- Client bundle -->
  <script src="/client.js"></script>
</body>
</html>`;
  }
}

// Global SSR context instance
let ssrContext = null;

// SSR Renderer for server-side component rendering
export class SSRRenderer {
  constructor(options = {}) {
    this.options = options;
    this.context = new SSRContext(options);
  }

  // Render component to string on server
  async renderToString(Component, props = {}, options = {}) {
    // Create server-side component instance
    const component = new Component(props);

    // Set SSR context
    const prevContext = ssrContext;
    ssrContext = this.context;

    try {
      // Render component to HTML string
      const html = component.renderToString();

      // Generate full HTML document
      const fullHTML = this.context.generateHTMLShell(html, options);

      return {
        html: fullHTML,
        context: this.context,
        serverState: this.context.serverState,
        metaTags: Object.fromEntries(this.context.metaTags)
      };
    } finally {
      ssrContext = prevContext;
    }
  }

  // Render component tree to string
  async renderComponentTree(componentTree, options = {}) {
    const results = [];

    for (const component of componentTree) {
      const result = await this.renderToString(
        component.component,
        component.props,
        component.options
      );
      results.push(result);
    }

    return results;
  }

  // Pre-render routes for static generation
  async preRenderRoutes(routes, options = {}) {
    const results = [];

    for (const route of routes) {
      try {
        const result = await this.renderToString(
          route.component,
          route.props,
          { ...options, currentRoute: route }
        );

        results.push({
          route: route.path,
          html: result.html,
          success: true
        });
      } catch (error) {
        results.push({
          route: route.path,
          error: error.message,
          success: false
        });
      }
    }

    return results;
  }
}

// Client-side Hydration Manager
export class HydrationManager {
  constructor() {
    this.hydratedComponents = new Set();
    this.pendingHydrations = new Map();
  }

  // Hydrate component with server-rendered content
  hydrate(Component, container, options = {}) {
    const {
      initialData = window.__INITIAL_DATA__,
      serverState = window.__SERVER_STATE__,
      routes = window.__ROUTES__
    } = options;

    // Create component instance
    const component = new Component();

    // Set up hydration data
    component.hydrationData = {
      initialData,
      serverState,
      routes,
      container
    };

    // Hydrate the component
    component.hydrate(container, {
      initialData,
      serverState
    });

    // Mark as hydrated
    this.hydratedComponents.add(component);

    return component;
  }

  // Progressive hydration for better performance
  async progressiveHydration(components, options = {}) {
    const {
      chunkSize = 5,
      delay = 100
    } = options;

    for (let i = 0; i < components.length; i += chunkSize) {
      const chunk = components.slice(i, i + chunkSize);

      // Hydrate chunk
      chunk.forEach(({ Component, container, props }) => {
        this.hydrate(Component, container, props);
      });

      // Wait before next chunk (except for last chunk)
      if (i + chunkSize < components.length) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  // Check if component is hydrated
  isHydrated(component) {
    return this.hydratedComponents.has(component);
  }

  // Get hydration statistics
  getHydrationStats() {
    return {
      hydratedCount: this.hydratedComponents.size,
      pendingCount: this.pendingHydrations.size,
      totalComponents: this.hydratedComponents.size + this.pendingHydrations.size
    };
  }
}

// Global hydration manager instance
export const hydrationManager = new HydrationManager();

// Universal Component wrapper for SSR compatibility
export const createUniversalComponent = (componentFn) => {
  return createComponent((props) => {
    // Server-side rendering
    if (typeof window === 'undefined') {
      return componentFn(props);
    }

    // Client-side rendering with hydration
    const component = componentFn(props);

    // Use hydration manager if available
    if (component.hydrationData) {
      hydrationManager.hydrate(component, component.hydrationData.container);
    }

    return component;
  });
};

// Data fetching utilities for SSR
export class DataFetcher {
  constructor(options = {}) {
    this.cache = new Map();
    this.pendingRequests = new Map();
    this.defaultTTL = options.ttl || 5 * 60 * 1000; // 5 minutes
  }

  // Fetch data for SSR
  async fetchForSSR(url, options = {}) {
    const {
      cache = true,
      ttl = this.defaultTTL,
      headers = {}
    } = options;

    // Check cache first
    if (cache && this.cache.has(url)) {
      const cached = this.cache.get(url);
      if (Date.now() - cached.timestamp < ttl) {
        return cached.data;
      }
    }

    // Fetch data
    try {
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'public, max-age=300',
          ...headers
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Cache the result
      if (cache) {
        this.cache.set(url, {
          data,
          timestamp: Date.now()
        });
      }

      return data;
    } catch (error) {
      console.error('SSR data fetch error:', error);
      throw error;
    }
  }

  // Prefetch data for routes
  async prefetchRouteData(routes) {
    const promises = routes.map(async (route) => {
      try {
        const data = await this.fetchForSSR(route.dataUrl);
        return { route: route.path, data, success: true };
      } catch (error) {
        return { route: route.path, error: error.message, success: false };
      }
    });

    return Promise.all(promises);
  }

  // Clear cache
  clearCache() {
    this.cache.clear();
  }

  // Get cache statistics
  getCacheStats() {
    return {
      size: this.cache.size,
      hitRate: this.cache.size > 0 ? (this.cache.size / (this.cache.size + this.pendingRequests.size)) : 0
    };
  }
}

// Global data fetcher instance
export const dataFetcher = new DataFetcher();

// SEO utilities for SSR
export class SEOUtils {
  constructor() {
    this.defaultMeta = {
      title: 'Pydance Application',
      description: 'Modern full-stack application built with Pydance Framework',
      keywords: 'pydance, python, web framework, ssr, reactive',
      author: 'Pydance Team',
      robots: 'index, follow'
    };
  }

  // Generate meta tags for page
  generateMetaTags(pageMeta = {}) {
    const meta = { ...this.defaultMeta, ...pageMeta };

    return {
      title: meta.title,
      meta: [
        { name: 'description', content: meta.description },
        { name: 'keywords', content: meta.keywords },
        { name: 'author', content: meta.author },
        { name: 'robots', content: meta.robots },
        { property: 'og:title', content: meta.title },
        { property: 'og:description', content: meta.description },
        { property: 'og:type', content: 'website' },
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: meta.title },
        { name: 'twitter:description', content: meta.description }
      ]
    };
  }

  // Generate structured data for rich snippets
  generateStructuredData(data) {
    return {
      '@context': 'https://schema.org',
      '@type': data.type || 'WebApplication',
      name: data.name || this.defaultMeta.title,
      description: data.description || this.defaultMeta.description,
      url: data.url || window.location.href,
      ...data
    };
  }

  // Generate sitemap for SEO
  generateSitemap(routes) {
    const baseUrl = window.location.origin;

    return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${routes.map(route => `
    <url>
      <loc>${baseUrl}${route.path}</loc>
      <lastmod>${new Date().toISOString()}</lastmod>
      <changefreq>${route.changefreq || 'weekly'}</changefreq>
      <priority>${route.priority || '0.8'}</priority>
    </url>
  `).join('')}
</urlset>`;
  }
}

// Global SEO utilities instance
export const seoUtils = new SEOUtils();

// SSR Error Boundary for graceful error handling
export const createSSRErrorBoundary = (fallbackComponent) => {
  return createComponent((props) => {
    const [error, setError] = useState(null);
    const [errorInfo, setErrorInfo] = useState(null);

    // Server-side error handling
    if (typeof window === 'undefined') {
      try {
        return props.children;
      } catch (serverError) {
        console.error('SSR Error:', serverError);
        return fallbackComponent({
          error: serverError,
          errorInfo: { componentStack: 'Server-side error' }
        });
      }
    }

    // Client-side error handling
    useEffect(() => {
      const handleError = (event) => {
        setError(event.error);
        setErrorInfo(event.errorInfo || {});
      };

      window.addEventListener('error', handleError);
      window.addEventListener('unhandledrejection', handleError);

      return () => {
        window.removeEventListener('error', handleError);
        window.removeEventListener('unhandledrejection', handleError);
      };
    }, []);

    if (error) {
      return fallbackComponent({ error, errorInfo, resetError: () => {
        setError(null);
        setErrorInfo(null);
      }});
    }

    return props.children;
  });
};

// Universal Router for SSR applications
export class UniversalRouter {
  constructor(routes = []) {
    this.routes = routes;
    this.currentRoute = null;
    this.params = {};
  }

  // Match route for current path
  matchRoute(path) {
    for (const route of this.routes) {
      const match = this.matchPath(route.path, path);
      if (match) {
        return {
          route,
          params: match.params,
          path
        };
      }
    }
    return null;
  }

  // Simple path matching (can be enhanced with path-to-regexp)
  matchPath(pattern, path) {
    const paramNames = [];
    const regexPattern = pattern
      .replace(/:([^/]+)/g, (match, paramName) => {
        paramNames.push(paramName);
        return '([^/]+)';
      })
      .replace(/\*/g, '.*');

    const regex = new RegExp(`^${regexPattern}$`);
    const match = path.match(regex);

    if (match) {
      const params = {};
      paramNames.forEach((name, index) => {
        params[name] = match[index + 1];
      });
      return { params };
    }

    return null;
  }

  // Render route component
  async renderRoute(path, options = {}) {
    const match = this.matchRoute(path);

    if (!match) {
      throw new Error(`Route not found: ${path}`);
    }

    this.currentRoute = match;
    this.params = match.params;

    // Fetch data for route if needed
    if (match.route.dataFetcher) {
      const data = await match.route.dataFetcher(match.params);
      options.initialData = { ...options.initialData, ...data };
    }

    // Render component
    const renderer = new SSRRenderer(options);
    return renderer.renderToString(match.route.component, {
      params: match.params,
      ...options
    });
  }

  // Get current route
  getCurrentRoute() {
    return this.currentRoute;
  }

  // Get route parameters
  getParams() {
    return this.params;
  }
}

// Export SSR utilities
export default {
  SSRContext,
  SSRRenderer,
  HydrationManager,
  hydrationManager,
  createUniversalComponent,
  DataFetcher,
  dataFetcher,
  SEOUtils,
  seoUtils,
  createSSRErrorBoundary,
  UniversalRouter
};
