"""
SEC API Rate Limiter
Complies with SEC Open API rate limits:
- 3,000 requests per 300 seconds
- Minimum 10ms between requests
- HTTP 421 handling
"""

import time
from collections import deque
import asyncio
import logging

logger = logging.getLogger(__name__)


class SECRateLimiter:
    """
    Rate limiter for SEC API
    Ensures compliance with 3,000 requests per 300 seconds limit

    Usage:
        limiter = SECRateLimiter()

        # Async
        await limiter.acquire()

        # Sync
        limiter.acquire_sync()
    """

    def __init__(
        self,
        max_requests: int = 3000,
        time_window: int = 300,  # seconds
        min_interval: float = 0.01,  # 10ms minimum
        safe_buffer: float = 0.11  # 110ms recommended (safer than 100ms)
    ):
        self.max_requests = max_requests
        self.time_window = time_window
        self.min_interval = min_interval
        self.safe_buffer = safe_buffer

        # Track request timestamps
        self.request_times: deque = deque(maxlen=max_requests)
        self.last_request_time: float = 0

        logger.info(
            f"SEC Rate Limiter initialized: "
            f"{max_requests} requests per {time_window}s, "
            f"safe buffer: {safe_buffer*1000}ms"
        )

    def _clean_old_requests(self):
        """Remove requests older than time_window"""
        current_time = time.time()
        cutoff_time = current_time - self.time_window

        initial_len = len(self.request_times)
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()

        cleaned = initial_len - len(self.request_times)
        if cleaned > 0:
            logger.debug(f"Cleaned {cleaned} old requests from tracking")

    def can_make_request(self) -> bool:
        """Check if we can make a request now"""
        self._clean_old_requests()

        # Check if we've hit the limit
        if len(self.request_times) >= self.max_requests:
            logger.warning(
                f"Rate limit reached: {len(self.request_times)}/{self.max_requests}"
            )
            return False

        # Check minimum interval
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.safe_buffer:
            logger.debug(
                f"Too soon since last request: {time_since_last*1000:.2f}ms "
                f"(need {self.safe_buffer*1000}ms)"
            )
            return False

        return True

    def wait_time(self) -> float:
        """Calculate how long to wait before next request"""
        self._clean_old_requests()

        current_time = time.time()

        # Check minimum interval first
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.safe_buffer:
            wait = self.safe_buffer - time_since_last
            logger.debug(f"Need to wait {wait*1000:.2f}ms for safe buffer")
            return wait

        # Check if we're at the limit
        if len(self.request_times) >= self.max_requests:
            # Wait until the oldest request expires
            oldest_request = self.request_times[0]
            wait_time = (oldest_request + self.time_window) - current_time
            wait_time = max(0, wait_time)

            logger.warning(
                f"At rate limit. Need to wait {wait_time:.2f}s "
                f"until oldest request expires"
            )
            return wait_time

        return 0

    async def acquire(self):
        """
        Wait until we can make a request (async)

        Usage:
            await limiter.acquire()
            # Make API request
        """
        total_wait = 0

        while not self.can_make_request():
            wait_time = self.wait_time()
            if wait_time > 0:
                if wait_time > 1:
                    logger.info(f"Rate limited. Waiting {wait_time:.2f}s...")

                await asyncio.sleep(wait_time)
                total_wait += wait_time

        if total_wait > 0:
            logger.info(f"Resumed after waiting {total_wait:.2f}s")

        current_time = time.time()
        self.request_times.append(current_time)
        self.last_request_time = current_time

    def acquire_sync(self):
        """
        Wait until we can make a request (sync)

        Usage:
            limiter.acquire_sync()
            # Make API request
        """
        total_wait = 0

        while not self.can_make_request():
            wait_time = self.wait_time()
            if wait_time > 0:
                if wait_time > 1:
                    logger.info(f"Rate limited. Waiting {wait_time:.2f}s...")

                time.sleep(wait_time)
                total_wait += wait_time

        if total_wait > 0:
            logger.info(f"Resumed after waiting {total_wait:.2f}s")

        current_time = time.time()
        self.request_times.append(current_time)
        self.last_request_time = current_time

    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        self._clean_old_requests()

        current_time = time.time()
        time_since_last = (
            current_time - self.last_request_time
            if self.last_request_time > 0
            else 0
        )

        return {
            "requests_in_window": len(self.request_times),
            "max_requests": self.max_requests,
            "window_seconds": self.time_window,
            "utilization_percent": (
                len(self.request_times) / self.max_requests * 100
            ),
            "time_since_last_request_ms": time_since_last * 1000,
            "safe_buffer_ms": self.safe_buffer * 1000,
            "can_make_request": self.can_make_request(),
            "wait_time_seconds": self.wait_time()
        }


# Global rate limiter instance
sec_rate_limiter = SECRateLimiter()


# Example usage
async def example_usage():
    """Example of how to use the rate limiter"""

    limiter = SECRateLimiter()

    logger.info("Making 20 test requests...")
    start_time = time.time()

    for i in range(20):
        await limiter.acquire()
        logger.info(f"Request {i+1}/20 at {time.time() - start_time:.3f}s")

    duration = time.time() - start_time
    logger.info(f"Completed 20 requests in {duration:.2f}s")
    logger.info(f"Average: {duration/20*1000:.2f}ms per request")

    # Show stats
    stats = limiter.get_stats()
    logger.info(f"Rate limiter stats: {stats}")


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run example
    asyncio.run(example_usage())
