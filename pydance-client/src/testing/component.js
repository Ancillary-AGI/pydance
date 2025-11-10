/**
 * @fileoverview Framework-Agnostic Component Testing Utilities
 */

/**
 * Creates a test wrapper for components of any framework
 * @param {Function} componentFactory - Component factory function
 * @param {Object} defaultProps - Default props
 * @param {Object} options - Test configuration options
 * @returns {Object} Test utilities
 */
export function createTestComponent(componentFactory, defaultProps = {}, options = {}) {
  const {
    framework = 'generic', // 'react', 'vue', 'svelte', 'generic'
    renderMethod = 'render',
    mountMethod = 'mount',
    unmountMethod = 'unmount',
    updateMethod = 'update'
  } = options;

  return {
    /**
     * Render component with props
     * @param {Object} props - Component props
     * @returns {Object} Rendered component
     */
    render(props = {}) {
      const mergedProps = { ...defaultProps, ...props };

      try {
        // Framework-specific rendering
        if (framework === 'react') {
          // React-specific rendering logic would go here
          return componentFactory(mergedProps);
        } else if (framework === 'vue') {
          // Vue-specific rendering logic would go here
          return componentFactory(mergedProps);
        } else {
          // Generic rendering
          return componentFactory(mergedProps);
        }
      } catch (error) {
        console.error(`Error rendering component: ${error.message}`);
        throw error;
      }
    },

    /**
     * Mount component to DOM
     * @param {Object} props - Component props
     * @param {string|HTMLElement} container - Container
     * @returns {Object} Mounted component
     */
    mount(props = {}, container = null) {
      const instance = this.render(props);

      if (container) {
        if (typeof container === 'string') {
          container = document.querySelector(container);
        }

        if (container && instance[mountMethod]) {
          instance[mountMethod](container);
        } else if (container && instance.mount) {
          instance.mount(container);
        } else if (container) {
          // Fallback: append to container
          container.appendChild(instance.element || instance);
        }
      }

      return instance;
    },

    /**
     * Unmount component from DOM
     * @param {Object} instance - Component instance
     */
    unmount(instance) {
      if (instance && instance[unmountMethod]) {
        instance[unmountMethod]();
      } else if (instance && instance.unmount) {
        instance.unmount();
      } else if (instance && instance.element && instance.element.parentNode) {
        instance.element.parentNode.removeChild(instance.element);
      }
    },

    /**
     * Update component with new props
     * @param {Object} instance - Component instance
     * @param {Object} newProps - New props
     */
    update(instance, newProps = {}) {
      if (instance && instance[updateMethod]) {
        instance[updateMethod](newProps);
      } else if (instance && instance.update) {
        instance.update(newProps);
      } else {
        // Re-render with new props
        const updatedInstance = this.render({ ...instance.props, ...newProps });
        return updatedInstance;
      }
    },

    /**
     * Test component variations
     * @param {Array} propVariations - Prop variations
     * @returns {Array} Rendered instances
     */
    testVariations(propVariations = []) {
      return propVariations.map(props => this.render(props));
    },

    /**
     * Test component lifecycle
     * @param {Object} props - Component props
     * @param {Function} lifecycleTest - Lifecycle test function
     */
    async testLifecycle(props = {}, lifecycleTest) {
      const container = document.createElement('div');
      document.body.appendChild(container);

      try {
        const instance = this.mount(props, container);
        await lifecycleTest(instance);
      } finally {
        this.unmount(instance);
        document.body.removeChild(container);
      }
    },

    /**
     * Test component with different prop combinations
     * @param {Array} propMatrix - Matrix of prop combinations
     * @param {Function} testFn - Test function for each combination
     */
    async testPropMatrix(propMatrix = [], testFn) {
      for (const props of propMatrix) {
        const instance = this.render(props);
        await testFn(instance, props);
      }
    }
  };
}
