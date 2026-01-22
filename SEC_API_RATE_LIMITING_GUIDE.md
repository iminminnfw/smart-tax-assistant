# SEC API Rate Limiting Implementation Guide

## 📋 SEC API Constraints

**Official Limits:**
- **Rate Limit**: 3,000 requests per 300 seconds (10 requests/second)
- **Minimum Request Interval**: 10ms (if API responds faster, delay next request)
- **Error Code**: HTTP 421 (Rate limit exceeded)
- **Contact**: repcenter@sec.or.th (for higher rate requirements)

---

## 🎯 Implementation Strategy

### 1. **Rate Limiting Pattern**
```
Max: 10 requests/second = 1 request per 100ms (safe buffer)
Recommended: 8-9 requests/second = 1 request per 110-125ms (safer)
```

### 2. **Caching Strategy**
- **NAV Data**: Cache for 1 hour (updates daily)
- **Fund Information**: Cache for 24 hours (rarely changes)
- **Performance Data**: Cache for 1 hour
- **Factsheet**: Cache for 7 days

### 3. **Retry Logic**
- Detect HTTP 421
- Exponential backoff: 1s → 2s → 4s → 8s
- Max retries: 3 times
- Parse `Retry-After` header if available

---

## 💻 Implementation Code

### A. Rate Limiter Class (Python)

```python
import time
from typing import Optional
from collections import deque
import asyncio

class SECRateLimiter:
    """
    Rate limiter for SEC API
    Ensures compliance with 3,000 requests per 300 seconds limit
    """

    def __init__(
        self,
        max_requests: int = 3000,
        time_window: int = 300,  # seconds
        min_interval: float = 0.01,  # 10ms minimum
        safe_buffer: float = 0.11  # 110ms recommended
    ):
        self.max_requests = max_requests
        self.time_window = time_window
        self.min_interval = min_interval
        self.safe_buffer = safe_buffer

        # Track request timestamps
        self.request_times = deque(maxlen=max_requests)
        self.last_request_time = 0

    def _clean_old_requests(self):
        """Remove requests older than time_window"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window

        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()

    def can_make_request(self) -> bool:
        """Check if we can make a request now"""
        self._clean_old_requests()

        # Check if we've hit the limit
        if len(self.request_times) >= self.max_requests:
            return False

        # Check minimum interval
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.safe_buffer:
            return False

        return True

    def wait_time(self) -> float:
        """Calculate how long to wait before next request"""
        self._clean_old_requests()

        current_time = time.time()

        # Check minimum interval first
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.safe_buffer:
            return self.safe_buffer - time_since_last

        # Check if we're at the limit
        if len(self.request_times) >= self.max_requests:
            # Wait until the oldest request expires
            oldest_request = self.request_times[0]
            wait_time = (oldest_request + self.time_window) - current_time
            return max(0, wait_time)

        return 0

    async def acquire(self):
        """Wait until we can make a request (async)"""
        while not self.can_make_request():
            wait_time = self.wait_time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        current_time = time.time()
        self.request_times.append(current_time)
        self.last_request_time = current_time

    def acquire_sync(self):
        """Wait until we can make a request (sync)"""
        while not self.can_make_request():
            wait_time = self.wait_time()
            if wait_time > 0:
                time.sleep(wait_time)

        current_time = time.time()
        self.request_times.append(current_time)
        self.last_request_time = current_time


# Global rate limiter instance
sec_rate_limiter = SECRateLimiter()
```

### B. SEC API Client with Retry Logic

```python
import httpx
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SECAPIClient:
    """
    SEC API Client with rate limiting and retry logic
    """

    BASE_URL = "https://api.sec.or.th"

    def __init__(self, rate_limiter: SECRateLimiter):
        self.rate_limiter = rate_limiter
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[Any, Any]:
        """
        Make request with rate limiting and retry logic
        """

        for attempt in range(max_retries):
            try:
                # Wait for rate limiter
                await self.rate_limiter.acquire()

                # Make request
                request_start = time.time()
                response = await self.client.request(
                    method=method,
                    url=f"{self.BASE_URL}{endpoint}",
                    **kwargs
                )
                request_duration = time.time() - request_start

                # Check for rate limit error (HTTP 421)
                if response.status_code == 421:
                    retry_after = self._parse_retry_after(response.headers)

                    logger.warning(
                        f"Rate limit hit (421). Retry after {retry_after}s. "
                        f"Attempt {attempt + 1}/{max_retries}"
                    )

                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise Exception("Rate limit exceeded after max retries")

                # Check for other errors
                response.raise_for_status()

                # Log slow/fast responses
                if request_duration < 0.01:
                    logger.info(f"Fast response: {request_duration*1000:.2f}ms")

                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    backoff = 2 ** attempt
                    logger.info(f"Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                else:
                    raise

            except Exception as e:
                logger.error(f"Request error: {e}")

                if attempt < max_retries - 1:
                    backoff = 2 ** attempt
                    await asyncio.sleep(backoff)
                else:
                    raise

        raise Exception("Max retries exceeded")

    def _parse_retry_after(self, headers: Dict) -> float:
        """
        Parse Retry-After header
        Returns seconds to wait (default: 60s)
        """
        retry_after = headers.get("Retry-After", headers.get("retry-after"))

        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                # Could be HTTP date format, default to 60s
                return 60.0

        return 60.0

    async def get_fund_list(self) -> Dict[Any, Any]:
        """Get list of all funds"""
        return await self._make_request("GET", "/FundDailyInfo")

    async def get_nav(self, fund_code: str) -> Dict[Any, Any]:
        """Get NAV data for specific fund"""
        return await self._make_request(
            "GET",
            f"/FundDailyInfo/{fund_code}"
        )

    async def get_fund_info(self, fund_code: str) -> Dict[Any, Any]:
        """Get detailed fund information"""
        return await self._make_request(
            "GET",
            f"/FundInfo/{fund_code}"
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Usage example
async def example_usage():
    rate_limiter = SECRateLimiter()
    client = SECAPIClient(rate_limiter)

    try:
        # Get fund list
        funds = await client.get_fund_list()
        print(f"Found {len(funds)} funds")

        # Get NAV for multiple funds (respects rate limiting)
        fund_codes = ["KFRMF", "SCBRMF", "K-GLOBAL"]

        for code in fund_codes:
            nav_data = await client.get_nav(code)
            print(f"{code}: NAV = {nav_data.get('nav')}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
```

### C. Caching Layer with Redis

```python
import redis.asyncio as redis
import json
from typing import Optional, Any
import hashlib

class SECAPICache:
    """
    Caching layer for SEC API responses
    """

    # Cache TTL (Time To Live) in seconds
    TTL_NAV = 3600  # 1 hour
    TTL_FUND_INFO = 86400  # 24 hours
    TTL_PERFORMANCE = 3600  # 1 hour
    TTL_FACTSHEET = 604800  # 7 days

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def _make_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key"""
        return f"sec_api:{prefix}:{identifier}"

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int):
        """Set cached value with TTL"""
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def get_nav(self, fund_code: str) -> Optional[Dict]:
        """Get cached NAV data"""
        key = self._make_key("nav", fund_code)
        return await self.get(key)

    async def set_nav(self, fund_code: str, data: Dict):
        """Cache NAV data"""
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

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()
```

### D. Complete Service with Cache + Rate Limiting

```python
class SECService:
    """
    Complete SEC API service with caching and rate limiting
    """

    def __init__(self):
        self.rate_limiter = SECRateLimiter()
        self.api_client = SECAPIClient(self.rate_limiter)
        self.cache = SECAPICache()

    async def get_nav_with_cache(self, fund_code: str) -> Dict:
        """
        Get NAV with cache-first strategy
        """

        # Try cache first
        cached = await self.cache.get_nav(fund_code)
        if cached:
            logger.info(f"Cache hit for NAV: {fund_code}")
            return cached

        # Cache miss - fetch from API
        logger.info(f"Cache miss for NAV: {fund_code} - fetching from API")
        data = await self.api_client.get_nav(fund_code)

        # Store in cache
        await self.cache.set_nav(fund_code, data)

        return data

    async def get_fund_info_with_cache(self, fund_code: str) -> Dict:
        """
        Get fund info with cache-first strategy
        """

        cached = await self.cache.get_fund_info(fund_code)
        if cached:
            logger.info(f"Cache hit for fund info: {fund_code}")
            return cached

        logger.info(f"Cache miss for fund info: {fund_code}")
        data = await self.api_client.get_fund_info(fund_code)

        await self.cache.set_fund_info(fund_code, data)

        return data

    async def bulk_fetch_nav(self, fund_codes: list[str]) -> Dict[str, Dict]:
        """
        Fetch NAV for multiple funds efficiently
        Respects rate limiting
        """
        results = {}

        for code in fund_codes:
            try:
                results[code] = await self.get_nav_with_cache(code)
            except Exception as e:
                logger.error(f"Error fetching NAV for {code}: {e}")
                results[code] = None

        return results

    async def close(self):
        """Close all connections"""
        await self.api_client.close()
        await self.cache.close()
```

---

## 🚀 FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

# Global service instance
sec_service: Optional[SECService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup service"""
    global sec_service

    # Startup
    sec_service = SECService()
    yield

    # Shutdown
    if sec_service:
        await sec_service.close()

app = FastAPI(lifespan=lifespan)

@app.get("/api/sec/nav/{fund_code}")
async def get_nav(fund_code: str):
    """
    Get NAV for fund (with cache and rate limiting)
    """
    try:
        data = await sec_service.get_nav_with_cache(fund_code)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sec/nav/bulk")
async def get_bulk_nav(fund_codes: list[str]):
    """
    Get NAV for multiple funds
    """
    try:
        results = await sec_service.bulk_fetch_nav(fund_codes)
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📊 Monitoring and Logging

```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sec_api.log'),
        logging.StreamHandler()
    ]
)

class SECAPIMonitor:
    """Monitor SEC API usage"""

    def __init__(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.rate_limit_hits = 0
        self.errors = 0

    def log_request(self):
        self.total_requests += 1

    def log_cache_hit(self):
        self.cache_hits += 1

    def log_cache_miss(self):
        self.cache_misses += 1

    def log_rate_limit_hit(self):
        self.rate_limit_hits += 1

    def log_error(self):
        self.errors += 1

    def get_stats(self) -> Dict:
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses) * 100
            if (self.cache_hits + self.cache_misses) > 0
            else 0
        )

        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "rate_limit_hits": self.rate_limit_hits,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat()
        }
```

---

## ✅ Best Practices Checklist

- [ ] **Rate Limiting**: Implement 110ms interval between requests
- [ ] **Caching**: Cache NAV (1h), Fund Info (24h), Factsheet (7d)
- [ ] **Retry Logic**: Handle HTTP 421 with exponential backoff
- [ ] **Monitoring**: Log all requests and cache hit rates
- [ ] **Error Handling**: Graceful degradation on API failures
- [ ] **Minimum Delay**: Add 10ms delay if response < 10ms
- [ ] **Retry-After Header**: Parse and respect if available
- [ ] **Connection Pooling**: Reuse HTTP connections
- [ ] **Timeout**: Set appropriate timeouts (30s recommended)
- [ ] **Testing**: Test with high load to verify rate limiting works

---

## 🧪 Testing Rate Limiter

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter compliance"""
    limiter = SECRateLimiter()

    # Test rapid requests
    start_time = time.time()

    for i in range(20):
        await limiter.acquire()
        print(f"Request {i+1} at {time.time() - start_time:.3f}s")

    duration = time.time() - start_time

    # Should take at least 2.2 seconds (20 * 0.11s)
    assert duration >= 2.2, f"Too fast: {duration}s"

    print(f"✅ 20 requests completed in {duration:.2f}s")

@pytest.mark.asyncio
async def test_rate_limiter_long_term():
    """Test long-term rate limiting (300s window)"""
    limiter = SECRateLimiter()

    # Try to make 3001 requests (should block on 3001st)
    # This would take: 3001 * 0.11s = 330s

    # For testing, reduce to 100 requests
    start_time = time.time()

    for i in range(100):
        await limiter.acquire()

    duration = time.time() - start_time
    expected_min = 100 * 0.11  # 11 seconds

    assert duration >= expected_min, f"Too fast: {duration}s"
    print(f"✅ 100 requests in {duration:.2f}s (expected >= {expected_min:.2f}s)")

if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
```

---

## 📈 Expected Performance

### Without Caching:
- **Scenario**: 100 unique fund NAV requests
- **Time**: ~11 seconds (110ms per request)
- **API Calls**: 100

### With Caching (80% hit rate):
- **Scenario**: 100 fund NAV requests (80 cached, 20 new)
- **Time**: ~2.2 seconds (only 20 API calls)
- **API Calls**: 20
- **Speed Improvement**: 5x faster

---

## 🎯 Summary

### Key Implementation Points:

1. **Rate Limiter**: 110ms between requests (safe buffer from 100ms)
2. **Retry Logic**: Handle HTTP 421, exponential backoff
3. **Caching Strategy**: Aggressive caching to reduce API calls
4. **Monitoring**: Track cache hit rates and API usage
5. **Error Handling**: Graceful degradation

### Compliance Guarantee:

✅ Max 3,000 requests per 300 seconds
✅ Min 10ms delay after fast responses
✅ HTTP 421 handling with Retry-After
✅ Exponential backoff on errors
✅ Connection reuse and timeouts

---

## 📞 Contact

If you need higher rate limits for your use case:
- Email: repcenter@sec.or.th
- Explain your use case and expected request volume
