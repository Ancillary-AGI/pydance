
from pydance.utils.logging import get_logger
"""
Advanced cache manager with multiple cache levels and strategies.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class CacheLevel(Enum):
    L1 = "L1"  # In-memory, fastest
    L2 = "L2"  # Redis, distributed
    L3 = "L3"  # CDN, global

class CacheStrategy(Enum):
    LRU = "LRU"  # Least Recently Used
    LFU = "LFU"  # Least Frequently Used
    TTL = "TTL"  # Time To Live
    WRITE_THROUGH = "WRITE_THROUGH"
    WRITE_BACK = "WRITE_BACK"

@dataclass
class CacheConfig:
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    ttl_seconds: int = 3600  # 1 hour
    strategy: CacheStrategy = CacheStrategy.LRU
    enable_compression: bool = True
    compression_threshold: int = 1024  # 1KB
    enable_metrics: bool = True
    enable_warmup: bool = False
    warmup_file: Optional[str] = None

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    size_bytes: int = 0
    compressed: bool = False

class CacheMetricsCollector:
    """Collects cache metrics for monitoring and performance analysis"""

    def __init__(self):
        self.total_hits = 0
        self.total_misses = 0
        self.level_hits = {}
        self.level_misses = {}

    def record_hit(self, level: CacheLevel):
        """Record a cache hit"""
        self.total_hits += 1
        self.level_hits[level] = self.level_hits.get(level, 0) + 1

    def record_miss(self):
        """Record a cache miss"""
        self.total_misses += 1

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate"""
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0

    def get_level_metrics(self) -> Dict[str, Any]:
        """Get metrics per level"""
        return {
            level.value: {
                "hits": self.level_hits.get(level, 0),
                "misses": self.level_misses.get(level, 0)
            }
            for level in CacheLevel
        }

    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage (placeholder)"""
        return {"used": 0, "available": 0}


class CacheManager:
    """
    Advanced cache manager with multiple levels and strategies.
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self.caches: Dict[CacheLevel, Any] = {}
        self.metrics = CacheMetricsCollector()
        self.logger = get_logger("cache_manager")
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize all cache levels."""
        # Initialize L1 (Memory) cache
        self.caches[CacheLevel.L1] = MemoryCache(self.config)

        # Initialize L2 (Redis) cache if available
        try:
            self.caches[CacheLevel.L2] = RedisCache(self.config)
            self.logger.info("Redis cache initialized")
        except Exception as e:
            self.logger.warning(f"Redis cache not available: {e}")

        # Initialize L3 (CDN) cache if configured
        try:
            self.caches[CacheLevel.L3] = CDNCache(self.config)
            self.logger.info("CDN cache initialized")
        except Exception as e:
            self.logger.warning(f"CDN cache not available: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache using hierarchy."""
        cache_key = self._generate_key(key)

        # Try L1 cache first
        if CacheLevel.L1 in self.caches:
            value = await self.caches[CacheLevel.L1].get(cache_key)
            if value is not None:
                self.metrics.record_hit(CacheLevel.L1)
                return value

        # Try L2 cache
        if CacheLevel.L2 in self.caches:
            value = await self.caches[CacheLevel.L2].get(cache_key)
            if value is not None:
                self.metrics.record_hit(CacheLevel.L2)
                # Populate L1 cache
                await self.caches[CacheLevel.L1].set(cache_key, value)
                return value

        # Try L3 cache
        if CacheLevel.L3 in self.caches:
            value = await self.caches[CacheLevel.L3].get(cache_key)
            if value is not None:
                self.metrics.record_hit(CacheLevel.L3)
                # Populate L1 and L2 caches
                await self.caches[CacheLevel.L1].set(cache_key, value)
                if CacheLevel.L2 in self.caches:
                    await self.caches[CacheLevel.L2].set(cache_key, value)
                return value

        self.metrics.record_miss()
        return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in all cache levels."""
        cache_key = self._generate_key(key)
        ttl = ttl_seconds or self.config.ttl_seconds

        success = True

        # Set in L1 cache
        if CacheLevel.L1 in self.caches:
            if not await self.caches[CacheLevel.L1].set(cache_key, value, ttl):
                success = False

        # Set in L2 cache (write-through)
        if CacheLevel.L2 in self.caches:
            if not await self.caches[CacheLevel.L2].set(cache_key, value, ttl):
                success = False

        # Set in L3 cache (write-back for CDN)
        if CacheLevel.L3 in self.caches:
            if not await self.caches[CacheLevel.L3].set(cache_key, value, ttl):
                success = False

        return success

    async def delete(self, key: str) -> bool:
        """Delete value from all cache levels."""
        cache_key = self._generate_key(key)

        success = True

        # Delete from all levels
        for level in self.caches.values():
            if not await level.delete(cache_key):
                success = False

        return success

    async def clear(self):
        """Clear all cache levels."""
        for level in self.caches.values():
            await level.clear()

    def _generate_key(self, key: str) -> str:
        """Generate cache key with namespace."""
        return f"pydance:{hashlib.md5(key.encode()).hexdigest()}"

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return {
            "total_hits": self.metrics.total_hits,
            "total_misses": self.metrics.total_misses,
            "hit_rate": self.metrics.hit_rate,
            "level_metrics": self.metrics.get_level_metrics(),
            "memory_usage": self.metrics.get_memory_usage()
        }

    async def warmup(self, data: Dict[str, Any]):
        """Warmup cache with provided data."""
        for key, value in data.items():
            await self.set(key, value)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        for level in self.caches.values():
            await level.invalidate_pattern(pattern)

# Global cache manager
cache_manager = CacheManager(CacheConfig())


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return cache_manager





class MemoryCache:
    """In-memory cache implementation with automatic cleanup"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._data = {}
        self._access_order = []
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start background cleanup task for expired entries"""
        import asyncio

        async def cleanup_expired():
            while True:
                try:
                    await asyncio.sleep(60)  # Run cleanup every minute
                    await self._cleanup_expired_entries()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Log error but don't stop cleanup task
                    print(f"Cache cleanup error: {e}")

        # Start cleanup task
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_expired())
        except RuntimeError:
            # No event loop available, cleanup will be manual
            pass

    async def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = []

        for key, entry in self._data.items():
            if entry.expires_at and now > entry.expires_at:
                expired_keys.append(key)

        for key in expired_keys:
            del self._data[key]

        if expired_keys:
            print(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key in self._data:
            entry = self._data[key]
            if entry.expires_at and datetime.now() > entry.expires_at:
                del self._data[key]
                return None
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            return entry.value
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> bool:
        """Set value in memory cache"""
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            expires_at=expires_at
        )
        self._data[key] = entry
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        if key in self._data:
            del self._data[key]
            return True
        return False

    async def clear(self):
        """Clear memory cache"""
        self._data.clear()
        self._access_order.clear()
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern"""
        keys_to_delete = [key for key in self._data.keys() if pattern in key]
        for key in keys_to_delete:
            del self._data[key]

    def __del__(self):
        """Cleanup when cache is destroyed"""
        if self._cleanup_task:
            self._cleanup_task.cancel()


class RedisCache:
    """Redis cache implementation with connection pooling and clustering"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis = None
        self._pool = None
        self._cluster = None

    async def initialize(self, redis_url: str = None):
        """Initialize Redis connection"""
        try:
            import aioredis
            from aioredis import Redis, ConnectionPool

            if redis_url:
                # Use connection pool for better performance
                self._pool = ConnectionPool.from_url(redis_url, max_connections=20)
                self._redis = Redis(connection_pool=self._pool)
            else:
                # Default connection
                self._redis = Redis()

            # Test connection
            await self._redis.ping()
            print("Redis cache connected successfully")

        except ImportError:
            print("aioredis not installed, Redis cache disabled")
        except Exception as e:
            print(f"Redis connection failed: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> bool:
        """Set value in Redis cache"""
        if not self._redis:
            return False
        try:
            # Serialize to JSON if possible
            try:
                serialized_value = json.dumps(value)
            except:
                serialized_value = str(value)

            if ttl_seconds:
                await self._redis.setex(key, ttl_seconds, serialized_value)
            else:
                await self._redis.set(key, serialized_value)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache"""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    async def clear(self):
        """Clear Redis cache"""
        if self._redis:
            await self._redis.flushdb()

    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern"""
        if not self._redis:
            return
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            print(f"Redis pattern invalidate error: {e}")

    async def close(self):
        """Close Redis connection"""
        if self._pool:
            await self._pool.disconnect()
        if self._redis:
            await self._redis.close()


class CDNCache:
    """CDN cache implementation"""

    def __init__(self, config: CacheConfig):
        self.config = config

    async def get(self, key: str) -> Optional[Any]:
        """Get value from CDN cache (placeholder)"""
        # This would integrate with a CDN service
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> bool:
        """Set value in CDN cache (placeholder)"""
        # This would integrate with a CDN service
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from CDN cache (placeholder)"""
        return True

    async def clear(self):
        """Clear CDN cache (placeholder)"""
        pass

    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern (placeholder)"""
        pass
