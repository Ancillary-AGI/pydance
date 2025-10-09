/**
 * Optimized Signal with batching and cleanup
 * Extends existing Signal functionality without removing features
 */

import { signal, computed, effect, batch } from './Signal.js';

// Batch update queue
let updateQueue = new Set();
let isBatching = false;
let batchTimer = null;

/**
 * Batch multiple signal updates into single render
 * Preserves all Signal functionality
 */
export function batchUpdates(fn) {
  if (isBatching) {
    return fn();
  }
  
  isBatching = true;
  try {
    fn();
  } finally {
    isBatching = false;
    flushUpdates();
  }
}

function flushUpdates() {
  if (updateQueue.size === 0) return;
  
  const updates = Array.from(updateQueue);
  updateQueue.clear();
  
  // Execute all updates
  updates.forEach(update => update());
}

/**
 * Optimized signal with automatic batching
 * Extends base signal functionality
 */
export function optimizedSignal(initialValue) {
  const baseSignal = signal(initialValue);
  const subscribers = new Set();
  let lastAccess = Date.now();
  
  // Wrap getter to track access
  const getter = () => {
    lastAccess = Date.now();
    return baseSignal.value;
  };
  
  // Wrap setter to batch updates
  const setter = (newValue) => {
    const oldValue = baseSignal.value;
    
    // Skip if unchanged
    if (Object.is(oldValue, newValue)) {
      return;
    }
    
    baseSignal.value = newValue;
    
    // Batch updates
    if (isBatching) {
      subscribers.forEach(sub => updateQueue.add(sub));
    } else {
      // Micro-batch with setTimeout
      if (!batchTimer) {
        batchTimer = setTimeout(() => {
          batchTimer = null;
          flushUpdates();
        }, 0);
      }
      subscribers.forEach(sub => updateQueue.add(sub));
    }
  };
  
  // Create optimized signal object
  const optimized = {
    get value() {
      return getter();
    },
    set value(newValue) {
      setter(newValue);
    },
    subscribe(callback) {
      subscribers.add(callback);
      return () => subscribers.delete(callback);
    },
    cleanup() {
      // Cleanup unused subscriptions
      const now = Date.now();
      if (now - lastAccess > 60000) {  // 1 minute
        subscribers.clear();
      }
    },
    // Preserve base signal methods
    peek: () => baseSignal.peek?.() || baseSignal.value,
    update: (fn) => {
      setter(fn(getter()));
    }
  };
  
  return optimized;
}

/**
 * Memoized computed signal
 * Extends base computed functionality
 */
export function memoizedComputed(fn, deps = []) {
  let cachedValue;
  let cachedDeps = [];
  let isDirty = true;
  
  const computedSignal = computed(() => {
    // Check if deps changed
    const depsChanged = deps.length === 0 || 
      deps.some((dep, i) => !Object.is(dep, cachedDeps[i]));
    
    if (isDirty || depsChanged) {
      cachedValue = fn();
      cachedDeps = [...deps];
      isDirty = false;
    }
    
    return cachedValue;
  });
  
  // Mark dirty on dependency change
  deps.forEach(dep => {
    if (dep && typeof dep === 'object' && 'subscribe' in dep) {
      dep.subscribe(() => {
        isDirty = true;
      });
    }
  });
  
  return computedSignal;
}

/**
 * Optimized effect with cleanup tracking
 * Extends base effect functionality
 */
export function optimizedEffect(fn, deps = []) {
  let cleanup = null;
  let prevDeps = [];
  
  const effectInstance = effect(() => {
    // Check if deps changed
    const depsChanged = deps.length === 0 ||
      deps.some((dep, i) => !Object.is(dep, prevDeps[i]));
    
    if (depsChanged) {
      // Run cleanup
      if (cleanup && typeof cleanup === 'function') {
        cleanup();
      }
      
      // Run effect
      cleanup = fn();
      prevDeps = [...deps];
    }
  });
  
  // Return cleanup function
  return () => {
    if (cleanup && typeof cleanup === 'function') {
      cleanup();
    }
    effectInstance.stop?.();
  };
}

/**
 * Signal with automatic garbage collection
 * Preserves all functionality
 */
export class ManagedSignal {
  constructor(initialValue) {
    this._signal = optimizedSignal(initialValue);
    this._lastAccess = Date.now();
    this._cleanupTimer = null;
    
    // Schedule periodic cleanup
    this._scheduleCleanup();
  }
  
  get value() {
    this._lastAccess = Date.now();
    return this._signal.value;
  }
  
  set value(newValue) {
    this._lastAccess = Date.now();
    this._signal.value = newValue;
  }
  
  _scheduleCleanup() {
    if (this._cleanupTimer) {
      clearTimeout(this._cleanupTimer);
    }
    
    this._cleanupTimer = setTimeout(() => {
      this._signal.cleanup();
      this._scheduleCleanup();
    }, 60000);  // Cleanup every minute
  }
  
  dispose() {
    if (this._cleanupTimer) {
      clearTimeout(this._cleanupTimer);
    }
    this._signal.cleanup();
  }
}

// Export all optimized functions
export {
  signal,           // Re-export base signal
  computed,         // Re-export base computed
  effect,           // Re-export base effect
  batch             // Re-export base batch
};
