"""
SEC Service - Complete Integration
Combines rate limiting, API client, and caching for optimal SEC API usage
"""

from typing import Dict, Any, Optional, List
import logging

from .sec_rate_limiter import SECRateLimiter
from .sec_api_client import SECAPIClient
from .sec_cache import SECAPICache

logger = logging.getLogger(__name__)


class SECService:
    """
    Complete SEC API service with caching and rate limiting

    This service provides:
    - Automatic rate limiting (3,000 req/300s)
    - Redis caching with appropriate TTLs
    - HTTP 421 handling and retry logic
    - Comprehensive error handling
    - Performance monitoring

    Usage:
        service = SECService()

        # Get NAV with automatic caching
        nav = await service.get_nav("KFRMF")

        # Get fund info
        info = await service.get_fund_info("KFRMF")

        # Bulk operations
        results = await service.bulk_get_nav(["KFRMF", "SCBRMF"])
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        enable_cache: bool = True,
        rate_limiter: Optional[SECRateLimiter] = None
    ):
        # Initialize components
        self.rate_limiter = rate_limiter or SECRateLimiter()
        self.api_client = SECAPIClient(self.rate_limiter)
        self.cache = SECAPICache(redis_url, enabled=enable_cache)

        # Statistics
        self.stats = {
            "cache_saves": 0,  # API calls saved by cache
            "api_calls": 0     # Actual API calls made
        }

        logger.info(
            f"SEC Service initialized "
            f"(cache: {'enabled' if self.cache.enabled else 'disabled'})"
        )

    # ============================================================
    # NAV Operations
    # ============================================================

    async def get_nav(
        self,
        fund_code: str,
        as_of_date: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[Any, Any]:
        """
        Get NAV with cache-first strategy

        Args:
            fund_code: Fund code (e.g., "KFRMF")
            as_of_date: Date in YYYY-MM-DD format (optional)
            force_refresh: Skip cache and fetch from API

        Returns:
            NAV data
        """

        # Skip cache if force refresh or as_of_date specified
        if not force_refresh and as_of_date is None:
            # Try cache first
            cached = await self.cache.get_nav(fund_code)

            if cached:
                logger.info(f"✅ Cache hit for NAV: {fund_code}")
                self.stats["cache_saves"] += 1
                return cached

        # Cache miss or force refresh - fetch from API
        logger.info(
            f"📡 Fetching NAV from API: {fund_code} "
            f"({'force refresh' if force_refresh else 'cache miss'})"
        )

        data = await self.api_client.get_nav(fund_code, as_of_date)
        self.stats["api_calls"] += 1

        # Store in cache (only if no specific date)
        if as_of_date is None:
            await self.cache.set_nav(fund_code, data)

        return data

    async def bulk_get_nav(
        self,
        fund_codes: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get NAV for multiple funds efficiently
        Respects rate limiting and uses cache

        Args:
            fund_codes: List of fund codes
            force_refresh: Skip cache for all funds

        Returns:
            Dict with successful and failed results
        """
        logger.info(f"Bulk fetching NAV for {len(fund_codes)} funds")

        results = {}
        errors = {}
        cache_hits = 0

        for i, code in enumerate(fund_codes, 1):
            try:
                logger.info(f"Processing {i}/{len(fund_codes)}: {code}")

                # Try cache first (unless force refresh)
                if not force_refresh:
                    cached = await self.cache.get_nav(code)
                    if cached:
                        results[code] = cached
                        cache_hits += 1
                        logger.info(f"  ✅ Cache hit")
                        continue

                # Fetch from API
                logger.info(f"  📡 Fetching from API")
                data = await self.api_client.get_nav(code)
                results[code] = data
                self.stats["api_calls"] += 1

                # Cache it
                await self.cache.set_nav(code, data)

            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
                errors[code] = str(e)

        self.stats["cache_saves"] += cache_hits

        logger.info(
            f"✅ Bulk NAV complete: "
            f"{len(results)} successful, "
            f"{len(errors)} failed, "
            f"{cache_hits} from cache"
        )

        return {
            "successful": results,
            "failed": errors,
            "summary": {
                "total": len(fund_codes),
                "successful": len(results),
                "failed": len(errors),
                "cache_hits": cache_hits,
                "api_calls": len(fund_codes) - cache_hits
            }
        }

    # ============================================================
    # Fund Information Operations
    # ============================================================

    async def get_fund_info(
        self,
        fund_code: str,
        force_refresh: bool = False
    ) -> Dict[Any, Any]:
        """
        Get fund information with cache-first strategy

        Args:
            fund_code: Fund code
            force_refresh: Skip cache and fetch from API

        Returns:
            Fund info data
        """

        if not force_refresh:
            # Try cache first
            cached = await self.cache.get_fund_info(fund_code)

            if cached:
                logger.info(f"✅ Cache hit for fund info: {fund_code}")
                self.stats["cache_saves"] += 1
                return cached

        # Cache miss - fetch from API
        logger.info(f"📡 Fetching fund info from API: {fund_code}")

        data = await self.api_client.get_fund_info(fund_code)
        self.stats["api_calls"] += 1

        # Store in cache
        await self.cache.set_fund_info(fund_code, data)

        return data

    async def get_fund_list(
        self,
        force_refresh: bool = False
    ) -> List[Dict[Any, Any]]:
        """
        Get list of all funds with caching

        Args:
            force_refresh: Skip cache and fetch from API

        Returns:
            List of fund objects
        """

        if not force_refresh:
            # Try cache first
            cached = await self.cache.get_fund_list()

            if cached:
                logger.info("✅ Cache hit for fund list")
                self.stats["cache_saves"] += 1
                return cached

        # Cache miss - fetch from API
        logger.info("📡 Fetching fund list from API")

        data = await self.api_client.get_fund_list()
        self.stats["api_calls"] += 1

        # Store in cache
        await self.cache.set_fund_list(data)

        return data

    # ============================================================
    # Performance Operations
    # ============================================================

    async def get_performance(
        self,
        fund_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[Any, Any]:
        """
        Get fund performance data with caching

        Args:
            fund_code: Fund code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            force_refresh: Skip cache

        Returns:
            Performance data
        """

        # Only use cache if no date range specified
        if not force_refresh and start_date is None and end_date is None:
            cached = await self.cache.get_performance(fund_code)

            if cached:
                logger.info(f"✅ Cache hit for performance: {fund_code}")
                self.stats["cache_saves"] += 1
                return cached

        # Fetch from API
        logger.info(f"📡 Fetching performance from API: {fund_code}")

        data = await self.api_client.get_performance(
            fund_code,
            start_date,
            end_date
        )
        self.stats["api_calls"] += 1

        # Cache only if no date range
        if start_date is None and end_date is None:
            await self.cache.set_performance(fund_code, data)

        return data

    # ============================================================
    # Cache Management
    # ============================================================

    async def invalidate_fund_cache(self, fund_code: str):
        """
        Invalidate all cache entries for a specific fund

        Args:
            fund_code: Fund code
        """
        await self.cache.invalidate_fund(fund_code)
        logger.info(f"Cache invalidated for: {fund_code}")

    async def clear_cache(self):
        """Clear all SEC API cache"""
        await self.cache.clear_all()
        logger.info("All SEC API cache cleared")

    # ============================================================
    # Statistics and Monitoring
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics

        Returns:
            Combined stats from all components
        """
        cache_stats = self.cache.get_stats()
        api_stats = self.api_client.get_stats()

        total_operations = self.stats["cache_saves"] + self.stats["api_calls"]

        cache_efficiency = (
            self.stats["cache_saves"] / total_operations * 100
            if total_operations > 0
            else 0
        )

        return {
            "service_stats": {
                **self.stats,
                "total_operations": total_operations,
                "cache_efficiency_percent": round(cache_efficiency, 2)
            },
            "cache_stats": cache_stats,
            "api_client_stats": api_stats
        }

    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("SEC SERVICE STATISTICS")
        print("=" * 60)

        print("\n🎯 Service Stats:")
        for key, value in stats["service_stats"].items():
            print(f"  {key}: {value}")

        print("\n💾 Cache Stats:")
        for key, value in stats["cache_stats"].items():
            print(f"  {key}: {value}")

        print("\n📡 API Client Stats:")
        for key, value in stats["api_client_stats"].items():
            if key != "rate_limiter_stats":
                print(f"  {key}: {value}")

        print("=" * 60 + "\n")

    def reset_stats(self):
        """Reset all statistics"""
        self.stats = {
            "cache_saves": 0,
            "api_calls": 0
        }
        self.cache.reset_stats()
        self.api_client.reset_stats()
        logger.info("All statistics reset")

    # ============================================================
    # Cleanup
    # ============================================================

    async def close(self):
        """Close all connections"""
        await self.api_client.close()
        await self.cache.close()
        logger.info("SEC Service closed")


# ============================================================
# Example Usage
# ============================================================

async def example_usage():
    """Comprehensive example of SEC Service usage"""

    service = SECService(enable_cache=True)

    try:
        # Example 1: Get NAV (cache miss)
        print("\n" + "=" * 60)
        print("Example 1: Get NAV (First Time - Cache Miss)")
        print("=" * 60)

        nav1 = await service.get_nav("KFRMF")
        print(f"✅ NAV: {nav1}")

        # Example 2: Get NAV again (cache hit)
        print("\n" + "=" * 60)
        print("Example 2: Get NAV (Second Time - Cache Hit)")
        print("=" * 60)

        nav2 = await service.get_nav("KFRMF")
        print(f"✅ NAV: {nav2}")

        # Example 3: Bulk fetch with cache
        print("\n" + "=" * 60)
        print("Example 3: Bulk Fetch NAV")
        print("=" * 60)

        fund_codes = ["KFRMF", "SCBRMF", "K-GLOBAL"]
        bulk_results = await service.bulk_get_nav(fund_codes)
        print(f"✅ Summary: {bulk_results['summary']}")

        # Example 4: Force refresh
        print("\n" + "=" * 60)
        print("Example 4: Force Refresh (Skip Cache)")
        print("=" * 60)

        nav3 = await service.get_nav("KFRMF", force_refresh=True)
        print(f"✅ NAV: {nav3}")

        # Show statistics
        service.print_stats()

    except Exception as e:
        logger.error(f"❌ Example failed: {e}")

    finally:
        await service.close()


if __name__ == "__main__":
    import asyncio

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run example
    asyncio.run(example_usage())
