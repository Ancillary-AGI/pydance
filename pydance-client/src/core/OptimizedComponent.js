/**
 * Optimized Component with memoization and lazy rendering
 * Extends existing Component functionality without removing features
 */

import { ComponentInstance, createComponent } from './Component.js';
import { optimizedSignal, memoizedComputed } from './OptimizedSignal.js';

/**
 * Memoize component to prevent unnecessary re-renders
 * Preserves all Component functionality
 */
export function memoComponent(renderFn, arePropsEqual = null) {
  const memoCache = new Map();
  
  return (props = {}) => {
    // Generate cache key
    const cacheKey = arePropsEqual 
      ? JSON.stringify(props)
      : Object.entries(props)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([k, v]) => `${k}:${v}`)
          .join('|');
    
    // Check cache
    if (memoCache.has(cacheKey)) {
      const cached = memoCache.get(cacheKey);
      
      // Check if props actually changed
      if (arePropsEqual) {
        if (arePropsEqual(cached.props, props)) {
          return cached.instance;
        }
      }
    }
    
    // Create new instance
    const instance = new ComponentInstance(renderFn, props);
    
    // Cache with LRU eviction
    if (memoCache.size > 100) {
      const firstKey = memoCache.keys().next().value;
      memoCache.delete(firstKey);
    }
    
    memoCache.set(cacheKey, { props, instance });
    
    return instance;
  };
}

/**
 * Lazy component that loads on demand
 * Preserves all Component functionality
 */
export function lazyComponent(loader) {
  let loadedComponent = null;
  let loadPromise = null;
  
  return (props = {}) => {
    // Return loading placeholder
    if (!loadedComponent) {
      if (!loadPromise) {
        loadPromise = loader().then(module => {
          loadedComponent = module.default || module;
        });
      }
      
      // Return loading component
      return createComponent(() => ({
        $$typeof: Symbol.for('pydance.element'),
        tagName: 'div',
        props: { className: 'loading' },
        children: ['Loading...']
      }))(props);
    }
    
    // Return loaded component
    return loadedComponent(props);
  };
}

/**
 * Optimized ComponentInstance with performance enhancements
 * Extends base ComponentInstance
 */
export class OptimizedComponentInstance extends ComponentInstance {
  constructor(renderFn, props = {}) {
    super(renderFn, props);
    
    // Add performance tracking
    this.renderCount = 0;
    this.lastRenderTime = 0;
    
    // Add render throttling
    this.renderThrottle = 16;  // ~60fps
    this.pendingRender = false;
  }
  
  updateDOM(vdom) {
    // Throttle renders to 60fps
    if (this.pendingRender) {
      return;
    }
    
    this.pendingRender = true;
    
    requestAnimationFrame(() => {
      const startTime = performance.now();
      
      // Call parent updateDOM
      super.updateDOM(vdom);
      
      // Track performance
      this.renderCount++;
      this.lastRenderTime = performance.now() - startTime;
      this.pendingRender = false;
    });
  }
  
  getPerformanceMetrics() {
    return {
      renderCount: this.renderCount,
      lastRenderTime: this.lastRenderTime,
      averageRenderTime: this.lastRenderTime / this.renderCount
    };
  }
}

/**
 * Create optimized component
 * Preserves all createComponent functionality
 */
export function createOptimizedComponent(renderFn, options = {}) {
  const { memo = false, lazy = false } = options;
  
  let component = (props = {}) => {
    return new OptimizedComponentInstance(renderFn, props);
  };
  
  // Apply memoization if requested
  if (memo) {
    component = memoComponent(renderFn);
  }
  
  // Apply lazy loading if requested
  if (lazy && typeof renderFn === 'function' && renderFn.length === 0) {
    component = lazyComponent(renderFn);
  }
  
  return component;
}

/**
 * Component registry for efficient lookup
 * Preserves all functionality
 */
export class ComponentRegistry {
  constructor() {
    this.components = new Map();
    this.aliases = new Map();
  }
  
  register(name, component) {
    this.components.set(name, component);
    
    // Create lowercase alias for case-insensitive lookup
    const lowerName = name.toLowerCase();
    this.aliases.set(lowerName, name);
  }
  
  get(name) {
    // Try direct lookup
    if (this.components.has(name)) {
      return this.components.get(name);
    }
    
    // Try alias
    const alias = this.aliases.get(name.toLowerCase());
    return alias ? this.components.get(alias) : null;
  }
  
  has(name) {
    return this.components.has(name) || 
           this.aliases.has(name.toLowerCase());
  }
  
  unregister(name) {
    this.components.delete(name);
    this.aliases.delete(name.toLowerCase());
  }
  
  clear() {
    this.components.clear();
    this.aliases.clear();
  }
  
  getAll() {
    return Array.from(this.components.entries());
  }
}

// Global registry
const globalRegistry = new ComponentRegistry();

export function registerComponent(name, component) {
  globalRegistry.register(name, component);
}

export function getComponent(name) {
  return globalRegistry.get(name);
}

// Re-export base functionality
export { ComponentInstance, createComponent } from './Component.js';
