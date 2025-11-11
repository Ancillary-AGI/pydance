"""
Asynchronous Utilities for Pydance Framework.

This module provides async/await utilities, concurrent execution helpers,
and asynchronous programming tools.
"""

import asyncio
import threading
from typing import Any, Callable, List, Optional, TypeVar, Union, Coroutine
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)


class AsyncUtils:
    """Asynchronous utility functions"""

    @staticmethod
    async def gather_with_concurrency(n: int, *coroutines: Coroutine) -> List[Any]:
        """Gather coroutines with concurrency limit"""
        if n <= 0:
            raise ValueError("Concurrency limit must be positive")

        semaphore = asyncio.Semaphore(n)

        async def sem_coro(coro: Coroutine) -> Any:
            async with semaphore:
                return await coro

        return await asyncio.gather(*(sem_coro(coro) for coro in coroutines))

    @staticmethod
    def run_in_executor(func: Callable[..., T], *args, executor: Optional[ThreadPoolExecutor] = None, **kwargs) -> Coroutine[Any, Any, T]:
        """Run a function in a thread pool executor"""
        if executor is None:
            executor = ThreadPoolExecutor(max_workers=4)

        loop = asyncio.get_event_loop()
        return loop.run_in_executor(executor, func, *args, **kwargs)

    @staticmethod
    def run_in_process(func: Callable[..., T], *args, **kwargs) -> Coroutine[Any, Any, T]:
        """Run a function in a process pool executor"""
        executor = ProcessPoolExecutor(max_workers=2)  # Conservative default
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(executor, func, *args, **kwargs)

    @staticmethod
    async def timeout_async(coro: Coroutine, timeout: float, default: Any = None) -> Any:
        """Add timeout to a coroutine with default value"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Coroutine timed out after {timeout} seconds")
            return default

    @staticmethod
    async def retry_async(coro_func: Callable[[], Coroutine], max_attempts: int = 3,
                         delay: float = 1.0, backoff: float = 2.0,
                         exceptions: tuple = (Exception,)) -> Any:
        """Retry an async operation with exponential backoff"""
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        current_delay = delay
        last_exception = None

        for attempt in range(max_attempts):
            try:
                return await coro_func()
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {current_delay}s")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        logger.error(f"All {max_attempts} attempts failed")
        raise last_exception

    @staticmethod
    def async_cache(ttl_seconds: Optional[float] = None) -> Callable:
        """Async cache decorator with optional TTL"""
        def decorator(func: Callable) -> Callable:
            cache = {}
            timestamps = {} if ttl_seconds else None

            async def wrapper(*args, **kwargs):
                current_time = time.time() if ttl_seconds else None
                key = (args, tuple(sorted(kwargs.items())))

                # Check cache
                if key in cache:
                    if not ttl_seconds or (current_time - timestamps[key]) < ttl_seconds:
                        return cache[key]
                    else:
                        # Expired, remove
                        del cache[key]
                        del timestamps[key]

                # Compute new value
                result = await func(*args, **kwargs)
                cache[key] = result
                if ttl_seconds:
                    timestamps[key] = current_time

                return result

            wrapper.cache_clear = lambda: (cache.clear(), timestamps.clear() if timestamps else None)
            wrapper.cache_info = lambda: {'size': len(cache)}
            return wrapper
        return decorator

    @staticmethod
    async def sleep_until(condition_func: Callable[[], bool], timeout: float = 10.0,
                         check_interval: float = 0.1) -> bool:
        """Sleep until condition is met or timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(check_interval)
        return False

    @staticmethod
    async def periodic_task(interval: float, func: Callable, *args, **kwargs) -> asyncio.Task:
        """Create a periodic async task"""
        async def periodic():
            while True:
                await asyncio.sleep(interval)
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Periodic task failed: {e}")

        return asyncio.create_task(periodic())

    @staticmethod
    def to_async(func: Callable) -> Callable:
        """Convert a sync function to async by running in executor"""
        async def async_wrapper(*args, **kwargs):
            return await AsyncUtils.run_in_executor(func, *args, **kwargs)
        return async_wrapper

    @staticmethod
    async def map_async(func: Callable, items: List[Any], concurrency: int = 4) -> List[Any]:
        """Async map with concurrency control"""
        async def process_item(item):
            return await AsyncUtils.run_in_executor(func, item)

        coroutines = [process_item(item) for item in items]
        return await AsyncUtils.gather_with_concurrency(concurrency, *coroutines)

    @staticmethod
    async def filter_async(predicate: Callable, items: List[Any], concurrency: int = 4) -> List[Any]:
        """Async filter with concurrency control"""
        async def check_item(item):
            result = await AsyncUtils.run_in_executor(predicate, item)
            return (item, result) if result else None

        coroutines = [check_item(item) for item in items]
        results = await AsyncUtils.gather_with_concurrency(concurrency, *coroutines)
        return [item for item, _ in filter(None, results)]

    @staticmethod
    async def reduce_async(func: Callable, items: List[Any], initial: Any = None) -> Any:
        """Async reduce operation"""
        if not items:
            return initial

        accumulator = initial if initial is not None else items[0]
        start_idx = 1 if initial is not None else 0

        for item in items[start_idx:]:
            accumulator = await AsyncUtils.run_in_executor(func, accumulator, item)

        return accumulator


class ConcurrentUtils:
    """Concurrency utilities"""

    @staticmethod
    def run_async_in_thread(coro: Coroutine, timeout: Optional[float] = None) -> Any:
        """Run async code in a separate thread"""
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if timeout:
                    return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
                else:
                    return loop.run_until_complete(coro)
            finally:
                loop.close()

        result = [None]
        exception = [None]

        def thread_target():
            try:
                result[0] = run_in_thread()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=thread_target)
        thread.start()
        thread.join(timeout=timeout)

        if exception[0]:
            raise exception[0]
        return result[0]

    @staticmethod
    def create_thread_pool(max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """Create a configured thread pool executor"""
        return ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="pydance")

    @staticmethod
    def create_process_pool(max_workers: Optional[int] = None) -> ProcessPoolExecutor:
        """Create a configured process pool executor"""
        return ProcessPoolExecutor(max_workers=max_workers)


class EventUtils:
    """Async event utilities"""

    @staticmethod
    async def wait_for_event(event: asyncio.Event, timeout: Optional[float] = None) -> bool:
        """Wait for an asyncio event with timeout"""
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    @staticmethod
    async def debounce_async(func: Callable, delay: float, *args, **kwargs) -> Any:
        """Async debounce function"""
        await asyncio.sleep(delay)
        return await func(*args, **kwargs)

    @staticmethod
    async def throttle_async(func: Callable, interval: float, *args, **kwargs) -> Any:
        """Async throttle function"""
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start_time

        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)

        return result


# Convenience functions
async def gather_with_concurrency(n: int, *coroutines):
    """Gather with concurrency limit"""
    return await AsyncUtils.gather_with_concurrency(n, *coroutines)

def run_in_executor(func, *args, executor=None, **kwargs):
    """Run in executor"""
    return AsyncUtils.run_in_executor(func, *args, executor=executor, **kwargs)

async def timeout_async(coro, timeout, default=None):
    """Timeout async operation"""
    return await AsyncUtils.timeout_async(coro, timeout, default)

async def retry_async(coro_func, max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """Retry async operation"""
    return await AsyncUtils.retry_async(coro_func, max_attempts, delay, backoff, exceptions)

async def map_async(func, items, concurrency=4):
    """Async map"""
    return await AsyncUtils.map_async(func, items, concurrency)

async def filter_async(predicate, items, concurrency=4):
    """Async filter"""
    return await AsyncUtils.filter_async(predicate, items, concurrency)

async def reduce_async(func, items, initial=None):
    """Async reduce"""
    return await AsyncUtils.reduce_async(func, items, initial)
