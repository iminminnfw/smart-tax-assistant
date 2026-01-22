"""
SEC API Caching Layer
Reduces API calls by caching responses with appropriate TTLs
"""

import json
from typing import Optional, Any, Dict
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning(
        "redis package not installed. Install with: pip install redis"
    )

logger = logging.getLogger(__name__)


class SECAPICache:
    """
    Caching layer for SEC API responses

    Cache TTL (Time To Live) Strategy:
    - NAV Data: 1 hour (updates daily, but check more frequently)
    - Fund Info: 24 hours (rarely changes)
    - Performance Data: 1 hour
    - Factsheet: 7 days (very stable)

    Usage:
        cache = SECAPICache()

        # Try to get from cache
        data = await cache.get_nav("KFRMF")
        if data is None:
            # Cache miss - fetch from API
            data = await api.get_nav("KFRMF")
            # Store in cache
            await cache.set_nav("KFRMF", data)
    """

    # Cache TTL in seconds
    TTL_NAV = 3600  # 1 hour
    TTL_FUND_INFO = 86400  # 24 hours
    TTL_PERFORMANCE = 3600  # 1 hour
    TTL_FACTSHEET = 604800  # 7 days
    TTL_FUND_LIST = 86400  # 24 hours

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        enabled: bool = True
    ):
        self.enabled = enabled and REDIS_AVAILABLE

        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis not available. Caching will be disabled. "
                "Install redis with: pip install redis"
            )
            self.redis = None
            return

        if not enabled:
            logger.info("Caching disabled by configuration")
            self.redis = None
            return

        try:
            self.redis = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            logger.info(f"SEC API Cache initialized: {redis_url}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Continuing without cache")
            self.redis = None
            self.enabled = False

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }

    def _make_key(self, prefix: str, identifier: str) -> str:
        """
        Generate cache key

        Args:
            prefix: Key prefix (e.g., "nav", "fund_info")
            identifier: Unique identifier (e.g., fund code)

        Returns:
            Cache key (e.g., "sec_api:nav:KFRMF")
        """
        return f"sec_api:{prefix}:{identifier}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value

        Args:
            key: Cache key

        Returns:
            Cached value (parsed from JSON) or None if not found
        """
        if not self.enabled or self.redis is None:
            return None

        try:
            value = await self.redis.get(key)

            if value:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Cache JSON decode error for {key}: {e}")
            self.stats["errors"] += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            self.stats["errors"] += 1
            return None

    async def set(self, key: str, value: Any, ttl: int):
        """
        Set cached value with TTL

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
        """
        if not self.enabled or self.redis is None:
            return

        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )

            self.stats["sets"] += 1
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            self.stats["errors"] += 1

    async def delete(self, key: str):
        """
        Delete cached value

        Args:
            key: Cache key
        """
        if not self.enabled or self.redis is None:
            return

        try:
            await self.redis.delete(key)
            logger.debug(f"Cache deleted: {key}")

        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            self.stats["errors"] += 1

    # ============================================================
    # Specific Cache Methods
    # ============================================================

    async def get_nav(self, fund_code: str) -> Optional[Dict]:
        """
        Get cached NAV data

        Args:
            fund_code: Fund code (e.g., "KFRMF")

        Returns:
            NAV data or None
        """
        key = self._make_key("nav", fund_code)
        return await self.get(key)

    async def set_nav(self, fund_code: str, data: Dict):
        """
        Cache NAV data

        Args:
            fund_code: Fund code
            data: NAV data to cache
        """
        key = self._make_key("nav", fund_code)
        await self.set(key, data, self.TTL_NAV)

    async def get_fund_info(self, fund_code: str) -> Optional[Dict]:
        """Get cached fund info"""
        key = self._make_key("fund_info", fund_code)
        return await self.get(key)

    async def set_fund_info(self, fund_code: str, data: Dict):
        """Cache fund info"""
        key = self._make_key("fund_info", fund_code)
        await self.set(key, data, self.TTL_FUND_INFO)

    async def get_performance(self, fund_code: str) -> Optional[Dict]:
        """Get cached performance data"""
        key = self._make_key("performance", fund_code)
        return await self.get(key)

    async def set_performance(self, fund_code: str, data: Dict):
        """Cache performance data"""
        key = self._make_key("performance", fund_code)
        await self.set(key, data, self.TTL_PERFORMANCE)

    async def get_fund_list(self) -> Optional[list]:
        """Get cached fund list"""
        key = self._make_key("fund_list", "all")
        return await self.get(key)

    async def set_fund_list(self, data: list):
        """Cache fund list"""
        key = self._make_key("fund_list", "all")
        await self.set(key, data, self.TTL_FUND_LIST)

    async def invalidate_fund(self, fund_code: str):
        """
        Invalidate all cache entries for a fund

        Args:
            fund_code: Fund code
        """
        keys = [
            self._make_key("nav", fund_code),
            self._make_key("fund_info", fund_code),
            self._make_key("performance", fund_code)
        ]

        for key in keys:
            await self.delete(key)

        logger.info(f"Invalidated cache for fund: {fund_code}")

    # ============================================================
    # Utility Methods
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Statistics dictionary
        """
        total_requests = self.stats["hits"] + self.stats["misses"]

        hit_rate = (
            self.stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )

        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "enabled": self.enabled
        }

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }
        logger.info("Cache statistics reset")

    async def clear_all(self):
        """
        Clear all SEC API cache entries
        WARNING: This will delete all keys matching sec_api:*
        """
        if not self.enabled or self.redis is None:
            return

        try:
            # Scan for all sec_api:* keys
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match="sec_api:*",
                    count=100
                )

                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted} cache entries")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.stats["errors"] += 1

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("SEC API Cache closed")


# ============================================================
# Example Usage
# ============================================================

async def example_usage():
    """Example of how to use the cache"""

    cache = SECAPICache()

    if not cache.enabled:
        logger.warning("Cache is not enabled. Skipping example.")
        return

    try:
        # Simulate cache miss
        logger.info("=" * 60)
        logger.info("Example 1: Cache Miss")
        logger.info("=" * 60)

        nav_data = await cache.get_nav("KFRMF")
        logger.info(f"Cache result: {nav_data}")

        # Set cache
        logger.info("\n" + "=" * 60)
        logger.info("Example 2: Set Cache")
        logger.info("=" * 60)

        sample_data = {
            "fund_code": "KFRMF",
            "nav": 15.25,
            "date": "2025-01-10"
        }

        await cache.set_nav("KFRMF", sample_data)
        logger.info("✅ Data cached")

        # Cache hit
        logger.info("\n" + "=" * 60)
        logger.info("Example 3: Cache Hit")
        logger.info("=" * 60)

        nav_data = await cache.get_nav("KFRMF")
        logger.info(f"✅ Cache result: {nav_data}")

        # Show stats
        logger.info("\n" + "=" * 60)
        logger.info("Cache Statistics")
        logger.info("=" * 60)

        stats = cache.get_stats()
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    finally:
        await cache.close()


if __name__ == "__main__":
    import asyncio

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run example
    asyncio.run(example_usage())
