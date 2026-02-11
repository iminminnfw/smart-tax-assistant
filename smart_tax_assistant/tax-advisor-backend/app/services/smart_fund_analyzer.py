"""
Smart Fund Analyzer - Deep Investment Intelligence Engine
=========================================================

This module implements 4 Critical Intelligence Layers for the Smart Tax Assistant:

1. TRUE EXPOSURE INTELLIGENCE (API 3: Specifications)
   - Detect Feeder Funds (CIV, FIF, FOF)
   - Warn about Currency Risk, Layered Fees
   - Identify Master Fund exposure (ARK, BlackRock, etc.)

2. RELATIVE PERFORMANCE INTELLIGENCE (API 8 + 12: Benchmark + Statistics)
   - Contextualize Alpha with actual benchmark name
   - Generate human-readable performance narratives
   - Evaluate fund manager skill vs passive alternatives

3. TAX TRAP INTELLIGENCE (API 13: Dividend Policy)
   - Filter Accumulating vs Dividend-paying funds
   - Calculate dividend tax leakage for high-income users
   - Recommend tax-efficient alternatives

4. TRUST & COMPLIANCE INTELLIGENCE (API 6: Factsheet URLs)
   - Attach official SEC PDF links to every recommendation
   - Show data freshness (as_of_date)
   - Generate regulatory disclaimers

Author: Smart Tax Assistant Team
Version: 1.0.0 (Jan 2026)
"""

import asyncio
import logging
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict

# Import existing SEC API Client
from .sec_api_client import SECAPIClient

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class FundType(str, Enum):
    """Tax-deductible fund types in Thailand (2568)"""
    RMF = "RMF"
    THAI_ESG = "ThaiESG"
    # Note: SSF ended Dec 31, 2024


class ExposureType(str, Enum):
    """Fund exposure classification"""
    DOMESTIC = "domestic"
    GLOBAL = "global"
    MIXED = "mixed"


class RiskSeverity(str, Enum):
    """Risk warning severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DividendPolicy(str, Enum):
    """Dividend policy types"""
    ACCUMULATING = "N"  # No dividend - reinvests
    DISTRIBUTING = "Y"  # Pays dividends


class TaxEfficiencyRating(str, Enum):
    """Tax efficiency classification"""
    OPTIMAL = "optimal"
    GOOD = "good"
    SUBOPTIMAL = "suboptimal"
    INEFFICIENT = "inefficient"


# Feeder Fund Detection Codes (from SEC spec_code)
FEEDER_FUND_CODES = {
    "CIV": "Collective Investment Vehicle (กองทุนรวมที่ลงทุนในกองทุนรวมอื่น)",
    "FIF": "Foreign Investment Fund (ลงทุนในต่างประเทศ)",
    "FOF": "Fund of Funds (ลงทุนในกองทุนอื่นเป็นหลัก)",
}

# Known Master Fund Keywords
MASTER_FUND_KEYWORDS = [
    "ARK", "BlackRock", "Fidelity", "Vanguard", "iShares",
    "PIMCO", "JPMorgan", "Goldman", "Morgan Stanley",
    "Invesco", "Schroders", "Aberdeen", "Franklin",
    "UBS", "HSBC", "DWS", "Amundi", "BNP"
]

# Thai Tax Brackets (2568)
TAX_BRACKETS = [
    (150_000, 0.00),
    (300_000, 0.05),
    (500_000, 0.10),
    (750_000, 0.15),
    (1_000_000, 0.20),
    (2_000_000, 0.25),
    (5_000_000, 0.30),
    (float('inf'), 0.35),
]

DIVIDEND_WITHHOLDING_TAX = 0.10  # 10% flat rate


# ============================================================
# PYDANTIC OUTPUT MODELS
# ============================================================

class RiskWarning(BaseModel):
    """A single risk warning from intelligence analysis"""
    model_config = ConfigDict(use_enum_values=True)

    warning_type: str = Field(..., description="Type of warning (CURRENCY_RISK, LAYERED_FEES, etc.)")
    severity: RiskSeverity = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable warning message (Thai)")
    message_en: Optional[str] = Field(None, description="English version")
    mitigation: Optional[str] = Field(None, description="How to mitigate this risk")
    data_source: Optional[str] = Field(None, description="API source for this warning")


class TrueExposureAnalysis(BaseModel):
    """Layer 1: True Exposure Intelligence Output"""
    model_config = ConfigDict(use_enum_values=True)

    exposure_type: ExposureType = Field(..., description="domestic/global/mixed")
    is_feeder_fund: bool = Field(..., description="Whether this is a Feeder/FOF")
    spec_code: Optional[str] = Field(None, description="SEC specification code")
    spec_description: Optional[str] = Field(None, description="SEC specification description")
    master_fund_name: Optional[str] = Field(None, description="Identified master fund")
    master_fund_region: Optional[str] = Field(None, description="Master fund region (US, EU, etc.)")
    fx_hedging_percent: Optional[float] = Field(None, description="FX hedging percentage if available")
    warnings: List[RiskWarning] = Field(default_factory=list, description="Risk warnings")
    recommendation: str = Field("", description="Summary recommendation")


class BenchmarkComparison(BaseModel):
    """Benchmark comparison data for performance context"""
    benchmark_name: str = Field(..., description="Official benchmark name")
    benchmark_name_th: Optional[str] = Field(None, description="Thai name if available")
    fund_return: Optional[float] = Field(None, description="Fund return for comparison period")
    benchmark_return: Optional[float] = Field(None, description="Benchmark return (if available)")
    outperformance: Optional[float] = Field(None, description="Fund return - Benchmark return")


class PerformanceNarrative(BaseModel):
    """Layer 2: Relative Performance Intelligence Output"""
    model_config = ConfigDict(use_enum_values=True)

    # Raw statistics from API 12
    alpha: Optional[float] = Field(None, description="Alpha (excess return vs benchmark)")
    beta: Optional[float] = Field(None, description="Beta (market sensitivity)")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe Ratio (risk-adjusted return)")
    max_drawdown: Optional[float] = Field(None, description="Maximum Drawdown")
    tracking_error: Optional[float] = Field(None, description="Tracking Error")

    # Contextualized analysis
    benchmark: BenchmarkComparison = Field(..., description="Benchmark comparison")

    # Human-readable narratives (Thai)
    alpha_narrative: str = Field("", description="Contextualized Alpha explanation")
    beta_narrative: str = Field("", description="Beta risk explanation")
    sharpe_narrative: str = Field("", description="Risk-adjusted return explanation")
    overall_verdict: str = Field("", description="Overall performance verdict")

    # Manager skill assessment
    shows_manager_skill: bool = Field(False, description="Whether Alpha suggests skill")
    recommend_index_alternative: bool = Field(False, description="Whether to suggest passive fund")


class TaxEfficiencyAnalysis(BaseModel):
    """Layer 3: Tax Trap Intelligence Output"""
    model_config = ConfigDict(use_enum_values=True)

    dividend_policy: Optional[DividendPolicy] = Field(None, description="Y=Distributing, N=Accumulating")
    dividend_policy_description: Optional[str] = Field(None, description="Full policy text")

    # Tax analysis
    user_tax_bracket: float = Field(..., description="User's marginal tax rate")
    tax_efficiency_rating: TaxEfficiencyRating = Field(..., description="Overall tax efficiency")

    # Calculations
    estimated_dividend_yield: Optional[float] = Field(None, description="If distributing, expected yield")
    potential_tax_leakage: Optional[float] = Field(None, description="Tax lost to dividend withholding")
    potential_tax_leakage_percent: Optional[float] = Field(None, description="As percentage of investment")

    # Recommendation
    is_recommended_for_user: bool = Field(..., description="Whether suitable for this user")
    recommendation: str = Field("", description="Tax efficiency recommendation")
    alternative_suggestion: Optional[str] = Field(None, description="Better alternative if any")


class ComplianceEvidence(BaseModel):
    """Layer 4: Trust & Compliance Intelligence Output"""

    # Official documents
    pdf_factsheet_url: Optional[str] = Field(None, description="SEC official PDF link")
    amc_factsheet_url: Optional[str] = Field(None, description="AMC website link")
    prospectus_type: Optional[str] = Field(None, description="Monthly/IPO/Significant")

    # Data freshness
    factsheet_as_of_date: Optional[date] = Field(None, description="Data reference date")
    data_age_days: Optional[int] = Field(None, description="Days since last update")
    is_data_fresh: bool = Field(True, description="Whether data is recent (<45 days)")

    # Disclaimers
    disclaimers: List[str] = Field(default_factory=list, description="Regulatory disclaimers")
    verification_message: str = Field("", description="How to verify AI analysis")


class FundBasicInfo(BaseModel):
    """Basic fund information from standard APIs"""

    # Identifiers
    proj_id: str = Field(..., description="SEC Project ID")
    fund_code: str = Field(..., description="Fund ticker/code")
    fund_class_name: Optional[str] = Field(None, description="Share class name")

    # Names
    fund_name_th: Optional[str] = Field(None, description="Thai name")
    fund_name_en: Optional[str] = Field(None, description="English name")

    # Fund type
    fund_type: Optional[FundType] = Field(None, description="RMF/ThaiESG")

    # Management
    amc_code: Optional[str] = Field(None, description="AMC code")
    amc_name_th: Optional[str] = Field(None, description="AMC Thai name")

    # Current NAV
    nav_date: Optional[date] = Field(None, description="NAV date")
    nav_per_unit: Optional[float] = Field(None, description="NAV per unit")
    total_nav: Optional[float] = Field(None, description="Total NAV (AUM)")

    # Risk
    risk_spectrum: Optional[int] = Field(None, ge=1, le=8, description="Risk level 1-8")
    risk_spectrum_description: Optional[str] = Field(None, description="Risk level description")


class FundPerformance(BaseModel):
    """Historical performance data"""

    # Returns (percentage)
    return_1m: Optional[float] = Field(None, description="1 month return %")
    return_3m: Optional[float] = Field(None, description="3 month return %")
    return_6m: Optional[float] = Field(None, description="6 month return %")
    return_ytd: Optional[float] = Field(None, description="Year-to-date return %")
    return_1y: Optional[float] = Field(None, description="1 year return %")
    return_3y: Optional[float] = Field(None, description="3 year return % (annualized)")
    return_5y: Optional[float] = Field(None, description="5 year return % (annualized)")
    return_10y: Optional[float] = Field(None, description="10 year return % (annualized)")
    return_since_inception: Optional[float] = Field(None, description="Since inception return %")

    # Performance date
    performance_as_of_date: Optional[date] = Field(None, description="Performance data date")


class SmartFundAnalysisResult(BaseModel):
    """
    Complete Smart Fund Analysis Result

    This is the main output model combining all 4 intelligence layers
    with basic fund data for frontend consumption.
    """
    model_config = ConfigDict(use_enum_values=True)

    # Basic fund info
    fund_info: FundBasicInfo = Field(..., description="Basic fund details")

    # Historical performance
    performance: FundPerformance = Field(..., description="Return history")

    # === INTELLIGENCE LAYERS ===

    # Layer 1: True Exposure
    true_exposure: TrueExposureAnalysis = Field(..., description="Feeder fund & exposure analysis")

    # Layer 2: Relative Performance
    performance_intelligence: PerformanceNarrative = Field(..., description="Alpha/Beta with context")

    # Layer 3: Tax Efficiency
    tax_efficiency: TaxEfficiencyAnalysis = Field(..., description="Dividend policy analysis")

    # Layer 4: Compliance
    evidence: ComplianceEvidence = Field(..., description="Factsheet links & disclaimers")

    # Overall scoring
    overall_score: float = Field(..., ge=0, le=100, description="Combined suitability score")
    recommendation_rank: Optional[int] = Field(None, description="Rank among analyzed funds")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    analysis_version: str = Field("1.0.0", description="Analyzer version")


class SmartAnalysisBatchResult(BaseModel):
    """Batch analysis result for multiple funds"""

    funds: List[SmartFundAnalysisResult] = Field(..., description="Analyzed funds")

    # User context
    user_tax_bracket: float = Field(..., description="User's tax bracket used")
    user_risk_tolerance: Optional[str] = Field(None, description="User's risk profile")

    # Summary
    total_funds_analyzed: int = Field(..., description="Number of funds analyzed")
    recommended_funds_count: int = Field(..., description="Funds meeting criteria")

    # Filters applied
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters used")

    # Timing
    analysis_duration_ms: Optional[float] = Field(None, description="Processing time")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================
# SMART FUND ANALYZER CLASS
# ============================================================

class SmartFundAnalyzer:
    """
    Smart Fund Analyzer - Deep Investment Intelligence Engine

    Orchestrates multiple SEC API calls and applies 4 intelligence layers
    to provide comprehensive fund analysis for tax optimization.

    Usage:
        analyzer = SmartFundAnalyzer(sec_client)

        # Analyze single fund
        result = await analyzer.analyze_fund("KFGTECH-A", user_tax_bracket=0.25)

        # Batch analyze with filters
        results = await analyzer.analyze_funds_batch(
            fund_codes=["KFGTECH-A", "SCBRMGP"],
            user_tax_bracket=0.25,
            filter_accumulating_only=True
        )
    """

    def __init__(
        self,
        sec_client: SECAPIClient,
        cache_ttl_seconds: int = 3600
    ):
        """
        Initialize Smart Fund Analyzer

        Args:
            sec_client: Configured SECAPIClient instance
            cache_ttl_seconds: Cache TTL for API responses (default 1 hour)
        """
        self.sec_client = sec_client
        self.cache_ttl = cache_ttl_seconds

        # Simple in-memory cache
        self._cache: Dict[str, Tuple[Any, datetime]] = {}

        logger.info("SmartFundAnalyzer initialized")

    # ============================================================
    # MAIN ANALYSIS METHODS
    # ============================================================

    async def analyze_fund(
        self,
        fund_code: str,
        user_tax_bracket: float,
        proj_id: Optional[str] = None
    ) -> SmartFundAnalysisResult:
        """
        Perform comprehensive analysis on a single fund

        Args:
            fund_code: Fund ticker/code (e.g., "KFGTECH-A")
            user_tax_bracket: User's marginal tax rate (0.0-0.35)
            proj_id: SEC project ID if known (speeds up lookup)

        Returns:
            SmartFundAnalysisResult with all 4 intelligence layers
        """
        logger.info(f"Analyzing fund: {fund_code} (tax bracket: {user_tax_bracket:.0%})")

        # Step 1: Resolve proj_id if not provided
        if not proj_id:
            proj_id = await self._resolve_proj_id(fund_code)
            if not proj_id:
                raise ValueError(f"Fund not found: {fund_code}")

        # Step 2: Fetch all data in parallel
        raw_data = await self._fetch_all_fund_data(proj_id, fund_code)

        # Step 3: Apply intelligence layers
        result = await self._apply_intelligence_layers(
            raw_data=raw_data,
            fund_code=fund_code,
            proj_id=proj_id,
            user_tax_bracket=user_tax_bracket
        )

        logger.info(f"Analysis complete for {fund_code}: score={result.overall_score:.1f}")
        return result

    async def analyze_funds_batch(
        self,
        fund_codes: Optional[List[str]] = None,
        proj_ids: Optional[List[str]] = None,
        user_tax_bracket: float = 0.20,
        user_risk_tolerance: Optional[str] = None,
        fund_type_filter: Optional[FundType] = None,
        filter_accumulating_only: bool = False,
        max_risk_level: Optional[int] = None,
        min_return_1y: Optional[float] = None,
        limit: int = 50
    ) -> SmartAnalysisBatchResult:
        """
        Batch analyze multiple funds with filtering

        Args:
            fund_codes: List of fund codes to analyze
            proj_ids: List of SEC project IDs (alternative to fund_codes)
            user_tax_bracket: User's marginal tax rate
            user_risk_tolerance: conservative/moderate/aggressive
            fund_type_filter: Filter by RMF or ThaiESG
            filter_accumulating_only: Only include non-dividend funds
            max_risk_level: Maximum risk spectrum (1-8)
            min_return_1y: Minimum 1-year return percentage
            limit: Maximum funds to return

        Returns:
            SmartAnalysisBatchResult with ranked funds
        """
        start_time = datetime.now()

        logger.info(
            f"Batch analysis: {len(fund_codes or proj_ids or [])} funds, "
            f"tax_bracket={user_tax_bracket:.0%}"
        )

        # Get fund list if not provided
        if not fund_codes and not proj_ids:
            # Fetch all tax funds
            tax_funds = await self._fetch_tax_funds(fund_type_filter)
            proj_ids = [f.get("proj_id") for f in tax_funds if f.get("proj_id")]

        # Analyze in parallel batches
        results = []
        batch_size = 10  # Prevent overwhelming the API

        items = proj_ids if proj_ids else fund_codes

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            if proj_ids:
                batch_results = await asyncio.gather(
                    *[self._safe_analyze(None, user_tax_bracket, pid) for pid in batch],
                    return_exceptions=True
                )
            else:
                batch_results = await asyncio.gather(
                    *[self._safe_analyze(code, user_tax_bracket, None) for code in batch],
                    return_exceptions=True
                )

            for r in batch_results:
                if isinstance(r, SmartFundAnalysisResult):
                    results.append(r)
                elif isinstance(r, Exception):
                    logger.warning(f"Fund analysis failed: {r}")

        # Apply filters
        filtered_results = self._apply_filters(
            results=results,
            filter_accumulating_only=filter_accumulating_only,
            max_risk_level=max_risk_level,
            min_return_1y=min_return_1y
        )

        # Sort by overall score
        filtered_results.sort(key=lambda x: x.overall_score, reverse=True)

        # Assign ranks
        for i, r in enumerate(filtered_results[:limit], 1):
            r.recommendation_rank = i

        # Calculate timing
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return SmartAnalysisBatchResult(
            funds=filtered_results[:limit],
            user_tax_bracket=user_tax_bracket,
            user_risk_tolerance=user_risk_tolerance,
            total_funds_analyzed=len(results),
            recommended_funds_count=len(filtered_results),
            filters_applied={
                "fund_type": fund_type_filter.value if fund_type_filter else None,
                "accumulating_only": filter_accumulating_only,
                "max_risk_level": max_risk_level,
                "min_return_1y": min_return_1y
            },
            analysis_duration_ms=duration_ms
        )

    async def _safe_analyze(
        self,
        fund_code: Optional[str],
        user_tax_bracket: float,
        proj_id: Optional[str]
    ) -> Union[SmartFundAnalysisResult, Exception]:
        """Safe wrapper for analyze_fund that catches exceptions"""
        try:
            return await self.analyze_fund(
                fund_code=fund_code or "",
                user_tax_bracket=user_tax_bracket,
                proj_id=proj_id
            )
        except Exception as e:
            logger.error(f"Analysis failed for {fund_code or proj_id}: {e}")
            return e

    # ============================================================
    # DATA FETCHING (PARALLEL)
    # ============================================================

    async def _fetch_all_fund_data(
        self,
        proj_id: str,
        fund_code: str
    ) -> Dict[str, Any]:
        """
        Fetch all required API data in parallel

        APIs called:
        - Base: API 2 (fund info), API 11 (risk), API 15 (performance), API 20 (NAV)
        - Intelligence: API 3 (specs), API 6 (URLs), API 8 (benchmark),
                       API 12 (statistics), API 13 (dividend)
        """
        logger.debug(f"Fetching all data for {proj_id}")

        # Define all API calls
        api_calls = {
            # Base data
            "fund_info": self._fetch_fund_info(proj_id),
            "risk_level": self._fetch_risk_level(proj_id),
            "performance": self._fetch_performance(proj_id),
            "nav": self._fetch_nav(proj_id),

            # Intelligence data
            "specifications": self._fetch_specifications(proj_id),
            "factsheet_urls": self._fetch_factsheet_urls(proj_id),
            "benchmarks": self._fetch_benchmarks(proj_id),
            "statistics": self._fetch_statistics(proj_id),
            "dividend_policy": self._fetch_dividend_policy(proj_id),
        }

        # Execute all in parallel
        results = await asyncio.gather(
            *api_calls.values(),
            return_exceptions=True
        )

        # Map results back to keys
        data = {}
        for key, result in zip(api_calls.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"API call failed for {key}: {result}")
                data[key] = None
            else:
                data[key] = result

        data["proj_id"] = proj_id
        data["fund_code"] = fund_code

        return data

    async def _fetch_fund_info(self, proj_id: str) -> Optional[Dict]:
        """Fetch basic fund info (API 2)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/general-info/amcs",
                api_type="v1",
                page=1,
                params={"search": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch fund info: {e}")
            return None

    async def _fetch_risk_level(self, proj_id: str) -> Optional[Dict]:
        """Fetch risk spectrum (API 11)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/factsheet/risk-spectrum",
                api_type="v1",
                page=1,
                params={"proj_id": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch risk level: {e}")
            return None

    async def _fetch_performance(self, proj_id: str) -> Optional[Dict]:
        """Fetch historical performance (API 15)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/factsheet/performance",
                api_type="v1",
                page=1,
                params={"proj_id": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch performance: {e}")
            return None

    async def _fetch_nav(self, proj_id: str) -> Optional[Dict]:
        """Fetch current NAV (API 20)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/dailynav/latest",
                api_type="v1",
                page=1,
                params={"proj_id": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch NAV: {e}")
            return None

    async def _fetch_specifications(self, proj_id: str) -> Optional[Dict]:
        """Fetch fund specifications for Feeder Fund detection (API 3)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/general-info/specifications",
                api_type="v1",
                page=1,
                params={"search": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch specifications: {e}")
            return None

    async def _fetch_factsheet_urls(self, proj_id: str) -> Optional[Dict]:
        """Fetch factsheet URLs (API 6)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/factsheet/urls",
                api_type="v1",
                page=1,
                params={"search": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch factsheet URLs: {e}")
            return None

    async def _fetch_benchmarks(self, proj_id: str) -> Optional[Dict]:
        """Fetch benchmark information (API 8)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/factsheet/benchmarks",
                api_type="v1",
                page=1,
                params={"proj_id": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch benchmarks: {e}")
            return None

    async def _fetch_statistics(self, proj_id: str) -> Optional[Dict]:
        """Fetch fund statistics - Alpha, Beta, Sharpe (API 12)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/factsheet/statistics",
                api_type="v1",
                page=1,
                params={"proj_id": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch statistics: {e}")
            return None

    async def _fetch_dividend_policy(self, proj_id: str) -> Optional[Dict]:
        """Fetch dividend policy (API 13)"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/factsheet/dividend-policy",
                api_type="v1",
                page=1,
                params={"proj_id": proj_id}
            )
            items = response.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Failed to fetch dividend policy: {e}")
            return None

    async def _fetch_tax_funds(
        self,
        fund_type: Optional[FundType] = None
    ) -> List[Dict]:
        """Fetch list of tax-deductible funds"""
        try:
            tax_funds = await self.sec_client.get_tax_funds(
                fund_types=[fund_type.value] if fund_type else ["RMF", "ThaiESG"],
                max_pages=5
            )

            all_funds = []
            if "RMF" in tax_funds:
                all_funds.extend(tax_funds["RMF"])
            if "ThaiESG" in tax_funds:
                all_funds.extend(tax_funds["ThaiESG"])

            return all_funds
        except Exception as e:
            logger.error(f"Failed to fetch tax funds: {e}")
            return []

    async def _resolve_proj_id(self, fund_code: str) -> Optional[str]:
        """Resolve fund code to SEC project ID"""
        try:
            response = await self.sec_client.get_paginated(
                "/fund/general-info/amcs",
                api_type="v1",
                page=1,
                params={"search": fund_code}
            )
            items = response.get("items", [])
            for item in items:
                if item.get("proj_abbr_name", "").upper() == fund_code.upper():
                    return item.get("proj_id")
                if fund_code.upper() in item.get("proj_abbr_name", "").upper():
                    return item.get("proj_id")
            return items[0].get("proj_id") if items else None
        except Exception as e:
            logger.error(f"Failed to resolve proj_id for {fund_code}: {e}")
            return None

    # ============================================================
    # INTELLIGENCE LAYER PROCESSING
    # ============================================================

    async def _apply_intelligence_layers(
        self,
        raw_data: Dict[str, Any],
        fund_code: str,
        proj_id: str,
        user_tax_bracket: float
    ) -> SmartFundAnalysisResult:
        """
        Apply all 4 intelligence layers to raw API data
        """

        # Build basic info
        fund_info = self._build_fund_info(raw_data, fund_code, proj_id)

        # Build performance
        performance = self._build_performance(raw_data)

        # Layer 1: True Exposure Intelligence
        true_exposure = self._analyze_true_exposure(raw_data)

        # Layer 2: Relative Performance Intelligence
        performance_intelligence = self._analyze_performance(raw_data)

        # Layer 3: Tax Efficiency Intelligence
        tax_efficiency = self._analyze_tax_efficiency(raw_data, user_tax_bracket)

        # Layer 4: Compliance Evidence
        evidence = self._build_compliance_evidence(raw_data)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            fund_info=fund_info,
            performance=performance,
            true_exposure=true_exposure,
            performance_intelligence=performance_intelligence,
            tax_efficiency=tax_efficiency,
            user_tax_bracket=user_tax_bracket
        )

        return SmartFundAnalysisResult(
            fund_info=fund_info,
            performance=performance,
            true_exposure=true_exposure,
            performance_intelligence=performance_intelligence,
            tax_efficiency=tax_efficiency,
            evidence=evidence,
            overall_score=overall_score
        )

    def _build_fund_info(
        self,
        raw_data: Dict[str, Any],
        fund_code: str,
        proj_id: str
    ) -> FundBasicInfo:
        """Build FundBasicInfo from raw API data"""

        fund_data = raw_data.get("fund_info") or {}
        risk_data = raw_data.get("risk_level") or {}
        nav_data = raw_data.get("nav") or {}

        # Determine fund type from code
        fund_type = None
        code_upper = fund_code.upper()
        if "RMF" in code_upper:
            fund_type = FundType.RMF
        elif "THAIESG" in code_upper or "ESG" in code_upper:
            fund_type = FundType.THAI_ESG

        # Parse NAV date
        nav_date = None
        if nav_data.get("nav_date"):
            try:
                nav_date = datetime.strptime(
                    nav_data["nav_date"][:10], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                pass

        return FundBasicInfo(
            proj_id=proj_id,
            fund_code=fund_data.get("proj_abbr_name", fund_code),
            fund_class_name=fund_data.get("fund_class_name"),
            fund_name_th=fund_data.get("proj_name_th"),
            fund_name_en=fund_data.get("proj_name_en"),
            fund_type=fund_type,
            amc_code=fund_data.get("amc_code"),
            amc_name_th=fund_data.get("amc_name_th"),
            nav_date=nav_date,
            nav_per_unit=self._safe_float(nav_data.get("nav_per_unit")),
            total_nav=self._safe_float(nav_data.get("net_asset")),
            risk_spectrum=self._safe_int(risk_data.get("risk_spectrum")),
            risk_spectrum_description=risk_data.get("risk_spectrum_desc")
        )

    def _build_performance(self, raw_data: Dict[str, Any]) -> FundPerformance:
        """Build FundPerformance from raw API data"""

        perf_data = raw_data.get("performance") or {}

        # Parse performance date
        perf_date = None
        if perf_data.get("as_of_date"):
            try:
                perf_date = datetime.strptime(
                    perf_data["as_of_date"][:10], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                pass

        return FundPerformance(
            return_1m=self._safe_float(perf_data.get("return_1m")),
            return_3m=self._safe_float(perf_data.get("return_3m")),
            return_6m=self._safe_float(perf_data.get("return_6m")),
            return_ytd=self._safe_float(perf_data.get("return_ytd")),
            return_1y=self._safe_float(perf_data.get("return_1y")),
            return_3y=self._safe_float(perf_data.get("return_3y_annualized")),
            return_5y=self._safe_float(perf_data.get("return_5y_annualized")),
            return_10y=self._safe_float(perf_data.get("return_10y_annualized")),
            return_since_inception=self._safe_float(perf_data.get("return_since_inception")),
            performance_as_of_date=perf_date
        )

    # ============================================================
    # LAYER 1: TRUE EXPOSURE INTELLIGENCE
    # ============================================================

    def _analyze_true_exposure(self, raw_data: Dict[str, Any]) -> TrueExposureAnalysis:
        """
        Layer 1: Analyze true exposure for Feeder Fund detection

        Detects:
        - CIV, FIF, FOF spec codes
        - Master fund keywords (ARK, BlackRock, etc.)
        - Currency and layered fee risks
        """

        spec_data = raw_data.get("specifications") or {}
        stats_data = raw_data.get("statistics") or {}

        spec_code = spec_data.get("spec_code", "")
        spec_desc = spec_data.get("spec_desc", "")

        warnings = []
        exposure_type = ExposureType.DOMESTIC
        is_feeder = False
        master_fund_name = None
        master_fund_region = None
        fx_hedging = None

        # Check spec_code for Feeder Fund indicators
        if spec_code in FEEDER_FUND_CODES:
            is_feeder = True
            exposure_type = ExposureType.GLOBAL if spec_code == "FIF" else ExposureType.MIXED

            warnings.append(RiskWarning(
                warning_type="FEEDER_FUND",
                severity=RiskSeverity.MEDIUM,
                message=f"กองทุนนี้เป็น {FEEDER_FUND_CODES[spec_code]}",
                message_en=f"This is a {spec_code} fund",
                mitigation="ตรวจสอบค่าธรรมเนียมรวม (Total Expense Ratio)",
                data_source="API 3: Specifications"
            ))

        # Check for FIF (Foreign Investment Fund)
        if spec_code == "FIF" or "ต่างประเทศ" in spec_desc:
            exposure_type = ExposureType.GLOBAL

            warnings.append(RiskWarning(
                warning_type="CURRENCY_RISK",
                severity=RiskSeverity.HIGH,
                message="กองทุนนี้ลงทุนในต่างประเทศ มีความเสี่ยงค่าเงิน (FX Risk)",
                message_en="This fund invests overseas with currency risk",
                mitigation="ตรวจสอบ FX Hedging ratio และติดตามค่าเงินบาท",
                data_source="API 3: Specifications"
            ))

        # Check for Fund of Funds / CIV
        if spec_code in ["FOF", "CIV"] or "กองทุนรวมอื่น" in spec_desc:
            warnings.append(RiskWarning(
                warning_type="LAYERED_FEES",
                severity=RiskSeverity.MEDIUM,
                message="เป็น Feeder Fund - มีค่าธรรมเนียม 2 ชั้น (ไทย + ต้นทาง)",
                message_en="Feeder Fund with dual-layer fees",
                mitigation="เปรียบเทียบ Total Expense Ratio กับกองทุนที่ลงทุนตรง",
                data_source="API 3: Specifications"
            ))

        # Detect Master Fund from description
        for keyword in MASTER_FUND_KEYWORDS:
            if keyword.upper() in spec_desc.upper():
                master_fund_name = keyword

                # Determine region
                if keyword in ["ARK", "BlackRock", "Vanguard", "Fidelity", "iShares"]:
                    master_fund_region = "US"
                elif keyword in ["Schroders", "Aberdeen", "HSBC"]:
                    master_fund_region = "UK"
                elif keyword in ["Amundi", "BNP", "DWS"]:
                    master_fund_region = "EU"
                else:
                    master_fund_region = "Global"

                warnings.append(RiskWarning(
                    warning_type="MASTER_FUND_EXPOSURE",
                    severity=RiskSeverity.INFO,
                    message=f"กองทุนต้นทาง: {keyword} ({master_fund_region})",
                    message_en=f"Master Fund: {keyword} ({master_fund_region})",
                    mitigation="ศึกษาผลงานของกองทุนต้นทางประกอบการตัดสินใจ",
                    data_source="API 3: Specifications"
                ))
                break

        # Get FX hedging from statistics if available
        fx_hedging_str = stats_data.get("fx_hedging", "")
        if fx_hedging_str:
            try:
                # Parse percentage like "80%", "80", "ประมาณ 80%"
                import re
                match = re.search(r'(\d+)', str(fx_hedging_str))
                if match:
                    fx_hedging = float(match.group(1))

                    if fx_hedging < 50:
                        warnings.append(RiskWarning(
                            warning_type="LOW_FX_HEDGING",
                            severity=RiskSeverity.MEDIUM,
                            message=f"ป้องกันค่าเงินต่ำ ({fx_hedging:.0f}%) - มีความเสี่ยง FX สูง",
                            message_en=f"Low FX hedging ({fx_hedging:.0f}%)",
                            mitigation="พิจารณากองทุนที่ Hedge ค่าเงินมากกว่านี้",
                            data_source="API 12: Statistics"
                        ))
            except (ValueError, AttributeError):
                pass

        # Generate recommendation
        recommendation = self._generate_exposure_recommendation(
            is_feeder=is_feeder,
            exposure_type=exposure_type,
            warnings=warnings,
            master_fund_name=master_fund_name
        )

        return TrueExposureAnalysis(
            exposure_type=exposure_type,
            is_feeder_fund=is_feeder,
            spec_code=spec_code if spec_code else None,
            spec_description=spec_desc if spec_desc else None,
            master_fund_name=master_fund_name,
            master_fund_region=master_fund_region,
            fx_hedging_percent=fx_hedging,
            warnings=warnings,
            recommendation=recommendation
        )

    def _generate_exposure_recommendation(
        self,
        is_feeder: bool,
        exposure_type: ExposureType,
        warnings: List[RiskWarning],
        master_fund_name: Optional[str]
    ) -> str:
        """Generate human-readable exposure recommendation"""

        if not is_feeder and exposure_type == ExposureType.DOMESTIC:
            return "กองทุนลงทุนในประเทศโดยตรง ไม่มีความเสี่ยง FX หรือค่าธรรมเนียมซ้อน"

        parts = []

        if is_feeder:
            parts.append("เป็น Feeder Fund")
            if master_fund_name:
                parts.append(f"ลงทุนผ่าน {master_fund_name}")

        if exposure_type == ExposureType.GLOBAL:
            parts.append("มี Global Exposure")

        high_risks = [w for w in warnings if w.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]]
        if high_risks:
            parts.append("ควรศึกษาความเสี่ยงก่อนลงทุน")

        return " | ".join(parts) if parts else "ข้อมูล Exposure ไม่ชัดเจน"

    # ============================================================
    # LAYER 2: RELATIVE PERFORMANCE INTELLIGENCE
    # ============================================================

    def _analyze_performance(self, raw_data: Dict[str, Any]) -> PerformanceNarrative:
        """
        Layer 2: Analyze Alpha/Beta with benchmark context

        Combines API 8 (Benchmark) with API 12 (Statistics)
        to generate meaningful performance narratives.
        """

        stats_data = raw_data.get("statistics") or {}
        benchmark_data = raw_data.get("benchmarks") or {}
        perf_data = raw_data.get("performance") or {}

        # Parse statistics
        alpha = self._safe_float(stats_data.get("alpha"))
        beta = self._safe_float(stats_data.get("beta"))
        sharpe = self._safe_float(stats_data.get("sharpe_ratio"))
        max_drawdown_str = stats_data.get("maximum_drawdown", "")
        tracking_error = self._safe_float(stats_data.get("tracking_error"))

        # Parse max drawdown (might be percentage string)
        max_drawdown = None
        if max_drawdown_str:
            try:
                import re
                match = re.search(r'[-]?(\d+\.?\d*)', str(max_drawdown_str))
                if match:
                    max_drawdown = float(match.group(1))
                    # Drawdown should be negative
                    if max_drawdown > 0:
                        max_drawdown = -max_drawdown
            except (ValueError, AttributeError):
                pass

        # Get benchmark name
        benchmark_name = benchmark_data.get("benchmark", "ไม่ระบุ")
        benchmark_name = benchmark_name.strip('"') if benchmark_name else "ไม่ระบุ"

        fund_return_1y = self._safe_float(perf_data.get("return_1y"))

        # Build benchmark comparison
        benchmark = BenchmarkComparison(
            benchmark_name=benchmark_name,
            benchmark_name_th=benchmark_name,
            fund_return=fund_return_1y,
            benchmark_return=None,  # Would need additional API
            outperformance=alpha  # Alpha is the outperformance
        )

        # Generate narratives
        alpha_narrative = self._generate_alpha_narrative(alpha, benchmark_name)
        beta_narrative = self._generate_beta_narrative(beta)
        sharpe_narrative = self._generate_sharpe_narrative(sharpe)

        # Manager skill assessment
        shows_skill = alpha is not None and alpha > 0
        recommend_index = alpha is not None and alpha < -0.5  # Significantly underperforming

        # Overall verdict
        overall_verdict = self._generate_performance_verdict(
            alpha=alpha,
            beta=beta,
            sharpe=sharpe,
            benchmark_name=benchmark_name
        )

        return PerformanceNarrative(
            alpha=alpha,
            beta=beta,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            tracking_error=tracking_error,
            benchmark=benchmark,
            alpha_narrative=alpha_narrative,
            beta_narrative=beta_narrative,
            sharpe_narrative=sharpe_narrative,
            overall_verdict=overall_verdict,
            shows_manager_skill=shows_skill,
            recommend_index_alternative=recommend_index
        )

    def _generate_alpha_narrative(
        self,
        alpha: Optional[float],
        benchmark_name: str
    ) -> str:
        """Generate contextualized Alpha explanation"""

        if alpha is None:
            return "ไม่มีข้อมูล Alpha"

        if alpha > 2:
            verdict = "ผลงานดีเยี่ยม แสดงถึงความสามารถของผู้จัดการกองทุน"
            performance = "ชนะ"
        elif alpha > 0:
            verdict = "ผลงานดีกว่าตลาด"
            performance = "ชนะ"
        elif alpha > -1:
            verdict = "ผลงานใกล้เคียงตลาด"
            performance = "แพ้เล็กน้อย"
        else:
            verdict = "ผลงานต่ำกว่าตลาด ควรพิจารณากองทุน Index ที่ค่าธรรมเนียมถูกกว่า"
            performance = "แพ้"

        return f"{performance} {benchmark_name} อยู่ {abs(alpha):.2f}% ต่อปี | {verdict}"

    def _generate_beta_narrative(self, beta: Optional[float]) -> str:
        """Generate Beta risk explanation"""

        if beta is None:
            return "ไม่มีข้อมูล Beta"

        if beta < 0.7:
            return f"Beta {beta:.2f} - ผันผวนน้อยกว่าตลาดมาก (Defensive) เหมาะกับคนรับความเสี่ยงต่ำ"
        elif beta < 0.9:
            return f"Beta {beta:.2f} - ผันผวนน้อยกว่าตลาด (Low Volatility)"
        elif beta < 1.1:
            return f"Beta {beta:.2f} - ผันผวนใกล้เคียงตลาด"
        elif beta < 1.3:
            return f"Beta {beta:.2f} - ผันผวนมากกว่าตลาด (Aggressive)"
        else:
            return f"Beta {beta:.2f} - ผันผวนมากกว่าตลาดมาก (High Risk) เหมาะกับคนรับความเสี่ยงสูงได้"

    def _generate_sharpe_narrative(self, sharpe: Optional[float]) -> str:
        """Generate Sharpe Ratio explanation"""

        if sharpe is None:
            return "ไม่มีข้อมูล Sharpe Ratio"

        if sharpe > 1.5:
            return f"Sharpe {sharpe:.2f} - ผลตอบแทนต่อความเสี่ยงดีเยี่ยม (Excellent)"
        elif sharpe > 1.0:
            return f"Sharpe {sharpe:.2f} - ผลตอบแทนต่อความเสี่ยงดีมาก (Very Good)"
        elif sharpe > 0.5:
            return f"Sharpe {sharpe:.2f} - ผลตอบแทนต่อความเสี่ยงอยู่ในเกณฑ์ดี (Good)"
        elif sharpe > 0:
            return f"Sharpe {sharpe:.2f} - ผลตอบแทนต่อความเสี่ยงพอใช้ (Fair)"
        else:
            return f"Sharpe {sharpe:.2f} - ผลตอบแทนต่อความเสี่ยงต่ำ ควรพิจารณากองทุนอื่น"

    def _generate_performance_verdict(
        self,
        alpha: Optional[float],
        beta: Optional[float],
        sharpe: Optional[float],
        benchmark_name: str
    ) -> str:
        """Generate overall performance verdict"""

        parts = []

        # Alpha verdict
        if alpha is not None:
            if alpha > 1:
                parts.append(f"ผลงานดี ชนะ {benchmark_name}")
            elif alpha < -1:
                parts.append(f"ผลงานต่ำกว่า {benchmark_name}")

        # Sharpe verdict
        if sharpe is not None:
            if sharpe > 1:
                parts.append("Risk-adjusted return ดีมาก")
            elif sharpe < 0.3:
                parts.append("Risk-adjusted return ต่ำ")

        # Beta insight
        if beta is not None:
            if beta > 1.2:
                parts.append("ความผันผวนสูง")
            elif beta < 0.8:
                parts.append("ความผันผวนต่ำ")

        if not parts:
            return "ข้อมูลไม่เพียงพอสำหรับการประเมิน"

        return " | ".join(parts)

    # ============================================================
    # LAYER 3: TAX EFFICIENCY INTELLIGENCE
    # ============================================================

    def _analyze_tax_efficiency(
        self,
        raw_data: Dict[str, Any],
        user_tax_bracket: float
    ) -> TaxEfficiencyAnalysis:
        """
        Layer 3: Analyze dividend policy for tax optimization

        Key insight: For RMF/ThaiESG, capital gains are tax-free
        but dividends are subject to 10% withholding tax.
        High-income users should prefer Accumulating class funds.
        """

        dividend_data = raw_data.get("dividend_policy") or {}

        policy_code = dividend_data.get("dividend_policy", "")
        policy_desc = dividend_data.get("dividend_policy_desc", "")

        # Determine dividend policy
        dividend_policy = None
        if policy_code == "N":
            dividend_policy = DividendPolicy.ACCUMULATING
        elif policy_code == "Y":
            dividend_policy = DividendPolicy.DISTRIBUTING
        elif "ไม่จ่าย" in policy_desc or "สะสมมูลค่า" in policy_desc:
            dividend_policy = DividendPolicy.ACCUMULATING
        elif "จ่าย" in policy_desc:
            dividend_policy = DividendPolicy.DISTRIBUTING

        # Calculate tax efficiency
        if dividend_policy == DividendPolicy.ACCUMULATING:
            # Best case: No dividend tax leakage
            tax_efficiency = TaxEfficiencyRating.OPTIMAL
            is_recommended = True
            potential_leakage = 0.0
            potential_leakage_pct = 0.0

            recommendation = (
                "กองทุนนี้ไม่จ่ายเงินปันผล (Accumulating) "
                "กำไรจาก RMF/ThaiESG ไม่เสียภาษี - เหมาะสมที่สุดสำหรับการลดหย่อนภาษี"
            )
            alternative = None

        elif dividend_policy == DividendPolicy.DISTRIBUTING:
            # Calculate tax leakage for dividend-paying funds
            # Assume 3% dividend yield as estimate
            estimated_yield = 3.0
            potential_leakage_pct = estimated_yield * DIVIDEND_WITHHOLDING_TAX
            potential_leakage = 100_000 * (potential_leakage_pct / 100)  # Per 100K invested

            if user_tax_bracket >= 0.25:
                # High-income: Suboptimal
                tax_efficiency = TaxEfficiencyRating.SUBOPTIMAL
                is_recommended = False
                recommendation = (
                    f"คุณอยู่ในฐานภาษี {user_tax_bracket:.0%} "
                    f"กองทุนนี้จ่ายเงินปันผลซึ่งถูกหักภาษี 10% ณ ที่จ่าย "
                    f"ทำให้เสียประโยชน์ประมาณ {potential_leakage_pct:.2f}% ต่อปี"
                )
                alternative = "ควรเลือกกองทุนแบบ Accumulating (-A, -SSF-A) แทน"

            elif user_tax_bracket >= 0.15:
                # Medium-income: Acceptable but not optimal
                tax_efficiency = TaxEfficiencyRating.GOOD
                is_recommended = True
                recommendation = (
                    f"กองทุนจ่ายเงินปันผล ถูกหักภาษี 10% | "
                    f"ยังพอรับได้สำหรับฐานภาษี {user_tax_bracket:.0%}"
                )
                alternative = "ถ้าต้องการ optimize ภาษี ลองดูกองทุน Accumulating"

            else:
                # Low-income: Dividend might be fine
                tax_efficiency = TaxEfficiencyRating.GOOD
                is_recommended = True
                recommendation = (
                    "กองทุนจ่ายเงินปันผล | "
                    "เหมาะสำหรับผู้ที่ต้องการรายได้ระหว่างทาง"
                )
                alternative = None

        else:
            # Unknown policy
            tax_efficiency = TaxEfficiencyRating.GOOD  # Neutral
            is_recommended = True
            potential_leakage = None
            potential_leakage_pct = None
            estimated_yield = None
            recommendation = "ไม่พบข้อมูลนโยบายเงินปันผลที่ชัดเจน"
            alternative = None

        return TaxEfficiencyAnalysis(
            dividend_policy=dividend_policy,
            dividend_policy_description=policy_desc if policy_desc else None,
            user_tax_bracket=user_tax_bracket,
            tax_efficiency_rating=tax_efficiency,
            estimated_dividend_yield=estimated_yield if dividend_policy == DividendPolicy.DISTRIBUTING else None,
            potential_tax_leakage=potential_leakage,
            potential_tax_leakage_percent=potential_leakage_pct,
            is_recommended_for_user=is_recommended,
            recommendation=recommendation,
            alternative_suggestion=alternative
        )

    # ============================================================
    # LAYER 4: COMPLIANCE & EVIDENCE
    # ============================================================

    def _build_compliance_evidence(self, raw_data: Dict[str, Any]) -> ComplianceEvidence:
        """
        Layer 4: Build compliance evidence with factsheet links
        """

        url_data = raw_data.get("factsheet_urls") or {}

        pdf_url = url_data.get("pdf_factsheet")
        amc_url = url_data.get("amc_url_factsheet")
        prospectus_type = url_data.get("prospectus_type")

        # Parse as_of_date
        as_of_date = None
        data_age_days = None
        is_fresh = True

        if url_data.get("as_of_date"):
            try:
                as_of_date = datetime.strptime(
                    url_data["as_of_date"][:10], "%Y-%m-%d"
                ).date()

                data_age_days = (date.today() - as_of_date).days
                is_fresh = data_age_days <= 45  # Consider fresh if < 45 days
            except (ValueError, TypeError):
                pass

        # Standard disclaimers
        disclaimers = [
            "ผลการดำเนินงานในอดีตไม่ได้รับประกันผลตอบแทนในอนาคต",
            "ผู้ลงทุนควรศึกษาข้อมูลในหนังสือชี้ชวนก่อนตัดสินใจลงทุน",
            "การลงทุนมีความเสี่ยง ผู้ลงทุนควรทำความเข้าใจลักษณะสินค้า เงื่อนไขผลตอบแทน และความเสี่ยงก่อนตัดสินใจลงทุน"
        ]

        verification_msg = (
            "AI ได้วิเคราะห์จากข้อมูลทางการของสำนักงาน ก.ล.ต. "
            "คุณสามารถตรวจสอบและดาวน์โหลดเอกสารต้นฉบับได้จากลิงก์ด้านบน"
        )

        return ComplianceEvidence(
            pdf_factsheet_url=pdf_url,
            amc_factsheet_url=amc_url,
            prospectus_type=prospectus_type,
            factsheet_as_of_date=as_of_date,
            data_age_days=data_age_days,
            is_data_fresh=is_fresh,
            disclaimers=disclaimers,
            verification_message=verification_msg
        )

    # ============================================================
    # SCORING & FILTERING
    # ============================================================

    def _calculate_overall_score(
        self,
        fund_info: FundBasicInfo,
        performance: FundPerformance,
        true_exposure: TrueExposureAnalysis,
        performance_intelligence: PerformanceNarrative,
        tax_efficiency: TaxEfficiencyAnalysis,
        user_tax_bracket: float
    ) -> float:
        """
        Calculate overall suitability score (0-100)

        Weighted factors:
        - Performance (30%): Returns and risk-adjusted performance
        - Tax Efficiency (25%): Dividend policy match
        - Risk-Adjusted (20%): Alpha, Sharpe
        - Exposure Safety (15%): Feeder fund risks
        - Data Quality (10%): Fresh data, complete info
        """

        score = 50.0  # Start at neutral

        # === Performance Score (30%) ===
        perf_score = 0.0

        if performance.return_1y is not None:
            if performance.return_1y > 15:
                perf_score += 30
            elif performance.return_1y > 10:
                perf_score += 25
            elif performance.return_1y > 5:
                perf_score += 20
            elif performance.return_1y > 0:
                perf_score += 15
            else:
                perf_score += 5
        else:
            perf_score += 15  # Neutral if no data

        score += perf_score * 0.30

        # === Tax Efficiency Score (25%) ===
        tax_score = 0.0

        if tax_efficiency.tax_efficiency_rating == TaxEfficiencyRating.OPTIMAL:
            tax_score = 30
        elif tax_efficiency.tax_efficiency_rating == TaxEfficiencyRating.GOOD:
            tax_score = 22
        elif tax_efficiency.tax_efficiency_rating == TaxEfficiencyRating.SUBOPTIMAL:
            tax_score = 12
        else:
            tax_score = 5

        # Bonus for high-tax users avoiding dividends
        if user_tax_bracket >= 0.25 and tax_efficiency.is_recommended_for_user:
            tax_score += 5

        score += tax_score * 0.25

        # === Risk-Adjusted Score (20%) ===
        risk_adj_score = 15.0  # Neutral default

        if performance_intelligence.alpha is not None:
            if performance_intelligence.alpha > 2:
                risk_adj_score = 30
            elif performance_intelligence.alpha > 0:
                risk_adj_score = 22
            elif performance_intelligence.alpha > -1:
                risk_adj_score = 15
            else:
                risk_adj_score = 8

        if performance_intelligence.sharpe_ratio is not None:
            if performance_intelligence.sharpe_ratio > 1:
                risk_adj_score += 5
            elif performance_intelligence.sharpe_ratio < 0.3:
                risk_adj_score -= 5

        score += min(risk_adj_score, 30) * 0.20

        # === Exposure Safety Score (15%) ===
        exposure_score = 20.0  # Default

        # Deduct for high-severity warnings
        high_warnings = sum(
            1 for w in true_exposure.warnings
            if w.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]
        )
        exposure_score -= high_warnings * 5

        # Small bonus for domestic exposure (simpler)
        if true_exposure.exposure_type == ExposureType.DOMESTIC:
            exposure_score += 5

        score += max(exposure_score, 5) * 0.15

        # === Data Quality Score (10%) ===
        quality_score = 15.0

        # Check for missing critical data
        if performance.return_1y is None:
            quality_score -= 5
        if performance_intelligence.alpha is None:
            quality_score -= 3
        if tax_efficiency.dividend_policy is None:
            quality_score -= 3

        score += max(quality_score, 5) * 0.10

        # Ensure bounds
        return max(0, min(100, score))

    def _apply_filters(
        self,
        results: List[SmartFundAnalysisResult],
        filter_accumulating_only: bool,
        max_risk_level: Optional[int],
        min_return_1y: Optional[float]
    ) -> List[SmartFundAnalysisResult]:
        """Apply user filters to results"""

        filtered = results

        if filter_accumulating_only:
            filtered = [
                r for r in filtered
                if r.tax_efficiency.dividend_policy == DividendPolicy.ACCUMULATING
                or r.tax_efficiency.dividend_policy is None  # Include unknown
            ]

        if max_risk_level is not None:
            filtered = [
                r for r in filtered
                if r.fund_info.risk_spectrum is None  # Include if unknown
                or r.fund_info.risk_spectrum <= max_risk_level
            ]

        if min_return_1y is not None:
            filtered = [
                r for r in filtered
                if r.performance.return_1y is None  # Include if unknown
                or r.performance.return_1y >= min_return_1y
            ]

        return filtered

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                # Remove percentage signs and Thai text
                value = value.replace('%', '').replace(',', '').strip()
                if not value or value == '-':
                    return None
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def get_user_tax_bracket(self, annual_income: float) -> float:
        """
        Calculate marginal tax rate from annual income

        Thai tax brackets (2568):
        - 0-150,000: 0%
        - 150,001-300,000: 5%
        - 300,001-500,000: 10%
        - 500,001-750,000: 15%
        - 750,001-1,000,000: 20%
        - 1,000,001-2,000,000: 25%
        - 2,000,001-5,000,000: 30%
        - 5,000,001+: 35%
        """
        for threshold, rate in TAX_BRACKETS:
            if annual_income <= threshold:
                return rate
        return 0.35


# ============================================================
# FACTORY FUNCTION
# ============================================================

def create_smart_analyzer(
    api_key: Optional[str] = None
) -> SmartFundAnalyzer:
    """
    Factory function to create SmartFundAnalyzer with configured client

    Args:
        api_key: SEC API key (or use SEC_API_KEY env var)

    Returns:
        Configured SmartFundAnalyzer instance
    """
    from .sec_api_client import SECAPIClient

    client = SECAPIClient(api_key=api_key)
    return SmartFundAnalyzer(sec_client=client)


# ============================================================
# EXAMPLE USAGE
# ============================================================

async def example_usage():
    """Example of how to use SmartFundAnalyzer"""

    import json

    # Create analyzer
    analyzer = create_smart_analyzer()

    try:
        # Example 1: Analyze single fund
        print("=" * 70)
        print("Example 1: Single Fund Analysis")
        print("=" * 70)

        result = await analyzer.analyze_fund(
            fund_code="KFGTECH-A",
            user_tax_bracket=0.25  # 25% tax bracket
        )

        print(f"\nFund: {result.fund_info.fund_code}")
        print(f"NAV: {result.fund_info.nav_per_unit}")
        print(f"Risk Level: {result.fund_info.risk_spectrum}")
        print(f"\n--- True Exposure ---")
        print(f"Is Feeder Fund: {result.true_exposure.is_feeder_fund}")
        print(f"Exposure: {result.true_exposure.exposure_type}")
        for w in result.true_exposure.warnings:
            print(f"  Warning: {w.message}")
        print(f"\n--- Performance ---")
        print(f"Alpha Narrative: {result.performance_intelligence.alpha_narrative}")
        print(f"Beta Narrative: {result.performance_intelligence.beta_narrative}")
        print(f"\n--- Tax Efficiency ---")
        print(f"Policy: {result.tax_efficiency.dividend_policy}")
        print(f"Rating: {result.tax_efficiency.tax_efficiency_rating}")
        print(f"Recommendation: {result.tax_efficiency.recommendation}")
        print(f"\n--- Compliance ---")
        print(f"Factsheet: {result.evidence.pdf_factsheet_url}")
        print(f"As of: {result.evidence.factsheet_as_of_date}")
        print(f"\nOverall Score: {result.overall_score:.1f}/100")

        # Example 2: Batch analysis with filters
        print("\n" + "=" * 70)
        print("Example 2: Batch Analysis (Top 5 RMF for high-income user)")
        print("=" * 70)

        batch_result = await analyzer.analyze_funds_batch(
            fund_codes=["KFGTECH-A", "SCBRMGP", "KFLTFA70-A"],
            user_tax_bracket=0.30,
            filter_accumulating_only=True,
            max_risk_level=6,
            limit=5
        )

        print(f"\nAnalyzed: {batch_result.total_funds_analyzed} funds")
        print(f"Recommended: {batch_result.recommended_funds_count} funds")
        print(f"Duration: {batch_result.analysis_duration_ms:.0f}ms")

        for fund in batch_result.funds:
            print(f"\n#{fund.recommendation_rank}: {fund.fund_info.fund_code}")
            print(f"   Score: {fund.overall_score:.1f}")
            print(f"   Tax: {fund.tax_efficiency.tax_efficiency_rating}")

    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(example_usage())
