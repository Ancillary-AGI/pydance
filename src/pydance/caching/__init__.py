"""
Multi-level caching system for Pydance.
Provides in-memory, Redis, and CDN caching with cache hierarchies.
"""

from pydance.caching.cache_manager import CacheManager, CacheConfig, CacheLevel
from pydance.caching.memory_cache import MemoryCache
from pydance.caching.redis_cache import RedisCache
from pydance.caching.cdn_cache import CDNCache
from pydance.caching.cache_decorator import cache_result, invalidate_cache, cache_key
from pydance.caching.cache_metrics import CacheMetricsCollector

# Global cache manager instance
_cache_manager = None

def get_cache_manager(config=None) -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        from pydance.server.config import AppConfig
        app_config = config or AppConfig()
        cache_config = CacheConfig()
        _cache_manager = CacheManager(cache_config)
    return _cache_manager

__all__ = [
    'CacheManager', 'CacheConfig', 'CacheLevel',
    'MemoryCache', 'RedisCache', 'CDNCache',
    'cache_result', 'invalidate_cache', 'cache_key',
    'CacheMetricsCollector', 'get_cache_manager'
]
