/**
 * @fileoverview Event Testing Utilities
 */

/**
 * Creates a test event with enhanced testing capabilities
 */
export function createTestEvent(eventType, properties = {}) {
  const event = new Event(eventType);

  // Add custom properties
  Object.assign(event, properties);

  // Add test-specific methods
  event.__test = {
    /**
     * Check if event was prevented
     */
    get prevented() {
      return event.defaultPrevented;
    },

    /**
     * Check if event propagation was stopped
     */
    get propagationStopped() {
      return event.__test?.propagationStopped || false;
    },

    /**
     * Get event target chain
     */
    get targetChain() {
      return event.__test?.targetChain || [];
    }
  };

  return event;
}

/**
 * Event testing helpers
 */
export const eventHelpers = {
  /**
   * Create a sequence of events
   */
  createEventSequence(events) {
    return events.map(([type, props]) => createTestEvent(type, props));
  },

  /**
   * Simulate event dispatch with full lifecycle
   */
  async simulateEventDispatch(element, event) {
    const results = {
      dispatched: false,
      prevented: false,
      propagationStopped: false,
      listeners: []
    };

    // Track event listeners
    const originalAddEventListener = element.addEventListener;
    const listeners = [];

    element.addEventListener = function(type, listener, options) {
      listeners.push({ type, listener, options });
      return originalAddEventListener.call(this, type, listener, options);
    };

    // Dispatch event
    results.dispatched = element.dispatchEvent(event);
    results.prevented = event.defaultPrevented;
    results.listeners = listeners;

    return results;
  },

  /**
   * Test event bubbling
   */
  testEventBubbling(parentElement, childElement, eventType) {
    const events = [];
    const event = createTestEvent(eventType);

    // Add listeners to both elements
    parentElement.addEventListener(eventType, () => events.push('parent'));
    childElement.addEventListener(eventType, () => events.push('child'));

    // Dispatch from child
    childElement.dispatchEvent(event);

    return {
      events,
      expected: ['child', 'parent'], // Child first, then parent
      bubbled: events.length === 2
    };
  },

  /**
   * Create custom event types
   */
  createCustomEvent(eventType, detail = {}) {
    return new CustomEvent(eventType, { detail });
  },

  /**
   * Test event delegation
   */
  testEventDelegation(container, selector, eventType) {
    return new Promise((resolve) => {
      const results = {
        delegated: false,
        target: null,
        event: null
      };

      container.addEventListener(eventType, (event) => {
        if (event.target.matches && event.target.matches(selector)) {
          results.delegated = true;
          results.target = event.target;
          results.event = event;
          resolve(results);
        }
      });

      // Timeout if no delegation occurs
      setTimeout(() => resolve(results), 100);
    });
  }
};
