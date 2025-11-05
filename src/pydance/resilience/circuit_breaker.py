
from pydance.utils.logging import get_logger
"""
Circuit Breaker Pattern Implementation for Pydance

Provides fault tolerance and resilience for microservices and external API calls.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Exception = Exception
    success_threshold: int = 3
    timeout: float = 30.0
    name: str = "default"


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker"""
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_timeouts: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.last_state_change = time.time()
        self.logger = get_logger(f"CircuitBreaker-{config.name}")

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        if self.state != CircuitBreakerState.OPEN:
            return False

        return (time.time() - self.last_state_change) >= self.config.recovery_timeout

    def _record_success(self):
        """Record a successful call"""
        self.metrics.total_requests += 1
        self.metrics.total_successes += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                self._transition_to(CircuitBreakerState.CLOSED)

    def _record_failure(self):
        """Record a failed call"""
        self.metrics.total_requests += 1
        self.metrics.total_failures += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = time.time()

        if (self.state == CircuitBreakerState.CLOSED and
            self.metrics.consecutive_failures >= self.config.failure_threshold):
            self._transition_to(CircuitBreakerState.OPEN)
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to(CircuitBreakerState.OPEN)

    def _record_timeout(self):
        """Record a timeout"""
        self.metrics.total_requests += 1
        self.metrics.total_timeouts += 1
        self._record_failure()

    def _transition_to(self, new_state: CircuitBreakerState):
        """Transition to new state"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = time.time()
            self.metrics.state_changes += 1

            self.logger.info(
                f"Circuit breaker '{self.config.name}' transitioned from {old_state.value} to {new_state.value}"
            )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # Check if we should reject the call
        if self.state == CircuitBreakerState.OPEN:
            if not self._should_attempt_reset():
                raise Exception(f"Circuit breaker '{self.config.name}' is OPEN")

            # Attempt to reset
            self._transition_to(CircuitBreakerState.HALF_OPEN)
            self.metrics.consecutive_successes = 0

        # Execute the function with timeout
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                # For synchronous functions, run in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=self.config.timeout
                )

            self._record_success()
            return result

        except asyncio.TimeoutError:
            self._record_timeout()
            raise Exception(f"Circuit breaker '{self.config.name}' timeout after {self.config.timeout}s")

        except self.config.expected_exception as e:
            self._record_failure()
            raise

        except Exception as e:
            # Unexpected exception, still count as failure
            self._record_failure()
            raise

    def get_state(self) -> Dict[str, Any]:
        """Get current state and metrics"""
        return {
            'name': self.config.name,
            'state': self.state.value,
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'total_successes': self.metrics.total_successes,
                'total_failures': self.metrics.total_failures,
                'total_timeouts': self.metrics.total_timeouts,
                'consecutive_failures': self.metrics.consecutive_failures,
                'consecutive_successes': self.metrics.consecutive_successes,
                'last_failure_time': self.metrics.last_failure_time,
                'last_success_time': self.metrics.last_success_time,
                'state_changes': self.metrics.state_changes,
                'success_rate': (self.metrics.total_successes / self.metrics.total_requests * 100) if self.metrics.total_requests > 0 else 0,
                'failure_rate': (self.metrics.total_failures / self.metrics.total_requests * 100) if self.metrics.total_requests > 0 else 0,
            },
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout,
            }
        }


class CircuitBreakerRegistry:
    """Registry for managing circuit breakers"""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger("CircuitBreakerRegistry")

    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self._breakers:
            if config is None:
                config = CircuitBreakerConfig(name=name)
            self._breakers[name] = CircuitBreaker(config)
            self.logger.info(f"Created circuit breaker '{name}'")

        return self._breakers[name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {name: breaker.get_state() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            breaker.state = CircuitBreakerState.CLOSED
            breaker.metrics = CircuitBreakerMetrics()
            breaker.last_state_change = time.time()

    def remove_circuit_breaker(self, name: str):
        """Remove circuit breaker"""
        if name in self._breakers:
            del self._breakers[name]
            self.logger.info(f"Removed circuit breaker '{name}'")


# Global registry
circuit_breaker_registry = CircuitBreakerRegistry()

# Decorator for circuit breaker
def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to apply circuit breaker to function"""
    def decorator(func: Callable) -> Callable:
        breaker = circuit_breaker_registry.get_circuit_breaker(name, config)

        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                return await breaker.call(func, *args, **kwargs)
        else:
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper._circuit_breaker = breaker
        return wrapper

    return decorator

# Context manager for circuit breaker
class CircuitBreakerContext:
    """Context manager for circuit breaker"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.breaker = circuit_breaker_registry.get_circuit_breaker(name, config)
        self.result = None
        self.exception = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.exception = exc_val
            # Let the circuit breaker handle the exception
            try:
                await self.breaker.call(lambda: (_ for _ in ()).throw(exc_val))
            except:
                pass
        return False  # Don't suppress exceptions

# Utility functions
def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get circuit breaker by name"""
    return circuit_breaker_registry.get_circuit_breaker(name, config)

async def call_with_circuit_breaker(name: str, func: Callable, *args, **kwargs):
    """Call function with circuit breaker protection"""
    breaker = circuit_breaker_registry.get_circuit_breaker(name)
    return await breaker.call(func, *args, **kwargs)

__all__ = [
    'CircuitBreakerState', 'CircuitBreakerConfig', 'CircuitBreakerMetrics',
    'CircuitBreaker', 'CircuitBreakerRegistry', 'circuit_breaker_registry',
    'circuit_breaker', 'CircuitBreakerContext', 'get_circuit_breaker',
    'call_with_circuit_breaker'
]
