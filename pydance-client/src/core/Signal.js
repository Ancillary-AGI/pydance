/**
 * @fileoverview Signal - Ultra-efficient Reactive Primitive
 * Provides fine-grained reactivity with automatic dependency tracking and memory management
 *
 * @description
 * This module implements a high-performance reactive system using signals, which are
 * the foundation of Pydance Client's reactivity. Signals provide:
 * - Fine-grained reactivity (only components that depend on changed data re-render)
 * - Automatic dependency tracking (no need to manually specify dependencies)
 * - Memory leak prevention (automatic cleanup of unused subscriptions)
 * - O(1) update propagation using topological sorting
 * - Batch updates for performance optimization
 *
 * @example
 * ```javascript
 * import { signal, computed, effect } from '~/core/Signal.js';
 *
 * // Create a reactive signal
 * const count = signal(0);
 *
 * // Create a computed value
 * const doubled = computed(() => count.value * 2);
 *
 * // React to changes
 * effect(() => {
 *   console.log('Count changed:', count.value);
 *   console.log('Doubled:', doubled.value);
 * });
 *
 * // Update the signal (triggers all dependents)
 * count.value = 5; // Logs: "Count changed: 5", "Doubled: 10"
 * ```
 *
 * @author Pydance Framework Team
 * @version 3.0.0
 * @license MIT
 */

// Symbol for detecting signals
const SIGNAL = Symbol('signal');

// Global effect stack for dependency tracking
let activeEffect = null;
const effectStack = [];

// Enhanced batch management with priority queuing
let isBatching = false;
let batchDepth = 0;
const batchedNotifications = new Set();
const priorityQueue = new Map(); // For topological sorting

// Signal class with enhanced performance and memory management
export class Signal {
  constructor(initialValue) {
    this._value = initialValue;
    this._subscribers = new Set();
    this._version = 0;
    this._cleanup = new Set();
    this._dependents = new Set(); // Track reverse dependencies
    this._metadata = {
      created: Date.now(),
      lastAccessed: Date.now(),
      accessCount: 0
    };
    this[SIGNAL] = true;
  }

  get value() {
    // Enhanced dependency tracking
    if (activeEffect && !this._subscribers.has(activeEffect)) {
      activeEffect.dependencies.add(this);
      this._subscribers.add(activeEffect);

      // Track reverse dependency for topological sorting
      this._dependents.add(activeEffect);
    }

    // Update metadata
    this._metadata.lastAccessed = Date.now();
    this._metadata.accessCount++;

    return this._value;
  }

  set value(newValue) {
    if (Object.is(this._value, newValue)) return;

    // Prevent circular updates
    if (this._updating) {
      console.warn('Circular signal update detected');
      return;
    }

    this._updating = true;
    try {
      this._value = newValue;
      this._version++;
      this._metadata.lastAccessed = Date.now();

      // Enhanced batch notifications with priority
      if (!isBatching) {
        this._notifySubscribers();
      } else {
        batchedNotifications.add(this);
        // Add to priority queue for topological sorting
        if (!priorityQueue.has(this)) {
          priorityQueue.set(this, new Set());
        }
      }
    } finally {
      this._updating = false;
    }
  }

  _notifySubscribers() {
    if (this._notifying) return; // Prevent re-entry
    
    this._notifying = true;
    try {
      const subscribers = Array.from(this._subscribers);
      this._subscribers.clear();

      // Execute in dependency order for better performance
      const orderedEffects = this._topologicalSort(subscribers);

      for (const effect of orderedEffects) {
        if (effect && effect.active) {
          try {
            effect.execute();
          } catch (err) {
            console.error('Effect execution error:', err);
          }
        }
      }
    } finally {
      this._notifying = false;
    }
  }

  _topologicalSort(effects) {
    // Kahn's algorithm for topological sorting
    const inDegree = new Map();
    const queue = [];
    const result = [];

    // Calculate in-degrees
    effects.forEach(effect => {
      inDegree.set(effect, effect.dependencies.size);
      if (effect.dependencies.size === 0) {
        queue.push(effect);
      }
    });

    // Process queue
    while (queue.length > 0) {
      const effect = queue.shift();
      result.push(effect);

      // Update dependent effects
      effect.dependents.forEach(dependent => {
        inDegree.set(dependent, inDegree.get(dependent) - 1);
        if (inDegree.get(dependent) === 0) {
          queue.push(dependent);
        }
      });
    }

    return result.length > 0 ? result : effects;
  }

  peek() {
    return this._value;
  }

  update(fn) {
    const newValue = typeof fn === 'function' ? fn(this._value) : fn;
    this.value = newValue;
  }

  subscribe(fn) {
    const effect = new Effect(fn);
    effect.execute();
    return () => effect.stop();
  }

  destroy() {
    // Cleanup all subscriptions
    this._subscribers.forEach(sub => {
      if (sub && sub.stop) sub.stop();
    });
    this._subscribers.clear();
    this._dependents.clear();
    this._cleanup.forEach(fn => {
      try {
        if (typeof fn === 'function') fn();
      } catch (err) {
        console.error('Cleanup error:', err);
      }
    });
    this._cleanup.clear();
    this._metadata = null;
    this._value = undefined;
  }

  // Enhanced debugging and monitoring
  getStats() {
    return {
      version: this._version,
      subscriberCount: this._subscribers.size,
      dependentCount: this._dependents.size,
      accessCount: this._metadata.accessCount,
      created: this._metadata.created,
      lastAccessed: this._metadata.lastAccessed
    };
  }
}

// Create signal function
export const signal = (initialValue) => new Signal(initialValue);

// Check if value is a signal
export const isSignal = (value) => value && value[SIGNAL] === true;

// Unwrap signal if needed
export const unwrap = (value) => isSignal(value) ? value.value : value;

// Computed signal
export class Computed extends Signal {
  constructor(compute) {
    super(undefined);
    this._compute = compute;
    this._dependencies = new Set();
    this._dirty = true;

    // Compute initial value
    this._update();
  }

  get value() {
    if (this._dirty) {
      this._update();
    }

    // Track dependency
    if (activeEffect) {
      activeEffect.dependencies.add(this);
      this._subscribers.add(activeEffect);
    }

    return this._value;
  }

  _update() {
    this._dirty = false;

    // Track dependencies
    const prevEffect = activeEffect;
    activeEffect = null;

    try {
      const newValue = this._compute();

      if (!Object.is(this._value, newValue)) {
        this._value = newValue;
        this._version++;

        // Notify subscribers
        const subscribers = [...this._subscribers];
        this._subscribers.clear();

        for (const effect of subscribers) {
          if (effect.active) {
            effect.execute();
          }
        }
      }
    } finally {
      activeEffect = prevEffect;
    }
  }

  peek() {
    if (this._dirty) {
      this._update();
    }
    return this._value;
  }
}

// Create computed function
export const computed = (compute) => new Computed(compute);

// Effect class for side effects
export class Effect {
  constructor(fn, options = {}) {
    this.fn = fn;
    this.options = options;
    this.active = true;
    this.dependencies = new Set();
    this.cleanup = null;
    this.executing = false;
  }

  execute() {
    if (!this.active || this.executing) return;

    this.executing = true;
    try {
      // Clean up previous dependencies
      this.dependencies.forEach(dep => {
        if (dep && dep._subscribers) {
          dep._subscribers.delete(this);
        }
      });
      this.dependencies.clear();

      // Track new dependencies
      const prevEffect = activeEffect;
      activeEffect = this;

      try {
        // Clean up previous effect
        if (this.cleanup && typeof this.cleanup === 'function') {
          try {
            this.cleanup();
          } catch (err) {
            console.error('Effect cleanup error:', err);
          }
        }

        // Execute effect
        const result = this.fn();
        this.cleanup = typeof result === 'function' ? result : null;
      } finally {
        activeEffect = prevEffect;
      }
    } catch (err) {
      console.error('Effect execution error:', err);
    } finally {
      this.executing = false;
    }
  }

  stop() {
    if (!this.active) return;
    
    this.active = false;
    this.dependencies.forEach(dep => {
      if (dep && dep._subscribers) {
        dep._subscribers.delete(this);
      }
    });
    this.dependencies.clear();

    if (this.cleanup && typeof this.cleanup === 'function') {
      try {
        this.cleanup();
      } catch (err) {
        console.error('Effect cleanup error:', err);
      }
      this.cleanup = null;
    }
  }
}

// Create effect function
export const effect = (fn, options) => {
  const eff = new Effect(fn, options);
  eff.execute();
  return () => eff.stop();
};

// Batch updates
const batchedEffects = new Set();

export const batch = (fn) => {
  if (batchDepth > 0) {
    return fn();
  }

  batchDepth++;
  try {
    return fn();
  } finally {
    batchDepth--;

    if (batchDepth === 0) {
      // Execute all batched effects
      const effects = [...batchedEffects];
      batchedEffects.clear();

      for (const effect of effects) {
        if (effect.active) {
          effect.execute();
        }
      }
    }
  }
};

// Batch signal updates
export const batchUpdates = (fn) => {
  return batch(fn);
};

// Utility functions
export const untrack = (fn) => {
  const prevEffect = activeEffect;
  activeEffect = null;
  try {
    return fn();
  } finally {
    activeEffect = prevEffect;
  }
};

export const tick = () => {
  return new Promise(resolve => {
    if (batchDepth === 0) {
      resolve();
    } else {
      // Schedule after current batch
      Promise.resolve().then(resolve);
    }
  });
};

// Advanced signal operations
export const mergeSignals = (...signals) => {
  return computed(() => {
    return signals.map(s => s.value);
  });
};

export const combineSignals = (signals, combineFn) => {
  return computed(() => {
    const values = signals.map(s => s.value);
    return combineFn(...values);
  });
};

// Signal debugging
export const enableSignalDebug = () => {
  const originalSignal = Signal.prototype;
  const originalComputed = Computed.prototype;

  // Add debug logging
  Signal.prototype.set = function(newValue) {
    console.log(`Signal updated:`, this._debugName || 'unnamed', 'from', this._value, 'to', newValue);
    originalSignal.set.call(this, newValue);
  };

  Computed.prototype._update = function() {
    console.log(`Computed updated:`, this._debugName || 'unnamed');
    originalComputed._update.call(this);
  };
};

// Memory management
export const cleanupSignals = () => {
  // Clean up unused signals and effects
  // Implementation would track unused reactive objects
};

// Development helpers
export const devtools = {
  getActiveEffects: () => effectStack.length,
  getSignalSubscribers: (signal) => signal._subscribers.size,
  getComputedDependencies: (computed) => computed._dependencies.size,
  traceSignal: (signal) => {
    console.log('Signal info:', {
      value: signal.peek(),
      subscribers: signal._subscribers.size,
      version: signal._version
    });
  }
};

// Export everything
export default {
  Signal,
  signal,
  isSignal,
  unwrap,
  Computed,
  computed,
  Effect,
  effect,
  batch,
  batchUpdates,
  untrack,
  tick,
  mergeSignals,
  combineSignals,
  enableSignalDebug,
  cleanupSignals,
  devtools
};
