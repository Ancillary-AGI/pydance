/**
 * @fileoverview Plugin System - Extensible Ecosystem for Pydance Client
 * Provides a comprehensive plugin architecture for extending framework capabilities
 *
 * @description
 * This module implements Pydance Client's plugin system, which provides:
 * - Plugin registry and lifecycle management
 * - Plugin dependency resolution and loading
 * - Plugin marketplace and distribution
 * - Plugin development tools and templates
 * - Built-in ecosystem plugins for common use cases
 *
 * The plugin system enables:
 * - Router plugin for client-side routing
 * - State management plugin for global state
 * - Form handling plugin with validation
 * - HTTP client plugin for API integration
 * - Testing utilities plugin for component testing
 * - Performance monitoring and optimization plugins
 * - Custom plugin development and distribution
 *
 * @example
 * ```javascript
 * import { PluginRegistry, RouterPlugin, StatePlugin } from '~/core/PluginSystem.js';
 *
 * // Register plugins
 * PluginRegistry.register('router', RouterPlugin);
 * PluginRegistry.register('state', StatePlugin);
 *
 * // Use plugins in components
 * const MyComponent = createComponent(() => {
 *   const router = usePlugin('router');
 *   const state = usePlugin('state');
 *
 *   return jsx('div', {
 *     children: [
 *       jsx('h1', { children: 'My App' }),
 *       jsx('button', {
 *         onClick: () => router.navigate('/dashboard'),
 *         children: 'Go to Dashboard'
 *       })
 *     ]
 *   });
 * });
 * ```
 *
 * @author Pydance Framework Team
 * @version 0.1.0
 * @license MIT
 */

// Plugin Registry for managing ecosystem plugins
export class PluginRegistry {
  constructor() {
    this.plugins = new Map();
    this.instances = new Map();
    this.dependencies = new Map();
    this.loadOrder = [];
  }

  // Register a plugin class
  register(name, PluginClass, dependencies = []) {
    this.plugins.set(name, PluginClass);
    this.dependencies.set(name, dependencies);

    // Calculate load order based on dependencies
    this._calculateLoadOrder();

    console.log(`Plugin registered: ${name}`);
  }

  // Get a plugin instance
  get(name, config = {}) {
    if (!this.plugins.has(name)) {
      throw new Error(`Plugin not found: ${name}`);
    }

    if (!this.instances.has(name)) {
      const PluginClass = this.plugins.get(name);
      const instance = new PluginClass(config);
      this.instances.set(name, instance);

      // Initialize plugin
      instance.initialize();
    }

    return this.instances.get(name);
  }

  // Load all plugins in dependency order
  async loadAll(configs = {}) {
    for (const name of this.loadOrder) {
      const config = configs[name] || {};
      await this.get(name, config);
    }
  }

  // Unload a plugin
  unload(name) {
    if (this.instances.has(name)) {
      const instance = this.instances.get(name);
      instance.destroy();
      this.instances.delete(name);
    }
  }

  // Get all registered plugin names
  getPluginNames() {
    return Array.from(this.plugins.keys());
  }

  // Check if plugin is registered
  hasPlugin(name) {
    return this.plugins.has(name);
  }

  // Calculate load order based on dependencies
  _calculateLoadOrder() {
    const visited = new Set();
    const temp = new Set();
    const order = [];

    const visit = (name) => {
      if (temp.has(name)) {
        throw new Error(`Circular dependency detected for plugin: ${name}`);
      }
      if (!visited.has(name)) {
        temp.add(name);

        const deps = this.dependencies.get(name) || [];
        deps.forEach(dep => visit(dep));

        temp.delete(name);
        visited.add(name);
        order.push(name);
      }
    };

    this.plugins.forEach((_, name) => {
      if (!visited.has(name)) {
        visit(name);
      }
    });

    this.loadOrder = order;
  }

  // Get plugin statistics
  getStats() {
    return {
      totalPlugins: this.plugins.size,
      loadedPlugins: this.instances.size,
      loadOrder: this.loadOrder,
      dependencies: Object.fromEntries(this.dependencies)
    };
  }
}

// Global plugin registry instance
export const pluginRegistry = new PluginRegistry();

// Router Plugin for client-side routing
export class RouterPlugin {
  constructor(config = {}) {
    this.routes = new Map();
    this.currentRoute = null;
    this.history = [];
    this.listeners = new Set();
    this.basePath = config.basePath || '/';
    this.mode = config.mode || 'history'; // 'hash' or 'history'
  }

  initialize() {
    this.setupRouting();
    this.handleInitialRoute();
  }

  // Define a route
  addRoute(path, component, meta = {}) {
    this.routes.set(path, { component, meta });
  }

  // Navigate to a route
  navigate(path, state = {}) {
    const route = this.routes.get(path);
    if (!route) {
      throw new Error(`Route not found: ${path}`);
    }

    // Update URL
    if (this.mode === 'history') {
      window.history.pushState(state, '', this.basePath + path);
    } else {
      window.location.hash = path;
    }

    // Update current route
    this.currentRoute = { path, ...route, state };
    this.history.push(this.currentRoute);

    // Notify listeners
    this.notifyListeners();

    return this.currentRoute;
  }

  // Go back in history
  goBack() {
    if (this.history.length > 1) {
      this.history.pop();
      const previousRoute = this.history[this.history.length - 1];

      if (this.mode === 'history') {
        window.history.back();
      } else {
        window.location.hash = previousRoute.path;
      }

      this.currentRoute = previousRoute;
      this.notifyListeners();
    }
  }

  // Get current route
  getCurrentRoute() {
    return this.currentRoute;
  }

  // Subscribe to route changes
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // Setup routing based on mode
  setupRouting() {
    if (this.mode === 'history') {
      window.addEventListener('popstate', (event) => {
        this.handlePopState(event);
      });
    } else {
      window.addEventListener('hashchange', () => {
        this.handleHashChange();
      });
    }
  }

  // Handle browser back/forward buttons
  handlePopState(event) {
    const path = window.location.pathname.replace(this.basePath, '');
    this.currentRoute = { path, state: event.state };
    this.notifyListeners();
  }

  // Handle hash changes
  handleHashChange() {
    const path = window.location.hash.substring(1);
    const route = this.routes.get(path);
    if (route) {
      this.currentRoute = { path, ...route };
      this.notifyListeners();
    }
  }

  // Handle initial route
  handleInitialRoute() {
    let path;
    if (this.mode === 'history') {
      path = window.location.pathname.replace(this.basePath, '') || '/';
    } else {
      path = window.location.hash.substring(1) || '/';
    }

    const route = this.routes.get(path);
    if (route) {
      this.currentRoute = { path, ...route };
    }
  }

  // Notify route change listeners
  notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.currentRoute);
      } catch (error) {
        console.error('Route listener error:', error);
      }
    });
  }

  destroy() {
    this.listeners.clear();
    this.routes.clear();
    this.history = [];
  }
}

// State Management Plugin for global state
export class StatePlugin {
  constructor(config = {}) {
    this.stores = new Map();
    this.globalState = {};
    this.listeners = new Map();
    this.middleware = [];
  }

  initialize() {
    // Initialize global state management
    this.globalState = new Proxy(this.globalState, {
      set: (target, key, value) => {
        target[key] = value;
        this.notifyListeners(key, value);
        return true;
      }
    });
  }

  // Create a store
  createStore(name, initialState = {}, reducers = {}) {
    const store = {
      name,
      state: { ...initialState },
      reducers,
      listeners: new Set()
    };

    this.stores.set(name, store);
    return store;
  }

  // Get store state
  getState(storeName) {
    const store = this.stores.get(storeName);
    return store ? store.state : null;
  }

  // Dispatch action to store
  dispatch(storeName, action) {
    const store = this.stores.get(storeName);
    if (!store) {
      throw new Error(`Store not found: ${storeName}`);
    }

    const reducer = store.reducers[action.type];
    if (reducer) {
      const newState = reducer(store.state, action);
      store.state = { ...newState };
      store.listeners.forEach(listener => listener(store.state));
    }
  }

  // Subscribe to store changes
  subscribe(storeName, listener) {
    const store = this.stores.get(storeName);
    if (store) {
      store.listeners.add(listener);
      return () => store.listeners.delete(listener);
    }
  }

  // Subscribe to global state changes
  subscribeGlobal(key, listener) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }

    this.listeners.get(key).add(listener);
    return () => this.listeners.get(key)?.delete(listener);
  }

  // Notify listeners of state changes
  notifyListeners(key, value) {
    const keyListeners = this.listeners.get(key);
    if (keyListeners) {
      keyListeners.forEach(listener => {
        try {
          listener(value);
        } catch (error) {
          console.error('State listener error:', error);
        }
      });
    }
  }

  // Add middleware for state management
  addMiddleware(middleware) {
    this.middleware.push(middleware);
  }

  destroy() {
    this.stores.clear();
    this.listeners.clear();
    this.middleware = [];
  }
}

// HTTP Client Plugin for API integration
export class HttpClientPlugin {
  constructor(config = {}) {
    this.baseURL = config.baseURL || '';
    this.defaultHeaders = config.headers || {};
    this.interceptors = {
      request: [],
      response: []
    };
  }

  initialize() {
    // Setup default configuration
  }

  // Make HTTP request
  async request(method, url, options = {}) {
    const config = {
      method: method.toUpperCase(),
      headers: { ...this.defaultHeaders, ...options.headers },
      ...options
    };

    // Apply request interceptors
    for (const interceptor of this.interceptors.request) {
      await interceptor(config);
    }

    const response = await fetch(this.baseURL + url, config);

    // Apply response interceptors
    let processedResponse = response;
    for (const interceptor of this.interceptors.response) {
      processedResponse = await interceptor(processedResponse);
    }

    return processedResponse;
  }

  // Convenience methods
  async get(url, options = {}) {
    return this.request('GET', url, options);
  }

  async post(url, data, options = {}) {
    return this.request('POST', url, {
      ...options,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
  }

  async put(url, data, options = {}) {
    return this.request('PUT', url, {
      ...options,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
  }

  async delete(url, options = {}) {
    return this.request('DELETE', url, options);
  }

  // Add request interceptor
  addRequestInterceptor(interceptor) {
    this.interceptors.request.push(interceptor);
  }

  // Add response interceptor
  addResponseInterceptor(interceptor) {
    this.interceptors.response.push(interceptor);
  }

  destroy() {
    this.interceptors.request = [];
    this.interceptors.response = [];
  }
}

// Form Plugin for form handling and validation
export class FormPlugin {
  constructor(config = {}) {
    this.forms = new Map();
    this.validators = new Map();
    this.validationRules = config.validationRules || {};
  }

  initialize() {
    // Setup form validation rules
    this.setupDefaultValidators();
  }

  // Register a form
  registerForm(name, initialValues = {}, validationSchema = {}) {
    const form = {
      name,
      values: { ...initialValues },
      errors: {},
      touched: {},
      isSubmitting: false,
      isValid: true
    };

    this.forms.set(name, form);
    return form;
  }

  // Get form values
  getFormValues(formName) {
    const form = this.forms.get(formName);
    return form ? form.values : null;
  }

  // Set form value
  setFormValue(formName, field, value) {
    const form = this.forms.get(formName);
    if (form) {
      form.values[field] = value;
      form.touched[field] = true;

      // Validate field
      this.validateField(formName, field);
    }
  }

  // Validate entire form
  async validateForm(formName) {
    const form = this.forms.get(formName);
    if (!form) return false;

    const errors = {};
    let isValid = true;

    for (const field of Object.keys(form.values)) {
      const fieldErrors = await this.validateField(formName, field);
      if (fieldErrors.length > 0) {
        errors[field] = fieldErrors;
        isValid = false;
      }
    }

    form.errors = errors;
    form.isValid = isValid;

    return isValid;
  }

  // Validate single field
  async validateField(formName, field) {
    const form = this.forms.get(formName);
    if (!form) return [];

    const value = form.values[field];
    const rules = this.validationRules[field] || [];

    const errors = [];

    for (const rule of rules) {
      const isValid = await rule(value, form.values);
      if (!isValid) {
        errors.push(`${field} is invalid`);
      }
    }

    form.errors[field] = errors;
    return errors;
  }

  // Submit form
  async submitForm(formName, submitHandler) {
    const form = this.forms.get(formName);
    if (!form) {
      throw new Error(`Form not found: ${formName}`);
    }

    form.isSubmitting = true;

    try {
      const isValid = await this.validateForm(formName);
      if (!isValid) {
        throw new Error('Form validation failed');
      }

      await submitHandler(form.values);
    } finally {
      form.isSubmitting = false;
    }
  }

  // Setup default validators
  setupDefaultValidators() {
    this.validationRules = {
      email: [
        (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || 'Invalid email format'
      ],
      required: [
        (value) => value != null && value !== '' || 'This field is required'
      ],
      minLength: (minLength) => [
        (value) => value.length >= minLength || `Minimum length is ${minLength}`
      ],
      maxLength: (maxLength) => [
        (value) => value.length <= maxLength || `Maximum length is ${maxLength}`
      ]
    };
  }

  destroy() {
    this.forms.clear();
    this.validators.clear();
  }
}

// Performance Monitoring Plugin
export class PerformanceMonitorPlugin {
  constructor(config = {}) {
    this.metrics = new Map();
    this.intervals = new Map();
    this.thresholds = config.thresholds || {};
  }

  initialize() {
    this.startGlobalMonitoring();
  }

  // Monitor component performance
  monitorComponent(componentName, component) {
    const metrics = {
      renderCount: 0,
      totalRenderTime: 0,
      memoryUsage: 0,
      lastUpdate: Date.now()
    };

    this.metrics.set(componentName, metrics);

    // Monitor render performance
    const originalUpdateDOM = component.updateDOM.bind(component);
    component.updateDOM = function(vdom) {
      const startTime = performance.now();
      originalUpdateDOM(vdom);
      const endTime = performance.now();

      metrics.renderCount++;
      metrics.totalRenderTime += (endTime - startTime);
      metrics.lastUpdate = Date.now();

      // Check thresholds
      this.checkThresholds(componentName, metrics);
    }.bind(this);
  }

  // Check performance thresholds
  checkThresholds(componentName, metrics) {
    const thresholds = this.thresholds[componentName] || {};

    if (thresholds.maxRenderTime && metrics.totalRenderTime > thresholds.maxRenderTime) {
      console.warn(`Performance threshold exceeded for ${componentName}: render time`);
    }

    if (thresholds.maxMemoryUsage && metrics.memoryUsage > thresholds.maxMemoryUsage) {
      console.warn(`Performance threshold exceeded for ${componentName}: memory usage`);
    }
  }

  // Start global performance monitoring
  startGlobalMonitoring() {
    // Monitor FPS
    this.monitorFPS();

    // Monitor memory usage
    this.monitorMemory();

    // Monitor long tasks
    this.monitorLongTasks();
  }

  // Monitor frames per second
  monitorFPS() {
    let frameCount = 0;
    let lastTime = performance.now();

    const measureFPS = () => {
      frameCount++;
      const now = performance.now();
      const elapsed = now - lastTime;

      if (elapsed >= 1000) {
        const fps = frameCount / (elapsed / 1000);
        this.recordMetric('global', 'fps', fps);

        frameCount = 0;
        lastTime = now;
      }

      requestAnimationFrame(measureFPS);
    };

    requestAnimationFrame(measureFPS);
  }

  // Monitor memory usage
  monitorMemory() {
    if ('memory' in performance) {
      this.intervals.set('memory', setInterval(() => {
        const memory = performance.memory;
        this.recordMetric('global', 'memory', {
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize,
          limit: memory.jsHeapSizeLimit
        });
      }, 5000));
    }
  }

  // Monitor long tasks
  monitorLongTasks() {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.duration > 50) { // Tasks longer than 50ms
            this.recordMetric('global', 'longTask', {
              duration: entry.duration,
              startTime: entry.startTime
            });
          }
        });
      });

      try {
        observer.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        console.warn('Long task monitoring not supported');
      }
    }
  }

  // Record performance metric
  recordMetric(componentName, metricName, value) {
    if (!this.metrics.has(componentName)) {
      this.metrics.set(componentName, {});
    }

    const componentMetrics = this.metrics.get(componentName);
    componentMetrics[metricName] = value;
  }

  // Get performance metrics
  getMetrics(componentName = null) {
    if (componentName) {
      return this.metrics.get(componentName) || {};
    }
    return Object.fromEntries(this.metrics);
  }

  destroy() {
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals.clear();
    this.metrics.clear();
  }
}

// Plugin hook for use in components
export const usePlugin = (pluginName, config = {}) => {
  const component = currentComponent;
  if (!component) {
    throw new Error('usePlugin must be called within a component');
  }

  return component.usePlugin(pluginName, config);
};

// Export all plugins
export default {
  PluginRegistry,
  pluginRegistry,
  RouterPlugin,
  StatePlugin,
  HttpClientPlugin,
  FormPlugin,
  PerformanceMonitorPlugin,
  usePlugin
};
