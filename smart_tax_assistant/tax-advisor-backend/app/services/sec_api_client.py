"""
SEC API Client with Rate Limiting and Retry Logic
Handles HTTP 421, exponential backoff, and caching
"""

import httpx
import asyncio
import time
import os
from typing import Dict, Any, Optional, List
import logging

from .sec_rate_limiter import SECRateLimiter

logger = logging.getLogger(__name__)


class SECAPIClient:
    """
    SEC API Client with rate limiting and retry logic

    Features:
    - Rate limiting (3,000 req/300s)
    - HTTP 421 handling with Retry-After
    - Exponential backoff
    - Request/response logging
    - Connection pooling
    - Proper API Key authentication

    Usage:
        client = SECAPIClient()
        funds = await client.get_fund_list()
        nav = await client.get_nav("KFRMF")
    """

    # SEC API Base URLs
    FUND_FACTSHEET_URL = "https://api.sec.or.th/FundFactsheet"
    FUND_DAILY_INFO_URL = "https://api.sec.or.th/FundDailyInfo"

    def __init__(
        self,
        rate_limiter: Optional[SECRateLimiter] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        factsheet_api_key: Optional[str] = None,
        daily_info_api_key: Optional[str] = None
    ):
        self.rate_limiter = rate_limiter or SECRateLimiter()
        self.max_retries = max_retries

        # Load API Keys from environment or parameters
        self.factsheet_api_key = factsheet_api_key or os.getenv("FUND_FACTSHEET_API_KEY")
        self.daily_info_api_key = daily_info_api_key or os.getenv("FUND_DAILY_INFO_API_KEY")

        # Validate API Keys
        if not self.factsheet_api_key:
            logger.warning("⚠️ FUND_FACTSHEET_API_KEY not set! Some endpoints may not work.")
        if not self.daily_info_api_key:
            logger.warning("⚠️ FUND_DAILY_INFO_API_KEY not set! NAV endpoints may not work.")

        # Create HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0,
            "retries": 0,
            "total_wait_time": 0
        }

        logger.info(
            f"SEC API Client initialized "
            f"(Factsheet Key: {'✅' if self.factsheet_api_key else '❌'}, "
            f"DailyInfo Key: {'✅' if self.daily_info_api_key else '❌'})"
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        api_type: str = "factsheet",
        **kwargs
    ) -> Dict[Any, Any]:
        """
        Make request with rate limiting and retry logic

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/fund/dailynav")
            api_type: "factsheet" or "daily_info" to select correct API
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            Exception: After max retries exceeded or unrecoverable error
        """

        # Select correct base URL and API key based on api_type
        if api_type == "daily_info":
            base_url = self.FUND_DAILY_INFO_URL
            api_key = self.daily_info_api_key
        else:
            base_url = self.FUND_FACTSHEET_URL
            api_key = self.factsheet_api_key

        # Prepare headers with API Key
        headers = kwargs.pop("headers", {})
        if api_key:
            headers["Ocp-Apim-Subscription-Key"] = api_key
        else:
            logger.warning(f"⚠️ No API key for {api_type}! Request may fail.")

        for attempt in range(self.max_retries):
            try:
                # Wait for rate limiter
                await self.rate_limiter.acquire()

                # Make request
                request_start = time.time()

                response = await self.client.request(
                    method=method,
                    url=f"{base_url}{endpoint}",
                    headers=headers,
                    **kwargs
                )

                request_duration = time.time() - request_start

                # Update stats
                self.stats["total_requests"] += 1

                # Check for rate limit error (HTTP 421)
                if response.status_code == 421:
                    self.stats["rate_limit_hits"] += 1
                    retry_after = self._parse_retry_after(response.headers)

                    logger.warning(
                        f"⚠️  Rate limit hit (HTTP 421). "
                        f"Retry after {retry_after}s. "
                        f"Attempt {attempt + 1}/{self.max_retries}"
                    )

                    if attempt < self.max_retries - 1:
                        self.stats["retries"] += 1
                        self.stats["total_wait_time"] += retry_after
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        self.stats["failed_requests"] += 1
                        raise Exception(
                            "Rate limit exceeded after max retries. "
                            "Consider contacting repcenter@sec.or.th "
                            "for higher rate limits."
                        )

                # Check for other HTTP errors
                response.raise_for_status()

                # Log request timing
                if request_duration < 0.01:
                    logger.info(
                        f"⚡ Fast response: {request_duration*1000:.2f}ms "
                        f"for {method} {endpoint}"
                    )
                elif request_duration > 5:
                    logger.warning(
                        f"🐌 Slow response: {request_duration:.2f}s "
                        f"for {method} {endpoint}"
                    )

                self.stats["successful_requests"] += 1

                # Parse and return JSON
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"❌ HTTP error: {e.response.status_code} - {e}"
                )

                # Don't retry on client errors (4xx except 421)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 421:
                    self.stats["failed_requests"] += 1
                    raise

                # Retry on server errors (5xx)
                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt  # Exponential backoff
                    logger.info(f"🔄 Retrying in {backoff}s...")
                    self.stats["retries"] += 1
                    self.stats["total_wait_time"] += backoff
                    await asyncio.sleep(backoff)
                else:
                    self.stats["failed_requests"] += 1
                    raise

            except httpx.TimeoutException as e:
                logger.error(f"⏱️  Request timeout: {e}")

                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    logger.info(f"🔄 Retrying in {backoff}s...")
                    self.stats["retries"] += 1
                    await asyncio.sleep(backoff)
                else:
                    self.stats["failed_requests"] += 1
                    raise

            except Exception as e:
                logger.error(f"❌ Request error: {e}")

                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    logger.info(f"🔄 Retrying in {backoff}s...")
                    self.stats["retries"] += 1
                    await asyncio.sleep(backoff)
                else:
                    self.stats["failed_requests"] += 1
                    raise

        self.stats["failed_requests"] += 1
        raise Exception("Max retries exceeded")

    def _parse_retry_after(self, headers: Dict) -> float:
        """
        Parse Retry-After header from HTTP 421 response

        Args:
            headers: Response headers

        Returns:
            Seconds to wait (default: 60s if not found)
        """
        retry_after = headers.get("Retry-After") or headers.get("retry-after")

        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                # Could be HTTP date format
                logger.warning(
                    f"Cannot parse Retry-After: {retry_after}. "
                    "Using default 60s"
                )
                return 60.0

        return 60.0

    # ============================================================
    # SEC API Endpoints
    # ============================================================

    async def get_fund_list(self) -> List[Dict[Any, Any]]:
        """
        Get list of all funds

        Returns:
            List of fund objects
        """
        logger.info("Fetching fund list from SEC API")
        return await self._make_request("GET", "/fund/amc", api_type="factsheet")

    async def get_nav(self, fund_code: str, as_of_date: Optional[str] = None) -> Dict[Any, Any]:
        """
        Get NAV data for specific fund

        Args:
            fund_code: Fund code (e.g., "KFRMF")
            as_of_date: Date in YYYY-MM-DD format (optional)

        Returns:
            NAV data object
        """
        logger.info(f"Fetching NAV for {fund_code}")

        params = {}
        if as_of_date:
            params["asofdate"] = as_of_date

        return await self._make_request(
            "GET",
            f"/fund/dailynav/{fund_code}",
            api_type="daily_info",
            params=params
        )

    async def get_fund_info(self, fund_code: str) -> Dict[Any, Any]:
        """
        Get detailed fund information

        Args:
            fund_code: Fund code (e.g., "KFRMF")

        Returns:
            Fund info object
        """
        logger.info(f"Fetching fund info for {fund_code}")
        return await self._make_request(
            "GET",
            f"/fund/profile/{fund_code}",
            api_type="factsheet"
        )

    async def get_performance(
        self,
        fund_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[Any, Any]:
        """
        Get fund performance data

        Args:
            fund_code: Fund code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Performance data
        """
        logger.info(f"Fetching performance for {fund_code}")

        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return await self._make_request(
            "GET",
            f"/fund/performance/{fund_code}",
            api_type="factsheet",
            params=params
        )

    async def bulk_get_nav(self, fund_codes: List[str]) -> Dict[str, Any]:
        """
        Get NAV for multiple funds (with rate limiting)

        Args:
            fund_codes: List of fund codes

        Returns:
            Dict mapping fund_code to NAV data
        """
        logger.info(f"Bulk fetching NAV for {len(fund_codes)} funds")

        results = {}
        errors = {}

        for i, code in enumerate(fund_codes, 1):
            try:
                logger.info(f"Fetching {i}/{len(fund_codes)}: {code}")
                results[code] = await self.get_nav(code)

            except Exception as e:
                logger.error(f"Error fetching NAV for {code}: {e}")
                errors[code] = str(e)

        if errors:
            logger.warning(f"Failed to fetch {len(errors)} funds: {errors}")

        return {
            "successful": results,
            "failed": errors,
            "summary": {
                "total": len(fund_codes),
                "successful": len(results),
                "failed": len(errors)
            }
        }

    # ============================================================
    # Utility Methods
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics

        Returns:
            Stats dictionary
        """
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0
                else 0
            ),
            "rate_limiter_stats": self.rate_limiter.get_stats()
        }

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0,
            "retries": 0,
            "total_wait_time": 0
        }
        logger.info("Statistics reset")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("SEC API Client closed")


# ============================================================
# Example Usage
# ============================================================

async def example_usage():
    """Example of how to use the SEC API client"""

    client = SECAPIClient()

    try:
        # Get fund list
        logger.info("=" * 60)
        logger.info("Example 1: Get Fund List")
        logger.info("=" * 60)

        funds = await client.get_fund_list()
        logger.info(f"✅ Found {len(funds) if isinstance(funds, list) else 'N/A'} funds")

        # Get NAV for single fund
        logger.info("\n" + "=" * 60)
        logger.info("Example 2: Get NAV for Single Fund")
        logger.info("=" * 60)

        nav_data = await client.get_nav("KFRMF")
        logger.info(f"✅ NAV data: {nav_data}")

        # Bulk fetch NAV
        logger.info("\n" + "=" * 60)
        logger.info("Example 3: Bulk Fetch NAV")
        logger.info("=" * 60)

        fund_codes = ["KFRMF", "SCBRMF", "K-GLOBAL"]
        bulk_results = await client.bulk_get_nav(fund_codes)

        logger.info(f"✅ Bulk results: {bulk_results['summary']}")

        # Show statistics
        logger.info("\n" + "=" * 60)
        logger.info("Client Statistics")
        logger.info("=" * 60)

        stats = client.get_stats()
        for key, value in stats.items():
            if key != "rate_limiter_stats":
                logger.info(f"  {key}: {value}")

    except Exception as e:
        logger.error(f"❌ Example failed: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run example
    asyncio.run(example_usage())
