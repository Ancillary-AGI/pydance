"""
Advanced algorithm optimizations for Pydance.

This module provides high-performance algorithm implementations with:
- Optimized sorting and searching algorithms
- Efficient data structure operations
- Parallel processing capabilities
- Memory-efficient algorithms
- Algorithm selection based on data characteristics
"""

import math
import statistics
from typing import List, Dict, Any, Optional, Tuple, TypeVar, Generic, Callable, Union
from collections import defaultdict, Counter
import time


logger = get_logger(__name__)

T = TypeVar('T')


class SortAlgorithm(Enum):
    """Available sorting algorithms"""
    TIMSORT = "timsort"  # Python's built-in (already optimized)
    MERGE_SORT = "merge_sort"
    QUICK_SORT = "quick_sort"
    HEAP_SORT = "heap_sort"
    RADIX_SORT = "radix_sort"  # For integers
    BUCKET_SORT = "bucket_sort"  # For uniform distributions


class SearchAlgorithm(Enum):
    """Available search algorithms"""
    BINARY_SEARCH = "binary_search"
    INTERPOLATION_SEARCH = "interpolation_search"  # For uniform distributions
    FIBONACCI_SEARCH = "fibonacci_search"
    JUMP_SEARCH = "jump_search"
    EXPONENTIAL_SEARCH = "exponential_search"


@dataclass
class AlgorithmMetrics:
    """Metrics for algorithm performance tracking"""
    algorithm_name: str
    execution_time: float
    input_size: int
    comparisons: int = 0
    swaps: int = 0
    memory_peak: int = 0
    success: bool = True


class AdaptiveSorter:
    """
    Intelligent sorting algorithm selector and executor.

    Automatically chooses the best sorting algorithm based on:
    - Data size and characteristics
    - Data distribution
    - Memory constraints
    - Performance requirements
    """

    def __init__(self):
        self.metrics_history = []
        self.algorithm_performance = defaultdict(list)

    def sort(self, data: List[T], key: Callable[[T], Any] = None, reverse: bool = False) -> List[T]:
        """
        Sort data using the most appropriate algorithm.

        Args:
            data: List to sort
            key: Key function for comparison
            reverse: Sort in descending order

        Returns:
            Sorted list
        """
        if not data:
            return data

        start_time = time.time()

        # Analyze data characteristics
        data_size = len(data)
        data_type = self._analyze_data_type(data)
        distribution = self._analyze_distribution(data, key)

        # Select optimal algorithm
        algorithm = self._select_sort_algorithm(data_size, data_type, distribution)

        # Execute sorting
        try:
            if algorithm == SortAlgorithm.TIMSORT:
                result = sorted(data, key=key, reverse=reverse)
            elif algorithm == SortAlgorithm.MERGE_SORT:
                result = self._merge_sort(data.copy(), key, reverse)
            elif algorithm == SortAlgorithm.QUICK_SORT:
                result = self._quick_sort(data.copy(), key, reverse)
            elif algorithm == SortAlgorithm.HEAP_SORT:
                result = self._heap_sort(data.copy(), key, reverse)
            elif algorithm == SortAlgorithm.RADIX_SORT and data_type == 'integer':
                result = self._radix_sort(data.copy(), reverse)
            elif algorithm == SortAlgorithm.BUCKET_SORT:
                result = self._bucket_sort(data.copy(), key, reverse)
            else:
                # Fallback to timsort
                result = sorted(data, key=key, reverse=reverse)

            # Record metrics
            execution_time = time.time() - start_time
            metrics = AlgorithmMetrics(
                algorithm_name=algorithm.value,
                execution_time=execution_time,
                input_size=data_size
            )
            self._record_metrics(metrics)

            return result

        except Exception as e:
            logger.warning(f"Sorting failed with {algorithm.value}, falling back to timsort: {e}")
            return sorted(data, key=key, reverse=reverse)

    def _analyze_data_type(self, data: List[T]) -> str:
        """Analyze the data type for algorithm selection"""
        if not data:
            return 'unknown'

        sample = data[:min(100, len(data))]  # Sample first 100 items

        # Check if all integers
        if all(isinstance(x, int) for x in sample):
            return 'integer'

        # Check if all floats
        if all(isinstance(x, (int, float)) for x in sample):
            return 'numeric'

        # Check if all strings
        if all(isinstance(x, str) for x in sample):
            return 'string'

        return 'mixed'

    def _analyze_distribution(self, data: List[T], key: Callable = None) -> Dict[str, Any]:
        """Analyze data distribution characteristics"""
        if not data:
            return {}

        # Apply key function if provided
        values = [key(x) if key else x for x in data[:min(1000, len(data))]]

        # Calculate basic statistics
        try:
            mean_val = statistics.mean(values) if values else 0
            stdev_val = statistics.stdev(values) if len(values) > 1 else 0

            return {
                'mean': mean_val,
                'stdev': stdev_val,
                'is_uniform': stdev_val < (abs(mean_val) * 0.1) if mean_val != 0 else False,
                'range': max(values) - min(values) if values else 0
            }
        except (TypeError, ValueError):
            return {'uniform': False}

    def _select_sort_algorithm(self, size: int, data_type: str, distribution: Dict[str, Any]) -> SortAlgorithm:
        """Select the optimal sorting algorithm based on data characteristics"""

        # For small datasets, timsort is usually fastest
        if size <= 100:
            return SortAlgorithm.TIMSORT

        # For integers with large range, radix sort might be good
        if data_type == 'integer' and size > 1000:
            int_range = distribution.get('range', 0)
            if int_range > 0 and int_range < size * 10:  # Reasonable range
                return SortAlgorithm.RADIX_SORT

        # For uniform distributions, bucket sort can be excellent
        if distribution.get('is_uniform', False) and size > 500:
            return SortAlgorithm.BUCKET_SORT

        # For large datasets, merge sort is stable and efficient
        if size > 10000:
            return SortAlgorithm.MERGE_SORT

        # Default to timsort for most cases
        return SortAlgorithm.TIMSORT

    def _merge_sort(self, data: List[T], key: Callable = None, reverse: bool = False) -> List[T]:
        """Optimized merge sort implementation"""
        if len(data) <= 1:
            return data

        mid = len(data) // 2
        left = self._merge_sort(data[:mid], key, reverse)
        right = self._merge_sort(data[mid:], key, reverse)

        return self._merge(left, right, key, reverse)

    def _merge(self, left: List[T], right: List[T], key: Callable = None, reverse: bool = False) -> List[T]:
        """Merge two sorted lists"""
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            left_val = key(left[i]) if key else left[i]
            right_val = key(right[j]) if key else right[j]

            if (left_val <= right_val) != reverse:  # XOR with reverse
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])
        return result

    def _quick_sort(self, data: List[T], key: Callable = None, reverse: bool = False) -> List[T]:
        """Optimized quicksort with median-of-three pivot selection"""
        if len(data) <= 1:
            return data

        # Median-of-three pivot selection
        if len(data) >= 3:
            mid = len(data) // 2
            candidates = [(key(data[0]) if key else data[0], 0),
                         (key(data[mid]) if key else data[mid], mid),
                         (key(data[-1]) if key else data[-1], -1)]

            candidates.sort(key=lambda x: x[0])
            pivot_idx = candidates[1][1]  # Middle value
        else:
            pivot_idx = 0

        # Move pivot to end
        data[0], data[pivot_idx] = data[pivot_idx], data[0]
        pivot = key(data[0]) if key else data[0]

        # Partition
        i = 1
        for j in range(1, len(data)):
            val = key(data[j]) if key else data[j]
            if (val <= pivot) != reverse:
                data[i], data[j] = data[j], data[i]
                i += 1

        # Move pivot to correct position
        data[0], data[i-1] = data[i-1], data[0]

        # Recursively sort partitions
        left = self._quick_sort(data[:i-1], key, reverse)
        right = self._quick_sort(data[i:], key, reverse)

        return left + [data[i-1]] + right

    def _heap_sort(self, data: List[T], key: Callable = None, reverse: bool = False) -> List[T]:
        """Optimized heap sort"""
        # Build heap in-place
        for i in range(len(data) // 2 - 1, -1, -1):
            self._heapify(data, len(data), i, key, reverse)

        # Extract elements one by one
        for i in range(len(data) - 1, 0, -1):
            data[0], data[i] = data[i], data[0]
            self._heapify(data, i, 0, key, reverse)

        return data

    def _heapify(self, data: List[T], n: int, i: int, key: Callable = None, reverse: bool = False):
        """Heapify subtree rooted at index i"""
        extreme = i
        left = 2 * i + 1
        right = 2 * i + 2

        # Find the extreme element (max or min based on reverse)
        for child in [left, right]:
            if child < n:
                child_val = key(data[child]) if key else data[child]
                extreme_val = key(data[extreme]) if key else data[extreme]

                if (child_val > extreme_val) != reverse:
                    extreme = child

        if extreme != i:
            data[i], data[extreme] = data[extreme], data[i]
            self._heapify(data, n, extreme, key, reverse)

    def _radix_sort(self, data: List[int], reverse: bool = False) -> List[int]:
        """Radix sort for integers"""
        if not data:
            return data

        # Find the maximum number to determine number of digits
        max_num = max(abs(x) for x in data)
        if max_num == 0:
            return data

        digits = 0
        temp = max_num
        while temp > 0:
            digits += 1
            temp //= 10

        # Perform counting sort for each digit
        for digit in range(digits):
            data = self._counting_sort_by_digit(data, digit, reverse)

        return data

    def _counting_sort_by_digit(self, data: List[int], digit: int, reverse: bool) -> List[int]:
        """Counting sort by specific digit"""
        n = len(data)
        output = [0] * n
        count = [0] * 10

        # Count occurrences of each digit
        for num in data:
            digit_value = abs(num) // (10 ** digit) % 10
            count[digit_value] += 1

        # Modify count array to contain actual positions
        if reverse:
            for i in range(8, -1, -1):
                count[i] += count[i + 1]
        else:
            for i in range(1, 10):
                count[i] += count[i - 1]

        # Build output array
        for i in range(n - 1, -1, -1):
            digit_value = abs(data[i]) // (10 ** digit) % 10
            output[count[digit_value] - 1] = data[i]
            count[digit_value] -= 1

        return output

    def _bucket_sort(self, data: List[T], key: Callable = None, reverse: bool = False) -> List[T]:
        """Bucket sort for uniform distributions"""
        if not data:
            return data

        # Create buckets
        num_buckets = min(len(data) // 10, 100)  # Adaptive bucket count
        buckets = [[] for _ in range(num_buckets)]

        # Get min and max values
        values = [key(x) if key else x for x in data]
        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            return data  # All values are the same

        # Distribute elements into buckets
        for item in data:
            val = key(item) if key else item
            bucket_idx = int((val - min_val) / (max_val - min_val) * (num_buckets - 1))
            bucket_idx = max(0, min(bucket_idx, num_buckets - 1))
            buckets[bucket_idx].append(item)

        # Sort each bucket and combine
        result = []
        for bucket in buckets:
            if bucket:
                # Use insertion sort for small buckets
                if len(bucket) <= 20:
                    result.extend(self._insertion_sort(bucket, key, reverse))
                else:
                    # Use timsort for larger buckets
                    result.extend(sorted(bucket, key=key, reverse=reverse))

        return result

    def _insertion_sort(self, data: List[T], key: Callable = None, reverse: bool = False) -> List[T]:
        """Insertion sort for small arrays"""
        for i in range(1, len(data)):
            key_item = data[i]
            key_val = key(key_item) if key else key_item

            j = i - 1
            while j >= 0:
                current_val = key(data[j]) if key else data[j]
                if (key_val >= current_val) != reverse:
                    break
                data[j + 1] = data[j]
                j -= 1

            data[j + 1] = key_item

        return data

    def _record_metrics(self, metrics: AlgorithmMetrics):
        """Record algorithm performance metrics"""
        self.metrics_history.append(metrics)
        self.algorithm_performance[metrics.algorithm_name].append(metrics.execution_time)

        # Keep only recent metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history.pop(0)


class AdaptiveSearcher:
    """
    Intelligent search algorithm selector and executor.

    Automatically chooses the best search algorithm based on:
    - Data structure and size
    - Data distribution
    - Search pattern characteristics
    """

    def __init__(self):
        self.metrics_history = []

    def search(self, data: List[T], target: Any, key: Callable[[T], Any] = None) -> Optional[int]:
        """
        Search for target in data using optimal algorithm.

        Args:
            data: Sorted list to search in
            target: Value to search for
            key: Key function for comparison

        Returns:
            Index of target if found, None otherwise
        """
        if not data:
            return None

        data_size = len(data)
        data_type = self._analyze_search_data_type(data)
        distribution = self._analyze_search_distribution(data, key)

        # Select optimal algorithm
        algorithm = self._select_search_algorithm(data_size, data_type, distribution)

        start_time = time.time()

        try:
            if algorithm == SearchAlgorithm.BINARY_SEARCH:
                result = self._binary_search(data, target, key)
            elif algorithm == SearchAlgorithm.INTERPOLATION_SEARCH and distribution.get('is_uniform', False):
                result = self._interpolation_search(data, target, key)
            elif algorithm == SearchAlgorithm.FIBONACCI_SEARCH:
                result = self._fibonacci_search(data, target, key)
            elif algorithm == SearchAlgorithm.JUMP_SEARCH:
                result = self._jump_search(data, target, key)
            elif algorithm == SearchAlgorithm.EXPONENTIAL_SEARCH:
                result = self._exponential_search(data, target, key)
            else:
                # Fallback to binary search
                result = self._binary_search(data, target, key)

            # Record metrics
            execution_time = time.time() - start_time
            metrics = AlgorithmMetrics(
                algorithm_name=algorithm.value,
                execution_time=execution_time,
                input_size=data_size,
                success=result is not None
            )
            self.metrics_history.append(metrics)

            return result

        except Exception as e:
            logger.warning(f"Search failed with {algorithm.value}, falling back to binary search: {e}")
            return self._binary_search(data, target, key)

    def _analyze_search_data_type(self, data: List[T]) -> str:
        """Analyze data type for search algorithm selection"""
        if not data:
            return 'unknown'

        sample = data[:min(10, len(data))]

        if all(isinstance(x, (int, float)) for x in sample):
            return 'numeric'
        elif all(isinstance(x, str) for x in sample):
            return 'string'

        return 'mixed'

    def _analyze_search_distribution(self, data: List[T], key: Callable = None) -> Dict[str, Any]:
        """Analyze data distribution for search optimization"""
        if len(data) < 10:
            return {}

        values = [key(x) if key else x for x in data]

        try:
            # Check if data is uniformly distributed
            if len(values) >= 20:
                chunks = [values[i::5] for i in range(5)]  # Divide into 5 chunks
                chunk_means = [statistics.mean(chunk) for chunk in chunks if chunk]
                mean_variation = statistics.stdev(chunk_means) if len(chunk_means) > 1 else 0
                total_mean = statistics.mean(values)

                is_uniform = mean_variation < (abs(total_mean) * 0.1) if total_mean != 0 else False

                return {
                    'is_uniform': is_uniform,
                    'mean_variation': mean_variation
                }
        except (TypeError, ValueError):
            pass

        return {}

    def _select_search_algorithm(self, size: int, data_type: str, distribution: Dict[str, Any]) -> SearchAlgorithm:
        """Select optimal search algorithm"""

        # For very small datasets, linear search might be faster due to overhead
        if size <= 10:
            return SearchAlgorithm.BINARY_SEARCH  # Still use binary for consistency

        # For uniform numeric distributions, interpolation search is excellent
        if data_type == 'numeric' and distribution.get('is_uniform', False) and size > 100:
            return SearchAlgorithm.INTERPOLATION_SEARCH

        # For large datasets, exponential search can be good for unknown locations
        if size > 10000:
            return SearchAlgorithm.EXPONENTIAL_SEARCH

        # Default to binary search
        return SearchAlgorithm.BINARY_SEARCH

    def _binary_search(self, data: List[T], target: Any, key: Callable = None) -> Optional[int]:
        """Binary search implementation"""
        left, right = 0, len(data) - 1

        while left <= right:
            mid = (left + right) // 2
            mid_val = key(data[mid]) if key else data[mid]

            if mid_val == target:
                return mid
            elif mid_val < target:
                left = mid + 1
            else:
                right = mid - 1

        return None

    def _interpolation_search(self, data: List[T], target: Any, key: Callable = None) -> Optional[int]:
        """Interpolation search for uniform distributions"""
        left, right = 0, len(data) - 1

        # Get min and max values
        min_val = key(data[left]) if key else data[left]
        max_val = key(data[right]) if key else data[right]

        if min_val == max_val:
            # All values are the same
            if (key(data[0]) if key else data[0]) == target:
                return 0
            return None

        while left <= right and min_val <= target <= max_val:
            # Interpolation formula
            if key:
                left_val = key(data[left])
                right_val = key(data[right])
            else:
                left_val = data[left]
                right_val = data[right]

            if left_val == right_val:
                if left_val == target:
                    return left
                return None

            # Calculate position
            pos = left + int(((right - left) / (right_val - left_val)) * (target - left_val))

            # Ensure pos is within bounds
            pos = max(left, min(pos, right))

            if key:
                pos_val = key(data[pos])
            else:
                pos_val = data[pos]

            if pos_val == target:
                return pos
            elif pos_val < target:
                left = pos + 1
            else:
                right = pos - 1

        return None

    def _fibonacci_search(self, data: List[T], target: Any, key: Callable = None) -> Optional[int]:
        """Fibonacci search implementation"""
        n = len(data)

        # Initialize fibonacci numbers
        fib2 = 0  # (m-2)'th Fibonacci No.
        fib1 = 1  # (m-1)'th Fibonacci No.
        fib = fib2 + fib1  # m'th Fibonacci

        # fib stores the smallest Fibonacci number >= n
        while fib < n:
            fib2 = fib1
            fib1 = fib
            fib = fib2 + fib1

        # Marks the eliminated range from front
        offset = -1

        while fib > 1:
            # Check if fib2 is a valid location
            i = min(offset + fib2, n - 1)

            if key:
                val = key(data[i])
            else:
                val = data[i]

            if val < target:
                fib = fib1
                fib1 = fib2
                fib2 = fib - fib1
                offset = i
            elif val > target:
                fib = fib2
                fib1 = fib1 - fib2
                fib2 = fib - fib1
            else:
                return i

        # Comparing the last element
        if fib1 and offset + 1 < n:
            i = offset + 1
            if key:
                val = key(data[i])
            else:
                val = data[i]

            if val == target:
                return i

        return None

    def _jump_search(self, data: List[T], target: Any, key: Callable = None) -> Optional[int]:
        """Jump search implementation"""
        n = len(data)
        step = int(math.sqrt(n))

        # Find the block where target might be present
        prev = 0
        while prev < n:
            if key:
                val = key(data[min(prev + step, n) - 1])
            else:
                val = data[min(prev + step, n) - 1]

            if val < target:
                prev += step
            else:
                break

        # Linear search in the identified block
        for i in range(min(prev, n), min(prev + step, n)):
            if key:
                val = key(data[i])
            else:
                val = data[i]

            if val == target:
                return i

        return None

    def _exponential_search(self, data: List[T], target: Any, key: Callable = None) -> Optional[int]:
        """Exponential search implementation"""
        n = len(data)

        # If first element is target
        if key:
            first_val = key(data[0])
        else:
            first_val = data[0]

        if first_val == target:
            return 0

        # Find range for binary search
        i = 1
        while i < n:
            if key:
                val = key(data[i])
            else:
                val = data[i]

            if val <= target:
                i *= 2
            else:
                break

        # Binary search in found range
        left = i // 2
        right = min(i, n - 1)

        while left <= right:
            mid = (left + right) // 2
            if key:
                val = key(data[mid])
            else:
                val = data[mid]

            if val == target:
                return mid
            elif val < target:
                left = mid + 1
            else:
                right = mid - 1

        return None


# Global algorithm optimizers
_adaptive_sorter = AdaptiveSorter()
_adaptive_searcher = AdaptiveSearcher()


def optimized_sort(data: List[T], key: Callable[[T], Any] = None, reverse: bool = False) -> List[T]:
    """Globally optimized sort function"""
    return _adaptive_sorter.sort(data, key, reverse)


def optimized_search(data: List[T], target: Any, key: Callable[[T], Any] = None) -> Optional[int]:
    """Globally optimized search function"""
    return _adaptive_searcher.search(data, target, key)


def get_algorithm_metrics() -> Dict[str, Any]:
    """Get performance metrics for all algorithms"""
    return {
        'sorter_metrics': {
            'total_sorts': len(_adaptive_sorter.metrics_history),
            'algorithm_performance': dict(_adaptive_sorter.algorithm_performance),
            'recent_metrics': [
                {
                    'algorithm': m.algorithm_name,
                    'time': m.execution_time,
                    'size': m.input_size
                }
                for m in _adaptive_sorter.metrics_history[-10:]
            ]
        },
        'searcher_metrics': {
            'total_searches': len(_adaptive_searcher.metrics_history),
            'recent_metrics': [
                {
                    'algorithm': m.algorithm_name,
                    'time': m.execution_time,
                    'size': m.input_size,
                    'success': m.success
                }
                for m in _adaptive_searcher.metrics_history[-10:]
            ]
        }
    }


__all__ = [
    'AdaptiveSorter',
    'AdaptiveSearcher',
    'SortAlgorithm',
    'SearchAlgorithm',
    'AlgorithmMetrics',
    'optimized_sort',
    'optimized_search',
    'get_algorithm_metrics'
]
