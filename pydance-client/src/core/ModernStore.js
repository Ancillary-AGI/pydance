/**
 * Modern Store - Zustand/RTK-style state management
 * Sophisticated state management with slices, async actions, and devtools
 */

import { signal, computed, effect } from './Signal.js';

// Structural sharing for performance
function structuralSharing(prev, next) {
  if (prev === next) return prev;
  if (typeof prev !== 'object' || typeof next !== 'object') return next;
  if (prev === null || next === null) return next;
  if (Array.isArray(prev) && Array.isArray(next)) {
    if (prev.length !== next.length) return next;
    let changed = false;
    const result = prev.map((item, i) => {
      const newItem = structuralSharing(item, next[i]);
      if (newItem !== item) changed = true;
      return newItem;
    });
    return changed ? result : prev;
  }
  const keys = Object.keys(next);
  let changed = false;
  const result = {};
  for (const key of keys) {
    result[key] = structuralSharing(prev[key], next[key]);
    if (result[key] !== prev[key]) changed = true;
  }
  return changed ? result : prev;
}

// Immer-like produce function with proxy
function produce(state, recipe) {
  if (state === null || typeof state !== 'object') {
    throw new Error('produce expects an object or array');
  }
  
  const changes = new Map();
  const draft = createDraft(state, changes);
  recipe(draft);
  return applyChanges(state, changes);
}

function createDraft(obj, changes, path = []) {
  if (obj === null || typeof obj !== 'object') return obj;
  
  return new Proxy(obj, {
    get(target, prop) {
      const value = target[prop];
      if (typeof value === 'object' && value !== null) {
        return createDraft(value, changes, [...path, prop]);
      }
      return value;
    },
    set(target, prop, value) {
      const fullPath = [...path, prop].join('.');
      changes.set(fullPath, value);
      return true;
    }
  });
}

function applyChanges(state, changes) {
  if (changes.size === 0) return state;
  
  const result = Array.isArray(state) ? [...state] : { ...state };
  
  for (const [path, value] of changes) {
    const keys = path.split('.');
    let current = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      current[key] = Array.isArray(current[key]) ? [...current[key]] : { ...current[key] };
      current = current[key];
    }
    
    current[keys[keys.length - 1]] = value;
  }
  
  return result;
}

// Create slice (Redux Toolkit style)
export function createSlice({ name, initialState, reducers, extraReducers }) {
  const slice = {
    name,
    initialState,
    reducers: {},
    actions: {}
  };

  // Create actions and reducers
  Object.entries(reducers).forEach(([key, reducer]) => {
    slice.actions[key] = (payload) => ({ type: `${name}/${key}`, payload });
    slice.reducers[`${name}/${key}`] = reducer;
  });

  if (extraReducers) {
    Object.assign(slice.reducers, extraReducers);
  }

  return slice;
}

// Create store (Zustand style) with middleware support
export function create(initializer) {
  let state = typeof initializer === 'function' ? {} : initializer;
  const listeners = new Set();
  const middlewares = [];
  
  const api = {
    getState: () => state,
    
    setState: (partial, replace = false) => {
      const nextState = replace
        ? (typeof partial === 'function' ? partial(state) : partial)
        : Object.assign({}, state, typeof partial === 'function' ? partial(state) : partial);
      
      // Structural sharing
      const finalState = structuralSharing(state, nextState);
      
      if (finalState !== state) {
        const prevState = state;
        state = finalState;
        listeners.forEach(listener => {
          try {
            listener(state, prevState);
          } catch (err) {
            console.error('Store listener error:', err);
          }
        });
      }
    },
    
    subscribe: (listener, selector, equalityFn = Object.is) => {
      if (selector) {
        let currentSlice = selector(state);
        const wrappedListener = (nextState, prevState) => {
          const nextSlice = selector(nextState);
          if (!equalityFn(currentSlice, nextSlice)) {
            currentSlice = nextSlice;
            listener(nextSlice, selector(prevState));
          }
        };
        listeners.add(wrappedListener);
        return () => listeners.delete(wrappedListener);
      }
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    
    destroy: () => {
      listeners.clear();
      state = {};
    },
    
    use: (middleware) => {
      middlewares.push(middleware);
    }
  };

  // Initialize with set/get
  if (typeof initializer === 'function') {
    const set = (partial, replace) => api.setState(partial, replace);
    const get = () => api.getState();
    state = initializer(set, get, api);
  }

  return api;
}

// Async thunk (RTK style)
export function createAsyncThunk(typePrefix, payloadCreator) {
  const pending = `${typePrefix}/pending`;
  const fulfilled = `${typePrefix}/fulfilled`;
  const rejected = `${typePrefix}/rejected`;

  const thunk = (arg) => async (dispatch, getState) => {
    dispatch({ type: pending, meta: { arg } });
    
    try {
      const result = await payloadCreator(arg, { dispatch, getState });
      dispatch({ type: fulfilled, payload: result, meta: { arg } });
      return result;
    } catch (error) {
      dispatch({ type: rejected, payload: error, meta: { arg }, error: true });
      throw error;
    }
  };

  thunk.pending = pending;
  thunk.fulfilled = fulfilled;
  thunk.rejected = rejected;

  return thunk;
}

// Memoized selector (Reselect style)
export function createSelector(...funcs) {
  const resultFunc = funcs.pop();
  let lastArgs = null;
  let lastResult = null;

  return (state) => {
    const args = funcs.map(f => f(state));
    
    if (lastArgs && args.every((arg, i) => arg === lastArgs[i])) {
      return lastResult;
    }

    lastArgs = args;
    lastResult = resultFunc(...args);
    return lastResult;
  };
}

// Combine slices
export function configureStore({ reducer, middleware = [], devTools = true }) {
  const slices = Object.entries(reducer);
  const initialState = {};
  
  slices.forEach(([key, slice]) => {
    initialState[key] = slice.initialState;
  });

  const state = signal(initialState);
  const listeners = new Set();
  const middlewareChain = [...middleware];

  const store = {
    getState: () => state.value,
    
    dispatch: (action) => {
      let result = action;
      
      // Apply middleware
      middlewareChain.forEach(mw => {
        result = mw(store)(store.dispatch)(result);
      });

      // Handle thunks
      if (typeof result === 'function') {
        return result(store.dispatch, store.getState);
      }

      // Apply reducers
      const newState = { ...state.value };
      slices.forEach(([key, slice]) => {
        const reducer = slice.reducers?.[action.type];
        if (reducer) {
          newState[key] = reducer(newState[key], action);
        }
      });

      state.value = newState;
      listeners.forEach(l => l(newState));

      return result;
    },

    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    }
  };

  // DevTools integration
  if (devTools && typeof window !== 'undefined' && window.__REDUX_DEVTOOLS_EXTENSION__) {
    const devTools = window.__REDUX_DEVTOOLS_EXTENSION__.connect();
    devTools.init(state.value);
    
    const originalDispatch = store.dispatch;
    store.dispatch = (action) => {
      const result = originalDispatch(action);
      devTools.send(action, store.getState());
      return result;
    };
  }

  return store;
}

// Middleware
export const thunkMiddleware = (store) => (next) => (action) => {
  if (typeof action === 'function') {
    return action(store.dispatch, store.getState);
  }
  return next(action);
};

export const loggerMiddleware = (store) => (next) => (action) => {
  console.log('dispatching', action);
  const result = next(action);
  console.log('next state', store.getState());
  return result;
};

// Persist middleware
export function persist(config, options = {}) {
  const { name, storage = localStorage, serialize = JSON.stringify, deserialize = JSON.parse } = options;
  
  return (set, get, api) => {
    // Load persisted state
    try {
      const persisted = storage.getItem(name);
      if (persisted) {
        const state = deserialize(persisted);
        set(state, true);
      }
    } catch (err) {
      console.error('Failed to load persisted state:', err);
    }
    
    // Initialize store
    const store = config(set, get, api);
    
    // Subscribe to changes
    api.subscribe((state) => {
      try {
        storage.setItem(name, serialize(state));
      } catch (err) {
        console.error('Failed to persist state:', err);
      }
    });
    
    return store;
  };
}

// Devtools middleware
export function devtools(config, options = {}) {
  return (set, get, api) => {
    const { name = 'store', enabled = true } = options;
    
    if (!enabled || typeof window === 'undefined' || !window.__REDUX_DEVTOOLS_EXTENSION__) {
      return config(set, get, api);
    }
    
    const devtools = window.__REDUX_DEVTOOLS_EXTENSION__.connect({ name });
    devtools.init(get());
    
    const wrappedSet = (partial, replace) => {
      set(partial, replace);
      devtools.send({ type: 'setState', payload: partial }, get());
    };
    
    return config(wrappedSet, get, api);
  };
}

// Immer middleware
export function immer(config) {
  return (set, get, api) => {
    const wrappedSet = (fn, replace) => {
      if (typeof fn === 'function') {
        set((state) => produce(state, fn), replace);
      } else {
        set(fn, replace);
      }
    };
    return config(wrappedSet, get, api);
  };
}

// Combine stores
export function combine(stores) {
  const combined = {};
  const listeners = new Set();
  
  Object.entries(stores).forEach(([key, store]) => {
    combined[key] = store.getState();
    store.subscribe((state) => {
      combined[key] = state;
      listeners.forEach(l => l(combined));
    });
  });
  
  return {
    getState: () => combined,
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    }
  };
}

// Shallow equality
export function shallow(a, b) {
  if (Object.is(a, b)) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) return false;
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  return keysA.every(key => Object.is(a[key], b[key]));
}
