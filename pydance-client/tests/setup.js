/**
 * @fileoverview Test Setup - Global test configuration and utilities
 */

// Global test environment setup
import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';

// Setup JSDOM environment
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost:3000',
  pretendToBeVisual: true,
  resources: 'usable',
});

// Global variables
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.HTMLElement = dom.window.HTMLElement;
global.HTMLDivElement = dom.window.HTMLDivElement;
global.HTMLButtonElement = dom.window.HTMLButtonElement;
global.HTMLInputElement = dom.window.HTMLInputElement;
global.HTMLFormElement = dom.window.HTMLFormElement;
global.HTMLAnchorElement = dom.window.HTMLAnchorElement;
global.HTMLImageElement = dom.window.HTMLImageElement;
global.HTMLScriptElement = dom.window.HTMLScriptElement;
global.HTMLStyleElement = dom.window.HTMLStyleElement;
global.HTMLHeadElement = dom.window.HTMLHeadElement;
global.HTMLBodyElement = dom.window.HTMLBodyElement;
global.HTMLParagraphElement = dom.window.HTMLParagraphElement;
global.HTMLSpanElement = dom.window.HTMLSpanElement;
global.HTMLUListElement = dom.window.HTMLUListElement;
global.HTMLOListElement = dom.window.HTMLOListElement;
global.HTMLLIElement = dom.window.HTMLLIElement;
global.Node = dom.window.Node;
global.Text = dom.window.Text;
global.Comment = dom.window.Comment;
global.DocumentFragment = dom.window.DocumentFragment;
global.Range = dom.window.Range;
global.Event = dom.window.Event;
global.CustomEvent = dom.window.CustomEvent;
global.MouseEvent = dom.window.MouseEvent;
global.KeyboardEvent = dom.window.KeyboardEvent;
global.FocusEvent = dom.window.FocusEvent;
global.InputEvent = dom.window.InputEvent;
global.EventTarget = dom.window.EventTarget;

// DOM APIs
global.requestAnimationFrame = dom.window.requestAnimationFrame;
global.cancelAnimationFrame = dom.window.cancelAnimationFrame;
global.setTimeout = dom.window.setTimeout;
global.clearTimeout = dom.window.clearTimeout;
global.setInterval = dom.window.setInterval;
global.clearInterval = dom.window.clearInterval;

// Storage APIs
global.localStorage = dom.window.localStorage;
global.sessionStorage = dom.window.sessionStorage;

// Location and history APIs
global.location = dom.window.location;
global.history = dom.window.history;

// Console (for testing)
global.console = {
  ...console,
  // Override console methods to avoid noise in tests
  log: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  debug: vi.fn(),
};

// Performance API - mock performance.now() to avoid jsdom recursive bug
global.performance = {
  ...dom.window.performance,
  now: () => Date.now(),
  mark: dom.window.performance.mark,
  measure: dom.window.performance.measure,
  getEntriesByName: dom.window.performance.getEntriesByName,
  getEntriesByType: dom.window.performance.getEntriesByType,
  clearMarks: dom.window.performance.clearMarks,
  clearMeasures: dom.window.performance.clearMeasures,
};

// Crypto API - handle read-only property
try {
  global.crypto = dom.window.crypto;
} catch (e) {
  // If crypto is read-only, define it using Object.defineProperty
  Object.defineProperty(global, 'crypto', {
    value: {
      getRandomValues: (array) => {
        for (let i = 0; i < array.length; i++) {
          array[i] = Math.floor(Math.random() * 256);
        }
        return array;
      },
      randomUUID: () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0;
          const v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
      }
    },
    writable: false,
    configurable: true
  });
}

// URL and URLSearchParams
global.URL = dom.window.URL;
global.URLSearchParams = dom.window.URLSearchParams;

// Fetch API
global.fetch = vi.fn();
global.Request = dom.window.Request;
global.Response = dom.window.Response;
global.Headers = dom.window.Headers;

// AbortController
global.AbortController = dom.window.AbortController;

// ResizeObserver
global.ResizeObserver = dom.window.ResizeObserver;

// IntersectionObserver
global.IntersectionObserver = dom.window.IntersectionObserver;

// MutationObserver
global.MutationObserver = dom.window.MutationObserver;

// WebSocket
global.WebSocket = dom.window.WebSocket;

// File API
global.File = dom.window.File;
global.FileReader = dom.window.FileReader;
global.Blob = dom.window.Blob;

// FormData
global.FormData = dom.window.FormData;

// Test utilities
global.createElement = (tag, props = {}, children = []) => {
  const element = document.createElement(tag);

  Object.entries(props).forEach(([key, value]) => {
    if (key === 'className') {
      element.className = value;
    } else if (key.startsWith('on') && typeof value === 'function') {
      element.addEventListener(key.toLowerCase().slice(2), value);
    } else {
      element.setAttribute(key, value);
    }
  });

  children.forEach(child => {
    if (typeof child === 'string') {
      element.textContent = child;
    } else if (child instanceof Node) {
      element.appendChild(child);
    }
  });

  return element;
};

global.createSignal = (initialValue) => {
  let value = initialValue;
  const subscribers = new Set();

  const signal = {
    get value() {
      return value;
    },
    set value(newValue) {
      if (Object.is(value, newValue)) return;
      value = newValue;
      subscribers.forEach(subscriber => subscriber(value));
    },
    subscribe: (subscriber) => {
      subscribers.add(subscriber);
      return () => subscribers.delete(subscriber);
    },
  };

  return signal;
};

global.createComponent = (renderFn) => {
  return (props = {}) => {
    const instance = {
      props,
      renderFn,
      render: () => renderFn(props),
      mount: (container) => {
        const html = instance.render();
        if (typeof container === 'string') {
          container = document.querySelector(container);
        }
        if (container) {
          container.innerHTML = html;
        }
        return container;
      },
    };
    return instance;
  };
};

// Test lifecycle hooks
beforeAll(async () => {
  // Setup before all tests
  console.log('🧪 Setting up test environment...');
});

afterAll(async () => {
  // Cleanup after all tests
  console.log('🧪 Cleaning up test environment...');
});

beforeEach(() => {
  // Reset DOM before each test
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Reset mocks
  vi.clearAllMocks();

  // Reset localStorage
  localStorage.clear();
  sessionStorage.clear();
});

afterEach(() => {
  // Cleanup after each test
  // Remove any global event listeners
  // Reset any global state
});

// Custom matchers
expect.extend({
  toBeSignal(received) {
    const pass = received && typeof received.subscribe === 'function' && 'value' in received;
    if (pass) {
      return {
        message: () => `expected ${received} not to be a signal`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a signal`,
        pass: false,
      };
    }
  },

  toBeComponent(received) {
    const pass = received && typeof received.render === 'function' && typeof received.mount === 'function';
    if (pass) {
      return {
        message: () => `expected ${received} not to be a component`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a component`,
        pass: false,
      };
    }
  },

  toHaveBeenCalledWithSignal(received, signal) {
    const calls = received.mock.calls;
    const pass = calls.some(call =>
      call.some(arg => arg && typeof arg.subscribe === 'function' && 'value' in arg)
    );

    if (pass) {
      return {
        message: () => `expected ${received} not to have been called with a signal`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to have been called with a signal`,
        pass: false,
      };
    }
  },
});

// Global test helpers
global.testUtils = {
  createMockElement: (tag = 'div', props = {}) => {
    return createElement(tag, props);
  },

  createMockEvent: (type, props = {}) => {
    return new Event(type, props);
  },

  createMockSignal: (initialValue) => {
    return createSignal(initialValue);
  },

  createMockComponent: (renderFn) => {
    return createComponent(renderFn);
  },

  waitFor: (condition, timeout = 1000) => {
    return new Promise((resolve, reject) => {
      const start = Date.now();

      const check = () => {
        try {
          if (condition()) {
            resolve();
          } else if (Date.now() - start > timeout) {
            reject(new Error('Timeout waiting for condition'));
          } else {
            setTimeout(check, 10);
          }
        } catch (error) {
          reject(error);
        }
      };

      check();
    });
  },

  triggerEvent: (element, eventType, data = {}) => {
    const event = new CustomEvent(eventType, { detail: data });
    element.dispatchEvent(event);
    return event;
  },

  simulateUserInteraction: (element, action = 'click') => {
    const rect = element.getBoundingClientRect();
    const event = new MouseEvent(action, {
      view: window,
      bubbles: true,
      cancelable: true,
      clientX: rect.left + rect.width / 2,
      clientY: rect.top + rect.height / 2,
    });

    element.dispatchEvent(event);
    return event;
  },
};

// Mock fetch for tests
global.fetch = vi.fn();

// Mock console methods for cleaner test output
const originalConsole = { ...console };

beforeEach(() => {
  // Restore original console before each test
  Object.assign(console, originalConsole);
});

afterEach(() => {
  // Mock console methods after each test to reduce noise
  if (process.env.NODE_ENV === 'test') {
    console.log = vi.fn();
    console.warn = vi.fn();
    console.error = vi.fn();
    console.info = vi.fn();
    console.debug = vi.fn();
  }
});

console.log('✅ Test environment setup complete');
