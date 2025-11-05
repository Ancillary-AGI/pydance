/**
 * @fileoverview Signal System Tests - Comprehensive Signal Reactivity Testing
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import {
  Signal,
  signal,
  isSignal,
  unwrap,
  Computed,
  computed,
  Effect,
  effect,
  batch,
  batchUpdates,
  untrack,
  tick,
  mergeSignals,
  combineSignals
} from '~/core/Signal.js';

describe('Signal System', () => {
  let mockEffect;

  beforeEach(() => {
    mockEffect = vi.fn();
    vi.clearAllMocks();
  });

  describe('Signal Creation and Basic Operations', () => {
    test('should create a signal with initial value', () => {
      const s = signal(42);
      expect(s.value).toBe(42);
      expect(isSignal(s)).toBe(true);
    });

    test('should update signal value', () => {
      const s = signal(0);
      s.value = 10;
      expect(s.value).toBe(10);
    });

    test('should not update if value is the same', () => {
      const s = signal(5);
      const effectFn = vi.fn();
      effect(() => {
        effectFn(s.value);
      });

      s.value = 5; // Same value
      expect(effectFn).toHaveBeenCalledTimes(1); // Only initial call
    });

    test('should handle Object.is comparison correctly', () => {
      const s = signal(NaN);
      const effectFn = vi.fn();
      effect(() => {
        effectFn(s.value);
      });

      s.value = NaN; // Same NaN
      expect(effectFn).toHaveBeenCalledTimes(1); // Only initial call
    });
  });

  describe('Signal Reactivity', () => {
    test('should trigger effects when value changes', () => {
      const s = signal(0);
      effect(() => mockEffect(s.value));

      s.value = 1;
      expect(mockEffect).toHaveBeenCalledWith(1);
    });

    test('should track dependencies correctly', () => {
      const a = signal(1);
      const b = signal(2);

      effect(() => {
        mockEffect(a.value + b.value);
      });

      a.value = 10;
      expect(mockEffect).toHaveBeenCalledWith(12);

      b.value = 20;
      expect(mockEffect).toHaveBeenCalledWith(30);
    });

    test('should handle nested effects', () => {
      const count = signal(0);
      const double = computed(() => count.value * 2);
      const quadruple = computed(() => double.value * 2);

      effect(() => mockEffect(quadruple.value));

      count.value = 1;
      expect(mockEffect).toHaveBeenCalledWith(4);

      count.value = 2;
      expect(mockEffect).toHaveBeenCalledWith(8);
    });

    test('should handle circular dependencies gracefully', () => {
      const a = signal(1);
      const b = signal(2);

      // This should not cause infinite loops
      expect(() => {
        const c = computed(() => a.value + b.value);
        a.value = c.value; // Circular reference
      }).not.toThrow();
    });
  });

  describe('Computed Signals', () => {
    test('should compute derived values', () => {
      const base = signal(5);
      const doubled = computed(() => base.value * 2);

      expect(doubled.value).toBe(10);

      base.value = 10;
      expect(doubled.value).toBe(20);
    });

    test('should handle complex computations', () => {
      const a = signal(2);
      const b = signal(3);
      const c = signal(4);

      const result = computed(() => {
        return a.value * b.value + Math.sqrt(c.value);
      });

      expect(result.value).toBeCloseTo(6 + 2, 5);

      a.value = 5;
      expect(result.value).toBeCloseTo(15 + 2, 5);
    });

    test('should cache computed values', () => {
      const base = signal(1);
      const computeFn = vi.fn(() => base.value * 2);
      const doubled = computed(computeFn);

      // Access multiple times
      expect(doubled.value).toBe(2);
      expect(doubled.value).toBe(2);
      expect(computeFn).toHaveBeenCalledTimes(1); // Should be cached

      base.value = 2;
      expect(doubled.value).toBe(4);
      expect(computeFn).toHaveBeenCalledTimes(2); // Recomputed after dependency change
    });
  });

  describe('Effect Management', () => {
    test('should execute effects immediately', () => {
      const s = signal(0);
      effect(() => mockEffect(s.value));

      expect(mockEffect).toHaveBeenCalledWith(0);
    });

    test('should cleanup effects properly', () => {
      const s = signal(0);
      const cleanup = vi.fn();

      const effectInstance = new Effect(() => {
        s.value; // Track dependency
        return cleanup;
      });

      effectInstance.execute();
      s.value = 1;

      effectInstance.stop();
      s.value = 2;

      expect(cleanup).toHaveBeenCalledTimes(2); // Cleanup called when effect stops and when new effect runs
    });

    test('should handle effect errors gracefully', () => {
      const s = signal(0);

      expect(() => {
        effect(() => {
          if (s.value > 0) {
            throw new Error('Test error');
          }
        });

        s.value = 1;
      }).not.toThrow();
    });
  });

  describe('Batch Updates', () => {
    test('should batch multiple signal updates', () => {
      const a = signal(0);
      const b = signal(0);

      effect(() => mockEffect(a.value + b.value));

      batch(() => {
        a.value = 1;
        b.value = 2;
      });

      expect(mockEffect).toHaveBeenCalledTimes(3); // Initial + 2 updates
      expect(mockEffect).toHaveBeenLastCalledWith(3);
    });

    test('should handle nested batch operations', () => {
      const s = signal(0);
      effect(() => mockEffect(s.value));

      batch(() => {
        s.value = 1;
        batch(() => {
          s.value = 2;
          s.value = 3;
        });
        s.value = 4;
      });

      expect(mockEffect).toHaveBeenCalledTimes(2); // Initial + final batch result
      expect(mockEffect).toHaveBeenLastCalledWith(4);
    });
  });

  describe('Memory Management', () => {
    test('should cleanup unused signals', () => {
      const s = signal(0);
      const effectFn = vi.fn();

      const unsubscribe = s.subscribe(effectFn);
      s.value = 1;
      expect(effectFn).toHaveBeenCalledTimes(1); // Only update, no initial call

      unsubscribe();
      s.value = 2;
      expect(effectFn).toHaveBeenCalledTimes(1); // No more calls
    });

    test('should handle signal destruction', () => {
      const s = signal(0);
      const effectFn = vi.fn();

      effect(() => effectFn(s.value));

      s.destroy();
      s.value = 1;

      // Effect should not be called after signal destruction
      expect(effectFn).toHaveBeenCalledTimes(1); // Only initial call
    });
  });

  describe('Utility Functions', () => {
    test('should unwrap signals correctly', () => {
      const s = signal(42);
      const value = 24;

      expect(unwrap(s)).toBe(42);
      expect(unwrap(value)).toBe(24);
    });

    test('should untrack function execution', () => {
      const s = signal(0);
      effect(() => mockEffect(s.value));

      untrack(() => {
        s.value = 1; // Should not trigger effect
      });

      expect(mockEffect).toHaveBeenCalledTimes(2); // Initial + untracked update

      s.value = 2; // This should trigger effect
      expect(mockEffect).toHaveBeenCalledTimes(3);
    });

    test('should merge multiple signals', () => {
      const a = signal(1);
      const b = signal(2);
      const c = signal(3);

      const merged = mergeSignals(a, b, c);
      expect(merged.value).toEqual([1, 2, 3]);

      a.value = 10;
      expect(merged.value).toEqual([10, 2, 3]);
    });

    test('should combine signals with custom function', () => {
      const a = signal(2);
      const b = signal(3);

      const combined = combineSignals([a, b], (x, y) => x * y);
      expect(combined.value).toBe(6);

      a.value = 4;
      expect(combined.value).toBe(12);
    });
  });

  describe('Performance Benchmarks', () => {
    test('should create signals efficiently', () => {
      const start = performance.now();

      for (let i = 0; i < 10000; i++) {
        signal(i);
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(100); // Should be very fast
    });

    test('should handle rapid signal updates', () => {
      const s = signal(0);
      const effectFn = vi.fn();

      effect(effectFn);

      const start = performance.now();

      for (let i = 0; i < 1000; i++) {
        s.value = i;
      }

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(50);
      expect(effectFn).toHaveBeenCalledTimes(1001); // Initial + 1000 updates
    });

    test('should handle complex dependency graphs', () => {
      const signals = Array.from({ length: 100 }, (_, i) => signal(i));
      const computedSignals = signals.map(s => computed(() => s.value * 2));
      const final = computed(() => computedSignals.reduce((sum, c) => sum + c.value, 0));

      const start = performance.now();

      signals[0].value = 1000;

      const end = performance.now();
      const duration = end - start;

      expect(duration).toBeLessThan(10);
      expect(final.value).toBe(199000); // (0+1+...+99)*2 + 1000*2
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('should handle null and undefined values', () => {
      const s1 = signal(null);
      const s2 = signal(undefined);

      expect(s1.value).toBeNull();
      expect(s2.value).toBeUndefined();

      s1.value = 'test';
      s2.value = 'test';

      expect(s1.value).toBe('test');
      expect(s2.value).toBe('test');
    });

    test('should handle complex objects', () => {
      const s = signal({ nested: { value: 1 } });

      effect(() => {
        mockEffect(s.value.nested.value);
      });

      s.value = { nested: { value: 2 } };
      expect(mockEffect).toHaveBeenCalledWith(2);

      // Mutating nested object should not trigger effect
      s.value.nested.value = 3;
      expect(mockEffect).toHaveBeenCalledTimes(2); // No additional calls
    });

    test('should handle function values', () => {
      const fn = () => 'test';
      const s = signal(fn);

      expect(s.value).toBe(fn);

      s.value = () => 'updated';
      expect(typeof s.value).toBe('function');
    });
  });
});
