/**
 * Server-Side Rendering Support for Pydance Client
 * Enables hydrating client components with server-rendered markup
 */

export class SSRRenderer {
  constructor(clientFramework) {
    this.client = clientFramework;
    this.hydratedComponents = new Set();
    this.serverData = {};
  }

  /**
   * Initialize SSR data from server
   */
  initializeSSRData(data) {
    if (window.__SSR_DATA__) {
      this.serverData = window.__SSR_DATA__;
    } else if (data) {
      this.serverData = data;
    }

    // Mark SSR hydrated
    if (window.__PYDANCE_SSR__ || window.__SSR_ENABLED__) {
      this.enableHydration();
    }
  }

  /**
   * Enable client-side hydration mode
   */
  enableHydration() {
    if (typeof window === 'undefined') {
      // Server-side: prepare for rendering
      return;
    }

    // Client-side: enable hydration
    this.hydrationMode = true;

    // Hijack component mounting to use hydration
    this.originalMount = this.client.mount;
    this.client.mount = this.hydrateComponent.bind(this);

    console.log('🔄 SSR Hydration enabled');
  }

  /**
   * Hydrate a component with server-rendered markup
   */
  async hydrateComponent(componentName, props = {}, element) {
    const elementId = element?.id || element?.dataset?.componentId;

    if (!this.hydrationMode || this.hydratedComponents.has(elementId)) {
      // Fall back to normal mounting
      return this.originalMount.call(this.client, componentName, props, element);
    }

    try {
      // Get server-rendered data
      const serverProps = this.getServerProps(componentName, elementId);

      // Merge server and client props
      const finalProps = {
        ...serverProps,
        ...props,
        _isHydrated: true,
        _serverRendered: true
      };

      // Hydrate the component
      const ComponentClass = await this.client.getComponent(componentName);
      const component = new ComponentClass(finalProps);

      // Attach to existing DOM element for hydration
      component.element = element;
      component.container = element;

      // Initialize component state from server data
      if (serverProps && serverProps.state) {
        component.state = { ...component.state, ...serverProps.state };
      }

      // Bind events and setup reactivity for client-side updates
      component._bindEvents();
      if (component.setupReactivity) {
        component.setupReactivity();
      }

      this.hydratedComponents.add(elementId);

      console.log(`✓ Hydrated: ${componentName}`);
      return component;

    } catch (error) {
      console.warn(`Failed to hydrate ${componentName}, falling back to client rendering:`, error);
      return this.originalMount.call(this.client, componentName, props, element);
    }
  }

  /**
   * Get server-rendered props for a component
   */
  getServerProps(componentName, elementId) {
    // Try to find server data by component name and ID
    const data = this.serverData?.components?.[componentName] ||
                 this.serverData?.components?.[elementId];

    if (data) {
      return data.props || data;
    }

    return {};
  }

  /**
   * Pre-render component on server
   * (This runs on server-side Node.js environment)
   */
  static async renderToString(componentName, props = {}, framework) {
    // This would be called from the Python SSR backend
    // Returns HTML string for server-side rendering
    if (typeof window !== 'undefined') {
      throw new Error('renderToString should only be called on server');
    }

    try {
      // Dynamic import the component
      const module = await import(`../components/${componentName}.js`);
      const ComponentClass = module[componentName] || module.default;

      const component = new ComponentClass(props);

      // Render to string
      let html = component.render();

      // Add SSR data for hydration
      const ssrData = {
        componentName,
        props,
        state: component.state || {},
        timestamp: Date.now()
      };

      html = html.replace(
        '<div',
        `<div data-ssr-component="${componentName}" data-ssr-hydrate="true"`
      );

      // Inject component data
      const dataScript = `<script type="application/json" data-ssr-props="${componentName}">${JSON.stringify(ssrData)}</script>`;
      html = html.replace('</div>', `</div>${dataScript}`);

      return html;

    } catch (error) {
      console.error(`SSR renderToString failed for ${componentName}:`, error);
      return `<div data-ssr-error="${componentName}">Error rendering component</div>`;
    }
  }

  /**
   * Create client-side hydration script
   */
  static createHydrationScript() {
    return `
      <script>
        (function() {
          const components = document.querySelectorAll('[data-ssr-hydrate]');
          function init() {
            if (window.PydanceClient?.ssrRenderer) {
              components.forEach(el => {
                window.PydanceClient.ssrRenderer.hydrateComponent(el.dataset.ssrComponent, {}, el);
              });
            } else setTimeout(init, 10);
          }
          document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
        })();
      </script>
    `;
  }

  /**
   * Check if component was server-rendered
   */
  isServerRendered(element) {
    return element?.hasAttribute('data-ssr-hydrate');
  }

  /**
   * Get hydration status for debugging
   */
  getHydrationStatus() {
    return {
      mode: this.hydrationMode ? 'hydration' : 'client-only',
      hydratedCount: this.hydratedComponents.size,
      hydratedComponents: Array.from(this.hydratedComponents),
      serverDataAvailable: !!Object.keys(this.serverData).length
    };
  }
}
