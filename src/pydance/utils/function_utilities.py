"""
Function Utilities and Decorators for Pydance Framework.

This module provides functional programming utilities, decorators, and function
manipulation tools. Focused on composition, caching, and function enhancement.
"""

import asyncio
import functools
import time
import logging
from typing import Callable, Any, TypeVar, Optional, Union
from functools import wraps, lru_cache
import threading

T = TypeVar('T')
logger = logging.getLogger(__name__)


class FunctionUtils:
    """Functional programming utilities"""

    @staticmethod
    def compose(*functions: Callable) -> Callable:
        """Compose multiple functions together (right to left)"""
        if not functions:
            raise ValueError("At least one function must be provided")

        def composed(*args, **kwargs):
            result = functions[-1](*args, **kwargs)
            for func in reversed(functions[:-1]):
                result = func(result)
            return result
        return composed

    @staticmethod
    def pipe(value: Any, *functions: Callable) -> Any:
        """Pipe a value through multiple functions (left to right)"""
        result = value
        for func in functions:
            result = func(result)
        return result

    @staticmethod
    def curry(func: Callable) -> Callable:
        """Curry a function"""
        @functools.wraps(func)
        def curried(*args, **kwargs):
            if len(args) + len(kwargs) >= func.__code__.co_argcount:
                return func(*args, **kwargs)
            return lambda *more_args, **more_kwargs: curried(
                *(args + more_args), **{**kwargs, **more_kwargs}
            )
        return curried

    @staticmethod
    def memoize(func: Callable) -> Callable:
        """Memoize a function with automatic cache management"""
        cache = {}

        @wraps(func)
        def memoized(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in cache:
                cache[key] = func(*args, **kwargs)
            return cache[key]

        memoized.cache_clear = cache.clear
        memoized.cache_info = lambda: {'size': len(cache)}
        return memoized

    @staticmethod
    def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
              exceptions: tuple = (Exception,), on_retry: Optional[Callable] = None) -> Callable:
        """Retry decorator with exponential backoff"""
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if delay < 0:
            raise ValueError("delay must be non-negative")
        if backoff <= 1:
            raise ValueError("backoff must be greater than 1")

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_delay = delay
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            if on_retry:
                                on_retry(attempt + 1, e, current_delay)
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            logger.warning(f"All {max_attempts} attempts failed for {func.__name__}")

                raise last_exception
            return wrapper
        return decorator

    @staticmethod
    def timeout(seconds: float, timeout_exception: Exception = TimeoutError) -> Callable:
        """Timeout decorator using asyncio (cross-platform)"""
        if seconds <= 0:
            raise ValueError("timeout must be positive")

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                except asyncio.TimeoutError:
                    raise timeout_exception(f"Function {func.__name__} timed out after {seconds} seconds")

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, run in thread pool
                async def run_with_timeout():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return await asyncio.wait_for(
                            loop.run_in_executor(None, func, *args, **kwargs),
                            timeout=seconds
                        )
                    finally:
                        loop.close()

                try:
                    return asyncio.run(run_with_timeout())
                except asyncio.TimeoutError:
                    raise timeout_exception(f"Function {func.__name__} timed out after {seconds} seconds")

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator

    @staticmethod
    def debounce(delay: float) -> Callable:
        """Debounce decorator"""
        if delay < 0:
            raise ValueError("delay must be non-negative")

        def decorator(func: Callable) -> Callable:
            last_call = [0.0]
            lock = threading.Lock()

            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                with lock:
                    if current_time - last_call[0] >= delay:
                        last_call[0] = current_time
                        return func(*args, **kwargs)
                return None  # Or return last result if needed
            return wrapper
        return decorator

    @staticmethod
    def throttle(interval: float) -> Callable:
        """Throttle decorator"""
        if interval <= 0:
            raise ValueError("interval must be positive")

        def decorator(func: Callable) -> Callable:
            last_call = [0.0]
            lock = threading.Lock()

            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                with lock:
                    if current_time - last_call[0] >= interval:
                        last_call[0] = current_time
                        return func(*args, **kwargs)
                return None  # Or return last result if needed
            return wrapper
        return decorator

    @staticmethod
    def singleton(cls: type) -> type:
        """Singleton decorator for classes"""
        instances = {}
        lock = threading.Lock()

        @wraps(cls)
        def get_instance(*args, **kwargs):
            if cls not in instances:
                with lock:
                    if cls not in instances:  # Double-check locking
                        instances[cls] = cls(*args, **kwargs)
            return instances[cls]

        return get_instance

    @staticmethod
    def rate_limit(calls_per_second: float) -> Callable:
        """Rate limiting decorator"""
        if calls_per_second <= 0:
            raise ValueError("calls_per_second must be positive")

        interval = 1.0 / calls_per_second
        last_call = [0.0]
        lock = threading.Lock()

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                with lock:
                    time_since_last = current_time - last_call[0]
                    if time_since_last < interval:
                        sleep_time = interval - time_since_last
                        time.sleep(sleep_time)
                    last_call[0] = time.time()
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def log_execution_time(level: int = logging.INFO) -> Callable:
        """Decorator to log function execution time"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    execution_time = end_time - start_time
                    logger.log(level, f"{func.__name__} executed in {execution_time:.4f} seconds")
                    return result
                except Exception as e:
                    end_time = time.time()
                    execution_time = end_time - start_time
                    logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
                    raise
            return wrapper
        return decorator

    @staticmethod
    def validate_input(*validators) -> Callable:
        """Input validation decorator"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Validate positional arguments
                for i, validator in enumerate(validators):
                    if i < len(args) and validator:
                        if not validator(args[i]):
                            raise ValueError(f"Validation failed for argument {i}")

                # Could extend to validate kwargs if needed
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def cache_with_ttl(ttl_seconds: float) -> Callable:
        """Cache decorator with time-to-live"""
        if ttl_seconds <= 0:
            raise ValueError("TTL must be positive")

        def decorator(func: Callable) -> Callable:
            cache = {}
            timestamps = {}

            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                key = (args, tuple(sorted(kwargs.items())))

                # Check if cached and not expired
                if key in cache and (current_time - timestamps.get(key, 0)) < ttl_seconds:
                    return cache[key]

                # Compute new value
                result = func(*args, **kwargs)
                cache[key] = result
                timestamps[key] = current_time

                # Clean expired entries (simple cleanup)
                expired_keys = [k for k, t in timestamps.items()
                              if current_time - t >= ttl_seconds]
                for k in expired_keys:
                    cache.pop(k, None)
                    timestamps.pop(k, None)

                return result

            wrapper.cache_clear = lambda: (cache.clear(), timestamps.clear())
            return wrapper
        return decorator


# Convenience functions and decorators
def compose(*functions):
    """Compose functions"""
    return FunctionUtils.compose(*functions)

def pipe(value, *functions):
    """Pipe value through functions"""
    return FunctionUtils.pipe(value, *functions)

def curry(func):
    """Curry function"""
    return FunctionUtils.curry(func)

def memoize(func):
    """Memoize function"""
    return FunctionUtils.memoize(func)

def retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """Retry decorator"""
    return FunctionUtils.retry(max_attempts, delay, backoff, exceptions)

def timeout(seconds, timeout_exception=TimeoutError):
    """Timeout decorator"""
    return FunctionUtils.timeout(seconds, timeout_exception)

def debounce(delay):
    """Debounce decorator"""
    return FunctionUtils.debounce(delay)

def throttle(interval):
    """Throttle decorator"""
    return FunctionUtils.throttle(interval)

def singleton(cls):
    """Singleton decorator"""
    return FunctionUtils.singleton(cls)

def rate_limit(calls_per_second):
    """Rate limit decorator"""
    return FunctionUtils.rate_limit(calls_per_second)

def log_execution_time(level=logging.INFO):
    """Log execution time decorator"""
    return FunctionUtils.log_execution_time(level)

def validate_input(*validators):
    """Validate input decorator"""
    return FunctionUtils.validate_input(*validators)

def cache_with_ttl(ttl_seconds):
    """Cache with TTL decorator"""
    return FunctionUtils.cache_with_ttl(ttl_seconds)
