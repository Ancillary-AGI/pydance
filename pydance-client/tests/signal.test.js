/**
 * Signal Tests for Pydance Client
 * Tests the core signal functionality
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { signal, computed, effect, batch } from '~/core/Signal.js';

describe('Signal System', () => {
  let count;
  let doubleCount;
  let effectSpy;

  beforeEach(() => {
    count = signal(0);
    doubleCount = computed(() => count.value * 2);
    effectSpy = vi.fn();
  });

  describe('Basic Signals', () => {
    it('should create a signal with initial value', () => {
      expect(count.value).toBe(0);
    });

    it('should update signal value', () => {
      count.value = 5;
      expect(count.value).toBe(5);
    });

    it('should notify subscribers when value changes', () => {
      const spy = vi.fn();
      count.subscribe(spy);

      count.value = 10;

      expect(spy).toHaveBeenCalledWith(10);
      expect(spy).toHaveBeenCalledTimes(1);
    });

    it('should not notify subscribers when value does not change', () => {
      const spy = vi.fn();
      count.subscribe(spy);

      count.value = 0; // Same value

      expect(spy).not.toHaveBeenCalled();
    });
  });

  describe('Computed Values', () => {
    it('should compute value based on signal', () => {
      expect(doubleCount.value).toBe(0);

      count.value = 3;
      expect(doubleCount.value).toBe(6);
    });

    it('should update when dependency changes', () => {
      count.value = 5;
      expect(doubleCount.value).toBe(10);

      count.value = 7;
      expect(doubleCount.value).toBe(14);
    });

    it('should notify subscribers when computed value changes', () => {
      const spy = vi.fn();
      doubleCount.subscribe(spy);

      count.value = 3;

      expect(spy).toHaveBeenCalledWith(6);
      expect(spy).toHaveBeenCalledTimes(1);
    });
  });

  describe('Effects', () => {
    it('should run effect when dependencies change', () => {
      effect(() => {
        effectSpy(count.value);
      });

      count.value = 5;

      expect(effectSpy).toHaveBeenCalledWith(5);
    });

    it('should run effect immediately', () => {
      effect(() => {
        effectSpy(count.value);
      });

      expect(effectSpy).toHaveBeenCalledWith(0);
    });

    it('should cleanup effect on disposal', () => {
      const cleanupSpy = vi.fn();
      const dispose = effect(() => {
        count.value;
        return cleanupSpy;
      });

      dispose();

      count.value = 5;

      expect(cleanupSpy).toHaveBeenCalled();
      expect(effectSpy).not.toHaveBeenCalled();
    });
  });

  describe('Batching', () => {
    it('should batch multiple updates', () => {
      const spy = vi.fn();

      effect(() => {
        spy(count.value);
      });

      batch(() => {
        count.value = 1;
        count.value = 2;
        count.value = 3;
      });

      expect(spy).toHaveBeenCalledTimes(2); // Initial + final
      expect(spy).toHaveBeenLastCalledWith(3);
    });

    it('should handle nested batches', () => {
      const spy = vi.fn();

      effect(() => {
        spy(count.value);
      });

      batch(() => {
        count.value = 1;
        batch(() => {
          count.value = 2;
          count.value = 3;
        });
        count.value = 4;
      });

      expect(spy).toHaveBeenCalledTimes(2); // Initial + final
      expect(spy).toHaveBeenLastCalledWith(4);
    });
  });

  describe('Complex Dependencies', () => {
    it('should handle multiple dependencies', () => {
      const a = signal(1);
      const b = signal(2);
      const sum = computed(() => a.value + b.value);
      const product = computed(() => sum.value * 2);

      expect(sum.value).toBe(3);
      expect(product.value).toBe(6);

      a.value = 5;
      expect(sum.value).toBe(7);
      expect(product.value).toBe(14);

      b.value = 10;
      expect(sum.value).toBe(15);
      expect(product.value).toBe(30);
    });

    it('should handle diamond dependencies correctly', () => {
      const base = signal(2);
      const double = computed(() => base.value * 2);
      const triple = computed(() => base.value * 3);
      const sum = computed(() => double.value + triple.value);

      expect(sum.value).toBe(10);

      base.value = 4;
      expect(sum.value).toBe(20);
    });
  });

  describe('Memory Management', () => {
    it('should cleanup subscriptions', () => {
      const spy = vi.fn();
      const unsubscribe = count.subscribe(spy);

      count.value = 5;
      expect(spy).toHaveBeenCalledWith(5);

      unsubscribe();

      count.value = 10;
      expect(spy).toHaveBeenCalledTimes(1); // Should not be called again
    });

    it('should cleanup computed subscriptions', () => {
      const spy = vi.fn();
      const computedSpy = vi.fn();

      const unsubscribeComputed = doubleCount.subscribe(computedSpy);
      const unsubscribeEffect = effect(() => {
        spy(count.value);
      });

      count.value = 5;
      expect(computedSpy).toHaveBeenCalledWith(10);
      expect(spy).toHaveBeenCalledWith(5);

      unsubscribeComputed();
      unsubscribeEffect();

      count.value = 10;
      expect(computedSpy).toHaveBeenCalledTimes(1);
      expect(spy).toHaveBeenCalledTimes(2); // Initial + one more
    });
  });
});
