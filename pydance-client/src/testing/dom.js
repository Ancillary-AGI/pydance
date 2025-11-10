/**
 * @fileoverview DOM Testing Utilities
 */

/**
 * Creates a test DOM element with enhanced testing capabilities
 * @param {string} tagName - HTML tag name
 * @param {Object} attributes - Element attributes
 * @param {string|Array} content - Element content
 * @returns {HTMLElement} Test element
 */
export function createTestElement(tagName, attributes = {}, content = '') {
  const element = document.createElement(tagName);

  // Set attributes
  Object.entries(attributes).forEach(([key, value]) => {
    if (key === 'className') {
      element.className = value;
    } else if (key === 'style' && typeof value === 'object') {
      Object.assign(element.style, value);
    } else if (key.startsWith('data-')) {
      element.setAttribute(key, value);
    } else {
      element[key] = value;
    }
  });

  // Set content
  if (typeof content === 'string') {
    element.textContent = content;
  } else if (Array.isArray(content)) {
    content.forEach(child => {
      if (typeof child === 'string') {
        element.appendChild(document.createTextNode(child));
      } else if (child instanceof Node) {
        element.appendChild(child);
      }
    });
  }

  // Add test-specific methods
  element.__test = {
    /**
     * Get all event listeners
     */
    getEventListeners() {
      return element.__test?.eventListeners || {};
    },

    /**
     * Simulate an event
     */
    trigger(eventType, eventData = {}) {
      const event = new Event(eventType, eventData);
      element.dispatchEvent(event);
      return event;
    },

    /**
     * Get computed style
     */
    getComputedStyle() {
      return window.getComputedStyle(element);
    },

    /**
     * Check if element is visible
     */
    isVisible() {
      return element.offsetWidth > 0 || element.offsetHeight > 0 ||
             element.getClientRects().length > 0;
    },

    /**
     * Get element bounds
     */
    getBounds() {
      return element.getBoundingClientRect();
    }
  };

  return element;
}

/**
 * DOM testing helpers
 */
export const domHelpers = {
  /**
   * Create a test container
   */
  createContainer(attributes = {}) {
    const container = createTestElement('div', {
      id: 'test-container',
      style: {
        position: 'absolute',
        left: '-9999px',
        top: '-9999px',
        width: '1000px',
        height: '1000px'
      },
      ...attributes
    });

    document.body.appendChild(container);
    return container;
  },

  /**
   * Clean up test containers
   */
  cleanup() {
    const containers = document.querySelectorAll('[id^="test-container"]');
    containers.forEach(container => container.remove());
  },

  /**
   * Wait for DOM changes
   */
  async waitForDomChange(element, timeout = 1000) {
    return new Promise((resolve, reject) => {
      const observer = new MutationObserver((mutations) => {
        observer.disconnect();
        resolve(mutations);
      });

      observer.observe(element, {
        childList: true,
        subtree: true,
        attributes: true,
        characterData: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error('DOM change timeout'));
      }, timeout);
    });
  },

  /**
   * Query elements with test utilities
   */
  queryTest(selector) {
    const element = document.querySelector(selector);
    if (element && element.__test) {
      return element;
    }
    return null;
  },

  /**
   * Create mock event
   */
  createMockEvent(eventType, properties = {}) {
    const event = new Event(eventType);
    Object.assign(event, properties);
    return event;
  },

  /**
   * Test element interactions
   */
  testInteraction(element, interaction) {
    const results = {
      before: element.outerHTML,
      actions: [],
      after: null
    };

    // Perform interaction
    if (typeof interaction === 'function') {
      interaction(element);
      results.actions.push('custom function');
    } else if (interaction.type === 'click') {
      element.click();
      results.actions.push('click');
    } else if (interaction.type === 'input') {
      element.value = interaction.value;
      element.dispatchEvent(new Event('input'));
      results.actions.push(`input: ${interaction.value}`);
    }

    results.after = element.outerHTML;
    return results;
  }
};
