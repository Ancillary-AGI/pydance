/**
 * @fileoverview Test Runner and Suite Management
 */

/**
 * Test case class
 */
export class TestCase {
  constructor(name, fn, options = {}) {
    this.name = name;
    this.fn = fn;
    this.options = {
      timeout: 5000,
      retries: 0,
      ...options
    };
    this.status = 'pending'; // pending, running, passed, failed, skipped
    this.error = null;
    this.duration = 0;
  }

  async run() {
    this.status = 'running';
    const startTime = performance.now();

    try {
      await this._runWithTimeout();
      this.status = 'passed';
    } catch (error) {
      this.status = 'failed';
      this.error = error;
    } finally {
      this.duration = performance.now() - startTime;
    }
  }

  async _runWithTimeout() {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error(`Test "${this.name}" timed out after ${this.options.timeout}ms`));
      }, this.options.timeout);

      this.fn()
        .then(() => {
          clearTimeout(timeoutId);
          resolve();
        })
        .catch((error) => {
          clearTimeout(timeoutId);
          reject(error);
        });
    });
  }
}

/**
 * Test suite class
 */
export class TestSuite {
  constructor(name, options = {}) {
    this.name = name;
    this.options = {
      beforeAll: [],
      afterAll: [],
      beforeEach: [],
      afterEach: [],
      ...options
    };
    this.tests = [];
    this.status = 'pending';
    this.results = {
      passed: 0,
      failed: 0,
      skipped: 0,
      total: 0,
      duration: 0
    };
  }

  addTest(name, fn, options = {}) {
    const test = new TestCase(name, fn, options);
    this.tests.push(test);
    return test;
  }

  async run() {
    this.status = 'running';
    const startTime = performance.now();

    try {
      // Run beforeAll hooks
      for (const hook of this.options.beforeAll) {
        await hook();
      }

      // Run each test
      for (const test of this.tests) {
        // Run beforeEach hooks
        for (const hook of this.options.beforeEach) {
          await hook();
        }

        await test.run();

        // Run afterEach hooks
        for (const hook of this.options.afterEach) {
          await hook();
        }

        // Update results
        this.results[test.status]++;
        this.results.total++;
      }

      // Run afterAll hooks
      for (const hook of this.options.afterAll) {
        await hook();
      }

      this.status = 'completed';
    } catch (error) {
      this.status = 'failed';
      console.error(`Suite "${this.name}" failed:`, error);
    } finally {
      this.results.duration = performance.now() - startTime;
    }

    return this.results;
  }
}

/**
 * Test runner class
 */
export class TestRunner {
  constructor(options = {}) {
    this.options = {
      verbose: false,
      bail: false,
      timeout: 5000,
      ...options
    };
    this.suites = [];
    this.globalResults = {
      suites: { passed: 0, failed: 0, total: 0 },
      tests: { passed: 0, failed: 0, skipped: 0, total: 0 },
      duration: 0
    };
  }

  addSuite(suite) {
    this.suites.push(suite);
    return suite;
  }

  async run() {
    const startTime = performance.now();
    console.log('🚀 Starting test runner...');

    for (const suite of this.suites) {
      if (this.options.verbose) {
        console.log(`\n📋 Running suite: ${suite.name}`);
      }

      const results = await suite.run();

      // Update global results
      this.globalResults.suites.total++;
      if (suite.status === 'completed') {
        this.globalResults.suites.passed++;
      } else {
        this.globalResults.suites.failed++;
      }

      this.globalResults.tests.passed += results.passed;
      this.globalResults.tests.failed += results.failed;
      this.globalResults.tests.skipped += results.skipped;
      this.globalResults.tests.total += results.total;

      // Log suite results
      if (this.options.verbose) {
        console.log(`✅ Passed: ${results.passed}, ❌ Failed: ${results.failed}, ⏭️ Skipped: ${results.skipped}`);
      }

      // Bail on first failure if requested
      if (this.options.bail && results.failed > 0) {
        console.log('🛑 Bailing on first failure');
        break;
      }
    }

    this.globalResults.duration = performance.now() - startTime;

    // Print final results
    this._printResults();

    return this.globalResults;
  }

  _printResults() {
    const { suites, tests, duration } = this.globalResults;

    console.log('\n📊 Test Results:');
    console.log(`Suites: ${suites.passed}/${suites.total} passed`);
    console.log(`Tests: ${tests.passed}/${tests.total} passed, ${tests.failed} failed, ${tests.skipped} skipped`);
    console.log(`Duration: ${duration.toFixed(2)}ms`);

    if (tests.failed === 0) {
      console.log('🎉 All tests passed!');
    } else {
      console.log('💥 Some tests failed');
    }
  }
}

/**
 * Global test runner instance
 */
export const testRunner = new TestRunner();
