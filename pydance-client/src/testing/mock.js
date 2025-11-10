/**
 * @fileoverview Mocking Framework for Pydance Client
 */

/**
 * Mock class for JavaScript testing
 */
export class Mock {
  constructor(name = 'Mock') {
    this._name = name;
    this._calls = [];
    this._returnValue = undefined;
    this._sideEffect = undefined;
    this._children = {};
  }

  get name() {
    return this._name;
  }

  get calls() {
    return [...this._calls];
  }

  get callCount() {
    return this._calls.length;
  }

  get returnValue() {
    return this._returnValue;
  }

  set returnValue(value) {
    this._returnValue = value;
  }

  get sideEffect() {
    return this._sideEffect;
  }

  set sideEffect(fn) {
    this._sideEffect = fn;
  }

  /**
   * Mock function call
   */
  call(...args) {
    this._calls.push(args);

    if (this._sideEffect) {
      if (typeof this._sideEffect === 'function') {
        return this._sideEffect(...args);
      }
      return this._sideEffect;
    }

    return this._returnValue;
  }

  /**
   * Reset mock state
   */
  reset() {
    this._calls.length = 0;
    this._returnValue = undefined;
    this._sideEffect = undefined;
    Object.values(this._children).forEach(child => child.reset());
  }

  /**
   * Get property or create child mock
   */
  get(target, prop) {
    if (prop in this._children) {
      return this._children[prop];
    }

    if (typeof prop === 'string' && prop !== 'then' && prop !== 'catch') {
      this._children[prop] = new Mock(`${this._name}.${prop}`);
      return this._children[prop];
    }

    return undefined;
  }
}

/**
 * Create a mock function
 */
export function createMock(name = 'mock') {
  const mock = new Mock(name);

  const mockFn = (...args) => mock.call(...args);

  // Copy mock properties to function
  Object.defineProperties(mockFn, {
    calls: { get: () => mock.calls },
    callCount: { get: () => mock.callCount },
    returnValue: {
      get: () => mock.returnValue,
      set: (value) => mock.returnValue = value
    },
    sideEffect: {
      get: () => mock.sideEffect,
      set: (fn) => mock.sideEffect = fn
    },
    reset: { value: () => mock.reset() }
  });

  // Add proxy for property access
  return new Proxy(mockFn, {
    get(target, prop) {
      if (prop in target) return target[prop];
      return mock.get(target, prop);
    }
  });
}

/**
 * Stub a method on an object
 */
export function stub(obj, methodName, implementation) {
  const original = obj[methodName];
  const mock = createMock(`${obj.constructor.name}.${methodName}`);

  if (implementation) {
    mock.sideEffect = implementation;
  }

  obj[methodName] = mock;

  return {
    restore() {
      obj[methodName] = original;
    },
    mock
  };
}

/**
 * Patch an object property
 */
export function patch(obj, prop, value) {
  const original = obj[prop];
  obj[prop] = value;

  return {
    restore() {
      obj[prop] = original;
    }
  };
}
