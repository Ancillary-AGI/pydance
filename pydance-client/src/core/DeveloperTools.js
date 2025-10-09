/**
 * Developer Tools - Advanced Debugging and Development Tools
 * Provides React DevTools-like functionality for Pydance Client
 */

import { performanceMonitor, memoryManager } from './Diff.js';
import { jsxDevTools } from './JSX.js';

// Component inspector
export class ComponentInspector {
  constructor() {
    this.components = new Map();
    this.selectedComponent = null;
    this.isEnabled = false;
    this.tree = null;
  }

  enable() {
    this.isEnabled = true;
    this.injectStyles();
    this.createPanel();
    console.log('🔧 Component Inspector enabled');
  }

  disable() {
    this.isEnabled = false;
    this.removePanel();
    console.log('🔧 Component Inspector disabled');
  }

  injectStyles() {
    if (document.getElementById('pydance-devtools-styles')) return;

    const style = document.createElement('style');
    style.id = 'pydance-devtools-styles';
    style.textContent = `
      .pydance-devtools-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 350px;
        height: 100vh;
        background: #f8f9fa;
        border-left: 1px solid #dee2e6;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 12px;
        overflow: hidden;
        box-shadow: -2px 0 10px rgba(0,0,0,0.1);
      }

      .pydance-devtools-header {
        background: #007bff;
        color: white;
        padding: 8px 12px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .pydance-devtools-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 16px;
      }

      .pydance-devtools-content {
        height: calc(100vh - 40px);
        overflow-y: auto;
        padding: 12px;
      }

      .pydance-devtools-section {
        margin-bottom: 16px;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        overflow: hidden;
      }

      .pydance-devtools-section-header {
        background: #e9ecef;
        padding: 8px 12px;
        font-weight: bold;
        border-bottom: 1px solid #dee2e6;
      }

      .pydance-devtools-component-tree {
        max-height: 300px;
        overflow-y: auto;
      }

      .pydance-devtools-component-item {
        padding: 4px 8px;
        cursor: pointer;
        border-bottom: 1px solid #f1f3f4;
        transition: background-color 0.2s;
      }

      .pydance-devtools-component-item:hover {
        background: #f1f3f4;
      }

      .pydance-devtools-component-item.selected {
        background: #e3f2fd;
        border-left: 3px solid #007bff;
      }

      .pydance-devtools-props {
        margin-top: 8px;
        padding: 8px;
        background: #f8f9fa;
        border-radius: 4px;
        font-family: monospace;
        font-size: 11px;
      }

      .pydance-devtools-prop {
        margin-bottom: 4px;
      }

      .pydance-devtools-prop-key {
        color: #d73a49;
        font-weight: bold;
      }

      .pydance-devtools-prop-value {
        color: #032f62;
      }

      .pydance-devtools-metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 8px;
      }

      .pydance-devtools-metric {
        background: white;
        padding: 6px;
        border-radius: 4px;
        text-align: center;
        border: 1px solid #dee2e6;
      }

      .pydance-devtools-metric-value {
        font-size: 16px;
        font-weight: bold;
        color: #007bff;
      }

      .pydance-devtools-metric-label {
        font-size: 10px;
        color: #6c757d;
        margin-top: 2px;
      }

      .pydance-devtools-controls {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
      }

      .pydance-devtools-btn {
        padding: 4px 8px;
        border: 1px solid #dee2e6;
        background: white;
        border-radius: 4px;
        cursor: pointer;
        font-size: 11px;
        transition: background-color 0.2s;
      }

      .pydance-devtools-btn:hover {
        background: #f8f9fa;
      }

      .pydance-devtools-btn.primary {
        background: #007bff;
        color: white;
        border-color: #007bff;
      }

      .pydance-devtools-btn.primary:hover {
        background: #0056b3;
      }

      .pydance-highlight {
        outline: 2px solid #ff6b35 !important;
        outline-offset: 2px !important;
      }

      .pydance-devtools-log {
        background: #1e1e1e;
        color: #d4d4d4;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 11px;
        padding: 8px;
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
        margin-top: 8px;
      }

      .pydance-devtools-log-entry {
        margin-bottom: 2px;
        padding: 2px 0;
      }

      .pydance-devtools-log-info { color: #4fc3f7; }
      .pydance-devtools-log-warn { color: #ffb74d; }
      .pydance-devtools-log-error { color: #f48fb1; }
    `;
    document.head.appendChild(style);
  }

  createPanel() {
    if (document.getElementById('pydance-devtools-panel')) return;

    const panel = document.createElement('div');
    panel.id = 'pydance-devtools-panel';
    panel.className = 'pydance-devtools-panel';
    panel.innerHTML = `
      <div class="pydance-devtools-header">
        <span>🔧 Pydance DevTools</span>
        <button class="pydance-devtools-close" onclick="window.__PYDANCE_DEVTOOLS__.disable()">×</button>
      </div>
      <div class="pydance-devtools-content">
        <div class="pydance-devtools-controls">
          <button class="pydance-devtools-btn primary" onclick="window.__PYDANCE_DEVTOOLS__.refresh()">Refresh</button>
          <button class="pydance-devtools-btn" onclick="window.__PYDANCE_DEVTOOLS__.clearLog()">Clear Log</button>
          <button class="pydance-devtools-btn" onclick="window.__PYDANCE_DEVTOOLS__.exportData()">Export</button>
        </div>

        <div class="pydance-devtools-section">
          <div class="pydance-devtools-section-header">📊 Performance Metrics</div>
          <div class="pydance-devtools-metrics">
            <div class="pydance-devtools-metric">
              <div class="pydance-devtools-metric-value" id="diff-time">0ms</div>
              <div class="pydance-devtools-metric-label">Avg Diff Time</div>
            </div>
            <div class="pydance-devtools-metric">
              <div class="pydance-devtools-metric-value" id="patch-time">0ms</div>
              <div class="pydance-devtools-metric-label">Avg Patch Time</div>
            </div>
            <div class="pydance-devtools-metric">
              <div class="pydance-devtools-metric-value" id="memory-usage">0MB</div>
              <div class="pydance-devtools-metric-label">Memory Usage</div>
            </div>
            <div class="pydance-devtools-metric">
              <div class="pydance-devtools-metric-value" id="component-count">0</div>
              <div class="pydance-devtools-metric-label">Components</div>
            </div>
          </div>
        </div>

        <div class="pydance-devtools-section">
          <div class="pydance-devtools-section-header">🌳 Component Tree</div>
          <div class="pydance-devtools-component-tree" id="component-tree">
            <div class="pydance-devtools-component-item">No components found</div>
          </div>
        </div>

        <div class="pydance-devtools-section">
          <div class="pydance-devtools-section-header">📋 Props & State</div>
          <div id="component-props" class="pydance-devtools-props">
            Select a component to view props and state
          </div>
        </div>

        <div class="pydance-devtools-section">
          <div class="pydance-devtools-section-header">📝 Activity Log</div>
          <div class="pydance-devtools-log" id="activity-log"></div>
        </div>
      </div>
    `;

    document.body.appendChild(panel);
    this.panel = panel;
    this.setupEventListeners();
  }

  removePanel() {
    const panel = document.getElementById('pydance-devtools-panel');
    if (panel) {
      panel.remove();
      this.panel = null;
    }
  }

  setupEventListeners() {
    // Global click listener for component selection
    document.addEventListener('click', (e) => {
      if (!this.isEnabled) return;

      const target = e.target;
      const componentElement = target.closest('[data-component-id]');

      if (componentElement) {
        const componentId = componentElement.getAttribute('data-component-id');
        this.selectComponent(componentId);
      }
    });

    // Global error listener
    window.addEventListener('error', (e) => {
      this.log('error', 'Global error', { message: e.message, filename: e.filename, line: e.lineno });
    });
  }

  registerComponent(component) {
    if (!this.isEnabled) return;

    const id = Math.random().toString(36).substr(2, 9);
    this.components.set(id, {
      id,
      name: component.constructor.name,
      instance: component,
      element: component.element,
      props: component.props,
      state: component.state,
      renderCount: 0,
      lastRender: Date.now()
    });

    // Add data attribute to element for selection
    if (component.element) {
      component.element.setAttribute('data-component-id', id);
    }

    this.log('info', `Component registered: ${component.constructor.name}`, { id });
    this.refresh();
  }

  unregisterComponent(id) {
    const component = this.components.get(id);
    if (component && component.element) {
      component.element.removeAttribute('data-component-id');
    }
    this.components.delete(id);
    this.log('info', `Component unregistered: ${id}`);
    this.refresh();
  }

  selectComponent(id) {
    this.selectedComponent = id;
    this.refresh();
    this.highlightComponent(id);
  }

  highlightComponent(id) {
    // Remove previous highlights
    document.querySelectorAll('.pydance-highlight').forEach(el => {
      el.classList.remove('pydance-highlight');
    });

    const component = this.components.get(id);
    if (component && component.element) {
      component.element.classList.add('pydance-highlight');
      component.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  refresh() {
    if (!this.panel) return;

    this.updateMetrics();
    this.updateComponentTree();
    this.updatePropsView();
  }

  updateMetrics() {
    const metrics = performanceMonitor.getMetrics();

    const diffTime = document.getElementById('diff-time');
    const patchTime = document.getElementById('patch-time');
    const memoryUsage = document.getElementById('memory-usage');
    const componentCount = document.getElementById('component-count');

    if (diffTime) diffTime.textContent = `${performanceMonitor.getAverageTime('diff').toFixed(2)}ms`;
    if (patchTime) patchTime.textContent = `${performanceMonitor.getAverageTime('patch').toFixed(2)}ms`;
    if (memoryUsage) {
      const memory = performance.memory;
      memoryUsage.textContent = `${((memory ? memory.usedJSHeapSize : 0) / 1024 / 1024).toFixed(1)}MB`;
    }
    if (componentCount) componentCount.textContent = this.components.size.toString();
  }

  updateComponentTree() {
    const treeContainer = document.getElementById('component-tree');
    if (!treeContainer) return;

    if (this.components.size === 0) {
      treeContainer.innerHTML = '<div class="pydance-devtools-component-item">No components found</div>';
      return;
    }

    const treeHTML = Array.from(this.components.entries()).map(([id, component]) => {
      const isSelected = id === this.selectedComponent;
      return `
        <div class="pydance-devtools-component-item ${isSelected ? 'selected' : ''}"
             onclick="window.__PYDANCE_DEVTOOLS__.selectComponent('${id}')">
          <strong>${component.name}</strong>
          <div style="font-size: 10px; color: #6c757d;">
            Props: ${Object.keys(component.props).length} |
            State: ${Object.keys(component.state).length} |
            Renders: ${component.renderCount}
          </div>
        </div>
      `;
    }).join('');

    treeContainer.innerHTML = treeHTML;
  }

  updatePropsView() {
    const propsContainer = document.getElementById('component-props');
    if (!propsContainer) return;

    if (!this.selectedComponent) {
      propsContainer.innerHTML = 'Select a component to view props and state';
      return;
    }

    const component = this.components.get(this.selectedComponent);
    if (!component) {
      propsContainer.innerHTML = 'Component not found';
      return;
    }

    const propsHTML = `
      <div class="pydance-devtools-prop">
        <span class="pydance-devtools-prop-key">Name:</span>
        <span class="pydance-devtools-prop-value">${component.name}</span>
      </div>
      <div class="pydance-devtools-prop">
        <span class="pydance-devtools-prop-key">ID:</span>
        <span class="pydance-devtools-prop-value">${component.id}</span>
      </div>
      <div class="pydance-devtools-prop">
        <span class="pydance-devtools-prop-key">Render Count:</span>
        <span class="pydance-devtools-prop-value">${component.renderCount}</span>
      </div>
      <div class="pydance-devtools-prop">
        <span class="pydance-devtools-prop-key">Last Render:</span>
        <span class="pydance-devtools-prop-value">${new Date(component.lastRender).toLocaleTimeString()}</span>
      </div>

      <h5 style="margin: 12px 0 8px 0; color: #495057;">Props:</h5>
      ${Object.entries(component.props).map(([key, value]) => `
        <div class="pydance-devtools-prop">
          <span class="pydance-devtools-prop-key">${key}:</span>
          <span class="pydance-devtools-prop-value">${this.formatValue(value)}</span>
        </div>
      `).join('')}

      <h5 style="margin: 12px 0 8px 0; color: #495057;">State:</h5>
      ${Object.entries(component.state).map(([key, value]) => `
        <div class="pydance-devtools-prop">
          <span class="pydance-devtools-prop-key">${key}:</span>
          <span class="pydance-devtools-prop-value">${this.formatValue(value)}</span>
        </div>
      `).join('')}
    `;

    propsContainer.innerHTML = propsHTML;
  }

  formatValue(value) {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'string') return `"${value}"`;
    if (typeof value === 'function') return 'function() { ... }';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  }

  log(level, message, data = {}) {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;

    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `pydance-devtools-log-entry pydance-devtools-log-${level}`;
    entry.textContent = `[${timestamp}] ${message}`;

    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Keep only last 100 entries
    while (logContainer.children.length > 100) {
      logContainer.removeChild(logContainer.firstChild);
    }

    // Also log to console
    console.log(`[PydanceDevTools] ${message}`, data);
  }

  clearLog() {
    const logContainer = document.getElementById('activity-log');
    if (logContainer) {
      logContainer.innerHTML = '';
    }
  }

  exportData() {
    const data = {
      timestamp: new Date().toISOString(),
      metrics: performanceMonitor.getMetrics(),
      components: Array.from(this.components.entries()).map(([id, comp]) => ({
        id,
        name: comp.name,
        props: comp.props,
        state: comp.state,
        renderCount: comp.renderCount
      })),
      memory: memoryManager.getStats ? memoryManager.getStats() : null
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pydance-devtools-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Performance profiler
export class PerformanceProfiler {
  constructor() {
    this.isProfiling = false;
    this.startTime = null;
    this.measurements = [];
    this.enabled = false;
  }

  startProfiling() {
    this.isProfiling = true;
    this.startTime = performance.now();
    this.measurements = [];

    performanceMonitor.enable();
    jsxDevTools.enableDebug();

    console.log('🔍 Performance profiling started');
  }

  stopProfiling() {
    this.isProfiling = false;
    const endTime = performance.now();
    const duration = endTime - this.startTime;

    const report = {
      duration,
      measurements: this.measurements,
      metrics: performanceMonitor.getMetrics(),
      timestamp: new Date().toISOString()
    };

    performanceMonitor.disable();
    jsxDevTools.disableDebug();

    console.log('🔍 Performance profiling completed', report);
    return report;
  }

  measure(name, fn) {
    if (!this.isProfiling) return fn();

    const start = performance.now();
    const result = fn();
    const end = performance.now();
    const duration = end - start;

    this.measurements.push({
      name,
      duration,
      start,
      end,
      timestamp: new Date().toISOString()
    });

    return result;
  }

  async measureAsync(name, asyncFn) {
    if (!this.isProfiling) return await asyncFn();

    const start = performance.now();
    const result = await asyncFn();
    const end = performance.now();
    const duration = end - start;

    this.measurements.push({
      name,
      duration,
      start,
      end,
      async: true,
      timestamp: new Date().toISOString()
    });

    return result;
  }
}

// Memory analyzer
export class MemoryAnalyzer {
  constructor() {
    this.snapshots = [];
    this.isEnabled = false;
  }

  enable() {
    this.isEnabled = true;
    console.log('💾 Memory analyzer enabled');
  }

  disable() {
    this.isEnabled = false;
    console.log('💾 Memory analyzer disabled');
  }

  takeSnapshot(label = '') {
    if (!this.isEnabled) return;

    const snapshot = {
      label: label || `Snapshot ${this.snapshots.length + 1}`,
      timestamp: new Date().toISOString(),
      memory: this.getMemoryInfo(),
      components: this.getComponentInfo(),
      dom: this.getDOMInfo()
    };

    this.snapshots.push(snapshot);
    console.log('📸 Memory snapshot taken:', label);
    return snapshot;
  }

  getMemoryInfo() {
    if (!('memory' in performance)) {
      return { unsupported: true };
    }

    const memory = performance.memory;
    return {
      used: memory.usedJSHeapSize,
      total: memory.totalJSHeapSize,
      limit: memory.jsHeapSizeLimit,
      usagePercentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
    };
  }

  getComponentInfo() {
    // This would need to be implemented with component registry
    return {
      count: 0,
      types: {}
    };
  }

  getDOMInfo() {
    return {
      nodeCount: document.getElementsByTagName('*').length,
      elementCount: document.getElementsByTagName('*').length,
      textNodeCount: document.querySelectorAll('*').length - document.getElementsByTagName('*').length
    };
  }

  compareSnapshots(snapshot1, snapshot2) {
    const comparison = {
      memoryDiff: {
        used: snapshot2.memory.used - snapshot1.memory.used,
        percentage: ((snapshot2.memory.used - snapshot1.memory.used) / snapshot1.memory.used) * 100
      },
      domDiff: {
        nodes: snapshot2.dom.nodeCount - snapshot1.dom.nodeCount,
        elements: snapshot2.dom.elementCount - snapshot1.dom.elementCount
      },
      timeDiff: new Date(snapshot2.timestamp) - new Date(snapshot1.timestamp)
    };

    return comparison;
  }

  generateReport() {
    if (this.snapshots.length === 0) {
      return { error: 'No snapshots available' };
    }

    const report = {
      summary: {
        snapshotCount: this.snapshots.length,
        timeRange: {
          start: this.snapshots[0].timestamp,
          end: this.snapshots[this.snapshots.length - 1].timestamp
        }
      },
      snapshots: this.snapshots,
      trends: this.calculateTrends()
    };

    return report;
  }

  calculateTrends() {
    if (this.snapshots.length < 2) {
      return null;
    }

    const trends = {
      memory: {
        direction: 'stable',
        change: 0
      },
      dom: {
        direction: 'stable',
        change: 0
      }
    };

    const first = this.snapshots[0];
    const last = this.snapshots[this.snapshots.length - 1];

    const memoryChange = last.memory.used - first.memory.used;
    const domChange = last.dom.nodeCount - first.dom.nodeCount;

    trends.memory.change = memoryChange;
    trends.memory.direction = memoryChange > 0 ? 'increasing' : memoryChange < 0 ? 'decreasing' : 'stable';

    trends.dom.change = domChange;
    trends.dom.direction = domChange > 0 ? 'increasing' : domChange < 0 ? 'decreasing' : 'stable';

    return trends;
  }
}

// Main developer tools class
export class DeveloperTools {
  constructor() {
    this.inspector = new ComponentInspector();
    this.profiler = new PerformanceProfiler();
    this.analyzer = new MemoryAnalyzer();
    this.isEnabled = false;
  }

  enable() {
    this.isEnabled = true;
    this.inspector.enable();
    this.analyzer.enable();

    // Global reference for easy access
    window.__PYDANCE_DEVTOOLS__ = this;

    console.log('🚀 Pydance Developer Tools enabled');
  }

  disable() {
    this.isEnabled = false;
    this.inspector.disable();
    this.analyzer.disable();

    delete window.__PYDANCE_DEVTOOLS__;
    console.log('🚀 Pydance Developer Tools disabled');
  }

  // Convenience methods
  inspect() {
    this.inspector.enable();
  }

  profile() {
    this.profiler.startProfiling();
  }

  analyze() {
    this.analyzer.enable();
  }

  // Component registration helpers
  registerComponent(component) {
    this.inspector.registerComponent(component);
  }

  unregisterComponent(id) {
    this.inspector.unregisterComponent(id);
  }

  // Logging helpers
  log(level, message, data) {
    this.inspector.log(level, message, data);
  }

  // Performance helpers
  measure(name, fn) {
    return this.profiler.measure(name, fn);
  }

  measureAsync(name, asyncFn) {
    return this.profiler.measureAsync(name, asyncFn);
  }

  // Memory helpers
  snapshot(label) {
    return this.analyzer.takeSnapshot(label);
  }

  getMemoryReport() {
    return this.analyzer.generateReport();
  }
}

// Global instance
export const devTools = new DeveloperTools();

// Auto-enable in development
if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
  window.addEventListener('load', () => {
    console.log('💡 Pydance Client Developer Tools available');
    console.log('Run: devTools.enable() to start debugging');
  });
}

// Export for global use
if (typeof window !== 'undefined') {
  window.devTools = devTools;
  window.__PYDANCE_DEVTOOLS__ = devTools;
}
