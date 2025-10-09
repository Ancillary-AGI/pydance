/**
 * Shared test utilities for frontend testing.
 *
 * This module provides common test utilities and helpers
 * that can be used across all frontend test files.
 */

// Test utilities class
export class TestUtils {
    static createTestContainer() {
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);
        return container;
    }

    static cleanupTestContainer() {
        const container = document.getElementById('test-container');
        if (container) {
            container.remove();
        }
    }

    static waitForNextTick() {
        return new Promise(resolve => setTimeout(resolve, 0));
    }

    static waitFor(timeMs) {
        return new Promise(resolve => setTimeout(resolve, timeMs));
    }

    static triggerEvent(element, eventName, options = {}) {
        const event = new Event(eventName, options);
        element.dispatchEvent(event);
        return event;
    }

    static createMockComponent(name = 'MockComponent') {
        return {
            name,
            render: () => `<div data-testid="${name}-root">${name} Component</div>`,
            mount: (container) => {
                container.innerHTML = this.render();
            },
            unmount: () => {},
            update: () => {}
        };
    }

    static createMockSignal(initialValue = null) {
        return {
            value: initialValue,
            subscribers: [],
            subscribe(callback) {
                this.subscribers.push(callback);
                return () => {
                    this.subscribers = this.subscribers.filter(sub => sub !== callback);
                };
            },
            setValue(newValue) {
                this.value = newValue;
                this.subscribers.forEach(callback => callback(newValue));
            }
        };
    }

    static createMockHook(initialValue = null) {
        return {
            value: initialValue,
            setValue: (newValue) => {
                this.value = newValue;
            }
        };
    }

    static simulateUserInteraction(element, action, ...args) {
        switch (action) {
            case 'click':
                this.triggerEvent(element, 'click');
                break;
            case 'input':
                if (element.tagName === 'INPUT') {
                    element.value = args[0] || '';
                    this.triggerEvent(element, 'input');
                }
                break;
            case 'change':
                if (element.tagName === 'INPUT' || element.tagName === 'SELECT') {
                    element.value = args[0] || '';
                    this.triggerEvent(element, 'change');
                }
                break;
            case 'submit':
                this.triggerEvent(element, 'submit');
                break;
            default:
                throw new Error(`Unknown action: ${action}`);
        }
    }

    static assertElementExists(container, selector) {
        const element = container.querySelector(selector);
        if (!element) {
            throw new Error(`Element not found: ${selector}`);
        }
        return element;
    }

    static assertElementHasText(element, expectedText) {
        if (element.textContent !== expectedText) {
            throw new Error(`Expected text "${expectedText}", got "${element.textContent}"`);
        }
    }

    static assertElementHasAttribute(element, attribute, expectedValue) {
        const actualValue = element.getAttribute(attribute);
        if (actualValue !== expectedValue) {
            throw new Error(`Expected ${attribute}="${expectedValue}", got "${actualValue}"`);
        }
    }

    static measurePerformance(fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        return {
            duration: end - start,
            result
        };
    }

    static async measureAsyncPerformance(fn) {
        const start = performance.now();
        const result = await fn();
        const end = performance.now();
        return {
            duration: end - start,
            result
        };
    }
}

// Test data factories
export class TestDataFactory {
    static createUserData(overrides = {}) {
        return {
            id: Date.now(),
            username: `testuser_${Date.now()}`,
            email: `test_${Date.now()}@example.com`,
            password: 'testpass123',
            isActive: true,
            createdAt: new Date().toISOString(),
            ...overrides
        };
    }

    static createProductData(overrides = {}) {
        return {
            id: Date.now(),
            name: `Test Product ${Date.now()}`,
            price: 29.99,
            category: 'test',
            inStock: true,
            createdAt: new Date().toISOString(),
            ...overrides
        };
    }

    static createTodoData(overrides = {}) {
        return {
            id: Date.now(),
            text: `Test Todo ${Date.now()}`,
            completed: false,
            createdAt: new Date().toISOString(),
            ...overrides
        };
    }

    static createComponentProps(overrides = {}) {
        return {
            className: 'test-component',
            id: `test-${Date.now()}`,
            'data-testid': 'test-component',
            ...overrides
        };
    }
}

// Mock implementations
export class MockImplementations {
    static createMockFramework() {
        return {
            config: {},
            services: new Map(),
            stores: new Map(),
            components: new Map(),
            initialized: false,

            registerService(name, service) {
                this.services.set(name, service);
            },

            getService(name) {
                return this.services.get(name);
            },

            registerComponent(name, component) {
                this.components.set(name, component);
            },

            async mount(selector) {
                // Mock mounting logic
                this.initialized = true;
            },

            destroy() {
                this.services.clear();
                this.stores.clear();
                this.components.clear();
                this.initialized = false;
            },

            on(event, handler) {
                // Mock event subscription
                return () => {}; // Return unsubscribe function
            },

            emit(event, data) {
                // Mock event emission
            }
        };
    }

    static createMockComponent() {
        return {
            props: {},
            state: {},
            mounted: false,
            unmounted: false,

            mount(container) {
                this.mounted = true;
                if (typeof this.render === 'function') {
                    container.innerHTML = this.render();
                }
            },

            unmount() {
                this.unmounted = true;
            },

            update() {
                // Mock update logic
            },

            render() {
                return '<div>Mock Component</div>';
            }
        };
    }

    static createMockSignal(initialValue = null) {
        const subscribers = [];
        let currentValue = initialValue;

        return {
            get value() {
                return currentValue;
            },

            set value(newValue) {
                currentValue = newValue;
                subscribers.forEach(callback => callback(newValue));
            },

            subscribe(callback) {
                subscribers.push(callback);
                return () => {
                    const index = subscribers.indexOf(callback);
                    if (index > -1) {
                        subscribers.splice(index, 1);
                    }
                };
            }
        };
    }
}

// Performance testing utilities
export class PerformanceUtils {
    static async benchmark(fn, iterations = 100) {
        const times = [];

        for (let i = 0; i < iterations; i++) {
            const start = performance.now();
            await fn();
            const end = performance.now();
            times.push(end - start);
        }

        return {
            min: Math.min(...times),
            max: Math.max(...times),
            avg: times.reduce((a, b) => a + b, 0) / times.length,
            median: this.calculateMedian(times),
            total: times.reduce((a, b) => a + b, 0)
        };
    }

    static calculateMedian(numbers) {
        const sorted = [...numbers].sort((a, b) => a - b);
        const mid = Math.floor(sorted.length / 2);
        return sorted.length % 2 === 0
            ? (sorted[mid - 1] + sorted[mid]) / 2
            : sorted[mid];
    }

    static generateLoad(count = 100) {
        const data = [];
        for (let i = 0; i < count; i++) {
            data.push(TestDataFactory.createUserData({ id: i }));
        }
        return data;
    }
}

// DOM testing utilities
export class DOMTestUtils {
    static findByTestId(container, testId) {
        return container.querySelector(`[data-testid="${testId}"]`);
    }

    static findAllByTestId(container, testId) {
        return container.querySelectorAll(`[data-testid="${testId}"]`);
    }

    static findByClass(container, className) {
        return container.querySelector(`.${className}`);
    }

    static findAllByClass(container, className) {
        return container.querySelectorAll(`.${className}`);
    }

    static findByTag(container, tagName) {
        return container.querySelector(tagName);
    }

    static findAllByTag(container, tagName) {
        return container.querySelectorAll(tagName);
    }

    static simulateTyping(element, text, delay = 50) {
        return new Promise(async (resolve) => {
            element.value = '';
            element.focus();

            for (const char of text) {
                element.value += char;
                this.triggerEvent(element, 'input');
                if (delay > 0) {
                    await TestUtils.waitFor(delay);
                }
            }

            this.triggerEvent(element, 'change');
            resolve();
        });
    }

    static simulateKeyPress(element, key, modifiers = {}) {
        const event = new KeyboardEvent('keydown', {
            key,
            ctrlKey: modifiers.ctrl || false,
            shiftKey: modifiers.shift || false,
            altKey: modifiers.alt || false,
            metaKey: modifiers.meta || false
        });

        element.dispatchEvent(event);
        return event;
    }
}

// Error testing utilities
export class ErrorTestUtils {
    static expectError(fn, expectedError) {
        try {
            fn();
            throw new Error('Expected error was not thrown');
        } catch (error) {
            if (expectedError instanceof Error) {
                if (!(error instanceof Error) || error.message !== expectedError.message) {
                    throw new Error(`Expected error "${expectedError.message}", got "${error.message}"`);
                }
            } else if (typeof expectedError === 'string') {
                if (error.message !== expectedError) {
                    throw new Error(`Expected error "${expectedError}", got "${error.message}"`);
                }
            }
        }
    }

    static async expectAsyncError(fn, expectedError) {
        try {
            await fn();
            throw new Error('Expected error was not thrown');
        } catch (error) {
            if (expectedError instanceof Error) {
                if (!(error instanceof Error) || error.message !== expectedError.message) {
                    throw new Error(`Expected error "${expectedError.message}", got "${error.message}"`);
                }
            } else if (typeof expectedError === 'string') {
                if (error.message !== expectedError) {
                    throw new Error(`Expected error "${expectedError}", got "${error.message}"`);
                }
            }
        }
    }
}

// Test configuration
export const TestConfig = {
    timeout: 5000,
    retryAttempts: 3,
    performanceThreshold: 100, // milliseconds
    memoryThreshold: 50 * 1024 * 1024, // 50MB
    enableConsoleLogging: false,
    enablePerformanceMonitoring: true
};

// Global test setup
export function setupTestEnvironment() {
    // Setup global test environment
    if (typeof global !== 'undefined') {
        global.testUtils = TestUtils;
        global.testDataFactory = TestDataFactory;
        global.mockImplementations = MockImplementations;
        global.performanceUtils = PerformanceUtils;
        global.domTestUtils = DOMTestUtils;
        global.errorTestUtils = ErrorTestUtils;
        global.testConfig = TestConfig;
    }
}

// Global test cleanup
export function cleanupTestEnvironment() {
    // Cleanup global test environment
    if (typeof global !== 'undefined') {
        delete global.testUtils;
        delete global.testDataFactory;
        delete global.mockImplementations;
        delete global.performanceUtils;
        delete global.domTestUtils;
        delete global.errorTestUtils;
        delete global.testConfig;
    }
}
