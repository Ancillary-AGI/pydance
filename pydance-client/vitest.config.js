import { defineConfig } from 'vitest/config';
import { resolve } from 'path';

export default defineConfig({
  test: {
    // Environment
    environment: 'jsdom',
    globals: true,
    setupFiles: [resolve(__dirname, 'tests/setup.js')],

    // Include patterns
    include: [
      'tests/**/*.{test,spec}.{js,ts,jsx,tsx}',
      'src/**/*.{test,spec}.{js,ts,jsx,tsx}'
    ],

    // Exclude patterns
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/coverage/**',
      '**/*.d.ts',
      '**/vite.config.*',
      '**/tailwind.config.*',
      '**/postcss.config.*'
    ],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'tests/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/vite.config.*',
        '**/index.html',
        '**/examples/**',
        'scripts/**',
        'docs/**',
        'coverage/**'
      ],
      all: true,
      lines: 85,
      functions: 85,
      branches: 80,
      statements: 85,
      // Include source files in coverage
      include: [
        'src/**/*.{js,ts,jsx,tsx}'
      ]
    },

    // Performance optimizations
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        isolate: true
      }
    },

    // Test environment options
    environmentOptions: {
      jsdom: {
        resources: 'usable',
        runScripts: 'dangerously',
        pretendToBeVisual: true,
        html: `<!DOCTYPE html>
<html>
<head>
  <title>Pydance Client Tests</title>
</head>
<body>
  <div id="app"></div>
  <div id="test-root"></div>
</body>
</html>`
      }
    },

    // Reporter configuration
    reporter: process.env.CI ? ['verbose', 'github-actions'] : ['verbose'],

    // Watch mode configuration
    watch: {
      include: ['src/**/*', 'tests/**/*'],
      exclude: ['dist/**', 'node_modules/**', 'coverage/**']
    },

    // Test timeout
    testTimeout: 10000,

    // Hook timeout
    hookTimeout: 10000,

    // Bail out after first test failure in CI
    bail: process.env.CI ? 1 : 0,

    // Retry configuration
    retry: process.env.CI ? 2 : 0,

    // Silent mode for cleaner output
    silent: false,

    // Log heap usage
    logHeapUsage: true,

    // Clear mocks between tests
    clearMocks: true,

    // Restore mocks between tests
    restoreMocks: true,

    // Unmocked module paths
    unstubbedModulePaths: [],

    // Global test configuration
    globals: true,

    // Sequence configuration for tests that depend on each other
    sequence: {
      shuffle: false,
      concurrent: false
    },

    // Benchmark configuration
    benchmark: {
      include: ['**/*.{bench,benchmark}.{js,ts}'],
      exclude: ['node_modules', 'dist'],
      reporter: ['verbose']
    }
  },

  // Define global constants for tests
  define: {
    __TEST__: true,
    __DEV__: false,
    __PROD__: false
  },

  // Resolve configuration for tests
  resolve: {
    alias: {
      '~': resolve(__dirname, 'src'),
      '#': resolve(__dirname, 'src'),
      '~/core': resolve(__dirname, 'src/core'),
      '~/components': resolve(__dirname, 'src/components'),
      '~/services': resolve(__dirname, 'src/services'),
      '~/stores': resolve(__dirname, 'src/stores'),
      '~/hooks': resolve(__dirname, 'src/hooks'),
      '~/utils': resolve(__dirname, 'src/utils'),
      '~/types': resolve(__dirname, 'src/types'),
      '~/tests': resolve(__dirname, 'tests'),
      '~/mocks': resolve(__dirname, 'tests/mocks')
    }
  },

  // Optimize dependencies for testing
  optimizeDeps: {
    include: [
      '~/core/Signal.js',
      '~/core/Component.js',
      '~/core/JSX.js'
    ],
    exclude: ['__tests__']
  },

  // ESBuild configuration for tests
  esbuild: {
    target: 'es2022',
    minify: false,
    sourcemap: true,
    legalComments: 'none'
  }
});
