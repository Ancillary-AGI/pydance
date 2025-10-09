/**
 * @fileoverview Component System Tests - Comprehensive Component Testing
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import {
  ComponentInstance,
  createComponent,
  jsx,
  jsxs,
  Fragment,
  Context,
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
  useContext,
  useReducer,
  useImperativeHandle,
  memo
} from '~/core/Component.js';

describe('Component System', () => {
  let container;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
  });

  describe('Component Creation', () => {
    test('should create component with render function', () => {
      const TestComponent = createComponent(() => {
        return jsx('div', { children: 'Hello World' });
      });

      const component = new TestComponent();
      expect(component).toBeDefined();
      expect(typeof component.renderFn).toBe('function');
    });

    test('should handle component props', () => {
      const TestComponent = createComponent((props) => {
        return jsx('div', { children: props.message });
      });

      const component = new TestComponent({ message: 'Hello' });
      const vdom = component.rendered.value;

      expect(vdom.children).toBe('Hello');
    });

    test('should handle component mounting', () => {
      const TestComponent = createComponent(() => {
        return jsx('div', { 'data-testid': 'mounted' });
      });

      const component = new TestComponent();
      component.mount(container);

      expect(container.querySelector('[data-testid="mounted"]')).toBeTruthy();
    });
  });

  describe('Hooks System', () => {
    test('should handle useState hook', () => {
      const TestComponent = createComponent(() => {
        const [count, setCount] = useState(0);
        return jsx('div', {
          children: [
            jsx('span', { children: count }),
            jsx('button', {
              onClick: () => setCount(c => c + 1),
              children: 'Increment'
            })
          ]
        });
      });

      const component = new TestComponent();
      expect(component).toBeDefined();
    });

    test('should handle useEffect hook', () => {
      const effectFn = vi.fn();
      const cleanupFn = vi.fn();

      const TestComponent = createComponent(() => {
        const [count, setCount] = useState(0);

        useEffect(() => {
          effectFn(count);
          return cleanupFn;
        }, [count]);

        return jsx('div', { children: count });
      });

      const component = new TestComponent();
      expect(effectFn).toHaveBeenCalledWith(0);
    });

    test('should handle useMemo hook', () => {
      const computeFn = vi.fn(() => 'computed');

      const TestComponent = createComponent(() => {
        const [count] = useState(0);
        const memoized = useMemo(() => computeFn(count), [count]);

        return jsx('div', { children: memoized });
      });

      const component = new TestComponent();
      expect(computeFn).toHaveBeenCalledTimes(1);
    });

    test('should handle useCallback hook', () => {
      const TestComponent = createComponent(() => {
        const [count] = useState(0);
        const callback = useCallback(() => count, [count]);

        return jsx('button', { onClick: callback });
      });

      const component = new TestComponent();
      expect(typeof component.rendered.value.props.onClick).toBe('function');
    });

    test('should handle useRef hook', () => {
      const TestComponent = createComponent(() => {
        const ref = useRef(null);
        return jsx('div', { ref, children: 'test' });
      });

      const component = new TestComponent();
      expect(component.rendered.value.props.ref).toBeDefined();
    });

    test('should handle useReducer hook', () => {
      const reducer = (state, action) => {
        switch (action.type) {
          case 'increment':
            return { count: state.count + 1 };
          default:
            return state;
        }
      };

      const TestComponent = createComponent(() => {
        const [state, dispatch] = useReducer(reducer, { count: 0 });
        return jsx('div', {
          children: [
            jsx('span', { children: state.count }),
            jsx('button', {
              onClick: () => dispatch({ type: 'increment' }),
              children: 'Increment'
            })
          ]
        });
      });

      const component = new TestComponent();
      expect(component).toBeDefined();
    });
  });

  describe('Context System', () => {
    test('should handle context creation and usage', () => {
      const ThemeContext = new Context('light');

      const ThemeProvider = createComponent((props) => {
        return jsx(ThemeContext.Provider, {
          value: props.theme,
          children: props.children
        });
      });

      const ThemeConsumer = createComponent(() => {
        const theme = useContext(ThemeContext);
        return jsx('div', {
          'data-theme': theme,
          children: `Current theme: ${theme}`
        });
      });

      const App = createComponent(() => {
        return jsx(ThemeProvider, {
          theme: 'dark',
          children: jsx(ThemeConsumer)
        });
      });

      const component = new App();
      expect(component).toBeDefined();
    });
  });

  describe('JSX Runtime', () => {
    test('should create JSX elements', () => {
      const element = jsx('div', {
        className: 'test',
        children: 'Hello'
      });

      expect(element.tagName).toBe('div');
      expect(element.props.className).toBe('test');
      expect(element.children).toBe('Hello');
    });

    test('should create JSX fragments', () => {
      const fragment = jsx(Fragment, {
        children: [
          jsx('div', { children: 'First' }),
          jsx('div', { children: 'Second' })
        ]
      });

      expect(fragment.children).toHaveLength(2);
    });

    test('should handle nested JSX', () => {
      const nested = jsx('div', {
        children: jsx('span', {
          children: jsx('strong', {
            children: 'Bold text'
          })
        })
      });

      expect(nested.children.children.children).toBe('Bold text');
    });
  });

  describe('Component Memoization', () => {
    test('should memoize components correctly', () => {
      const renderFn = vi.fn(() => jsx('div', { children: 'test' }));
      const MemoizedComponent = memo(createComponent(renderFn));

      const component1 = new MemoizedComponent({ prop: 'value1' });
      const component2 = new MemoizedComponent({ prop: 'value1' });

      // Should reuse the same render function for same props
      expect(renderFn).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error Handling', () => {
    test('should handle component errors gracefully', () => {
      const ErrorComponent = createComponent(() => {
        throw new Error('Component error');
      });

      expect(() => {
        const component = new ErrorComponent();
      }).toThrow('Component error');
    });

    test('should handle hook errors', () => {
      const BadHookComponent = createComponent(() => {
        // This should throw an error outside of component context
        expect(() => useState(0)).toThrow();
      });

      expect(() => {
        const component = new BadHookComponent();
      }).toThrow();
    });
  });

  describe('Lifecycle Management', () => {
    test('should handle component mounting and unmounting', () => {
      const mountFn = vi.fn();
      const unmountFn = vi.fn();

      const LifecycleComponent = createComponent(() => {
        useEffect(() => {
          mountFn();
          return () => unmountFn();
        }, []);

        return jsx('div', { children: 'lifecycle' });
      });

      const component = new LifecycleComponent();
      component.mount(container);

      expect(mountFn).toHaveBeenCalledTimes(1);

      component.unmount();
      expect(unmountFn).toHaveBeenCalledTimes(1);
    });
  });

  describe('Performance Benchmarks', () => {
    test('should create components efficiently', () => {
      const start = performance.now();

      for (let i = 0; i < 1000; i++) {
        const TestComponent = createComponent(() => jsx('div', { children: i }));
        new TestComponent();
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(100);
    });

    test('should handle large component trees', () => {
      const createNestedComponent = (depth) => {
        if (depth === 0) {
          return jsx('div', { children: 'leaf' });
        }

        return jsx('div', {
          children: Array.from({ length: 5 }, (_, i) =>
            createNestedComponent(depth - 1)
          )
        });
      };

      const start = performance.now();
      const component = createComponent(() => createNestedComponent(10));
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });

    test('should handle rapid re-renders', () => {
      const TestComponent = createComponent(() => {
        const [count, setCount] = useState(0);
        return jsx('div', { children: count });
      });

      const component = new TestComponent();

      const start = performance.now();

      for (let i = 0; i < 100; i++) {
        component.props.value = { count: i };
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(50);
    });
  });

  describe('Complex State Management', () => {
    test('should handle complex nested state', () => {
      const ComplexComponent = createComponent(() => {
        const [state, setState] = useState({
          user: {
            profile: {
              name: 'John',
              settings: {
                theme: 'dark',
                notifications: true
              }
            }
          },
          posts: []
        });

        return jsx('div', {
          children: [
            jsx('span', { children: state.user.profile.name }),
            jsx('button', {
              onClick: () => setState(prev => ({
                ...prev,
                user: {
                  ...prev.user,
                  profile: {
                    ...prev.user.profile,
                    settings: {
                      ...prev.user.profile.settings,
                      theme: 'light'
                    }
                  }
                }
              })),
              children: 'Change Theme'
            })
          ]
        });
      });

      const component = new ComplexComponent();
      expect(component).toBeDefined();
    });

    test('should handle multiple state updates', () => {
      const MultiStateComponent = createComponent(() => {
        const [count, setCount] = useState(0);
        const [name, setName] = useState('test');
        const [items, setItems] = useState([]);

        return jsx('div', {
          children: [
            jsx('span', { children: `${name}: ${count}` }),
            jsx('button', {
              onClick: () => {
                setCount(c => c + 1);
                setName('updated');
                setItems(prev => [...prev, count + 1]);
              },
              children: 'Update All'
            })
          ]
        });
      });

      const component = new MultiStateComponent();
      expect(component).toBeDefined();
    });
  });

  describe('Event Handling', () => {
    test('should handle DOM events', () => {
      const clickHandler = vi.fn();

      const EventComponent = createComponent(() => {
        return jsx('button', {
          onClick: clickHandler,
          children: 'Click me'
        });
      });

      const component = new EventComponent();
      component.mount(container);

      const button = container.querySelector('button');
      button.click();

      expect(clickHandler).toHaveBeenCalled();
    });

    test('should handle custom events', () => {
      const customHandler = vi.fn();

      const CustomEventComponent = createComponent(() => {
        useEffect(() => {
          const handleCustomEvent = (event) => {
            customHandler(event.detail);
          };

          container.addEventListener('custom-event', handleCustomEvent);
          return () => container.removeEventListener('custom-event', handleCustomEvent);
        }, []);

        return jsx('div', { children: 'Custom Event Component' });
      });

      const component = new CustomEventComponent();
      component.mount(container);

      const event = new CustomEvent('custom-event', { detail: 'test-data' });
      container.dispatchEvent(event);

      expect(customHandler).toHaveBeenCalledWith('test-data');
    });
  });

  describe('Component Composition', () => {
    test('should compose components correctly', () => {
      const ChildComponent = createComponent((props) => {
        return jsx('span', { children: `Child: ${props.text}` });
      });

      const ParentComponent = createComponent(() => {
        return jsx('div', {
          children: [
            jsx(ChildComponent, { text: 'Hello' }),
            jsx(ChildComponent, { text: 'World' })
          ]
        });
      });

      const component = new ParentComponent();
      const vdom = component.rendered.value;

      expect(vdom.children).toHaveLength(2);
      expect(vdom.children[0].children).toBe('Child: Hello');
      expect(vdom.children[1].children).toBe('Child: World');
    });

    test('should handle conditional rendering', () => {
      const ConditionalComponent = createComponent(() => {
        const [show, setShow] = useState(true);

        return jsx('div', {
          children: show ? jsx('span', { children: 'Visible' }) : null
        });
      });

      const component = new ConditionalComponent();
      let vdom = component.rendered.value;

      expect(vdom.children).toBeTruthy();

      component.props.value = { show: false };
      vdom = component.rendered.value;

      expect(vdom.children).toBeNull();
    });
  });

  describe('Memory Management', () => {
    test('should cleanup component resources', () => {
      const cleanupFn = vi.fn();

      const CleanupComponent = createComponent(() => {
        useEffect(() => {
          return cleanupFn;
        }, []);

        return jsx('div', { children: 'cleanup test' });
      });

      const component = new CleanupComponent();
      component.mount(container);

      component.unmount();
      expect(cleanupFn).toHaveBeenCalledTimes(1);
    });

    test('should handle component destruction', () => {
      const TestComponent = createComponent(() => {
        const [count] = useState(0);
        return jsx('div', { children: count });
      });

      const component = new TestComponent();
      component.mount(container);

      expect(component.mounted).toBe(true);

      component.unmount();
      expect(component.mounted).toBe(false);
    });
  });
});
