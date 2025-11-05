/**
 * @fileoverview Client-side Logging System
 * Provides comprehensive logging capabilities for Pydance Client
 *
 * @description
 * This module implements a client-side logging system that integrates
 * with the server-side logging and provides developer tools for debugging.
 *
 * Features:
 * - Multiple log levels (DEBUG, INFO, WARN, ERROR)
 * - Structured logging with context
 * - Performance monitoring
 * - Remote logging to server
 * - Development tools integration
 *
 * @author Pydance Framework Team
 * @version 0.1.0
 * @license MIT
 */

// Log levels
export const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  OFF: 4
};

// Log level names
const LOG_LEVEL_NAMES = {
  [LOG_LEVELS.DEBUG]: 'DEBUG',
  [LOG_LEVELS.INFO]: 'INFO',
  [LOG_LEVELS.WARN]: 'WARN',
  [LOG_LEVELS.ERROR]: 'ERROR'
};

// Global configuration
let config = {
  level: LOG_LEVELS.INFO,
  enableConsole: true,
  enableRemote: false,
  remoteEndpoint: '/api/logs',
  enablePerformance: true,
  maxLogs: 1000,
  enableStackTrace: false,
  filters: [],
  formatters: []
};

// Log storage
let logs = [];
let logId = 0;

// Performance tracking
const performanceMarks = new Map();

// Logger class
export class Logger {
  constructor(name, options = {}) {
    this.name = name;
    this.level = options.level || config.level;
    this.context = options.context || {};
    this.filters = options.filters || [];
    this.formatters = options.formatters || [];
  }

  debug(message, ...args) {
    this._log(LOG_LEVELS.DEBUG, message, args);
  }

  info(message, ...args) {
    this._log(LOG_LEVELS.INFO, message, args);
  }

  warn(message, ...args) {
    this._log(LOG_LEVELS.WARN, message, args);
  }

  error(message, ...args) {
    this._log(LOG_LEVELS.ERROR, message, args);
  }

  _log(level, message, args) {
    if (level < this.level || level < config.level) return;

    // Apply filters
    if (!this._passesFilters(level, message, args)) return;

    const logEntry = this._createLogEntry(level, message, args);

    // Store log
    logs.push(logEntry);
    if (logs.length > config.maxLogs) {
      logs.shift();
    }

    // Apply formatters
    const formattedEntry = this._applyFormatters(logEntry);

    // Console output
    if (config.enableConsole) {
      this._consoleOutput(formattedEntry);
    }

    // Remote logging
    if (config.enableRemote) {
      this._remoteLog(formattedEntry);
    }

    // Emit event for devtools
    if (window && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent('pydance:log', { detail: formattedEntry }));
    }
  }

  _createLogEntry(level, message, args) {
    const now = new Date();
    const entry = {
      id: ++logId,
      timestamp: now.toISOString(),
      level,
      levelName: LOG_LEVEL_NAMES[level],
      logger: this.name,
      message,
      args: args.length > 0 ? args : undefined,
      context: { ...this.context },
      stack: config.enableStackTrace ? new Error().stack : undefined,
      performance: config.enablePerformance ? this._getPerformanceData() : undefined
    };

    return entry;
  }

  _passesFilters(level, message, args) {
    // Global filters
    for (const filter of config.filters) {
      if (!filter(level, message, args, this.name)) return false;
    }

    // Logger-specific filters
    for (const filter of this.filters) {
      if (!filter(level, message, args, this.name)) return false;
    }

    return true;
  }

  _applyFormatters(entry) {
    let formatted = entry;

    // Global formatters
    for (const formatter of config.formatters) {
      formatted = formatter(formatted);
    }

    // Logger-specific formatters
    for (const formatter of this.formatters) {
      formatted = formatter(formatted);
    }

    return formatted;
  }

  _consoleOutput(entry) {
    const prefix = `[${entry.timestamp}] ${entry.levelName} ${entry.logger}`;
    const message = entry.args ? `${entry.message} ${JSON.stringify(entry.args)}` : entry.message;

    switch (entry.level) {
      case LOG_LEVELS.DEBUG:
        console.debug(`${prefix}: ${message}`, entry.context);
        break;
      case LOG_LEVELS.INFO:
        console.info(`${prefix}: ${message}`, entry.context);
        break;
      case LOG_LEVELS.WARN:
        console.warn(`${prefix}: ${message}`, entry.context);
        break;
      case LOG_LEVELS.ERROR:
        console.error(`${prefix}: ${message}`, entry.context);
        if (entry.stack) console.error(entry.stack);
        break;
    }
  }

  async _remoteLog(entry) {
    try {
      await fetch(config.remoteEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      console.warn('Failed to send log to remote endpoint:', error);
    }
  }

  _getPerformanceData() {
    if (!window.performance) return null;

    return {
      memory: window.performance.memory ? {
        used: window.performance.memory.usedJSHeapSize,
        total: window.performance.memory.totalJSHeapSize,
        limit: window.performance.memory.jsHeapSizeLimit
      } : undefined,
      timing: window.performance.timing ? {
        loadTime: window.performance.timing.loadEventEnd - window.performance.timing.navigationStart,
        domReady: window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart
      } : undefined
    };
  }

  // Context management
  withContext(context) {
    return new Logger(this.name, {
      ...this.options,
      context: { ...this.context, ...context }
    });
  }

  child(name) {
    return new Logger(`${this.name}.${name}`, {
      ...this.options,
      context: { ...this.context }
    });
  }

  // Performance monitoring
  startTimer(label) {
    if (!config.enablePerformance) return () => {};

    const startTime = performance.now();
    const mark = `${this.name}:${label}:${Date.now()}`;

    performanceMarks.set(mark, startTime);

    return () => {
      const endTime = performance.now();
      const duration = endTime - startTime;

      this.info(`Timer ${label} completed`, { duration: `${duration.toFixed(2)}ms` });

      performanceMarks.delete(mark);

      return duration;
    };
  }

  measure(label, fn) {
    const endTimer = this.startTimer(label);
    try {
      return fn();
    } finally {
      endTimer();
    }
  }

  async measureAsync(label, fn) {
    const endTimer = this.startTimer(label);
    try {
      return await fn();
    } finally {
      endTimer();
    }
  }
}

// Logger factory
const loggers = new Map();

export function getLogger(name) {
  if (!loggers.has(name)) {
    loggers.set(name, new Logger(name));
  }
  return loggers.get(name);
}

// Convenience functions
export const logger = {
  debug: (message, ...args) => getLogger('pydance').debug(message, ...args),
  info: (message, ...args) => getLogger('pydance').info(message, ...args),
  warn: (message, ...args) => getLogger('pydance').warn(message, ...args),
  error: (message, ...args) => getLogger('pydance').error(message, ...args)
};

// Configuration
export function configure(options = {}) {
  config = { ...config, ...options };

  // Update existing loggers
  for (const logger of loggers.values()) {
    logger.level = config.level;
  }
}

export function setLevel(level) {
  config.level = level;
}

export function enableRemote(endpoint) {
  config.enableRemote = true;
  config.remoteEndpoint = endpoint;
}

export function disableRemote() {
  config.enableRemote = false;
}

// Filters
export function addFilter(filter) {
  config.filters.push(filter);
}

export function clearFilters() {
  config.filters = [];
}

// Formatters
export function addFormatter(formatter) {
  config.formatters.push(formatter);
}

export function clearFormatters() {
  config.formatters = [];
}

// Log retrieval for debugging
export function getLogs(level = null, limit = 100) {
  let filteredLogs = logs;

  if (level !== null) {
    filteredLogs = logs.filter(log => log.level >= level);
  }

  return filteredLogs.slice(-limit);
}

export function clearLogs() {
  logs = [];
}

// Performance utilities
export function startGlobalTimer(label) {
  return getLogger('performance').startTimer(label);
}

export function measureGlobal(label, fn) {
  return getLogger('performance').measure(label, fn);
}

export async function measureGlobalAsync(label, fn) {
  return getLogger('performance').measureAsync(label, fn);
}

// Development tools integration
export const devtools = {
  getLogs,
  clearLogs,
  getConfig: () => ({ ...config }),
  getLoggerStats: () => ({
    totalLoggers: loggers.size,
    totalLogs: logs.length,
    config: { ...config }
  }),

  // Chrome DevTools integration
  installDevTools() {
    if (typeof window === 'undefined') return;

    // Add to window for console access
    window.pydanceLogs = {
      getLogs,
      clearLogs,
      getLogger: getLogger,
      configure,
      devtools: this
    };

    console.log('Pydance logging devtools installed. Access via window.pydanceLogs');
  }
};

// Auto-install devtools in development
if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
  devtools.installDevTools();
}

// Export default
export default {
  Logger,
  getLogger,
  logger,
  configure,
  setLevel,
  enableRemote,
  disableRemote,
  addFilter,
  clearFilters,
  addFormatter,
  clearFormatters,
  getLogs,
  clearLogs,
  startGlobalTimer,
  measureGlobal,
  measureGlobalAsync,
  devtools,
  LOG_LEVELS
};
