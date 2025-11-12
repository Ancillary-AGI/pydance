"""
SSR Cache for Pydance Framework.

This module provides caching capabilities for server-side rendered content
to improve performance and reduce server load.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0


class SSRCache:
    """
    High-performance cache for SSR content.

    Uses memory-based caching with TTL support and LRU eviction.
    """

    def __init__(self, max_size: int = 1000, ttl: int = 300, cleanup_interval: int = 60):
        self.max_size = max_size
        self.default_ttl = ttl
        self.cleanup_interval = cleanup_interval
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: list = []  # For LRU tracking

        # Start cleanup task
        self._cleanup_task = None

    async def start(self) -> None:
        """Start the cache cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the cache cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        entry = self.cache.get(key)

        if entry is None:
            return None

        # Check if expired
        if time.time() - entry.timestamp > entry.ttl:
            await self.delete(key)
            return None

        # Update access statistics
        entry.access_count += 1
        entry.last_accessed = time.time()

        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        return entry.data

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        if len(self.cache) >= self.max_size:
            await self._evict_lru()

        entry = CacheEntry(
            data=value,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )

        self.cache[key] = entry

        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        hit_rate = total_accesses / max(1, len(self.access_order))

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'access_order_length': len(self.access_order),
            'total_accesses': total_accesses,
            'hit_rate': hit_rate,
            'oldest_entry': min((e.timestamp for e in self.cache.values()), default=0),
            'newest_entry': max((e.timestamp for e in self.cache.values()), default=0)
        }

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.access_order:
            return

        # Remove oldest entry (first in access_order)
        oldest_key = self.access_order.pop(0)
        if oldest_key in self.cache:
            del self.cache[oldest_key]

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cache cleanup: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = []

        for key, entry in self.cache.items():
            if current_time - entry.timestamp > entry.ttl:
                expired_keys.append(key)

        for key in expired_keys:
            await self.delete(key)

    def generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({
            'args': args,
            'kwargs': kwargs
        }, sort_keys=True)

        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    async def get_or_set(
        self,
        key: str,
        factory_func: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or set using factory function."""
        value = await self.get(key)
        if value is None:
            value = await factory_func()
            await self.set(key, value, ttl)
        return value

    async def batch_get(self, keys: list) -> Dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        for key in keys:
            results[key] = await self.get(key)
        return results

    async def batch_set(self, items: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set multiple values in cache."""
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def increment_access_count(self, key: str) -> int:
        """Increment and return access count for a key."""
        entry = self.cache.get(key)
        if entry:
            entry.access_count += 1
            entry.last_accessed = time.time()
            return entry.access_count
        return 0

