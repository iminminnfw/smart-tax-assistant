"""
SEC API Client with Rate Limiting and Retry Logic
Handles HTTP 421, exponential backoff, caching, and pagination

New SEC Open Data Portal (Jan 2026):
- Pagination: 100 items per page (fixed by SEC)
- Use current_page parameter to navigate pages
- Response includes: total_pages, total_items, page_size, items

Uses curl_cffi with browser impersonation to bypass bot detection.
"""

from curl_cffi import requests as curl_requests
from curl_cffi.requests import AsyncSession
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
    Updated for New SEC Open Data Portal (Jan 2026)

    Features:
    - Rate limiting (5,000 req/300s - New Portal)
    - Single API Key for all endpoints
    - HTTP 421 handling with Retry-After
    - Exponential backoff
    - Request/response logging
    - Browser impersonation (curl_cffi) to bypass bot detection

    Usage:
        client = SECAPIClient()
        funds = await client.get_fund_list()
        nav = await client.get_nav("KFRMF")
    """

    # SEC API Base URLs (New Portal v1 - Jan 2026)
    BASE_URL = "https://api.sec.or.th/v1"

    # Legacy URLs (kept for reference)
    FUND_FACTSHEET_URL = "https://api.sec.or.th/FundFactsheet"
    FUND_DAILY_INFO_URL = "https://api.sec.or.th/FundDailyInfo"

    def __init__(
        self,
        rate_limiter: Optional[SECRateLimiter] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        api_key: Optional[str] = None,
        impersonate: str = "chrome110"
    ):
        self.rate_limiter = rate_limiter or SECRateLimiter()
        self.max_retries = max_retries
        self.timeout = timeout
        self.impersonate = impersonate  # Browser to impersonate

        # Load API Key from environment or parameter (New Portal uses single key)
        self.api_key = api_key or os.getenv("SEC_API_KEY")

        # Validate API Key
        if not self.api_key:
            logger.warning("⚠️ SEC_API_KEY not set! API calls may not work.")

        # curl_cffi session will be created per-request or use AsyncSession
        self._session: Optional[AsyncSession] = None

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
            f"(API Key: {'✅' if self.api_key else '❌'}, "
            f"Impersonate: {self.impersonate})"
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        api_type: str = "v1",
        **kwargs
    ) -> Dict[Any, Any]:
        """
        Make request with rate limiting and retry logic (using curl_cffi)

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/fund/general-info/amcs")
            api_type: "v1" (new portal), "factsheet", or "daily_info" (legacy)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            Exception: After max retries exceeded or unrecoverable error
        """

        # Select correct base URL based on api_type
        if api_type == "v1":
            base_url = self.BASE_URL
        elif api_type == "daily_info":
            base_url = self.FUND_DAILY_INFO_URL
        else:
            base_url = self.FUND_FACTSHEET_URL

        # Prepare headers with API Key (single key for all endpoints - New Portal)
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/json"
        headers["Cache-Control"] = "no-cache"
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        else:
            logger.warning("⚠️ No SEC_API_KEY set! Request may fail.")

        # Get params from kwargs
        params = kwargs.pop("params", None)

        for attempt in range(self.max_retries):
            try:
                # Wait for rate limiter
                await self.rate_limiter.acquire()

                # Make request using curl_cffi with browser impersonation
                request_start = time.time()
                url = f"{base_url}{endpoint}"

                logger.debug(f"Making request: {method} {url}")

                # Use asyncio.to_thread for sync curl_cffi call
                # This allows us to use curl_cffi's impersonation feature
                response = await asyncio.to_thread(
                    lambda: curl_requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        impersonate=self.impersonate,
                        timeout=self.timeout
                    )
                )

                request_duration = time.time() - request_start

                # Update stats
                self.stats["total_requests"] += 1

                # Check for rate limit error (HTTP 421)
                if response.status_code == 421:
                    self.stats["rate_limit_hits"] += 1
                    retry_after = self._parse_retry_after(dict(response.headers))

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
                if response.status_code >= 400:
                    error_text = response.text[:500] if response.text else "No response body"
                    logger.error(f"❌ HTTP {response.status_code}: {error_text}")

                    # Don't retry on client errors (4xx except 421)
                    if 400 <= response.status_code < 500 and response.status_code != 421:
                        self.stats["failed_requests"] += 1
                        raise Exception(f"HTTP {response.status_code}: {error_text}")

                    # Retry on server errors (5xx)
                    if attempt < self.max_retries - 1:
                        backoff = 2 ** attempt
                        logger.info(f"🔄 Retrying in {backoff}s...")
                        self.stats["retries"] += 1
                        self.stats["total_wait_time"] += backoff
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        self.stats["failed_requests"] += 1
                        raise Exception(f"HTTP {response.status_code} after max retries")

                # Log request timing
                if request_duration < 0.1:
                    logger.debug(
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

            except Exception as e:
                error_msg = str(e)

                # Check if it's a timeout
                if "timeout" in error_msg.lower():
                    logger.error(f"⏱️  Request timeout: {e}")
                else:
                    logger.error(f"❌ Request error: {e}")

                if attempt < self.max_retries - 1:
                    backoff = 2 ** attempt
                    logger.info(f"🔄 Retrying in {backoff}s...")
                    self.stats["retries"] += 1
                    self.stats["total_wait_time"] += backoff
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
    # Pagination Support (New SEC Portal - Jan 2026)
    # ============================================================

    async def _make_paginated_request(
        self,
        method: str,
        endpoint: str,
        api_type: str = "factsheet",
        max_pages: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make paginated request - automatically fetches all pages

        SEC API Pagination:
        - page_size: 100 (fixed, cannot be changed)
        - current_page: starts at 1
        - Response includes: total_pages, total_items, items

        Args:
            method: HTTP method
            endpoint: API endpoint
            api_type: "factsheet" or "daily_info"
            max_pages: Maximum pages to fetch (None = all pages)
            **kwargs: Additional request parameters

        Returns:
            Dict with all items combined and pagination metadata
        """
        all_items = []
        current_page = 1
        total_pages = 1
        total_items = 0
        page_size = 100  # Fixed by SEC

        # Get existing params or create new
        params = kwargs.pop("params", {})

        while current_page <= total_pages:
            # Check max_pages limit
            if max_pages and current_page > max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break

            # Set current page
            params["current_page"] = current_page

            logger.info(
                f"Fetching page {current_page}"
                f"{f'/{total_pages}' if total_pages > 1 else ''}"
                f" from {endpoint}"
            )

            # Make request
            response = await self._make_request(
                method=method,
                endpoint=endpoint,
                api_type=api_type,
                params=params,
                **kwargs
            )

            # Parse paginated response
            if isinstance(response, dict):
                # Update pagination info from response
                total_pages = response.get("total_pages", 1)
                total_items = response.get("total_items", 0)
                page_size = response.get("page_size", 100)
                response_page = response.get("current_page", current_page)

                # Get items from this page
                items = response.get("items", [])
                if items:
                    all_items.extend(items)
                    logger.info(
                        f"Page {response_page}: Got {len(items)} items "
                        f"(total so far: {len(all_items)})"
                    )
                else:
                    # No items, might be end of data
                    logger.info(f"Page {response_page}: No items returned")
                    break

            elif isinstance(response, list):
                # Old format: direct array (no pagination)
                all_items = response
                logger.info(f"Non-paginated response: {len(response)} items")
                break

            else:
                logger.warning(f"Unexpected response type: {type(response)}")
                break

            current_page += 1

        # Return combined result
        return {
            "items": all_items,
            "pagination": {
                "total_items": total_items if total_items else len(all_items),
                "total_pages": total_pages,
                "page_size": page_size,
                "fetched_pages": current_page - 1,
                "fetched_items": len(all_items)
            }
        }

    async def get_paginated(
        self,
        endpoint: str,
        api_type: str = "factsheet",
        page: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get a single page of paginated data

        Args:
            endpoint: API endpoint
            api_type: "factsheet" or "daily_info"
            page: Page number (starts at 1)
            **kwargs: Additional request parameters

        Returns:
            Single page response with pagination metadata
        """
        params = kwargs.pop("params", {})
        params["current_page"] = page

        return await self._make_request(
            "GET",
            endpoint,
            api_type=api_type,
            params=params,
            **kwargs
        )

    # ============================================================
    # SEC API Endpoints
    # ============================================================

    async def get_amcs(
        self,
        max_pages: Optional[int] = None
    ) -> List[Dict[Any, Any]]:
        """
        Get list of all Asset Management Companies (AMCs)

        Args:
            max_pages: Maximum pages to fetch (None = all pages)

        Returns:
            List of all AMC objects
        """
        logger.info("Fetching AMC list from SEC API v1 (paginated)")

        result = await self._make_paginated_request(
            "GET",
            "/fund/general-info/amcs",
            api_type="v1",
            max_pages=max_pages
        )

        logger.info(
            f"AMC list complete: {result['pagination']['fetched_items']} AMCs "
            f"from {result['pagination']['fetched_pages']} pages"
        )

        return result["items"]

    async def get_fund_list(
        self,
        search: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[Any, Any]]:
        """
        Get list of all funds (with automatic pagination)
        Uses /v1/fund/general-info/profiles endpoint

        Args:
            search: Search by fund name, abbreviation, or company name
            max_pages: Maximum pages to fetch (None = all pages)

        Returns:
            List of all fund objects with proj_abbr_name, fund_status, etc.
        """
        logger.info("Fetching fund list from SEC API v1 /profiles (paginated)")

        params = {}
        if search:
            params["ch"] = search

        result = await self._make_paginated_request(
            "GET",
            "/fund/general-info/profiles",
            api_type="v1",
            max_pages=max_pages,
            params=params
        )

        logger.info(
            f"Fund list complete: {result['pagination']['fetched_items']} funds "
            f"from {result['pagination']['fetched_pages']} pages"
        )

        return result["items"]

    async def get_fund_list_page(self, page: int = 1, search: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a single page of fund list

        Args:
            page: Page number (starts at 1)
            search: Search by fund name, abbreviation, or company name

        Returns:
            Paginated response with items and pagination info
        """
        logger.info(f"Fetching fund list page {page}")

        params = {}
        if search:
            params["ch"] = search

        return await self.get_paginated(
            "/fund/general-info/profiles",
            api_type="v1",
            page=page,
            params=params
        )

    async def get_fund_specifications(
        self,
        search: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[Any, Any]]:
        """
        Get fund specifications (fund type classifications)
        Uses /v1/fund/general-info/specifications endpoint

        Returns spec_code per fund (e.g., RMF, ThaiESG, CIV, etc.)

        Args:
            search: Search by proj_id or fund_class_name
            max_pages: Maximum pages to fetch (None = all pages)

        Returns:
            List of fund specification objects with proj_id, spec_code, spec_desc
        """
        logger.info("Fetching fund specifications from SEC API v1 (paginated)")

        params = {}
        if search:
            params["search"] = search

        result = await self._make_paginated_request(
            "GET",
            "/fund/general-info/specifications",
            api_type="v1",
            max_pages=max_pages,
            params=params
        )

        logger.info(
            f"Fund specifications complete: {result['pagination']['fetched_items']} specs "
            f"from {result['pagination']['fetched_pages']} pages"
        )

        return result["items"]

    async def get_tax_funds(
        self,
        fund_types: Optional[List[str]] = None,
        max_pages: Optional[int] = None
    ) -> Dict[str, List[Dict[Any, Any]]]:
        """
        Get tax-deductible funds (RMF, ThaiESG)
        Uses /v1/fund/general-info/profiles with search parameter
        to fetch only relevant funds (much faster than fetching all)

        Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (ซื้อได้ถึง 31 ธ.ค. 2567)
              SSF is no longer tax-deductible (ended Dec 31, 2024)

        Args:
            fund_types: List of fund types to fetch ["RMF", "ThaiESG"]
                       If None, fetches all tax fund types
            max_pages: Maximum pages per fund type (None = all)

        Returns:
            Dict with fund types as keys, list of funds as values
        """
        if fund_types is None:
            fund_types = ["RMF", "ThaiESG"]

        logger.info(f"Fetching tax funds: {fund_types}")

        results = {
            "RMF": [],
            "ThaiESG": [],
            "pagination": {}
        }

        # Search RMF funds directly using profiles API search
        if "RMF" in fund_types:
            logger.info("Searching for RMF funds...")
            rmf_funds = await self.get_fund_list(search="RMF", max_pages=max_pages)
            # Filter only active funds (Registered or IPO)
            for fund in rmf_funds:
                fund_status = fund.get("fund_status", "")
                fund_code = fund.get("proj_abbr_name", "").upper()
                if fund_status in ("Registered", "IPO") and "RMF" in fund_code:
                    results["RMF"].append(fund)

        # Search ThaiESG funds directly using profiles API search
        if "ThaiESG" in fund_types:
            logger.info("Searching for ThaiESG funds...")
            esg_funds = await self.get_fund_list(search="THAIESG", max_pages=max_pages)
            # Filter only active funds
            for fund in esg_funds:
                fund_status = fund.get("fund_status", "")
                if fund_status in ("Registered", "IPO"):
                    results["ThaiESG"].append(fund)

            # Also check fund_class_tax_incentive_type field
            # Some ThaiESG funds might not have "THAIESG" in name
            if not results["ThaiESG"]:
                logger.info("Trying broader ESG search...")
                esg_funds2 = await self.get_fund_list(search="ESG", max_pages=max_pages)
                for fund in esg_funds2:
                    fund_status = fund.get("fund_status", "")
                    tax_type = fund.get("fund_class_tax_incentive_type", "")
                    if fund_status in ("Registered", "IPO") and "Thai ESG" in tax_type:
                        results["ThaiESG"].append(fund)

        # Add summary
        results["pagination"] = {
            "rmf_count": len(results["RMF"]),
            "thai_esg_count": len(results["ThaiESG"]),
            "total_tax_funds": (
                len(results["RMF"]) +
                len(results["ThaiESG"])
            )
        }

        logger.info(
            f"Tax funds found: "
            f"RMF={len(results['RMF'])}, "
            f"ThaiESG={len(results['ThaiESG'])}"
        )

        return results

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
        Get detailed fund information using profiles API search

        Args:
            fund_code: Fund code (e.g., "KFRMF")

        Returns:
            Fund info object (first match)
        """
        logger.info(f"Fetching fund info for {fund_code}")
        funds = await self.get_fund_list(search=fund_code, max_pages=1)
        if funds:
            return funds[0]
        return {}

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
        """Close the HTTP client (no-op for curl_cffi sync requests)"""
        # curl_cffi handles connection cleanup automatically
        logger.info("SEC API Client closed")

    def make_request_sync(
        self,
        method: str,
        endpoint: str,
        api_type: str = "v1",
        **kwargs
    ) -> Dict[Any, Any]:
        """
        Make synchronous request (useful for simple scripts/testing)

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            api_type: "v1" (new portal), "factsheet", or "daily_info" (legacy)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data
        """
        # Select correct base URL based on api_type
        if api_type == "v1":
            base_url = self.BASE_URL
        elif api_type == "daily_info":
            base_url = self.FUND_DAILY_INFO_URL
        else:
            base_url = self.FUND_FACTSHEET_URL

        # Prepare headers
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/json"
        headers["Cache-Control"] = "no-cache"
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key

        params = kwargs.pop("params", None)
        url = f"{base_url}{endpoint}"

        # Wait for rate limiter (sync)
        self.rate_limiter.acquire_sync()

        self.stats["total_requests"] += 1

        response = curl_requests.get(
            url,
            headers=headers,
            params=params,
            impersonate=self.impersonate,
            timeout=self.timeout
        )

        if response.status_code == 200:
            self.stats["successful_requests"] += 1
            return response.json()
        else:
            self.stats["failed_requests"] += 1
            raise Exception(f"HTTP {response.status_code}: {response.text[:500]}")


# ============================================================
# Example Usage
# ============================================================

async def example_usage():
    """Example of how to use the SEC API client with curl_cffi"""

    # You can pass API key directly or set SEC_API_KEY environment variable
    client = SECAPIClient(
        api_key="55cd28016a844bc799d2e7a550e8f85a"  # Replace with your key
    )

    try:
        # Example 1: Get AMC list (Asset Management Companies)
        logger.info("=" * 60)
        logger.info("Example 1: Get AMC List (Page 1)")
        logger.info("=" * 60)

        amcs = await client.get_amcs(max_pages=1)
        logger.info(f"✅ Found {len(amcs)} AMCs")
        if amcs:
            for amc in amcs[:3]:
                logger.info(f"   - {amc.get('comp_name_th', 'N/A')}")

        # Example 2: Get fund list from /profiles (single page)
        logger.info("\n" + "=" * 60)
        logger.info("Example 2: Get Fund List from /profiles (Page 1)")
        logger.info("=" * 60)

        page1 = await client.get_fund_list_page(page=1)
        if isinstance(page1, dict):
            items = page1.get('items', [])
            logger.info(f"✅ Page 1: {len(items)} funds")
            logger.info(f"   Total pages: {page1.get('total_pages', 'N/A')}")
            logger.info(f"   Total items: {page1.get('total_items', 'N/A')}")
            if items:
                for fund in items[:3]:
                    logger.info(
                        f"   - {fund.get('proj_abbr_name', 'N/A')}: "
                        f"{fund.get('proj_name_th', 'N/A')} "
                        f"[{fund.get('fund_status', 'N/A')}]"
                    )

        # Example 3: Get tax funds (RMF, ThaiESG) - SSF หมดสิทธิ์แล้ว
        logger.info("\n" + "=" * 60)
        logger.info("Example 3: Get Tax Funds (RMF/ThaiESG only)")
        logger.info("Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (ended Dec 31, 2024)")
        logger.info("=" * 60)

        tax_funds = await client.get_tax_funds(max_pages=2)
        logger.info(f"✅ Tax funds summary: {tax_funds['pagination']}")

        # Show some RMF examples
        if tax_funds["RMF"]:
            logger.info(f"   Sample RMF funds ({len(tax_funds['RMF'])} total):")
            for fund in tax_funds["RMF"][:3]:
                logger.info(
                    f"     - {fund.get('proj_abbr_name', 'N/A')}: "
                    f"{fund.get('proj_name_th', 'N/A')}"
                )

        # Show some ThaiESG examples
        if tax_funds["ThaiESG"]:
            logger.info(f"   Sample ThaiESG funds ({len(tax_funds['ThaiESG'])} total):")
            for fund in tax_funds["ThaiESG"][:3]:
                logger.info(
                    f"     - {fund.get('proj_abbr_name', 'N/A')}: "
                    f"{fund.get('proj_name_th', 'N/A')}"
                )

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
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


def quick_test():
    """Quick sync test for SEC API connection"""
    print("🚀 Quick SEC API Test (curl_cffi)")

    client = SECAPIClient(
        api_key="55cd28016a844bc799d2e7a550e8f85a"  # Replace with your key
    )

    try:
        result = client.make_request_sync(
            "GET",
            "/fund/general-info/profiles",
            api_type="v1",
            params={"current_page": 1, "ch": "RMF"}
        )

        items = result.get('items', [])
        print(f"✅ SUCCESS! Got {len(items)} funds (searching 'RMF')")
        if items:
            print(f"   First fund: {items[0].get('proj_abbr_name', 'N/A')} - {items[0].get('proj_name_th', 'N/A')}")

        print(f"   Stats: {client.get_stats()}")

    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check for quick test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        # Run full async example
        asyncio.run(example_usage())

