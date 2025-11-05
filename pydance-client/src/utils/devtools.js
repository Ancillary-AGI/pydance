/**
 * @fileoverview Pydance Client Developer Tools
 * Advanced debugging and development utilities for Pydance Client
 *
 * @description
 * This module provides comprehensive developer tools for debugging,
 * performance monitoring, and development workflow enhancement.
 *
 * Features:
 * - Component tree inspection
 * - Signal debugging and tracing
 * - Performance profiling
 * - Memory leak detection
 * - Hot reload integration
 * - Development server integration
 *
 * @author Pydance Framework Team
 * @version 0.1.0
 * @license MIT
 */

import { signal, computed, effect, isSignal, unwrap } from '../core/Signal.js';
import { getLogger } from './logger.js';

// Development mode detection
const isDevelopment = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' ||
   window.location.hostname === '127.0.0.1' ||
   window.location.hostname === '0.0.0.0' ||
   process?.env?.NODE_ENV === 'development');

// Logger for devtools
const logger = getLogger('devtools');

// Component registry for inspection
const componentRegistry = new Map();
const componentTree = new Map();

// Signal registry for debugging
const signalRegistry = new Map();
const effectRegistry = new Map();

// Performance monitoring
const performanceMetrics = {
  renderTime: new Map(),
  updateTime: new Map(),
  memoryUsage: [],
  componentCount: 0,
  signalCount: 0,
  effectCount: 0
};

// Component Inspector
export class ComponentInspector {
  constructor() {
    this.selectedComponent = null;
    this.highlightedElement = null;
    this.overlay = null;
  }

  // Inspect component tree
  inspectComponentTree() {
    const tree = {
      root: null,
      components: {},
      hierarchy: {}
    };

    for (const [id, component] of componentRegistry) {
      tree.components[id] = {
        name: component.constructor.name,
        props: this._sanitizeProps(component.props),
        state: this._sanitizeState(component.state),
        signals: this._getComponentSignals(component),
        children: componentTree.get(id) || []
      };
    }

    // Build hierarchy
    for (const [id, component] of componentRegistry) {
      if (component.parent) {
        const parentId = this._getComponentId(component.parent);
        if (!tree.hierarchy[parentId]) {
          tree.hierarchy[parentId] = [];
        }
        tree.hierarchy[parentId].push(id);
      } else {
        tree.root = id;
      }
    }

    return tree;
  }

  // Highlight component in DOM
  highlightComponent(componentId) {
    this.clearHighlight();

    const component = componentRegistry.get(componentId);
    if (!component || !component.element) return;

    this.selectedComponent = component;
    this.highlightedElement = component.element;

    // Create highlight overlay
    this.overlay = document.createElement('div');
    this.overlay.style.cssText = `
      position: absolute;
      pointer-events: none;
      background: rgba(255, 0, 0, 0.1);
      border: 2px solid #ff0000;
      border-radius: 2px;
      z-index: 999999;
    `;

    const rect = component.element.getBoundingClientRect();
    this.overlay.style.top = rect.top + window.scrollY + 'px';
    this.overlay.style.left = rect.left + window.scrollX + 'px';
    this.overlay.style.width = rect.width + 'px';
    this.overlay.style.height = rect.height + 'px';

    document.body.appendChild(this.overlay);

    // Add component info tooltip
    this._showComponentInfo(component, rect);
  }

  clearHighlight() {
    if (this.overlay) {
      this.overlay.remove();
      this.overlay = null;
    }

    if (this.tooltip) {
      this.tooltip.remove();
      this.tooltip = null;
    }

    this.selectedComponent = null;
    this.highlightedElement = null;
  }

  _showComponentInfo(component, rect) {
    this.tooltip = document.createElement('div');
    this.tooltip.style.cssText = `
      position: absolute;
      background: #333;
      color: #fff;
      padding: 8px 12px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 12px;
      z-index: 1000000;
      max-width: 300px;
      word-wrap: break-word;
    `;

    const info = `
      <strong>${component.constructor.name}</strong><br>
      Props: ${Object.keys(component.props || {}).length}<br>
      State: ${Object.keys(component.state || {}).length}<br>
      Signals: ${this._getComponentSignals(component).length}
    `;

    this.tooltip.innerHTML = info;

    const tooltipRect = this.tooltip.getBoundingClientRect();
    this.tooltip.style.top = rect.top + window.scrollY - tooltipRect.height - 5 + 'px';
    this.tooltip.style.left = rect.left + window.scrollX + 'px';

    document.body.appendChild(this.tooltip);
  }

  _sanitizeProps(props) {
    if (!props) return {};

    const sanitized = {};
    for (const [key, value] of Object.entries(props)) {
      if (isSignal(value)) {
        sanitized[key] = { type: 'signal', value: unwrap(value) };
      } else if (typeof value === 'function') {
        sanitized[key] = { type: 'function' };
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }

  _sanitizeState(state) {
    if (!state) return {};

    const sanitized = {};
    for (const [key, value] of Object.entries(state)) {
      if (isSignal(value)) {
        sanitized[key] = { type: 'signal', value: unwrap(value) };
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }

  _getComponentSignals(component) {
    const signals = [];

    // Check component properties for signals
    const checkObject = (obj, path = '') => {
      if (!obj || typeof obj !== 'object') return;

      for (const [key, value] of Object.entries(obj)) {
        const currentPath = path ? `${path}.${key}` : key;

        if (isSignal(value)) {
          signals.push({
            path: currentPath,
            value: unwrap(value),
            signal: value
          });
        } else if (typeof value === 'object' && value !== null) {
          checkObject(value, currentPath);
        }
      }
    };

    checkObject(component.props);
    checkObject(component.state);

    return signals;
  }

  _getComponentId(component) {
    for (const [id, comp] of componentRegistry) {
      if (comp === component) return id;
    }
    return null;
  }
}

// Signal Debugger
export class SignalDebugger {
  constructor() {
    this.watchedSignals = new Set();
    this.signalHistory = new Map();
    this.breakpoints = new Set();
  }

  // Watch signal for changes
  watchSignal(signal, label = 'unnamed') {
    if (!isSignal(signal)) {
      logger.warn('Cannot watch non-signal:', signal);
      return;
    }

    this.watchedSignals.add(signal);
    this.signalHistory.set(signal, []);

    // Add effect to track changes
    effect(() => {
      const value = signal.value;
      const history = this.signalHistory.get(signal) || [];
      history.push({
        timestamp: Date.now(),
        value: value,
        stack: new Error().stack
      });

      // Keep only last 100 changes
      if (history.length > 100) {
        history.shift();
      }

      logger.debug(`Signal ${label} changed:`, value);

      // Check breakpoints
      if (this.breakpoints.has(signal)) {
        this._triggerBreakpoint(signal, value, label);
      }
    });

    logger.info(`Watching signal: ${label}`);
  }

  // Stop watching signal
  unwatchSignal(signal) {
    this.watchedSignals.delete(signal);
    this.signalHistory.delete(signal);
  }

  // Get signal history
  getSignalHistory(signal) {
    return this.signalHistory.get(signal) || [];
  }

  // Add breakpoint
  addBreakpoint(signal, condition = null) {
    this.breakpoints.add(signal);
    logger.info('Breakpoint added to signal');
  }

  // Remove breakpoint
  removeBreakpoint(signal) {
    this.breakpoints.delete(signal);
    logger.info('Breakpoint removed from signal');
  }

  _triggerBreakpoint(signal, value, label) {
    logger.warn(`Breakpoint triggered on signal ${label}:`, value);

    // In browser environment, use debugger
    if (typeof window !== 'undefined' && window.debugger) {
      debugger;
    }
  }

  // Get all signals info
  getSignalsInfo() {
    const info = {};

    for (const signal of this.watchedSignals) {
      const history = this.getSignalHistory(signal);
      info[signal._debugName || 'unnamed'] = {
        currentValue: unwrap(signal),
        historyLength: history.length,
        lastChange: history[history.length - 1],
        stats: signal.getStats()
      };
    }

    return info;
  }
}

// Performance Profiler
export class PerformanceProfiler {
  constructor() {
    this.marks = new Map();
    this.measures = [];
    this.componentRenders = new Map();
  }

  // Start performance mark
  startMark(name) {
    if (!window.performance || !window.performance.mark) return;

    const markName = `pydance:${name}:${Date.now()}`;
    window.performance.mark(markName);
    this.marks.set(name, markName);

    return markName;
  }

  // End performance mark
  endMark(name) {
    if (!window.performance || !window.performance.measure) return;

    const startMark = this.marks.get(name);
    if (!startMark) return;

    const measureName = `pydance-measure:${name}`;
    try {
      window.performance.measure(measureName, startMark, name);
      const measure = window.performance.getEntriesByName(measureName)[0];

      const measureData = {
        name,
        startTime: measure.startTime,
        duration: measure.duration,
        timestamp: Date.now()
      };

      this.measures.push(measureData);

      // Keep only last 1000 measures
      if (this.measures.length > 1000) {
        this.measures.shift();
      }

      logger.debug(`Performance measure ${name}: ${measure.duration.toFixed(2)}ms`);

      return measureData;
    } catch (error) {
      logger.warn('Performance measurement failed:', error);
    }
  }

  // Profile component render
  profileComponentRender(componentId, renderFn) {
    const startMark = this.startMark(`component-render-${componentId}`);

    try {
      const result = renderFn();

      this.endMark(`component-render-${componentId}`);

      // Track render count and time
      const renders = this.componentRenders.get(componentId) || [];
      renders.push({
        timestamp: Date.now(),
        duration: this.getLastMeasure()?.duration || 0
      });

      // Keep only last 50 renders
      if (renders.length > 50) {
        renders.shift();
      }

      this.componentRenders.set(componentId, renders);

      return result;
    } catch (error) {
      this.endMark(`component-render-${componentId}`);
      throw error;
    }
  }

  // Get performance metrics
  getMetrics() {
    return {
      measures: this.measures.slice(-100), // Last 100 measures
      componentRenders: Object.fromEntries(this.componentRenders),
      memory: this._getMemoryInfo(),
      timing: this._getTimingInfo()
    };
  }

  // Get last measure
  getLastMeasure() {
    return this.measures[this.measures.length - 1];
  }

  _getMemoryInfo() {
    if (!window.performance || !window.performance.memory) return null;

    return {
      used: window.performance.memory.usedJSHeapSize,
      total: window.performance.memory.totalJSHeapSize,
      limit: window.performance.memory.jsHeapSizeLimit,
      usagePercent: (window.performance.memory.usedJSHeapSize / window.performance.memory.totalJSHeapSize * 100).toFixed(2)
    };
  }

  _getTimingInfo() {
    if (!window.performance || !window.performance.timing) return null;

    const timing = window.performance.timing;
    return {
      loadTime: timing.loadEventEnd - timing.navigationStart,
      domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
      firstPaint: timing.firstPaint || null,
      firstContentfulPaint: timing.firstContentfulPaint || null
    };
  }
}

// Memory Leak Detector
export class MemoryLeakDetector {
  constructor() {
    this.snapshots = [];
    this.leakThreshold = 10 * 1024 * 1024; // 10MB
  }

  // Take memory snapshot
  takeSnapshot(label = 'snapshot') {
    if (!window.performance || !window.performance.memory) {
      logger.warn('Memory monitoring not available');
      return null;
    }

    const snapshot = {
      timestamp: Date.now(),
      label,
      memory: {
        used: window.performance.memory.usedJSHeapSize,
        total: window.performance.memory.totalJSHeapSize,
        limit: window.performance.memory.jsHeapSizeLimit
      },
      components: componentRegistry.size,
      signals: signalRegistry.size,
      effects: effectRegistry.size
    };

    this.snapshots.push(snapshot);

    // Keep only last 50 snapshots
    if (this.snapshots.length > 50) {
      this.snapshots.shift();
    }

    logger.debug(`Memory snapshot taken: ${label}`, snapshot.memory);
    return snapshot;
  }

  // Detect potential memory leaks
  detectLeaks() {
    if (this.snapshots.length < 2) return [];

    const leaks = [];
    const recent = this.snapshots.slice(-5); // Last 5 snapshots

    // Check for continuous memory growth
    let growthTrend = 0;
    for (let i = 1; i < recent.length; i++) {
      const growth = recent[i].memory.used - recent[i - 1].memory.used;
      growthTrend += growth;
    }

    if (growthTrend > this.leakThreshold) {
      leaks.push({
        type: 'memory_growth',
        severity: 'high',
        message: `Continuous memory growth detected: ${(growthTrend / 1024 / 1024).toFixed(2)}MB over ${recent.length} snapshots`,
        trend: growthTrend
      });
    }

    // Check for component/signal leaks
    const first = recent[0];
    const last = recent[recent.length - 1];

    if (last.components > first.components + 10) {
      leaks.push({
        type: 'component_leak',
        severity: 'medium',
        message: `Component count increased by ${last.components - first.components} over time`,
        increase: last.components - first.components
      });
    }

    if (last.signals > first.signals + 20) {
      leaks.push({
        type: 'signal_leak',
        severity: 'medium',
        message: `Signal count increased by ${last.signals - first.signals} over time`,
        increase: last.signals - first.signals
      });
    }

    return leaks;
  }

  // Get memory report
  getMemoryReport() {
    return {
      snapshots: this.snapshots.slice(-10), // Last 10 snapshots
      leaks: this.detectLeaks(),
      summary: {
        totalSnapshots: this.snapshots.length,
        averageMemoryUsage: this._calculateAverageMemory(),
        peakMemoryUsage: this._calculatePeakMemory()
      }
    };
  }

  _calculateAverageMemory() {
    if (this.snapshots.length === 0) return 0;

    const total = this.snapshots.reduce((sum, snap) => sum + snap.memory.used, 0);
    return total / this.snapshots.length;
  }

  _calculatePeakMemory() {
    if (this.snapshots.length === 0) return 0;

    return Math.max(...this.snapshots.map(snap => snap.memory.used));
  }
}

// Hot Reload Integration
export class HotReloadManager {
  constructor() {
    this.listeners = new Set();
    this.isEnabled = false;
  }

  enable() {
    if (this.isEnabled) return;

    this.isEnabled = true;

    // Listen for hot reload events
    if (window && window.addEventListener) {
      window.addEventListener('pydance:hot-reload', this._handleHotReload.bind(this));
    }

    // Setup WebSocket connection for dev server
    this._connectToDevServer();

    logger.info('Hot reload enabled');
  }

  disable() {
    this.isEnabled = false;
    this.listeners.clear();

    if (this.ws) {
      this.ws.close();
    }

    logger.info('Hot reload disabled');
  }

  onReload(callback) {
    this.listeners.add(callback);
  }

  offReload(callback) {
    this.listeners.delete(callback);
  }

  _handleHotReload(event) {
    const { type, data } = event.detail;

    logger.info('Hot reload triggered:', type);

    // Notify all listeners
    for (const listener of this.listeners) {
      try {
        listener(type, data);
      } catch (error) {
        logger.error('Hot reload listener error:', error);
      }
    }

    // Handle different reload types
    switch (type) {
      case 'component':
        this._reloadComponent(data);
        break;
      case 'style':
        this._reloadStyles(data);
        break;
      case 'full':
        window.location.reload();
        break;
    }
  }

  _connectToDevServer() {
    try {
      this.ws = new WebSocket('ws://localhost:24678');

      this.ws.onopen = () => {
        logger.info('Connected to dev server for hot reload');
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        window.dispatchEvent(new CustomEvent('pydance:hot-reload', { detail: data }));
      };

      this.ws.onclose = () => {
        logger.info('Disconnected from dev server');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this._connectToDevServer(), 5000);
      };

      this.ws.onerror = (error) => {
        logger.warn('Dev server connection error:', error);
      };
    } catch (error) {
      logger.warn('Failed to connect to dev server:', error);
    }
  }

  _reloadComponent(data) {
    // Find and update component
    const { componentId, newCode } = data;

    // This would integrate with the component system to reload specific components
    logger.debug('Reloading component:', componentId);
  }

  _reloadStyles(data) {
    // Reload stylesheets
    const links = document.querySelectorAll('link[rel="stylesheet"]');
    links.forEach(link => {
      const url = new URL(link.href);
      url.searchParams.set('t', Date.now());
      link.href = url.toString();
    });

    logger.debug('Styles reloaded');
  }
}

// Main DevTools API
export class PydanceDevTools {
  constructor() {
    this.componentInspector = new ComponentInspector();
    this.signalDebugger = new SignalDebugger();
    this.performanceProfiler = new PerformanceProfiler();
    this.memoryLeakDetector = new MemoryLeakDetector();
    this.hotReloadManager = new HotReloadManager();

    this.enabled = false;
    this.plugins = new Map();
  }

  // Enable devtools
  enable() {
    if (this.enabled) return;

    this.enabled = true;

    // Enable hot reload in development
    if (isDevelopment) {
      this.hotReloadManager.enable();
    }

    // Start memory monitoring
    this.memoryLeakDetector.takeSnapshot('initial');

    // Periodic memory checks
    this.memoryCheckInterval = setInterval(() => {
      this.memoryLeakDetector.takeSnapshot('periodic');
    }, 30000); // Every 30 seconds

    // Install global API
    this._installGlobalAPI();

    logger.info('Pydance DevTools enabled');
  }

  // Disable devtools
  disable() {
    this.enabled = false;

    if (this.memoryCheckInterval) {
      clearInterval(this.memoryCheckInterval);
    }

    this.hotReloadManager.disable();

    logger.info('Pydance DevTools disabled');
  }

  // Register component for inspection
  registerComponent(component, id) {
    componentRegistry.set(id, component);
    performanceMetrics.componentCount++;
  }

  // Unregister component
  unregisterComponent(id) {
    componentRegistry.delete(id);
    componentTree.delete(id);
    performanceMetrics.componentCount--;
  }

  // Register signal for debugging
  registerSignal(signal, name = 'unnamed') {
    signal._debugName = name;
    signalRegistry.set(signal, name);
    performanceMetrics.signalCount++;
  }

  // Register effect for debugging
  registerEffect(effect, name = 'unnamed') {
    effectRegistry.set(effect, name);
    performanceMetrics.effectCount++;
  }

  // Add devtools plugin
  addPlugin(name, plugin) {
    this.plugins.set(name, plugin);
    logger.info(`DevTools plugin added: ${name}`);
  }

  // Get comprehensive devtools state
  getState() {
    return {
      enabled: this.enabled,
      components: this.componentInspector.inspectComponentTree(),
      signals: this.signalDebugger.getSignalsInfo(),
      performance: this.performanceProfiler.getMetrics(),
      memory: this.memoryLeakDetector.getMemoryReport(),
      plugins: Array.from(this.plugins.keys())
    };
  }

  // Export data for debugging
  exportData() {
    const data = this.getState();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pydance-devtools-${Date.now()}.json`;
    a.click();

    URL.revokeObjectURL(url);
  }

  _installGlobalAPI() {
    if (typeof window === 'undefined') return;

    window.__PYDANCE_DEVTOOLS__ = {
      // Core devtools
      inspect: () => this.componentInspector.inspectComponentTree(),
      highlight: (id) => this.componentInspector.highlightComponent(id),
      watchSignal: (signal, name) => this.signalDebugger.watchSignal(signal, name),
      profile: () => this.performanceProfiler.getMetrics(),
      memory: () => this.memoryLeakDetector.getMemoryReport(),

      // Utilities
      getState: () => this.getState(),
      export: () => this.exportData(),
      logger: getLogger('devtools'),

      // Component registry access
      components: componentRegistry,
      signals: signalRegistry,
      effects: effectRegistry
    };

    console.log('Pydance DevTools API installed. Access via window.__PYDANCE_DEVTOOLS__');
  }
}

// Global devtools instance
export const devtools = new PydanceDevTools();

// Auto-enable in development
if (isDevelopment) {
  // Delay to ensure DOM is ready
  if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
      window.addEventListener('DOMContentLoaded', () => {
        devtools.enable();
      });
    } else {
      setTimeout(() => devtools.enable(), 100);
    }
  }
}

// Export utilities
export default {
  PydanceDevTools,
  devtools,
  ComponentInspector,
  SignalDebugger,
  PerformanceProfiler,
  MemoryLeakDetector,
  HotReloadManager
};
