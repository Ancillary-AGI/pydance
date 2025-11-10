/**
 * @fileoverview Universal Frontend Test Setup
 *
 * Framework-agnostic test environment setup for frontend testing.
 * Compatible with any frontend framework (React, Vue, Svelte, etc.).
 */

import { beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';

// Setup JSDOM environment for DOM testing
const { JSDOM } = await import('jsdom');

const dom = new JSDOM('<!DOCTYPE html><html><head></head><body></body></html>', {
  url: 'http://localhost:3000',
  pretendToBeVisual: true,
  resources: 'usable',
});

// Global DOM APIs
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// HTML Elements
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

// Core DOM APIs
global.Node = dom.window.Node;
global.Text = dom.window.Text;
global.Comment = dom.window.Comment;
global.DocumentFragment = dom.window.DocumentFragment;
global.Event = dom.window.Event;
global.CustomEvent = dom.window.CustomEvent;
global.MouseEvent = dom.window.MouseEvent;
global.KeyboardEvent = dom.window.KeyboardEvent;
global.FocusEvent = dom.window.FocusEvent;
global.EventTarget = dom.window.EventTarget;

// Browser APIs
global.requestAnimationFrame = dom.window.requestAnimationFrame || ((cb) => setTimeout(cb, 16));
global.cancelAnimationFrame = dom.window.cancelAnimationFrame || clearTimeout;
global.setTimeout = dom.window.setTimeout;
global.clearTimeout = dom.window.clearTimeout;
global.setInterval = dom.window.setInterval;
global.clearInterval = dom.window.clearInterval;

// Storage APIs
global.localStorage = dom.window.localStorage;
global.sessionStorage = dom.window.sessionStorage;

// Location and History APIs
global.location = dom.window.location;
global.history = dom.window.history;

// Web APIs
global.URL = dom.window.URL;
global.URLSearchParams = dom.window.URLSearchParams;
global.AbortController = dom.window.AbortController;
global.ResizeObserver = dom.window.ResizeObserver;
global.IntersectionObserver = dom.window.IntersectionObserver;
global.MutationObserver = dom.window.MutationObserver;
global.WebSocket = dom.window.WebSocket;

// File APIs
global.File = dom.window.File;
global.FileReader = dom.window.FileReader;
global.Blob = dom.window.Blob;
global.FormData = dom.window.FormData;

// Performance API
global.performance = {
  now: () => Date.now(),
  mark: dom.window.performance?.mark || (() => {}),
  measure: dom.window.performance?.measure || (() => {}),
  getEntriesByName: dom.window.performance?.getEntriesByName || (() => []),
  getEntriesByType: dom.window.performance?.getEntriesByType || (() => []),
  clearMarks: dom.window.performance?.clearMarks || (() => {}),
  clearMeasures: dom.window.performance?.clearMeasures || (() => {}),
};

// Crypto API
global.crypto = {
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
};

// Mock fetch by default
global.fetch = vi.fn();

// Mock Request/Response
global.Request = dom.window.Request;
global.Response = dom.window.Response;
global.Headers = dom.window.Headers;

// Test lifecycle setup
beforeAll(async () => {
  console.log('🚀 Setting up universal frontend test environment...');
});

afterAll(async () => {
  console.log('🧹 Cleaning up test environment...');
});

beforeEach(() => {
  // Reset DOM state
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Clear all mocks
  vi.clearAllMocks();

  // Reset storage
  localStorage.clear();
  sessionStorage.clear();

  // Reset fetch mock
  global.fetch.mockReset();
});

afterEach(() => {
  // Additional cleanup can be added here
});

// Universal test utilities
global.testUtils = {
  /**
   * Create a DOM element for testing
   */
  createElement: (tag, props = {}, children = []) => {
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
        element.appendChild(document.createTextNode(child));
      } else if (child instanceof Node) {
        element.appendChild(child);
      }
    });

    return element;
  },

  /**
   * Create a reactive signal for testing
   */
  createSignal: (initialValue) => {
    let value = initialValue;
    const subscribers = new Set();

    return {
      get value() {
        return value;
      },
      set value(newValue) {
        if (Object.is(value, newValue)) return;
        value = newValue;
        subscribers.forEach(subscriber => subscriber(newValue, value));
      },
      subscribe: (callback) => {
        subscribers.add(callback);
        return () => subscribers.delete(callback);
      },
      get subscriberCount() {
        return subscribers.size;
      }
    };
  },

  /**
   * Create a generic component factory
   */
  createComponent: (renderFn) => {
    return (props = {}) => ({
      props,
      render: () => renderFn(props),
      mount: (container) => {
        const html = renderFn(props);
        if (typeof container === 'string') {
          container = document.querySelector(container);
        }
        if (container) {
          container.innerHTML = html;
        }
        return container;
      },
      update: (newProps) => {
        Object.assign(props, newProps);
      }
    });
  },

  /**
   * Wait for a condition to be met
   */
  waitFor: (condition, timeout = 1000) => {
    return new Promise((resolve, reject) => {
      const start = Date.now();

      const check = () => {
        try {
          if (condition()) {
            resolve();
          } else if (Date.now() - start > timeout) {
            reject(new Error(`Condition not met within ${timeout}ms`));
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

  /**
   * Trigger a custom event on an element
   */
  triggerEvent: (element, eventType, data = {}) => {
    const event = new CustomEvent(eventType, { detail: data });
    element.dispatchEvent(event);
    return event;
  },

  /**
   * Simulate user interaction
   */
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

  /**
   * Create a test container
   */
  createTestContainer: (id = 'test-container') => {
    const container = document.createElement('div');
    container.id = id;
    container.style.cssText = `
      position: absolute;
      left: -9999px;
      top: -9999px;
      width: 1000px;
      height: 1000px;
      overflow: hidden;
    `;
    document.body.appendChild(container);
    return container;
  },

  /**
   * Clean up test containers
   */
  cleanupTestContainers: () => {
    const containers = document.querySelectorAll('[id^="test-container"]');
    containers.forEach(container => container.remove());
  }
};

// Custom matchers for universal testing
expect.extend({
  toBeVisible(received) {
    const isVisible = received.offsetWidth > 0 && received.offsetHeight > 0 &&
                     received.getClientRects().length > 0;
    return {
      pass: isVisible,
      message: () => `Expected element to ${isVisible ? 'not ' : ''}be visible`
    };
  },

  toHaveClass(received, className) {
    const hasClass = received.classList.contains(className);
    return {
      pass: hasClass,
      message: () => `Expected element to ${hasClass ? 'not ' : ''}have class "${className}"`
    };
  },

  toHaveTextContent(received, expectedText) {
    const actualText = received.textContent.trim();
    const pass = actualText === expectedText;
    return {
      pass,
      message: () => `Expected text content "${expectedText}", got "${actualText}"`
    };
  },

  toBeSignal(received) {
    const isSignal = received &&
                    typeof received.subscribe === 'function' &&
                    'value' in received;
    return {
      pass: isSignal,
      message: () => `Expected ${received} to be a signal`
    };
  }
});

console.log('✅ Universal frontend test environment ready');
