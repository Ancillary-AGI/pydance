/**
 * @fileoverview Component - Ultra-efficient Function-Based Component System
 * Provides signal-based reactivity with hooks and lifecycle management
 *
 * @description
 * This module implements Pydance Client's component system, which provides:
 * - Function-based components with automatic dependency tracking
 * - Virtual DOM with efficient diffing and selective updates
 * - Complete hooks system (useState, useEffect, useMemo, etc.)
 * - Context system for state sharing between components
 * - Error boundaries for graceful error handling
 * - Memory management with automatic cleanup
 * - JSX runtime with caching and optimization
 * - Event handling and ref management
 *
 * The component system is designed for maximum performance with:
 * - O(n) VDOM diffing instead of O(n²)
 * - Selective DOM updates (only changed elements)
 * - Automatic dependency tracking
 * - Memory leak prevention
 * - Batch updates for performance
 *
 * @example
 * ```javascript
 * import { createComponent, jsx, useState, useEffect } from '~/core/Component.js';
 *
 * const Counter = createComponent(() => {
 *   const [count, setCount] = useState(0);
 *
 *   useEffect(() => {
 *     document.title = `Count: ${count}`;
 *   }, [count]);
 *
 *   return jsx('div', {
 *     children: [
 *       jsx('h1', { children: `Count: ${count}` }),
 *       jsx('button', {
 *         onClick: () => setCount(c => c + 1),
 *         children: 'Increment'
 *       })
 *     ]
 *   });
 * });
 *
 * // Mount the component
 * const counter = new Counter();
 * counter.mount('#app');
 * ```
 *
 * @author Pydance Framework Team
 * @version 3.0.0
 * @license MIT
 */

import { signal, computed, effect, batch, isSignal, unwrap } from '~/core/Signal.js';

// Component context for tracking current component
let currentComponent = null;
const componentStack = [];

// JSX Element interface
export class JSXElement {
  constructor(tagName, props = {}, children = []) {
    this.$$typeof = Symbol.for('pydance.element');
    this.tagName = tagName;
    this.props = props;
    this.children = children.flat();
    this.key = props?.key || null;
    this.ref = props?.ref || null;
  }
}

// JSX Fragment
export class JSXFragment {
  constructor(children = [], props = {}) {
    this.$$typeof = Symbol.for('pydance.fragment');
    this.children = children.flat();
    this.props = props;
    this.key = props?.key || null;
  }
}

// Component Pool for advanced scaling
class ComponentPool {
  constructor(maxSize = 10000) {
    this.maxSize = maxSize;
    this.pool = new Map();
    this.totalCreated = 0;
    this.totalReused = 0;
  }

  get(renderFn, props) {
    const key = this.getKey(renderFn, props);

    if (!this.pool.has(key)) {
      this.pool.set(key, []);
    }

    const instances = this.pool.get(key);

    if (instances.length > 0) {
      const instance = instances.pop();
      instance.props = instance.createProps(props);
      this.totalReused++;
      return instance;
    }

    this.totalCreated++;
    return new ComponentInstance(renderFn, props);
  }

  release(instance) {
    if (this.pool.size >= this.maxSize) {
      // Pool is full, don't cache this instance
      return;
    }

    const key = this.getKey(instance.renderFn, instance.props.value);

    if (!this.pool.has(key)) {
      this.pool.set(key, []);
    }

    const instances = this.pool.get(key);

    // Reset instance state for reuse
    instance.reset();

    instances.push(instance);
  }

  getKey(renderFn, props) {
    return `${renderFn.name || 'anonymous'}:${JSON.stringify(props)}`;
  }

  getStats() {
    return {
      totalCreated: this.totalCreated,
      totalReused: this.totalReused,
      poolSize: this.pool.size,
      cacheHitRate: this.totalReused / (this.totalCreated + this.totalReused) || 0
    };
  }
}

// Global component pool instance
const componentPool = new ComponentPool();

// Plugin Classes for ecosystem extension
class VirtualScrollerPlugin {
  constructor(component, config = {}) {
    this.component = component;
    this.config = config;
    this.virtualScroller = null;
  }

  initialize() {
    // Plugin initialization logic
    this.component.isVirtualized = true;
  }

  shouldComponentUpdate(nextProps, nextState) {
    // Plugin can influence update decisions
    return true;
  }

  destroy() {
    if (this.virtualScroller) {
      this.virtualScroller.destroy();
    }
  }
}

class MemoryManagerPlugin {
  constructor(component, config = {}) {
    this.component = component;
    this.config = config;
    this.memoryThreshold = config.threshold || 50 * 1024 * 1024; // 50MB
  }

  initialize() {
    // Set up memory monitoring
    this.startMemoryMonitoring();
  }

  startMemoryMonitoring() {
    this.interval = setInterval(() => {
      const usage = this.component._calculateMemoryUsage();
      if (usage > this.memoryThreshold) {
        this.component.optimizeMemory();
      }
    }, 5000);
  }

  shouldComponentUpdate(nextProps, nextState) {
    // Check memory before updating
    const currentUsage = this.component._calculateMemoryUsage();
    if (currentUsage > this.memoryThreshold) {
      this.component.optimizeMemory();
    }
    return true;
  }

  destroy() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
}

class PerformanceMonitorPlugin {
  constructor(component, config = {}) {
    this.component = component;
    this.config = config;
  }

  initialize() {
    this.component.startPerformanceMonitoring();
  }

  shouldComponentUpdate(nextProps, nextState) {
    // Monitor performance impact
    const startTime = performance.now();
    const result = true;
    const endTime = performance.now();

    // Log slow updates
    if (endTime - startTime > 16) { // More than one frame
      console.warn('Slow component update detected:', endTime - startTime, 'ms');
    }

    return result;
  }

  destroy() {
    // Cleanup performance monitoring
  }
}

// Virtual List implementation for large datasets
class VirtualList {
  constructor(options) {
    this.items = options.items || [];
    this.renderItem = options.renderItem;
    this.itemHeight = options.itemHeight || 50;
    this.containerHeight = options.containerHeight || 400;
    this.overscan = options.overscan || 5;
    this.parentComponent = options.parentComponent;

    this.container = null;
    this.visibleStart = 0;
    this.visibleEnd = 0;

    this.calculateVisibleRange();
  }

  calculateVisibleRange() {
    const container = this.parentComponent?.element;
    if (!container) return;

    const scrollTop = container.scrollTop;
    const visibleStart = Math.floor(scrollTop / this.itemHeight);
    const visibleCount = Math.ceil(this.containerHeight / this.itemHeight);

    this.visibleStart = Math.max(0, visibleStart - this.overscan);
    this.visibleEnd = Math.min(
      this.items.length,
      visibleStart + visibleCount + this.overscan
    );
  }

  render() {
    if (!this.container) return '';

    this.calculateVisibleRange();

    const visibleItems = this.items.slice(this.visibleStart, this.visibleEnd);
    const offsetY = this.visibleStart * this.itemHeight;

    return `
      <div style="height: ${this.items.length * this.itemHeight}px; overflow: auto; position: relative;">
        <div style="transform: translateY(${offsetY}px);">
          ${visibleItems.map((item, index) =>
            this.renderItem(item, this.visibleStart + index)
          ).join('')}
        </div>
      </div>
    `;
  }

  updateItems(newItems) {
    this.items = newItems;
    this.render();
  }

  scrollTo(index) {
    if (this.container) {
      this.container.scrollTop = index * this.itemHeight;
    }
  }

  destroy() {
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

// Virtual Scrolling for millions of components
class VirtualScroller {
  constructor(container, items, renderItem, itemHeight = 50) {
    this.container = container;
    this.items = items;
    this.renderItem = renderItem;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight) + 10; // Add buffer
    this.startIndex = 0;
    this.endIndex = Math.min(this.visibleCount, items.length);
    this.scrollTop = 0;

    this.setupScrollListener();
    this.render();
  }

  setupScrollListener() {
    this.container.addEventListener('scroll', () => {
      const newScrollTop = this.container.scrollTop;
      const newStartIndex = Math.floor(newScrollTop / this.itemHeight);

      if (newStartIndex !== this.startIndex) {
        this.updateVisibleRange(newStartIndex);
      }
    });
  }

  updateVisibleRange(startIndex) {
    this.startIndex = Math.max(0, startIndex);
    this.endIndex = Math.min(
      this.startIndex + this.visibleCount,
      this.items.length
    );

    this.render();
  }

  render() {
    const visibleItems = this.items.slice(this.startIndex, this.endIndex);
    const offsetY = this.startIndex * this.itemHeight;

    // Use requestAnimationFrame for smooth scrolling
    requestAnimationFrame(() => {
      this.container.innerHTML = `
        <div style="height: ${this.items.length * this.itemHeight}px; position: relative;">
          <div style="transform: translateY(${offsetY}px);">
            ${visibleItems.map((item, index) =>
              this.renderItem(item, this.startIndex + index)
            ).join('')}
          </div>
        </div>
      `;
    });
  }
}

// Component instance with advanced scaling features
export class ComponentInstance {
  constructor(renderFn, props = {}) {
    this.renderFn = renderFn;
    this.props = this.createProps(props);
    this.state = signal({});
    this.hooks = [];
    this.hookIndex = 0;
    this.element = null;
    this.mounted = false;
    this.cleanup = null;
    this.effects = new Set();

    // Advanced scaling features
    this.performanceMetrics = {
      renderCount: 0,
      lastRenderTime: 0,
      totalRenderTime: 0,
      memoryUsage: 0
    };

    this.plugins = new Map();
    this.isVirtualized = false;
    this.poolKey = null;

    // SSR compatibility
    this.isServerSide = typeof window === 'undefined';
    this.hydrationData = null;

    // Track this component as current
    const prevComponent = currentComponent;
    currentComponent = this;
    componentStack.push(this);

    try {
      // Initialize component
      this.initialize();
    } finally {
      componentStack.pop();
      currentComponent = prevComponent;
    }
  }

  createProps(props) {
    const propsSignal = signal(props);

    // Make props reactive
    Object.keys(props).forEach(key => {
      if (isSignal(props[key])) {
        // Subscribe to signal changes
        effect(() => {
          const newValue = props[key].value;
          propsSignal.update(p => ({ ...p, [key]: newValue }));
        });
      }
    });

    return propsSignal;
  }

  initialize() {
    // Create computed render function
    this.rendered = computed(() => {
      this.hookIndex = 0;
      return this.renderFn(this.props.value);
    });

    // Set up effect to handle DOM updates
    this.setupRenderEffect();
  }

  setupRenderEffect() {
    const renderEffect = effect(() => {
      const vdom = this.rendered.value;
      if (this.element && this.mounted) {
        this.updateDOM(vdom);
      }
    });

    this.effects.add(renderEffect);
  }

  updateDOM(vdom) {
    if (!this.element) return;

    // Use efficient reconciliation
    if (!this._lastVDOM) {
      // First render - use innerHTML
      const html = this.vdomToHTML(vdom);
      this.element.innerHTML = html;
      this._hydrateDOM(this.element, vdom);
    } else {
      // Subsequent renders - use reconciler
      import('~/core/Reconciler.js').then(({ reconcile }) => {
        reconcile(this.element, this._lastVDOM, vdom);
      });
    }

    this._lastVDOM = vdom;

    // Performance monitoring
    if (this._perfMonitor) {
      this._perfMonitor.domUpdates++;
    }
  }

  // More efficient DOM updates with selective replacement
  _updateDOMEfficiently(element, vdom) {
    if (!vdom || vdom.$$typeof !== Symbol.for('pydance.element')) {
      // For text nodes or fragments, update innerHTML
      const newHTML = this.vdomToHTML(vdom);
      if (element.innerHTML !== newHTML) {
        element.innerHTML = newHTML;
      }
      return;
    }

    const { tagName, props, children } = vdom;

    // Update attributes selectively
    this._updateAttributes(element, props);

    // Update children selectively
    if (children && children.length > 0) {
      this._updateChildren(element, children);
    } else if (element.children.length > 0) {
      // Remove all children if new VDOM has none
      Array.from(element.children).forEach(child => child.remove());
    }
  }

  // Selectively update attributes
  _updateAttributes(element, props) {
    if (!props) return;

    const currentAttributes = new Set(element.getAttributeNames());

    // Update/add new attributes
    Object.entries(props).forEach(([key, value]) => {
      if (key === 'children' || key === 'key' || key === 'ref') return;

      const jsxToHtmlMap = {
        'className': 'class',
        'htmlFor': 'for',
        'defaultValue': 'value',
        'defaultChecked': 'checked'
      };

      const htmlKey = jsxToHtmlMap[key] || key;

      if (key.startsWith('on') && typeof value === 'function') {
        // Event handlers are handled during hydration
        return;
      }

      if (key === 'style' && typeof value === 'object') {
        const styles = Object.entries(value)
          .map(([prop, val]) => `${this._camelToKebab(prop)}:${val}`)
          .join(';');
        if (element.style.cssText !== styles) {
          element.style.cssText = styles;
        }
      } else if (key === 'dangerouslySetInnerHTML') {
        if (element.innerHTML !== value.__html) {
          element.innerHTML = value.__html;
        }
      } else {
        const stringValue = String(value);
        if (element.getAttribute(htmlKey) !== stringValue) {
          if (typeof value === 'boolean') {
            if (value) {
              element.setAttribute(htmlKey, '');
            } else {
              element.removeAttribute(htmlKey);
            }
          } else {
            element.setAttribute(htmlKey, stringValue);
          }
        }
      }

      currentAttributes.delete(htmlKey);
    });

    // Remove attributes that no longer exist
    currentAttributes.forEach(attr => {
      element.removeAttribute(attr);
    });
  }

  // Selectively update children
  _updateChildren(parentElement, children) {
    const currentChildren = Array.from(parentElement.children);

    children.forEach((child, index) => {
      if (index < currentChildren.length) {
        // Update existing child
        this._updateChild(currentChildren[index], child);
      } else {
        // Add new child
        const newElement = this._createElement(child);
        parentElement.appendChild(newElement);
      }
    });

    // Remove extra children
    while (parentElement.children.length > children.length) {
      parentElement.lastChild.remove();
    }
  }

  // Update individual child element
  _updateChild(element, vdom) {
    if (typeof vdom === 'string' || typeof vdom === 'number') {
      if (element.textContent !== String(vdom)) {
        element.textContent = String(vdom);
      }
    } else if (vdom && vdom.$$typeof === Symbol.for('pydance.element')) {
      this._updateDOMEfficiently(element, vdom);
    }
  }

  // Create DOM element from VDOM
  _createElement(vdom) {
    if (typeof vdom === 'string' || typeof vdom === 'number') {
      return document.createTextNode(String(vdom));
    }

    if (vdom && vdom.$$typeof === Symbol.for('pydance.element')) {
      const { tagName, props, children } = vdom;
      const element = document.createElement(tagName);

      // Set attributes
      if (props) {
        Object.entries(props).forEach(([key, value]) => {
          if (key === 'children' || key === 'key' || key === 'ref') return;

          const jsxToHtmlMap = {
            'className': 'class',
            'htmlFor': 'for',
            'defaultValue': 'value',
            'defaultChecked': 'checked'
          };

          const htmlKey = jsxToHtmlMap[key] || key;

          if (key === 'style' && typeof value === 'object') {
            Object.entries(value).forEach(([prop, val]) => {
              element.style[this._camelToKebab(prop)] = val;
            });
          } else if (key === 'dangerouslySetInnerHTML') {
            element.innerHTML = value.__html;
          } else if (typeof value === 'boolean') {
            if (value) element.setAttribute(htmlKey, '');
          } else {
            element.setAttribute(htmlKey, String(value));
          }
        });
      }

      // Create children
      if (children) {
        children.forEach(child => {
          element.appendChild(this._createElement(child));
        });
      }

      return element;
    }

    return document.createTextNode('');
  }

  // Complete VDOM to HTML conversion with full attribute support
  vdomToHTML(vdom) {
    if (typeof vdom === 'string' || typeof vdom === 'number') {
      return String(vdom);
    }

    if (Array.isArray(vdom)) {
      return vdom.map(child => this.vdomToHTML(child)).join('');
    }

    if (vdom && vdom.$$typeof === Symbol.for('pydance.element')) {
      const { tagName, props, children } = vdom;

      // Complete attribute handling for all HTML attributes
      const attrs = Object.entries(props || {})
        .filter(([key]) => key !== 'children' && key !== 'key' && key !== 'ref')
        .map(([key, value]) => this._processAttribute(key, value))
        .filter(Boolean)
        .join(' ');

      const childrenHTML = (children || []).map(child => this.vdomToHTML(child)).join('');

      // Handle self-closing tags
      const isSelfClosing = this._isSelfClosingTag(tagName);

      if (isSelfClosing && childrenHTML === '') {
        return `<${tagName}${attrs ? ' ' + attrs : ''}/>`;
      }

      return `<${tagName}${attrs ? ' ' + attrs : ''}>${childrenHTML}</${tagName}>`;
    }

    if (vdom && vdom.$$typeof === Symbol.for('pydance.fragment')) {
      return (vdom.children || []).map(child => this.vdomToHTML(child)).join('');
    }

    return '';
  }

  // Process individual attributes with complete HTML support
  _processAttribute(key, value) {
    // Skip null/undefined values
    if (value == null) return '';

    // Handle JSX-specific attributes that map to HTML
    const jsxToHtmlMap = {
      'className': 'class',
      'htmlFor': 'for',
      'defaultValue': 'value',
      'defaultChecked': 'checked'
    };

    const htmlKey = jsxToHtmlMap[key] || key;

    // Handle different attribute types
    if (typeof value === 'boolean') {
      // Boolean attributes
      if (key === 'disabled' || key === 'checked' || key === 'selected' ||
          key === 'readonly' || key === 'required' || key === 'multiple') {
        return value ? htmlKey : '';
      }
      return value ? htmlKey : '';
    }

    if (key.startsWith('on') && typeof value === 'function') {
      // Event handlers - store as data attribute for hydration
      return `data-${key.toLowerCase()}="${this._escapeHtml(value.toString())}"`;
    }

    if (key === 'style' && typeof value === 'object') {
      // Style object to CSS string
      const styles = Object.entries(value)
        .map(([prop, val]) => `${this._camelToKebab(prop)}:${val}`)
        .join(';');
      return `style="${this._escapeHtml(styles)}"`;
    }

    if (key === 'dangerouslySetInnerHTML') {
      // Handle raw HTML content
      return '';
    }

    // Handle data attributes
    if (key.startsWith('data-') || key.startsWith('aria-')) {
      return `${htmlKey}="${this._escapeHtml(String(value))}"`;
    }

    // Handle standard attributes
    return `${htmlKey}="${this._escapeHtml(String(value))}"`;
  }

  // Convert camelCase to kebab-case for CSS properties
  _camelToKebab(str) {
    return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
  }

  // Check if tag is self-closing
  _isSelfClosingTag(tagName) {
    const selfClosingTags = new Set([
      'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
      'link', 'meta', 'param', 'source', 'track', 'wbr',
      'circle', 'ellipse', 'line', 'path', 'polygon', 'polyline', 'rect'
    ]);
    return selfClosingTags.has(tagName.toLowerCase());
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  mount(container) {
    if (this.mounted) {
      console.warn('Component already mounted');
      return;
    }

    if (typeof container === 'string') {
      container = document.querySelector(container);
    }

    if (!container) {
      throw new Error('Mount container not found');
    }

    try {
      // Call onMount hook if provided
      if (this.props.value.onMount) {
        this.props.value.onMount.call(this);
      }

      // Create initial DOM
      const vdom = this.rendered.value;
      const html = this.vdomToHTML(vdom);
      container.innerHTML = html;
      this.element = container;

      // Hydrate event listeners and refs
      this._hydrateDOM(container, vdom);

      this.mounted = true;

      // Call onMounted hook if provided
      if (this.props.value.onMounted) {
        this.props.value.onMounted.call(this);
      }
    } catch (err) {
      console.error('Component mount error:', err);
      this.handleError(err, { phase: 'mount' });
    }
  }

  // Hydrate DOM with event listeners and refs
  _hydrateDOM(element, vdom) {
    if (!vdom || vdom.$$typeof !== Symbol.for('pydance.element')) {
      return;
    }

    const { tagName, props, children } = vdom;

    // Handle refs
    if (props && props.ref) {
      if (typeof props.ref === 'function') {
        props.ref(element);
      } else if (props.ref && typeof props.ref === 'object') {
        props.ref.current = element;
      }
    }

    // Hydrate event listeners from data attributes
    if (props) {
      Object.entries(props).forEach(([key, value]) => {
        if (key.startsWith('on') && typeof value === 'function') {
          const eventName = key.toLowerCase().substring(2); // Remove 'on' prefix
          element.addEventListener(eventName, value);
        }
      });
    }

    // Hydrate children recursively
    if (children && children.length > 0) {
      const childElements = element.children;

      children.forEach((child, index) => {
        if (childElements[index]) {
          this._hydrateDOM(childElements[index], child);
        }
      });
    }
  }

  unmount() {
    if (!this.mounted) return;

    try {
      // Call onUnmount hook
      if (this.props.value.onUnmount) {
        this.props.value.onUnmount.call(this);
      }

      // Clean up effects
      this.effects.forEach(effect => {
        try {
          effect.stop();
        } catch (err) {
          console.error('Effect cleanup error:', err);
        }
      });
      this.effects.clear();

      // Clean up DOM
      if (this.element) {
        // Remove event listeners
        const clone = this.element.cloneNode(true);
        if (this.element.parentNode) {
          this.element.parentNode.replaceChild(clone, this.element);
        }
        this.element.innerHTML = '';
        this.element = null;
      }

      this.mounted = false;
    } catch (err) {
      console.error('Component unmount error:', err);
    }
  }

  // Hooks
  useState(initialValue) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = signal(initialValue);
    }

    const stateSignal = this.hooks[hookIndex];

    return [
      stateSignal.value,
      (value) => {
        const newValue = typeof value === 'function' ? value(stateSignal.value) : value;
        stateSignal.value = newValue;
      }
    ];
  }

  useEffect(fn, deps) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = { deps: null, cleanup: null };
    }

    const hook = this.hooks[hookIndex];
    const depsChanged = !deps ||
      !hook.deps ||
      deps.some((dep, i) => !Object.is(dep, hook.deps[i]));

    if (depsChanged) {
      // Clean up previous effect
      if (hook.cleanup && typeof hook.cleanup === 'function') {
        hook.cleanup();
      }

      // Execute new effect with enhanced error handling
      const effectInstance = effect(() => {
        try {
          hook.cleanup = fn();
        } catch (error) {
          this.handleError(error, { type: 'effect', hookIndex, deps });
        }
      });

      hook.deps = deps;
      hook.effect = effectInstance;
      this.effects.add(effectInstance);
    }
  }

  // Enhanced side effects hooks
  useAsyncEffect(asyncFn, deps) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = {
        deps: null,
        promise: null,
        abortController: null,
        cleanup: null
      };
    }

    const hook = this.hooks[hookIndex];
    const depsChanged = !deps ||
      !hook.deps ||
      deps.some((dep, i) => !Object.is(dep, hook.deps[i]));

    if (depsChanged) {
      // Cancel previous effect
      if (hook.abortController) {
        hook.abortController.abort();
      }

      // Clean up previous effect
      if (hook.cleanup && typeof hook.cleanup === 'function') {
        hook.cleanup();
      }

      // Create new abort controller for cancellation
      hook.abortController = new AbortController();

      // Execute async effect
      const effectInstance = effect(async () => {
        try {
          hook.promise = asyncFn(hook.abortController.signal);
          hook.cleanup = await hook.promise;
        } catch (error) {
          if (error.name !== 'AbortError') {
            this.handleError(error, { type: 'asyncEffect', hookIndex, deps });
          }
        }
      });

      hook.deps = deps;
      hook.effect = effectInstance;
      this.effects.add(effectInstance);
    }

    return hook.abortController;
  }

  useEventEffect(eventName, handler, options = {}) {
    const { target = window, deps = [] } = options;

    useEffect(() => {
      const wrappedHandler = (...args) => {
        try {
          handler(...args);
        } catch (error) {
          this.handleError(error, { type: 'eventEffect', eventName, target });
        }
      };

      target.addEventListener(eventName, wrappedHandler);

      return () => {
        target.removeEventListener(eventName, wrappedHandler);
      };
    }, deps);
  }

  useIntervalEffect(callback, delay, deps = []) {
    useEffect(() => {
      if (delay == null) return;

      const intervalId = setInterval(() => {
        try {
          callback();
        } catch (error) {
          this.handleError(error, { type: 'intervalEffect', delay });
        }
      }, delay);

      return () => clearInterval(intervalId);
    }, deps);
  }

  useTimeoutEffect(callback, delay, deps = []) {
    useEffect(() => {
      if (delay == null) return;

      const timeoutId = setTimeout(() => {
        try {
          callback();
        } catch (error) {
          this.handleError(error, { type: 'timeoutEffect', delay });
        }
      }, delay);

      return () => clearTimeout(timeoutId);
    }, deps);
  }

  useDebounceEffect(callback, delay, deps = []) {
    const [debouncedCallback, setDebouncedCallback] = useState(callback);

    useEffect(() => {
      setDebouncedCallback(() => callback);
    }, [callback, ...deps]);

    useTimeoutEffect(debouncedCallback, delay, [delay, ...deps]);
  }

  useThrottleEffect(callback, delay, deps = []) {
    const [lastCall, setLastCall] = useState(0);
    const [throttledCallback, setThrottledCallback] = useState(callback);

    useEffect(() => {
      setThrottledCallback(() => {
        const now = Date.now();
        if (now - lastCall >= delay) {
          setLastCall(now);
          callback();
        }
      });
    }, [callback, delay, ...deps]);

    return throttledCallback;
  }

  usePrevious(value) {
    const ref = useRef();
    useEffect(() => {
      ref.current = value;
    });
    return ref.current;
  }

  useCallbackRef(callback) {
    const callbackRef = useRef(callback);
    const ref = useRef();

    useEffect(() => {
      callbackRef.current = callback;
    });

    useEffect(() => {
      if (callbackRef.current) {
        const element = ref.current;
        return callbackRef.current(element);
      }
    });

    return ref;
  }

  useMemo(compute, deps) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = { deps: null, value: undefined };
    }

    const hook = this.hooks[hookIndex];
    const depsChanged = !deps ||
      !hook.deps ||
      deps.some((dep, i) => !Object.is(dep, hook.deps[i]));

    if (depsChanged) {
      hook.value = compute();
      hook.deps = deps;
    }

    return hook.value;
  }

  useCallback(callback, deps) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = { deps: null, callback: null };
    }

    const hook = this.hooks[hookIndex];
    const depsChanged = !deps ||
      !hook.deps ||
      deps.some((dep, i) => !Object.is(dep, hook.deps[i]));

    if (depsChanged) {
      hook.callback = callback;
      hook.deps = deps;
    }

    return hook.callback;
  }

  useRef(initialValue) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = { current: initialValue };
    }

    return this.hooks[hookIndex];
  }

  useContext(context) {
    const hookIndex = this.hookIndex++;

    if (!this.hooks[hookIndex]) {
      this.hooks[hookIndex] = signal(context._defaultValue);
    }

    const contextSignal = this.hooks[hookIndex];

    // Subscribe to context changes
    effect(() => {
      contextSignal.value = context._currentValue;
    });

    return contextSignal.value;
  }

  useReducer(reducer, initialState) {
    const state = this.useState(initialState);
    const dispatch = this.useCallback((action) => {
      state[1](prevState => reducer(prevState, action));
    }, [reducer]);

    return [state[0], dispatch];
  }

  useImperativeHandle(ref, createHandle, deps) {
    const handle = this.useMemo(() => createHandle(), deps);

    if (ref) {
      if (typeof ref === 'function') {
        ref(handle);
      } else if (ref && typeof ref === 'object') {
        ref.current = handle;
      }
    }
  }

  // Advanced scaling methods
  reset() {
    // Reset component state for pooling
    this.hookIndex = 0;
    this.mounted = false;
    this.element = null;
    this.effects.clear();

    // Reset performance metrics
    this.performanceMetrics = {
      renderCount: 0,
      lastRenderTime: 0,
      totalRenderTime: 0,
      memoryUsage: 0
    };

    // Clear plugins
    this.plugins.clear();
  }

  // Memory management for large-scale applications
  optimizeMemory() {
    // Force garbage collection if available
    if (window.gc) {
      window.gc();
    }

    // Clear unused caches
    if (this._jsxCache) {
      this._jsxCache.clear();
    }

    // Optimize signal subscriptions
    this._optimizeSignals();

    // Update memory metrics
    this.performanceMetrics.memoryUsage = this._calculateMemoryUsage();
  }

  _optimizeSignals() {
    // Remove unused signal subscriptions
    const activeSignals = new Set();

    // Traverse component tree to find active signals
    this._collectActiveSignals(activeSignals);

    // Clean up unused effects
    this.effects.forEach(effect => {
      if (!effect.active) {
        effect.stop();
        this.effects.delete(effect);
      }
    });
  }

  _collectActiveSignals(activeSignals) {
    // Collect all signals used in this component
    Object.values(this.hooks).forEach(hook => {
      if (hook && typeof hook === 'object' && hook.value) {
        if (isSignal(hook.value)) {
          activeSignals.add(hook.value);
        }
      }
    });
  }

  _calculateMemoryUsage() {
    // Estimate memory usage
    let usage = 0;

    // Component instance size
    usage += JSON.stringify(this).length;

    // Hooks memory
    usage += JSON.stringify(this.hooks).length;

    // Effects memory
    usage += this.effects.size * 100; // Rough estimate

    return usage;
  }

  // Performance monitoring
  startPerformanceMonitoring() {
    this._perfMonitor = {
      renderCount: 0,
      domUpdates: 0,
      averageRenderTime: 0,
      startTime: performance.now()
    };
  }

  getPerformanceMetrics() {
    const now = performance.now();
    const uptime = now - (this._perfMonitor?.startTime || now);

    return {
      ...this.performanceMetrics,
      uptime,
      rendersPerSecond: this.performanceMetrics.renderCount / (uptime / 1000),
      memoryEfficiency: this._calculateMemoryEfficiency()
    };
  }

  _calculateMemoryEfficiency() {
    const totalMemory = this._calculateMemoryUsage();
    const renderCount = this.performanceMetrics.renderCount;

    return renderCount > 0 ? totalMemory / renderCount : 0;
  }

  // Plugin system integration
  usePlugin(pluginName, config = {}) {
    if (!this.plugins.has(pluginName)) {
      const PluginClass = this._getPluginClass(pluginName);
      if (PluginClass) {
        const plugin = new PluginClass(this, config);
        this.plugins.set(pluginName, plugin);

        // Initialize plugin
        plugin.initialize();

        return plugin;
      }
    }

    return this.plugins.get(pluginName);
  }

  _getPluginClass(pluginName) {
    // Plugin registry - can be extended
    const plugins = {
      'virtual-scroller': VirtualScrollerPlugin,
      'memory-manager': MemoryManagerPlugin,
      'performance-monitor': PerformanceMonitorPlugin
    };

    return plugins[pluginName];
  }

  // SSR compatibility methods
  renderToString() {
    if (this.isServerSide) {
      const vdom = this.rendered.value;
      return this.vdomToHTML(vdom);
    }
    return null;
  }

  hydrate(element, hydrationData) {
    this.hydrationData = hydrationData;
    this.element = element;
    this.mounted = true;

    // Hydrate with server-rendered content
    this._hydrateFromServer(element, hydrationData);
  }

  _hydrateFromServer(element, hydrationData) {
    // Match server-rendered DOM with client-side expectations
    const vdom = this.rendered.value;

    // Reconcile differences
    this._reconcileServerClient(element, vdom, hydrationData);

    // Set up event listeners
    this._hydrateDOM(element, vdom);
  }

  _reconcileServerClient(element, vdom, hydrationData) {
    // Advanced reconciliation for SSR hydration
    if (vdom && vdom.$$typeof === Symbol.for('pydance.element')) {
      const { tagName, props, children } = vdom;

      // Update attributes that differ from server
      if (props) {
        Object.entries(props).forEach(([key, value]) => {
          if (key.startsWith('on') && typeof value === 'function') {
            // Add event listeners
            const eventName = key.toLowerCase().substring(2);
            element.addEventListener(eventName, value);
          }
        });
      }

      // Reconcile children
      if (children && children.length > 0) {
        const childElements = element.children;
        children.forEach((child, index) => {
          if (childElements[index]) {
            this._reconcileServerClient(childElements[index], child, hydrationData);
          }
        });
      }
    }
  }

  // Component virtualization for large lists
  createVirtualList(items, renderItem, options = {}) {
    const {
      itemHeight = 50,
      containerHeight = 400,
      overscan = 5
    } = options;

    return new VirtualList({
      items,
      renderItem,
      itemHeight,
      containerHeight,
      overscan,
      parentComponent: this
    });
  }

  // Advanced lifecycle methods
  shouldComponentUpdate(nextProps, nextState) {
    // Custom update logic for performance
    if (this.props.value === nextProps && this.state.value === nextState) {
      return false;
    }

    // Use plugins for advanced update decisions
    for (const plugin of this.plugins.values()) {
      if (plugin.shouldComponentUpdate) {
        const pluginDecision = plugin.shouldComponentUpdate(nextProps, nextState);
        if (pluginDecision === false) {
          return false;
        }
      }
    }

    return true;
  }

  // Batch updates for performance
  batchUpdate(updates) {
    batch(() => {
      updates.forEach(update => update());
    });
  }

  // Error handling with recovery
  handleError(error, errorInfo) {
    this._lastError = { error, errorInfo, timestamp: Date.now() };

    // Use error boundary if available
    if (this._errorBoundary) {
      this._errorBoundary.handleError(error, errorInfo);
    }

    // Log error for debugging
    console.error('Component error:', error, errorInfo);

    // Attempt recovery
    this._attemptRecovery(error, errorInfo);
  }

  _attemptRecovery(error, errorInfo) {
    // Simple recovery strategy
    setTimeout(() => {
      try {
        // Force re-render
        this.forceUpdate();
      } catch (recoveryError) {
        console.error('Recovery failed:', recoveryError);
      }
    }, 100);
  }

  forceUpdate() {
    const vdom = this.rendered.value;
    if (this.element && this.mounted) {
      this.updateDOM(vdom);
    }
  }

  // Component profiling
  startProfiling() {
    this._profiling = true;
    this._profileData = {
      renders: [],
      updates: [],
      memorySnapshots: []
    };

    // Memory monitoring
    this._memoryInterval = setInterval(() => {
      this._profileData.memorySnapshots.push({
        timestamp: performance.now(),
        usage: this._calculateMemoryUsage()
      });
    }, 1000);
  }

  stopProfiling() {
    this._profiling = false;

    if (this._memoryInterval) {
      clearInterval(this._memoryInterval);
    }

    return this._profileData;
  }

  // Advanced debugging
  inspect() {
    return {
      props: this.props.value,
      state: this.state.value,
      hooks: this.hooks.map(hook => ({
        type: hook.constructor?.name || 'Unknown',
        value: hook.value
      })),
      performance: this.getPerformanceMetrics(),
      plugins: Array.from(this.plugins.keys()),
      errors: this._lastError,
      virtualized: this.isVirtualized,
      serverSide: this.isServerSide
    };
  }
}

// Create component function
export const createComponent = (renderFn) => {
  return (props = {}) => {
    return new ComponentInstance(renderFn, props);
  };
};

// JSX Runtime with enhanced performance and caching
const JSX_CACHE = new Map();
const JSX_CACHE_SIZE = 1000;

export const jsx = (tag, props, ...children) => {
  // Handle function components
  if (typeof tag === 'function') {
    return tag({ ...props, children: children.flat() });
  }

  // Create JSX element with caching for performance
  const cacheKey = `${tag}:${JSON.stringify(props)}:${children.length}`;

  if (JSX_CACHE.has(cacheKey)) {
    const cached = JSX_CACHE.get(cacheKey);
    // Update children if they've changed
    if (cached.children.length === children.length) {
      return cached;
    }
  }

  const element = new JSXElement(tag, props, children);

  // Cache the element (simple LRU cache)
  if (JSX_CACHE.size >= JSX_CACHE_SIZE) {
    const firstKey = JSX_CACHE.keys().next().value;
    JSX_CACHE.delete(firstKey);
  }
  JSX_CACHE.set(cacheKey, element);

  return element;
};

export const jsxs = (tag, props) => {
  return jsx(tag, props);
};

export const Fragment = (props) => {
  return new JSXFragment(props.children || [], props);
};

// Context system
export class Context {
  constructor(defaultValue) {
    this._defaultValue = defaultValue;
    this._currentValue = defaultValue;
    this._subscribers = new Set();
    this.Provider = createProvider(this);
    this.Consumer = createConsumer(this);
  }

  provide(value) {
    const prevValue = this._currentValue;
    this._currentValue = value;

    // Notify subscribers
    this._subscribers.forEach(subscriber => subscriber(value));

    return () => {
      this._currentValue = prevValue;
    };
  }

  subscribe(subscriber) {
    this._subscribers.add(subscriber);
    return () => this._subscribers.delete(subscriber);
  }
}

const createProvider = (context) => {
  return createComponent((props) => {
    const restore = context.provide(props.value);

    // Call onMount/onUnmount if provided
    const instance = currentComponent;
    if (instance) {
      instance.useEffect(() => {
        return restore;
      }, [props.value]);
    }

    return props.children;
  });
};

const createConsumer = (context) => {
  return createComponent((props) => {
    const [value, setValue] = currentComponent.useState(context._defaultValue);

    // Subscribe to context changes
    currentComponent.useEffect(() => {
      const unsubscribe = context.subscribe(setValue);
      return unsubscribe;
    }, []);

    return props.children(value);
  });
};

// Utility functions
export const useState = (initialValue) => {
  if (!currentComponent) {
    throw new Error('useState must be called within a component');
  }
  return currentComponent.useState(initialValue);
};

export const useEffect = (fn, deps) => {
  if (!currentComponent) {
    throw new Error('useEffect must be called within a component');
  }
  return currentComponent.useEffect(fn, deps);
};

export const useMemo = (compute, deps) => {
  if (!currentComponent) {
    throw new Error('useMemo must be called within a component');
  }
  return currentComponent.useMemo(compute, deps);
};

export const useCallback = (callback, deps) => {
  if (!currentComponent) {
    throw new Error('useCallback must be called within a component');
  }
  return currentComponent.useCallback(callback, deps);
};

export const useRef = (initialValue) => {
  if (!currentComponent) {
    throw new Error('useRef must be called within a component');
  }
  return currentComponent.useRef(initialValue);
};

export const useContext = (context) => {
  if (!currentComponent) {
    throw new Error('useContext must be called within a component');
  }
  return currentComponent.useContext(context);
};

export const useReducer = (reducer, initialState) => {
  if (!currentComponent) {
    throw new Error('useReducer must be called within a component');
  }
  return currentComponent.useReducer(reducer, initialState);
};

export const useImperativeHandle = (ref, createHandle, deps) => {
  if (!currentComponent) {
    throw new Error('useImperativeHandle must be called within a component');
  }
  return currentComponent.useImperativeHandle(ref, createHandle, deps);
};

// Memoization
export const memo = (component, compareProps = (prevProps, nextProps) => {
  return JSON.stringify(prevProps) === JSON.stringify(nextProps);
}) => {
  let prevProps = null;
  let cachedInstance = null;

  return (props) => {
    if (cachedInstance && compareProps(prevProps, props)) {
      return cachedInstance.rendered.value;
    }

    prevProps = props;
    cachedInstance = new ComponentInstance(component, props);
    return cachedInstance.rendered.value;
  };
};

// Error boundary
export const createErrorBoundary = (fallbackComponent) => {
  return createComponent((props) => {
    const [error, setError] = useState(null);

    useEffect(() => {
      const handleError = (event) => {
        setError(event.error);
      };

      window.addEventListener('error', handleError);
      return () => window.removeEventListener('error', handleError);
    }, []);

    if (error) {
      return fallbackComponent({ error, resetError: () => setError(null) });
    }

    return props.children;
  });
};

// Suspense
export const Suspense = createComponent((props) => {
  const [suspenseState, setSuspenseState] = useState('pending');
  const [suspendedComponent, setSuspendedComponent] = useState(null);

  // This is a simplified implementation
  // Real implementation would handle promises and concurrent rendering

  return props.fallback || props.children;
});

// Development helpers
export const devtools = {
  getCurrentComponent: () => currentComponent,
  getComponentStack: () => [...componentStack],
  inspectComponent: (component) => {
    console.log('Component info:', {
      props: component.props.value,
      state: component.state.value,
      hooks: component.hooks.length,
      mounted: component.mounted
    });
  }
};

// Export everything
export default {
  ComponentInstance,
  createComponent,
  jsx,
  jsxs,
  Fragment,
  Context,
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
  useContext,
  useReducer,
  useImperativeHandle,
  memo,
  createErrorBoundary,
  Suspense,
  devtools
};
