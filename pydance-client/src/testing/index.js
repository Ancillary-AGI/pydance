/**
 * @fileoverview Universal Frontend Testing Framework
 *
 * A comprehensive, framework-agnostic testing framework for frontend applications,
 * providing Jest/Vitest-like functionality and mocking capabilities.
 *
 * This framework is completely detached from any specific frontend framework
 * and can be used with React, Vue, Svelte, or any other framework.
 */

// Core testing utilities from Vitest
export { describe, it, test, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';

// Component testing (framework-agnostic)
export { createTestComponent } from './component.js';

// Reactive state testing
export { createTestSignal, signalHelpers } from './signal.js';

// DOM testing
export { createTestElement, domHelpers } from './dom.js';

// Event testing
export { createTestEvent, eventHelpers } from './events.js';

// Async testing
export { waitFor, waitForNextTick, asyncHelpers } from './async.js';

// Custom matchers
export { customMatchers } from './matchers.js';

// Fixtures and factories
export { createTestFixture, fixtureHelpers } from './fixtures.js';

// Mocking framework
export { Mock, createMock, patch, stub } from './mock.js';

// Test runners and utilities
export { TestRunner, TestSuite, TestCase } from './runner.js';

// Assertion helpers
export { assert, AssertionError } from './assertions.js';
