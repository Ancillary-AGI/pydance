/**
 * @fileoverview Custom Jest/Vitest Matchers
 */

/**
 * Custom matchers for enhanced testing
 */
export const customMatchers = {
  /**
   * Check if element has class
   */
  toHaveClass(received, className) {
    const pass = received.classList.contains(className);
    return {
      pass,
      message: () => `Expected element to ${pass ? 'not ' : ''}have class "${className}"`
    };
  },

  /**
   * Check if element has attribute
   */
  toHaveAttribute(received, attr, value) {
    const hasAttr = received.hasAttribute(attr);
    if (value === undefined) {
      return {
        pass: hasAttr,
        message: () => `Expected element to ${hasAttr ? 'not ' : ''}have attribute "${attr}"`
      };
    }

    const attrValue = received.getAttribute(attr);
    const pass = hasAttr && attrValue === value;
    return {
      pass,
      message: () => `Expected element to have attribute "${attr}" with value "${value}", got "${attrValue}"`
    };
  },

  /**
   * Check if element contains text
   */
  toHaveTextContent(received, expectedText) {
    const actualText = received.textContent.trim();
    const pass = actualText === expectedText;
    return {
      pass,
      message: () => `Expected element text content to be "${expectedText}", got "${actualText}"`
    };
  },

  /**
   * Check if element is visible
   */
  toBeVisible(received) {
    const isVisible = received.offsetWidth > 0 && received.offsetHeight > 0 &&
                     received.getClientRects().length > 0;
    return {
      pass: isVisible,
      message: () => `Expected element to ${isVisible ? 'not ' : ''}be visible`
    };
  },

  /**
   * Check if signal has specific value
   */
  toHaveValue(received, expectedValue) {
    const pass = received.value === expectedValue;
    return {
      pass,
      message: () => `Expected signal to have value ${expectedValue}, got ${received.value}`
    };
  },

  /**
   * Check if mock was called with specific args
   */
  toHaveBeenCalledWith(received, ...expectedArgs) {
    const calls = received.calls || [];
    const pass = calls.some(call => {
      return call.length === expectedArgs.length &&
             call.every((arg, i) => arg === expectedArgs[i]);
    });
    return {
      pass,
      message: () => `Expected mock to have been called with [${expectedArgs.join(', ')}]`
    };
  },

  /**
   * Check if element has specific style
   */
  toHaveStyle(received, property, expectedValue) {
    const computedStyle = window.getComputedStyle(received);
    const actualValue = computedStyle[property];
    const pass = actualValue === expectedValue;
    return {
      pass,
      message: () => `Expected element to have style "${property}: ${expectedValue}", got "${actualValue}"`
    };
  }
};

/**
 * Register custom matchers with expect
 */
export function registerMatchers() {
  if (typeof expect !== 'undefined' && expect.extend) {
    expect.extend(customMatchers);
  }
}

// Auto-register if in test environment
if (typeof window !== 'undefined' && window.location?.hostname === 'localhost') {
  registerMatchers();
}
