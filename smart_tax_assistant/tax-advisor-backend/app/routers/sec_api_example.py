"""
SEC API Endpoints (Example)
FastAPI routes for SEC API integration with rate limiting and caching

Add to main.py:
    from app.routers import sec_api_example
    app.include_router(sec_api_example.router, prefix="/api/sec", tags=["SEC API"])
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from contextlib import asynccontextmanager
import logging

from ..services.sec_service import SECService

logger = logging.getLogger(__name__)

# Global service instance (will be initialized in lifespan)
sec_service: Optional[SECService] = None


# ============================================================
# Lifespan Management
# ============================================================

@asynccontextmanager
async def lifespan(app):
    """
    Initialize and cleanup SEC service

    Add this to your main FastAPI app:
        app = FastAPI(lifespan=lifespan)
    """
    global sec_service

    # Startup
    logger.info("Initializing SEC service...")
    sec_service = SECService(
        redis_url="redis://localhost:6379",
        enable_cache=True
    )
    logger.info("✅ SEC service initialized")

    yield

    # Shutdown
    if sec_service:
        logger.info("Closing SEC service...")
        await sec_service.close()
        logger.info("✅ SEC service closed")


# ============================================================
# Router
# ============================================================

router = APIRouter()


# ============================================================
# Health Check
# ============================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns service status and statistics
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        stats = sec_service.get_stats()

        return {
            "status": "healthy",
            "service": "SEC API",
            "cache_enabled": sec_service.cache.enabled,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Fund List
# ============================================================

@router.get("/funds")
async def get_fund_list(
    force_refresh: bool = Query(
        False,
        description="Skip cache and fetch fresh data"
    )
):
    """
    Get list of all funds from SEC

    - **force_refresh**: Skip cache (default: false)

    Returns:
        List of fund objects with codes, names, and AMC info
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        funds = await sec_service.get_fund_list(force_refresh=force_refresh)

        return {
            "success": True,
            "count": len(funds) if isinstance(funds, list) else 0,
            "data": funds
        }

    except Exception as e:
        logger.error(f"Failed to fetch fund list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# NAV Operations
# ============================================================

@router.get("/nav/{fund_code}")
async def get_nav(
    fund_code: str,
    as_of_date: Optional[str] = Query(
        None,
        description="Date in YYYY-MM-DD format"
    ),
    force_refresh: bool = Query(
        False,
        description="Skip cache and fetch fresh data"
    )
):
    """
    Get NAV (Net Asset Value) for a specific fund

    - **fund_code**: Fund code (e.g., "KFRMF")
    - **as_of_date**: Optional date in YYYY-MM-DD format
    - **force_refresh**: Skip cache (default: false)

    Returns:
        NAV data including current value, date, and historical data
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        nav_data = await sec_service.get_nav(
            fund_code=fund_code,
            as_of_date=as_of_date,
            force_refresh=force_refresh
        )

        return {
            "success": True,
            "fund_code": fund_code,
            "data": nav_data
        }

    except Exception as e:
        logger.error(f"Failed to fetch NAV for {fund_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nav/bulk")
async def bulk_get_nav(
    fund_codes: List[str],
    force_refresh: bool = Query(
        False,
        description="Skip cache and fetch fresh data"
    )
):
    """
    Get NAV for multiple funds in one request

    This endpoint automatically handles rate limiting and uses cache
    when available for optimal performance.

    Request body:
    ```json
    ["KFRMF", "SCBRMF", "K-GLOBAL"]
    ```

    - **fund_codes**: List of fund codes
    - **force_refresh**: Skip cache for all funds (default: false)

    Returns:
        Dict with successful and failed results, plus summary
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    if not fund_codes:
        raise HTTPException(
            status_code=400,
            detail="fund_codes list cannot be empty"
        )

    if len(fund_codes) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 fund codes per request"
        )

    try:
        results = await sec_service.bulk_get_nav(
            fund_codes=fund_codes,
            force_refresh=force_refresh
        )

        return {
            "success": True,
            **results
        }

    except Exception as e:
        logger.error(f"Bulk NAV fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Fund Information
# ============================================================

@router.get("/fund/{fund_code}")
async def get_fund_info(
    fund_code: str,
    force_refresh: bool = Query(
        False,
        description="Skip cache and fetch fresh data"
    )
):
    """
    Get detailed information about a fund

    - **fund_code**: Fund code (e.g., "KFRMF")
    - **force_refresh**: Skip cache (default: false)

    Returns:
        Detailed fund information including:
        - Fund name and type
        - Investment policy
        - Risk level
        - Fees and expenses
        - AMC information
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        fund_info = await sec_service.get_fund_info(
            fund_code=fund_code,
            force_refresh=force_refresh
        )

        return {
            "success": True,
            "fund_code": fund_code,
            "data": fund_info
        }

    except Exception as e:
        logger.error(f"Failed to fetch fund info for {fund_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Performance
# ============================================================

@router.get("/performance/{fund_code}")
async def get_performance(
    fund_code: str,
    start_date: Optional[str] = Query(
        None,
        description="Start date in YYYY-MM-DD format"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date in YYYY-MM-DD format"
    ),
    force_refresh: bool = Query(
        False,
        description="Skip cache and fetch fresh data"
    )
):
    """
    Get fund performance data

    - **fund_code**: Fund code (e.g., "KFRMF")
    - **start_date**: Optional start date (YYYY-MM-DD)
    - **end_date**: Optional end date (YYYY-MM-DD)
    - **force_refresh**: Skip cache (default: false)

    Returns:
        Performance data including:
        - Historical returns
        - Sharpe ratio
        - Maximum drawdown
        - Volatility
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        performance = await sec_service.get_performance(
            fund_code=fund_code,
            start_date=start_date,
            end_date=end_date,
            force_refresh=force_refresh
        )

        return {
            "success": True,
            "fund_code": fund_code,
            "data": performance
        }

    except Exception as e:
        logger.error(f"Failed to fetch performance for {fund_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Cache Management
# ============================================================

@router.post("/cache/invalidate/{fund_code}")
async def invalidate_fund_cache(fund_code: str):
    """
    Invalidate cache for a specific fund

    This will force fresh data from SEC API on next request.

    - **fund_code**: Fund code to invalidate
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        await sec_service.invalidate_fund_cache(fund_code)

        return {
            "success": True,
            "message": f"Cache invalidated for {fund_code}"
        }

    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all SEC API cache

    WARNING: This will clear all cached data.
    Use with caution.
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        await sec_service.clear_cache()

        return {
            "success": True,
            "message": "All SEC API cache cleared"
        }

    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Statistics
# ============================================================

@router.get("/stats")
async def get_statistics():
    """
    Get comprehensive service statistics

    Returns:
        - Service stats (cache efficiency, operations)
        - Cache stats (hit rate, total requests)
        - API client stats (success rate, rate limit hits)
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        stats = sec_service.get_stats()

        return {
            "success": True,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stats/reset")
async def reset_statistics():
    """
    Reset all statistics counters

    This does not clear cache, only resets counters.
    """
    if sec_service is None:
        raise HTTPException(
            status_code=503,
            detail="SEC service not initialized"
        )

    try:
        sec_service.reset_stats()

        return {
            "success": True,
            "message": "Statistics reset"
        }

    except Exception as e:
        logger.error(f"Failed to reset statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
