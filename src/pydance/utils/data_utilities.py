"""
Data Manipulation Utilities for Pydance Framework.

This module provides utilities for data manipulation, transformation,
and processing operations.
"""

from typing import Any, Dict, List, Optional, Callable, TypeVar, Union, Iterator
import itertools
import copy
import json
from collections import defaultdict, deque

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class DataUtils:
    """Data manipulation utilities"""

    @staticmethod
    def deep_merge(dict1: Dict[K, V], dict2: Dict[K, V]) -> Dict[K, V]:
        """Deep merge two dictionaries"""
        if not isinstance(dict1, dict) or not isinstance(dict2, dict):
            raise TypeError("Both arguments must be dictionaries")

        result = copy.deepcopy(dict1)

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    @staticmethod
    def flatten_dict(d: Dict[str, Any], prefix: str = '', separator: str = '.') -> Dict[str, Any]:
        """Flatten a nested dictionary with customizable separator"""
        if not isinstance(d, dict):
            raise TypeError("Input must be a dictionary")

        items = []
        for k, v in d.items():
            new_key = f"{prefix}{separator}{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, separator).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def unflatten_dict(d: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
        """Unflatten a flattened dictionary"""
        if not isinstance(d, dict):
            raise TypeError("Input must be a dictionary")

        result = {}
        for key, value in d.items():
            parts = key.split(separator)
            current = result

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    @staticmethod
    def group_by(iterable: Iterator[T], key_func: Callable[[T], K]) -> Dict[K, List[T]]:
        """Group items by a key function"""
        groups = defaultdict(list)
        for item in iterable:
            key = key_func(item)
            groups[key].append(item)
        return dict(groups)

    @staticmethod
    def chunk(iterable: Iterator[T], size: int) -> Iterator[List[T]]:
        """Split iterable into chunks of specified size"""
        if size <= 0:
            raise ValueError("Chunk size must be positive")

        iterator = iter(iterable)
        while True:
            chunk = list(itertools.islice(iterator, size))
            if not chunk:
                break
            yield chunk

    @staticmethod
    def unique(iterable: Iterator[T], key_func: Optional[Callable[[T], Any]] = None) -> List[T]:
        """Get unique items from iterable"""
        seen = set()
        result = []

        for item in iterable:
            key = key_func(item) if key_func else item
            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

    @staticmethod
    def partition(predicate: Callable[[T], bool], iterable: Iterator[T]) -> tuple:
        """Partition iterable into two lists based on predicate"""
        true_items, false_items = [], []

        for item in iterable:
            if predicate(item):
                true_items.append(item)
            else:
                false_items.append(item)

        return true_items, false_items

    @staticmethod
    def find_first(predicate: Callable[[T], bool], iterable: Iterator[T], default: Optional[T] = None) -> Optional[T]:
        """Find first item matching predicate"""
        return next((item for item in iterable if predicate(item)), default)

    @staticmethod
    def count_occurrences(iterable: Iterator[T]) -> Dict[T, int]:
        """Count occurrences of each item"""
        return dict(itertools.Counter(iterable))

    @staticmethod
    def sliding_window(iterable: Iterator[T], size: int) -> Iterator[tuple]:
        """Create sliding window of specified size"""
        if size <= 0:
            raise ValueError("Window size must be positive")

        iterators = itertools.tee(iterable, size)
        for i, iterator in enumerate(iterators):
            next(itertools.islice(iterator, i, i), None)

        return zip(*iterators)

    @staticmethod
    def transpose(matrix: List[List[T]]) -> List[List[T]]:
        """Transpose a matrix (list of lists)"""
        if not matrix:
            return []

        # Check if all rows have the same length
        first_row_len = len(matrix[0])
        if not all(len(row) == first_row_len for row in matrix):
            raise ValueError("All rows must have the same length")

        return [list(row) for row in zip(*matrix)]

    @staticmethod
    def remove_none_values(d: Dict[K, Optional[V]]) -> Dict[K, V]:
        """Remove None values from dictionary"""
        return {k: v for k, v in d.items() if v is not None}

    @staticmethod
    def pick_keys(d: Dict[K, V], keys: List[K]) -> Dict[K, V]:
        """Pick specific keys from dictionary"""
        return {k: d[k] for k in keys if k in d}

    @staticmethod
    def omit_keys(d: Dict[K, V], keys: List[K]) -> Dict[K, V]:
        """Omit specific keys from dictionary"""
        return {k: v for k, v in d.items() if k not in keys}

    @staticmethod
    def rename_keys(d: Dict[K, V], key_map: Dict[K, K]) -> Dict[K, V]:
        """Rename keys in dictionary"""
        result = {}
        for old_key, value in d.items():
            new_key = key_map.get(old_key, old_key)
            result[new_key] = value
        return result

    @staticmethod
    def safe_get(d: Dict[K, Any], key: K, default: Any = None, path: Optional[str] = None) -> Any:
        """Safely get nested dictionary value"""
        if path:
            keys = path.split('.')
            current = d
            try:
                for k in keys:
                    current = current[k]
                return current
            except (KeyError, TypeError):
                return default
        else:
            return d.get(key, default)


class CollectionUtils:
    """Collection manipulation utilities"""

    @staticmethod
    def zip_with_keys(keys: List[K], values: List[V]) -> Dict[K, V]:
        """Create dictionary from keys and values lists"""
        if len(keys) != len(values):
            raise ValueError("Keys and values must have the same length")
        return dict(zip(keys, values))

    @staticmethod
    def interleave(*iterables: Iterator[T]) -> Iterator[T]:
        """Interleave multiple iterables"""
        return itertools.chain.from_iterable(zip(*iterables))

    @staticmethod
    def take_while(predicate: Callable[[T], bool], iterable: Iterator[T]) -> Iterator[T]:
        """Take items while predicate is true"""
        for item in iterable:
            if not predicate(item):
                break
            yield item

    @staticmethod
    def drop_while(predicate: Callable[[T], bool], iterable: Iterator[T]) -> Iterator[T]:
        """Drop items while predicate is true, then return rest"""
        iterator = iter(iterable)
        for item in iterator:
            if not predicate(item):
                yield item
                break
        yield from iterator

    @staticmethod
    def frequencies(iterable: Iterator[T]) -> Dict[T, int]:
        """Count frequencies of items (alias for count_occurrences)"""
        return DataUtils.count_occurrences(iterable)


class JSONUtils:
    """JSON manipulation utilities"""

    @staticmethod
    def safe_json_loads(s: str, default: Any = None) -> Any:
        """Safely parse JSON string"""
        try:
            return json.loads(s)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def safe_json_dumps(obj: Any, default: Any = None, **kwargs) -> Optional[str]:
        """Safely serialize to JSON string"""
        try:
            return json.dumps(obj, **kwargs)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def pretty_json(obj: Any, indent: int = 2) -> str:
        """Pretty print JSON"""
        return json.dumps(obj, indent=indent, sort_keys=True)


# Convenience functions
def deep_merge(dict1, dict2):
    """Deep merge dictionaries"""
    return DataUtils.deep_merge(dict1, dict2)

def flatten_dict(d, prefix='', separator='.'):
    """Flatten nested dictionary"""
    return DataUtils.flatten_dict(d, prefix, separator)

def group_by(iterable, key_func):
    """Group items by key function"""
    return DataUtils.group_by(iterable, key_func)

def chunk(iterable, size):
    """Split into chunks"""
    return list(DataUtils.chunk(iterable, size))

def unique(iterable, key_func=None):
    """Get unique items"""
    return DataUtils.unique(iterable, key_func)

def partition(predicate, iterable):
    """Partition by predicate"""
    return DataUtils.partition(predicate, iterable)

def safe_get(d, key, default=None, path=None):
    """Safely get nested value"""
    return DataUtils.safe_get(d, key, default, path)
