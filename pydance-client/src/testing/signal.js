/**
 * @fileoverview Signal Testing Utilities
 */

/**
 * Creates a test signal with enhanced testing capabilities
 * @param {any} initialValue - Initial signal value
 * @returns {Object} Test signal utilities
 */
export function createTestSignal(initialValue) {
  let value = initialValue;
  const subscribers = new Set();
  const callHistory = [];

  const signal = {
    /**
     * Get current value
     */
    get value() {
      callHistory.push({ type: 'get', value });
      return value;
    },

    /**
     * Set new value
     */
    set value(newValue) {
      const oldValue = value;
      value = newValue;
      callHistory.push({ type: 'set', oldValue, newValue });

      // Notify subscribers
      subscribers.forEach(callback => {
        try {
          callback(newValue, oldValue);
        } catch (error) {
          console.error('Signal subscriber error:', error);
        }
      });
    },

    /**
     * Subscribe to value changes
     */
    subscribe(callback) {
      subscribers.add(callback);
      callHistory.push({ type: 'subscribe', callback });

      // Return unsubscribe function
      return () => {
        subscribers.delete(callback);
        callHistory.push({ type: 'unsubscribe', callback });
      };
    },

    /**
     * Update value using a function
     */
    update(updater) {
      const newValue = updater(value);
      this.value = newValue;
    },

    /**
     * Reset signal to initial value
     */
    reset() {
      this.value = initialValue;
      callHistory.length = 0; // Clear history
    }
  };

  // Test-specific methods
  signal.__test = {
    /**
     * Get call history
     */
    getCallHistory() {
      return [...callHistory];
    },

    /**
     * Clear call history
     */
    clearHistory() {
      callHistory.length = 0;
    },

    /**
     * Get subscriber count
     */
    getSubscriberCount() {
      return subscribers.size;
    },

    /**
     * Check if signal was called with specific value
     */
    wasCalledWith(expectedValue) {
      return callHistory.some(call =>
        call.type === 'set' && call.newValue === expectedValue
      );
    },

    /**
     * Get all values the signal has had
     */
    getValueHistory() {
      const values = [initialValue];
      callHistory.forEach(call => {
        if (call.type === 'set') {
          values.push(call.newValue);
        }
      });
      return values;
    }
  };

  return signal;
}

/**
 * Signal testing helpers
 */
export const signalHelpers = {
  /**
   * Create multiple test signals
   */
  createSignalBatch(count, initialValue = undefined) {
    return Array.from({ length: count }, () => createTestSignal(initialValue));
  },

  /**
   * Create a computed signal for testing
   */
  createComputedSignal(dependencies, computeFn) {
    const computed = {
      get value() {
        return computeFn(...dependencies.map(dep => dep.value));
      }
    };

    // Add test methods
    computed.__test = {
      getDependencies() {
        return dependencies;
      },
      getComputeFunction() {
        return computeFn;
      }
    };

    return computed;
  },

  /**
   * Test signal reactions
   */
  testReaction(signal, reactionFn, testValues) {
    const results = [];
    const unsubscribe = signal.subscribe((newValue, oldValue) => {
      try {
        const result = reactionFn(newValue, oldValue);
        results.push({ newValue, oldValue, result, success: true });
      } catch (error) {
        results.push({ newValue, oldValue, error, success: false });
      }
    });

    // Test with different values
    testValues.forEach(testValue => {
      signal.value = testValue;
    });

    unsubscribe();
    return results;
  }
};
