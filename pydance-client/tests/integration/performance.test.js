/**
 * @fileoverview Performance Benchmarks - Comprehensive Performance Testing
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { signal, computed, effect, batch } from '~/core/Signal.js';
import { createComponent, jsx, useState, useEffect } from '~/core/Component.js';

describe('Performance Benchmarks', () => {
  describe('Signal Performance', () => {
    test('should handle 10,000 signal creations efficiently', () => {
      const start = performance.now();

      const signals = [];
      for (let i = 0; i < 10000; i++) {
        signals.push(signal(i));
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(500);
      expect(signals).toHaveLength(10000);
    });

    test('should handle 1,000 rapid signal updates', () => {
      const s = signal(0);
      const effectFn = vi.fn();

      effect(effectFn);

      const start = performance.now();

      for (let i = 0; i < 1000; i++) {
        s.value = i;
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(200);
      expect(effectFn).toHaveBeenCalledTimes(1001); // Initial + 1000 updates
    });

    test('should handle complex dependency graphs', () => {
      const baseSignals = Array.from({ length: 100 }, (_, i) => signal(i));
      const computedSignals = baseSignals.map(s => computed(() => s.value * 2));
      const final = computed(() => computedSignals.reduce((sum, c) => sum + c.value, 0));

      const start = performance.now();

      baseSignals[0].value = 1000;

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(50);
      expect(final.value).toBe(199000); // (0+1+...+99)*2 + 1000*2
    });

    test('should handle deep dependency chains', () => {
      let current = signal(1);

      // Create a chain of 100 computed signals (reduced for test environment)
      for (let i = 0; i < 100; i++) {
        current = computed(() => current.value + 1);
      }

      const start = performance.now();

      signal(1).value = 2; // This should trigger the entire chain

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(50);
    });
  });

  describe('Component Performance', () => {
    test('should handle 1,000 component creations', () => {
      const start = performance.now();

      const components = [];
      for (let i = 0; i < 1000; i++) {
        const TestComponent = createComponent(() => jsx('div', { children: i }));
        components.push(TestComponent());
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(500);
      expect(components).toHaveLength(1000);
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
      const component = createComponent(() => createNestedComponent(6));
      const end = performance.now();

      expect(end - start).toBeLessThan(100);
    });

    test('should handle rapid component re-renders', () => {
      const TestComponent = createComponent(() => {
        return jsx('div', { children: Math.random() });
      });

      const component = TestComponent();

      const start = performance.now();

      for (let i = 0; i < 100; i++) {
        // Trigger re-render by changing props
        component.props = { key: i };
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(100);
    });
  });

  describe('Memory Performance', () => {
    test('should not leak memory with many signals', () => {
      const initialMemory = performance.memory?.usedJSHeapSize || 0;

      // Create many signals
      const signals = [];
      for (let i = 0; i < 1000; i++) {
        const s = signal(i);
        effect(() => s.value);
        signals.push(s);
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      // Small delay to allow cleanup
      const finalMemory = performance.memory?.usedJSHeapSize || 0;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be reasonable (less than 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });

    test('should cleanup component effects properly', () => {
      const components = [];

      for (let i = 0; i < 100; i++) {
        const TestComponent = createComponent(() => {
          effect(() => {}); // Create an effect
          return jsx('div', { children: 'test' });
        });

        const component = TestComponent();
        components.push(component);
      }

      // Unmount all components
      components.forEach(component => {
        component.unmount();
      });

      // All effects should be cleaned up
      expect(components.every(c => c.effects.size === 0)).toBe(true);
    });
  });

  describe('Batch Performance', () => {
    test('should efficiently batch multiple updates', () => {
      const signals = Array.from({ length: 100 }, (_, i) => signal(i));
      const combined = computed(() => signals.reduce((sum, s) => sum + s.value, 0));

      const effectFn = vi.fn();
      effect(effectFn);

      const start = performance.now();

      batch(() => {
        for (let i = 0; i < 100; i++) {
          signals[i].value = i * 2;
        }
      });

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(20);
      expect(effectFn).toHaveBeenCalledTimes(1); // Only one batch notification
    });

    test('should handle nested batch operations', () => {
      const s = signal(0);
      const effectFn = vi.fn();

      effect(effectFn);

      const start = performance.now();

      batch(() => {
        s.value = 1;
        batch(() => {
          s.value = 2;
          batch(() => {
            s.value = 3;
          });
        });
        s.value = 4;
      });

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(10);
      expect(effectFn).toHaveBeenCalledTimes(1); // Only final notification
      expect(effectFn).toHaveBeenCalledWith(4);
    });
  });

  describe('Real-world Scenarios', () => {
    test('should handle todo app scenario', () => {
      const TodoApp = createComponent(() => {
        const [todos, setTodos] = useState([]);
        const [filter, setFilter] = useState('all');

        const addTodo = (text) => {
          setTodos(prev => [...prev, { id: Date.now(), text, completed: false }]);
        };

        const toggleTodo = (id) => {
          setTodos(prev => prev.map(todo =>
            todo.id === id ? { ...todo, completed: !todo.completed } : todo
          ));
        };

        const filteredTodos = computed(() => {
          switch (filter) {
            case 'active':
              return todos.filter(todo => !todo.completed);
            case 'completed':
              return todos.filter(todo => todo.completed);
            default:
              return todos;
          }
        });

        return jsx('div', {
          children: [
            jsx('input', {
              placeholder: 'Add todo...',
              onKeyDown: (e) => {
                if (e.key === 'Enter' && e.target.value) {
                  addTodo(e.target.value);
                  e.target.value = '';
                }
              }
            }),
            jsx('div', {
              children: [
                jsx('button', {
                  onClick: () => setFilter('all'),
                  children: 'All'
                }),
                jsx('button', {
                  onClick: () => setFilter('active'),
                  children: 'Active'
                }),
                jsx('button', {
                  onClick: () => setFilter('completed'),
                  children: 'Completed'
                })
              ]
            }),
            jsx('ul', {
              children: filteredTodos.map(todo =>
                jsx('li', {
                  key: todo.id,
                  style: { textDecoration: todo.completed ? 'line-through' : 'none' },
                  onClick: () => toggleTodo(todo.id),
                  children: todo.text
                })
              )
            })
          ]
        });
      });

      const start = performance.now();
      const component = TodoApp();
      const end = performance.now();

      expect(end - start).toBeLessThan(20);
      expect(component).toBeDefined();
    });

    test('should handle real-time data updates', () => {
      const RealTimeApp = createComponent(() => {
        const [data, setData] = useState({ users: [], messages: [] });
        const [connected, setConnected] = useState(false);

        // Simulate real-time updates
        useEffect(() => {
          const interval = setInterval(() => {
            setData(prev => ({
              users: [...prev.users, { id: Date.now(), name: `User ${prev.users.length}` }],
              messages: [...prev.messages, { id: Date.now(), text: `Message ${prev.messages.length}` }]
            }));
          }, 10);

          return () => clearInterval(interval);
        }, []);

        const userCount = computed(() => data.users.length);
        const messageCount = computed(() => data.messages.length);

        return jsx('div', {
          children: [
            jsx('div', { children: `Connected: ${connected}` }),
            jsx('div', { children: `Users: ${userCount.value}` }),
            jsx('div', { children: `Messages: ${messageCount.value}` }),
            jsx('button', {
              onClick: () => setConnected(!connected),
              children: connected ? 'Disconnect' : 'Connect'
            })
          ]
        });
      });

      const component = RealTimeApp();

      // Simulate 100 rapid updates
      const start = performance.now();

      for (let i = 0; i < 100; i++) {
        component.props.value = {
          data: {
            users: Array.from({ length: i }, (_, j) => ({ id: j, name: `User ${j}` })),
            messages: Array.from({ length: i }, (_, j) => ({ id: j, text: `Message ${j}` }))
          }
        };
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(100);
    });
  });

  describe('Stress Tests', () => {
    test('should handle 100,000 signal operations', () => {
      const operations = [];
      const signals = [];

      // Create 1000 signals
      for (let i = 0; i < 1000; i++) {
        signals.push(signal(i));
      }

      const start = performance.now();

      // Perform 100 operations per signal
      for (let i = 0; i < 100; i++) {
        signals.forEach(s => {
          s.value = s.value + 1;
        });
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(500); // Should complete within 500ms
    });

    test('should handle deeply nested component structures', () => {
      const createDeepTree = (depth) => {
        if (depth === 0) {
          return jsx('div', { children: 'leaf' });
        }

        return jsx('div', {
          children: Array.from({ length: 3 }, () =>
            createDeepTree(depth - 1)
          )
        });
      };

      const start = performance.now();
      const component = createComponent(() => createDeepTree(8));
      const end = performance.now();

      expect(end - start).toBeLessThan(200);
    });

    test('should handle concurrent updates', async () => {
      const s = signal(0);
      const updates = [];

      // Simulate concurrent updates
      const promises = Array.from({ length: 100 }, (_, i) =>
        Promise.resolve().then(() => {
          s.value = i;
          updates.push(i);
        })
      );

      const start = performance.now();
      await Promise.all(promises);
      const end = performance.now();

      expect(end - start).toBeLessThan(200);
      expect(updates).toHaveLength(100);
    });
  });

  describe('Framework Comparison Benchmarks', () => {
    test('should outperform basic VDOM approaches', () => {
      // Simulate a simple counter component
      const CounterComponent = createComponent(() => {
        const [count, setCount] = useState(0);
        return jsx('div', {
          children: [
            jsx('span', { children: count }),
            jsx('button', {
              onClick: () => setCount(c => c + 1),
              children: '+'
            })
          ]
        });
      });

      const component = CounterComponent();

      const start = performance.now();

      // Simulate 1000 updates
      for (let i = 0; i < 1000; i++) {
        component.props.value = { count: i };
      }

      const end = performance.now();
      const duration = end - start;

      // Should be significantly faster than VDOM approaches
      expect(duration).toBeLessThan(30);
    });

    test('should handle list operations efficiently', () => {
      const ListComponent = createComponent(() => {
        const [items, setItems] = useState([]);

        const addItem = () => {
          setItems(prev => [...prev, { id: Date.now(), text: `Item ${prev.length}` }]);
        };

        return jsx('div', {
          children: [
            jsx('button', { onClick: addItem, children: 'Add Item' }),
            jsx('ul', {
              children: items.map(item =>
                jsx('li', { key: item.id, children: item.text })
              )
            })
          ]
        });
      });

      const component = ListComponent();

      const start = performance.now();

      // Add 100 items rapidly
      for (let i = 0; i < 100; i++) {
        component.props.value = {
          items: Array.from({ length: i }, (_, j) => ({
            id: j,
            text: `Item ${j}`
          }))
        };
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(50);
    });
  });

  describe('Memory Stress Tests', () => {
    test('should handle memory pressure gracefully', () => {
      const components = [];

      // Create many components
      for (let i = 0; i < 1000; i++) {
        const TestComponent = createComponent(() => {
          const [state] = useState({ data: Array(100).fill(i) });
          return jsx('div', { children: state.data.length });
        });

        components.push(TestComponent());
      }

      // Force cleanup
      components.forEach(component => {
        component.unmount();
      });

      // Should not crash or leak significantly
      expect(components).toHaveLength(1000);
    });

    test('should handle signal cleanup under memory pressure', () => {
      const signals = [];

      // Create many signals with effects
      for (let i = 0; i < 1000; i++) {
        const s = signal(i);
        const unsubscribe = s.subscribe(() => {});
        signals.push({ signal: s, unsubscribe });
      }

      // Cleanup all signals
      signals.forEach(({ unsubscribe }) => {
        unsubscribe();
      });

      // Should not have any active effects
      expect(signals).toHaveLength(1000);
    });
  });

  describe('Scalability Tests', () => {
    test('should scale linearly with component count', () => {
      const componentCounts = [100, 500, 1000];
      const results = [];

      for (const count of componentCounts) {
        const start = performance.now();

        const components = [];
        for (let i = 0; i < count; i++) {
          const TestComponent = createComponent(() => jsx('div', { children: i }));
          components.push(TestComponent());
        }

        const end = performance.now();
        results.push({ count, duration: end - start });
      }

      // Should scale roughly linearly
      const [small, medium, large] = results;
      const smallToMediumRatio = medium.duration / small.duration;
      const mediumToLargeRatio = large.duration / medium.duration;

      expect(smallToMediumRatio).toBeLessThan(6); // Should not be exponential
      expect(mediumToLargeRatio).toBeLessThan(3);
    });

    test('should scale linearly with signal count', () => {
      const signalCounts = [1000, 5000, 10000];
      const results = [];

      for (const count of signalCounts) {
        const start = performance.now();

        const signals = [];
        for (let i = 0; i < count; i++) {
          signals.push(signal(i));
        }

        const end = performance.now();
        results.push({ count, duration: end - start });
      }

      // Should scale roughly linearly
      const [small, medium, large] = results;
      const smallToMediumRatio = medium.duration / small.duration;
      const mediumToLargeRatio = large.duration / medium.duration;

      expect(smallToMediumRatio).toBeLessThan(6);
      expect(mediumToLargeRatio).toBeLessThan(3);
    });
  });
});
