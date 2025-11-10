/**
 * @fileoverview Async Testing Utilities
 */

/**
 * Wait for a condition to be true
 */
export async function waitFor(condition, options = {}) {
  const {
    timeout = 1000,
    interval = 50,
    message = 'Condition not met within timeout'
  } = options;

  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      if (await condition()) {
        return;
      }
    } catch (error) {
      // Continue waiting
    }

    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(message);
}

/**
 * Wait for next tick (Promise.resolve())
 */
export async function waitForNextTick() {
  await Promise.resolve();
}

/**
 * Async testing helpers
 */
export const asyncHelpers = {
  /**
   * Create a delayed promise
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /**
   * Test async function timing
   */
  async timeFunction(fn, ...args) {
    const start = performance.now();
    const result = await fn(...args);
    const end = performance.now();

    return {
      result,
      duration: end - start
    };
  },

  /**
   * Create a promise that resolves after n calls
   */
  createCountdownPromise(count) {
    let resolve;
    const promise = new Promise(r => resolve = r);

    return {
      promise,
      countdown: () => {
        count--;
        if (count <= 0) {
          resolve();
        }
      }
    };
  },

  /**
   * Test promise resolution/rejection
   */
  async testPromise(promiseFactory, shouldResolve = true) {
    try {
      const result = await promiseFactory();
      if (shouldResolve) {
        return { success: true, result };
      } else {
        return { success: false, error: 'Expected promise to reject but it resolved' };
      }
    } catch (error) {
      if (shouldResolve) {
        return { success: false, error };
      } else {
        return { success: true, error };
      }
    }
  },

  /**
   * Wait for multiple async operations
   */
  async waitForAll(promises, options = {}) {
    const { timeout = 5000 } = options;

    return Promise.race([
      Promise.all(promises),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Timeout waiting for all promises')), timeout)
      )
    ]);
  }
};
