/**
 * @fileoverview Assertion Helpers
 */

/**
 * Custom assertion error
 */
export class AssertionError extends Error {
  constructor(message, expected, actual) {
    super(message);
    this.name = 'AssertionError';
    this.expected = expected;
    this.actual = actual;
  }
}

/**
 * Basic assertion function
 */
export function assert(condition, message = 'Assertion failed') {
  if (!condition) {
    throw new AssertionError(message);
  }
}

/**
 * Assert that two values are equal
 */
export function assertEqual(actual, expected, message = null) {
  if (actual !== expected) {
    throw new AssertionError(
      message || `Expected ${expected}, but got ${actual}`,
      expected,
      actual
    );
  }
}

/**
 * Assert that two values are deeply equal
 */
export function assertDeepEqual(actual, expected, message = null) {
  const actualStr = JSON.stringify(actual);
  const expectedStr = JSON.stringify(expected);

  if (actualStr !== expectedStr) {
    throw new AssertionError(
      message || `Expected ${expectedStr}, but got ${actualStr}`,
      expected,
      actual
    );
  }
}

/**
 * Assert that a value is truthy
 */
export function assertTruthy(value, message = null) {
  if (!value) {
    throw new AssertionError(
      message || `Expected truthy value, but got ${value}`,
      true,
      value
    );
  }
}

/**
 * Assert that a value is falsy
 */
export function assertFalsy(value, message = null) {
  if (value) {
    throw new AssertionError(
      message || `Expected falsy value, but got ${value}`,
      false,
      value
    );
  }
}

/**
 * Assert that a function throws an error
 */
export function assertThrows(fn, expectedError = null, message = null) {
  try {
    fn();
    throw new AssertionError(
      message || 'Expected function to throw an error, but it did not',
      expectedError,
      null
    );
  } catch (error) {
    if (expectedError && !(error instanceof expectedError)) {
      throw new AssertionError(
        message || `Expected function to throw ${expectedError.name}, but threw ${error.name}`,
        expectedError,
        error
      );
    }
  }
}

/**
 * Assert that a promise resolves
 */
export async function assertResolves(promise, message = null) {
  try {
    await promise;
  } catch (error) {
    throw new AssertionError(
      message || `Expected promise to resolve, but it rejected with ${error.message}`,
      'resolved',
      'rejected'
    );
  }
}

/**
 * Assert that a promise rejects
 */
export async function assertRejects(promise, expectedError = null, message = null) {
  try {
    await promise;
    throw new AssertionError(
      message || 'Expected promise to reject, but it resolved',
      'rejected',
      'resolved'
    );
  } catch (error) {
    if (expectedError && !(error instanceof expectedError)) {
      throw new AssertionError(
        message || `Expected promise to reject with ${expectedError.name}, but rejected with ${error.name}`,
        expectedError,
        error
      );
    }
  }
}

/**
 * Assert that an element has a specific class
 */
export function assertHasClass(element, className, message = null) {
  if (!element.classList.contains(className)) {
    throw new AssertionError(
      message || `Expected element to have class "${className}"`,
      className,
      element.className
    );
  }
}

/**
 * Assert that an element has specific text content
 */
export function assertTextContent(element, expectedText, message = null) {
  const actualText = element.textContent.trim();
  if (actualText !== expectedText) {
    throw new AssertionError(
      message || `Expected text content "${expectedText}", but got "${actualText}"`,
      expectedText,
      actualText
    );
  }
}

/**
 * Assert that a mock was called
 */
export function assertCalled(mock, message = null) {
  if (!mock.called) {
    throw new AssertionError(
      message || 'Expected mock to be called',
      true,
      false
    );
  }
}

/**
 * Assert that a mock was called with specific arguments
 */
export function assertCalledWith(mock, ...expectedArgs) {
  const calls = mock.calls || [];
  const found = calls.some(call =>
    call.length === expectedArgs.length &&
    call.every((arg, i) => arg === expectedArgs[i])
  );

  if (!found) {
    throw new AssertionError(
      `Expected mock to be called with [${expectedArgs.join(', ')}]`,
      expectedArgs,
      calls
    );
  }
}
