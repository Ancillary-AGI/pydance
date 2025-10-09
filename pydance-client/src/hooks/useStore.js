/**
 * React-style hooks for store integration
 */

import { useState, useEffect, useRef, useMemo } from '~/core/Component.js';

// Use store with selector
export function useStore(store, selector = (s) => s, equalityFn) {
  const [state, setState] = useState(() => selector(store.getState()));
  const selectorRef = useRef(selector);
  const equalityRef = useRef(equalityFn);
  
  // Update refs
  selectorRef.current = selector;
  equalityRef.current = equalityFn;
  
  useEffect(() => {
    const checkForUpdates = () => {
      const newState = selectorRef.current(store.getState());
      setState(prev => {
        if (equalityRef.current) {
          return equalityRef.current(prev, newState) ? prev : newState;
        }
        return Object.is(prev, newState) ? prev : newState;
      });
    };
    
    checkForUpdates();
    return store.subscribe(checkForUpdates);
  }, [store]);
  
  return state;
}

// Use dispatch
export function useDispatch(store) {
  return useMemo(() => store.dispatch || store.setState, [store]);
}

// Use selector with memoization
export function useSelector(store, selector, equalityFn) {
  return useStore(store, selector, equalityFn);
}

// Use store actions
export function useStoreActions(store) {
  const state = store.getState();
  const actions = {};
  
  for (const key in state) {
    if (typeof state[key] === 'function') {
      actions[key] = state[key];
    }
  }
  
  return actions;
}

// Use store with shallow equality
export function useStoreShallow(store, selector) {
  return useStore(store, selector, shallowEqual);
}

function shallowEqual(a, b) {
  if (Object.is(a, b)) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) return false;
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  return keysA.every(key => Object.is(a[key], b[key]));
}
