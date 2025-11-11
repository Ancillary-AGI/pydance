"""
Performance Utilities for Pydance Framework.

This module provides performance monitoring, benchmarking, and optimization tools.
"""

import time
import threading
import psutil
import os
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
from contextlib import contextmanager
import logging
import statistics
import gc

T = TypeVar('T')
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system and application performance"""

    def __init__(self):
        self.start_time = time.time()
        self.check_psutil()

    def check_psutil(self):
        """Check if psutil is available"""
        try:
            import psutil
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
            logger.warning("psutil not available, some metrics will be limited")

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        if not self.psutil_available:
            return {'error': 'psutil not available'}

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }

    def get_cpu_usage(self) -> Dict[str, float]:
        """Get CPU usage information"""
        if not self.psutil_available:
            return {'error': 'psutil not available'}

        return {
            'process_percent': psutil.Process(os.getpid()).cpu_percent(),
            'system_percent': psutil.cpu_percent(interval=0.1)
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        if not self.psutil_available:
            return {'error': 'psutil not available'}

        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            'memory_available': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
            'uptime': time.time() - psutil.boot_time()
        }

    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()

    def record_metric(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []

            self.metrics[name].append({
                'value': value,
                'timestamp': time.time(),
                'tags': tags or {}
            })

            # Keep only last 1000 measurements per metric
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]

    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a metric"""
        with self.lock:
            if name not in self.metrics:
                return {'error': f'Metric {name} not found'}

            values = [m['value'] for m in self.metrics[name]]

            return {
                'count': len(values),
                'mean': statistics.mean(values) if values else 0,
                'median': statistics.median(values) if values else 0,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                'latest': values[-1] if values else None
            }

    def clear_metrics(self, name: Optional[str] = None):
        """Clear metrics"""
        with self.lock:
            if name:
                self.metrics.pop(name, None)
            else:
                self.metrics.clear()


class BenchmarkTimer:
    """High-precision benchmarking timer"""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start the timer"""
        self.start_time = time.perf_counter()
        return self

    def stop(self) -> float:
        """Stop the timer and return elapsed time"""
        if self.start_time is None:
            raise RuntimeError("Timer not started")

        self.end_time = time.perf_counter()
        return self.elapsed

    @property
    def elapsed(self) -> float:
        """Get elapsed time"""
        if self.start_time is None:
            return 0.0

        end_time = self.end_time or time.perf_counter()
        return end_time - self.start_time

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


@contextmanager
def timer(name: str = "operation", log_result: bool = True):
    """Context manager for timing operations"""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        if log_result:
            print(f"{name} took {elapsed:.6f} seconds")


def benchmark(func: Callable[..., T], iterations: int = 100, *args, **kwargs) -> Dict[str, float]:
    """Benchmark a function over multiple iterations"""
    if iterations <= 0:
        raise ValueError("Iterations must be positive")

    times = []

    # Warm up
    for _ in range(min(10, iterations // 10)):
        func(*args, **kwargs)

    # Actual benchmarking
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)

    return {
        'iterations': iterations,
        'min': min(times),
        'max': max(times),
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'total': sum(times),
        'result': result
    }


def profile_function(func: Callable[..., T], *args, **kwargs) -> tuple[T, Dict[str, Any]]:
    """Profile a function execution"""
    import cProfile
    import pstats
    import io

    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()

    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()

    return result, {
        'profile_output': s.getvalue(),
        'stats': ps.stats
    }


def memory_usage(func: Callable[..., T], *args, **kwargs) -> tuple[T, Dict[str, float]]:
    """Measure memory usage of a function"""
    if not psutil:
        raise ImportError("psutil required for memory profiling")

    process = psutil.Process(os.getpid())

    # Get initial memory
    initial_memory = process.memory_info().rss

    # Run function
    result = func(*args, **kwargs)

    # Get final memory
    final_memory = process.memory_info().rss

    return result, {
        'initial_mb': initial_memory / 1024 / 1024,
        'final_mb': final_memory / 1024 / 1024,
        'delta_mb': (final_memory - initial_memory) / 1024 / 1024
    }


class PerformanceProfiler:
    """Advanced performance profiler"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.monitor = PerformanceMonitor()

    def profile_method(self, method_name: str = None):
        """Decorator to profile method performance"""
        def decorator(func: Callable) -> Callable:
            name = method_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                with BenchmarkTimer(name) as timer:
                    result = func(*args, **kwargs)

                # Record metrics
                self.metrics.record_metric(f"{name}.execution_time", timer.elapsed)
                self.metrics.record_metric(f"{name}.call_count", 1)

                return result
            return wrapper
        return decorator

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'uptime': self.monitor.get_uptime(),
            'system_info': self.monitor.get_system_info(),
            'memory_usage': self.monitor.get_memory_usage(),
            'cpu_usage': self.monitor.get_cpu_usage(),
            'metrics': {}
        }

        # Add metric statistics
        for metric_name in self.metrics.metrics.keys():
            report['metrics'][metric_name] = self.metrics.get_metric_stats(metric_name)

        return report


class ThreadingUtils:
    """Threading utilities for performance"""

    @staticmethod
    def run_in_thread(func: Callable[..., T], *args, **kwargs) -> threading.Thread:
        """Run function in a separate thread"""
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def create_thread_pool(max_workers: Optional[int] = None):
        """Create a configured thread pool"""
        from concurrent.futures import ThreadPoolExecutor
        return ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="pydance-perf")

    @staticmethod
    def parallel_map(func: Callable[[T], Any], items: List[T], max_workers: Optional[int] = None) -> List[Any]:
        """Execute function in parallel over a list of items"""
        with ThreadingUtils.create_thread_pool(max_workers) as executor:
            return list(executor.map(func, items))


class MemoryProfiler:
    """Memory usage profiler"""

    @staticmethod
    def profile_memory_usage(func: Callable[..., T], *args, **kwargs) -> tuple[T, Dict[str, Any]]:
        """Profile memory usage during function execution"""
        try:
            import tracemalloc
        except ImportError:
            raise ImportError("tracemalloc required for memory profiling")

        tracemalloc.start()
        gc.collect()  # Clean up before measurement

        start_snapshot = tracemalloc.take_snapshot()

        result = func(*args, **kwargs)

        end_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # Calculate memory difference
        stats = end_snapshot.compare_to(start_snapshot, 'lineno')

        return result, {
            'memory_stats': [
                {
                    'size': stat.size,
                    'size_diff': stat.size_diff,
                    'count': stat.count,
                    'count_diff': stat.count_diff,
                    'traceback': stat.traceback.format() if stat.traceback else None
                } for stat in stats[:10]  # Top 10 memory users
            ],
            'total_size': sum(stat.size for stat in stats),
            'total_size_diff': sum(stat.size_diff for stat in stats)
        }


# Global instances
_performance_monitor = PerformanceMonitor()
_performance_metrics = PerformanceMetrics()
_performance_profiler = PerformanceProfiler()

# Convenience functions
def get_memory_usage():
    """Get current memory usage"""
    return _performance_monitor.get_memory_usage()

def get_cpu_usage():
    """Get current CPU usage"""
    return _performance_monitor.get_cpu_usage()

def record_metric(name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
    """Record a performance metric"""
    _performance_metrics.record_metric(name, value, tags)

def get_metric_stats(name: str):
    """Get metric statistics"""
    return _performance_metrics.get_metric_stats(name)

def profile_method(method_name: str = None):
    """Profile method decorator"""
    return _performance_profiler.profile_method(method_name)

def get_performance_report():
    """Get comprehensive performance report"""
    return _performance_profiler.get_performance_report()
