"""
Tax Fund Service
Filters SEC fund data for tax-saving funds (RMF, ThaiESG)
and provides tax optimization calculations

Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (ซื้อได้ถึง 31 ธ.ค. 2567)
      SSF is no longer tax-deductible (ended Dec 31, 2024)
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum

from .sec_service import SECService

logger = logging.getLogger(__name__)


class TaxFundCategory(str, Enum):
    """Tax-saving fund categories in Thailand (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)
    """
    RMF = "RMF"           # Retirement Mutual Fund - 30% of income, max 500K
    THAI_ESG = "ThaiESG"  # Thai ESG Fund - 30% of income, max 300K (valid until 2032)


@dataclass
class TaxDeductionLimits:
    """Thai tax deduction limits for ปี 2568

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)
    """
    RMF_PERCENT = 0.30          # 30% of assessable income
    RMF_MAX = 500_000           # Max 500,000 THB
    THAI_ESG_PERCENT = 0.30     # 30% of assessable income
    THAI_ESG_MAX = 300_000      # Max 300,000 THB (valid until 2032)

    # Tax brackets 2568
    TAX_BRACKETS = [
        (150_000, 0),
        (300_000, 0.05),
        (500_000, 0.10),
        (750_000, 0.15),
        (1_000_000, 0.20),
        (2_000_000, 0.25),
        (5_000_000, 0.30),
        (float('inf'), 0.35)
    ]


class TaxFundService:
    """
    Service for filtering and recommending tax-saving funds (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)

    Features:
    - Filter funds by tax category (RMF, ThaiESG)
    - Calculate tax savings potential
    - Get fund recommendations with NAV data
    - Calculate optimal allocation

    Usage:
        service = TaxFundService(sec_service)
        rmf_funds = await service.get_tax_funds('RMF')
        savings = service.calculate_tax_savings(income=1_200_000, rmf=200_000)
    """

    # Keywords for fund classification (ปี 2568 - ไม่รวม SSF)
    FUND_KEYWORDS = {
        TaxFundCategory.RMF: [
            'RMF', 'RETIREMENT', 'เพื่อการเลี้ยงชีพ', 'กองทุนรวมเพื่อการเลี้ยงชีพ'
        ],
        TaxFundCategory.THAI_ESG: [
            'THAIESG', 'THAI ESG', 'ESG', 'ไทยอีเอสจี', 'ธรรมาภิบาล'
        ]
    }

    def __init__(self, sec_service: SECService):
        self.sec = sec_service
        self.limits = TaxDeductionLimits()

        # Cache for fund list
        self._fund_cache: Optional[List[Dict]] = None

        logger.info("TaxFundService initialized")

    # ============================================================
    # Fund Filtering
    # ============================================================

    async def get_tax_funds(
        self,
        category: Optional[TaxFundCategory] = None,
        include_nav: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get tax-saving funds filtered by category (ปี 2568)

        Args:
            category: Filter by RMF or ThaiESG (None for all)
            include_nav: Include current NAV data (slower)
            limit: Maximum number of funds to return

        Returns:
            List of fund objects with tax_category field
        """
        logger.info(f"Fetching tax funds (category={category}, include_nav={include_nav})")

        # Get all funds from SEC
        all_funds = await self.sec.get_fund_list()

        if not isinstance(all_funds, list):
            logger.error(f"Unexpected fund list format: {type(all_funds)}")
            return []

        # Filter and classify funds
        tax_funds = []
        for fund in all_funds:
            fund_category = self._classify_fund(fund)

            if fund_category is None:
                continue

            if category is not None and fund_category != category:
                continue

            tax_funds.append({
                'fund_id': fund.get('unique_id'),
                'fund_code': fund.get('abbr_name', ''),
                'fund_name_th': fund.get('name_th', ''),
                'fund_name_en': fund.get('name_en', ''),
                'amc': fund.get('amc_name_th', ''),
                'amc_id': fund.get('amc_id'),
                'tax_category': fund_category.value,
                'risk_level': fund.get('risk_spectrum', '-'),
                'fund_type': fund.get('proj_retail_type', ''),
                'nav_date': fund.get('nav_date'),
                'last_nav': fund.get('last_nav')
            })

            if len(tax_funds) >= limit:
                break

        logger.info(f"Found {len(tax_funds)} tax funds")

        # Optionally fetch NAV data
        if include_nav and tax_funds:
            tax_funds = await self._enrich_with_nav(tax_funds)

        return tax_funds

    async def get_tax_funds_by_amc(
        self,
        amc_id: str,
        category: Optional[TaxFundCategory] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tax funds from a specific AMC

        Args:
            amc_id: AMC unique ID
            category: Optional category filter

        Returns:
            List of tax funds from the AMC
        """
        all_tax_funds = await self.get_tax_funds(category)
        return [f for f in all_tax_funds if f.get('amc_id') == amc_id]

    async def get_top_performing_funds(
        self,
        category: TaxFundCategory,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top performing funds in a category

        Args:
            category: Tax fund category
            top_n: Number of top funds to return

        Returns:
            Sorted list of funds by performance
        """
        funds = await self.get_tax_funds(category, include_nav=True)

        # Sort by 1-year return (if available)
        def get_return(fund):
            nav_data = fund.get('nav_data', {})
            return nav_data.get('ytd_return', 0) or 0

        sorted_funds = sorted(funds, key=get_return, reverse=True)
        return sorted_funds[:top_n]

    def _classify_fund(self, fund: Dict) -> Optional[TaxFundCategory]:
        """
        Classify a fund into tax category based on name and type

        Args:
            fund: Fund object from SEC API

        Returns:
            TaxFundCategory or None if not a tax fund
        """
        name_th = fund.get('name_th', '').upper()
        name_en = fund.get('name_en', '').upper()
        code = fund.get('abbr_name', '').upper()
        proj_type = fund.get('proj_retail_type', '').upper()

        search_text = f"{name_th} {name_en} {code} {proj_type}"

        # Check each category
        for category, keywords in self.FUND_KEYWORDS.items():
            for keyword in keywords:
                if keyword.upper() in search_text:
                    return category

        return None

    async def _enrich_with_nav(
        self,
        funds: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Add NAV data to funds list

        Args:
            funds: List of fund objects

        Returns:
            Funds with nav_data field added
        """
        fund_codes = [f['fund_code'] for f in funds if f.get('fund_code')]

        if not fund_codes:
            return funds

        # Bulk fetch NAV (respects rate limiting)
        nav_results = await self.sec.bulk_get_nav(fund_codes)
        successful = nav_results.get('successful', {})

        # Merge NAV data
        for fund in funds:
            code = fund.get('fund_code')
            if code and code in successful:
                fund['nav_data'] = successful[code]

        return funds

    # ============================================================
    # Tax Calculations
    # ============================================================

    def calculate_tax_bracket(self, annual_income: float, extra_deductions: float = 0) -> Dict[str, Any]:
        """
        Calculate tax bracket and rate for given income

        Args:
            annual_income: Annual assessable income
            extra_deductions: Additional personal deductions (family, insurance, social security, etc.)

        Returns:
            Tax bracket info with rate and tax amount
        """
        # Standard personal deduction
        personal_deduction = 60_000
        expense_deduction = min(annual_income * 0.5, 100_000)

        taxable_income = max(0, annual_income - personal_deduction - expense_deduction - extra_deductions)

        # Calculate tax
        total_tax = 0
        prev_threshold = 0
        marginal_rate = 0

        for threshold, rate in self.limits.TAX_BRACKETS:
            if taxable_income > prev_threshold:
                taxable_at_rate = min(taxable_income, threshold) - prev_threshold
                total_tax += taxable_at_rate * rate
                marginal_rate = rate
            prev_threshold = threshold

        return {
            'annual_income': annual_income,
            'taxable_income': taxable_income,
            'marginal_rate': marginal_rate,
            'marginal_rate_percent': marginal_rate * 100,
            'total_tax': total_tax,
            'effective_rate': total_tax / annual_income if annual_income > 0 else 0
        }

    def calculate_deduction_limits(self, annual_income: float) -> Dict[str, float]:
        """
        Calculate maximum deduction limits for each category (ปี 2568)

        Note: SSF หมดสิทธิ์ลดหย่อนแล้ว

        Args:
            annual_income: Annual assessable income

        Returns:
            Dict with max deduction for each category
        """
        rmf_limit = min(
            annual_income * self.limits.RMF_PERCENT,
            self.limits.RMF_MAX
        )

        thai_esg_limit = min(
            annual_income * self.limits.THAI_ESG_PERCENT,
            self.limits.THAI_ESG_MAX
        )

        return {
            'rmf_max': rmf_limit,
            'thai_esg_max': thai_esg_limit,
            'total_potential': rmf_limit + thai_esg_limit
        }

    def calculate_tax_savings(
        self,
        annual_income: float,
        rmf_investment: float = 0,
        thai_esg_investment: float = 0,
        existing_deductions: float = 0,
        family_deductions: float = 0,
    ) -> Dict[str, Any]:
        """
        Calculate tax savings from tax fund investments (ปี 2568)

        Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)

        Args:
            annual_income: Annual assessable income
            rmf_investment: Amount invested in RMF
            thai_esg_investment: Amount invested in ThaiESG
            existing_deductions: Other existing deductions (unused, kept for compat)
            family_deductions: Deductions from family, insurance, social security

        Returns:
            Detailed tax savings breakdown
        """
        limits = self.calculate_deduction_limits(annual_income)

        # Apply limits
        actual_rmf = min(rmf_investment, limits['rmf_max'])
        actual_thai_esg = min(thai_esg_investment, limits['thai_esg_max'])

        total_deduction = actual_rmf + actual_thai_esg

        # tax_before: with family deductions, but WITHOUT new RMF/ESG investment
        tax_without = self.calculate_tax_bracket(annual_income, extra_deductions=family_deductions)

        # tax_after: with family deductions AND new RMF/ESG investment
        effective_income = annual_income - total_deduction
        tax_with = self.calculate_tax_bracket(effective_income, extra_deductions=family_deductions)

        # Tax savings
        tax_saved = tax_without['total_tax'] - tax_with['total_tax']

        return {
            'investments': {
                'rmf': rmf_investment,
                'thai_esg': thai_esg_investment,
                'total': rmf_investment + thai_esg_investment
            },
            'actual_deductions': {
                'rmf': actual_rmf,
                'thai_esg': actual_thai_esg,
                'total': total_deduction
            },
            'limits': limits,
            'tax_before': tax_without['total_tax'],
            'tax_after': tax_with['total_tax'],
            'tax_saved': tax_saved,
            'effective_return': (
                tax_saved / total_deduction * 100
                if total_deduction > 0 else 0
            ),
            'marginal_rate': tax_without['marginal_rate_percent']
        }

    def calculate_optimal_allocation(
        self,
        annual_income: float,
        available_budget: float,
        existing_rmf: float = 0,
        existing_thai_esg: float = 0,
        priority: str = 'balanced',
        family_deductions: float = 0,
    ) -> Dict[str, Any]:
        """
        Calculate optimal allocation across tax fund categories (ปี 2568)

        Note: SSF หมดสิทธิ์ลดหย่อนแล้ว

        Args:
            annual_income: Annual income
            available_budget: Budget available for tax fund investment
            existing_*: Already invested amounts
            priority: 'tax_max', 'balanced', or 'conservative'

        Returns:
            Recommended allocation
        """
        limits = self.calculate_deduction_limits(annual_income)

        # Calculate remaining quota
        rmf_remaining = max(0, limits['rmf_max'] - existing_rmf)
        thai_esg_remaining = max(0, limits['thai_esg_max'] - existing_thai_esg)

        total_remaining = rmf_remaining + thai_esg_remaining
        budget = min(available_budget, total_remaining)

        # Allocation strategy
        allocation = {'rmf': 0, 'thai_esg': 0}
        remaining_budget = budget

        if priority == 'tax_max':
            # Maximize deductions: RMF first (higher limit), then ThaiESG
            allocation['rmf'] = min(remaining_budget, rmf_remaining)
            remaining_budget -= allocation['rmf']

            allocation['thai_esg'] = min(remaining_budget, thai_esg_remaining)

        elif priority == 'balanced':
            # Balanced: distribute proportionally
            if total_remaining > 0:
                rmf_ratio = rmf_remaining / total_remaining
                esg_ratio = thai_esg_remaining / total_remaining

                allocation['rmf'] = min(budget * rmf_ratio, rmf_remaining)
                allocation['thai_esg'] = min(budget * esg_ratio, thai_esg_remaining)

        else:  # conservative
            # ThaiESG first (shorter holding period), then RMF
            allocation['thai_esg'] = min(remaining_budget, thai_esg_remaining)
            remaining_budget -= allocation['thai_esg']

            allocation['rmf'] = min(remaining_budget, rmf_remaining)

        # Calculate savings with this allocation
        savings = self.calculate_tax_savings(
            annual_income,
            rmf_investment=existing_rmf + allocation['rmf'],
            thai_esg_investment=existing_thai_esg + allocation['thai_esg'],
            family_deductions=family_deductions,
        )

        return {
            'recommended_allocation': allocation,
            'total_investment': sum(allocation.values()),
            'remaining_budget': available_budget - sum(allocation.values()),
            'remaining_quota': {
                'rmf': rmf_remaining - allocation['rmf'],
                'thai_esg': thai_esg_remaining - allocation['thai_esg']
            },
            'tax_savings': savings['tax_saved'],
            'effective_return_percent': savings['effective_return'],
            'priority_used': priority
        }

    # ============================================================
    # Statistics
    # ============================================================

    async def get_fund_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available tax funds (ปี 2568)

        Returns:
            Count and breakdown by category
        """
        all_funds = await self.get_tax_funds(limit=1000)

        stats = {
            'total': len(all_funds),
            'by_category': {
                'RMF': 0,
                'ThaiESG': 0
            },
            'by_amc': {}
        }

        for fund in all_funds:
            category = fund.get('tax_category')
            amc = fund.get('amc', 'Unknown')

            if category:
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            stats['by_amc'][amc] = stats['by_amc'].get(amc, 0) + 1

        return stats


# ============================================================
# Example Usage
# ============================================================

async def example_usage():
    """Example of how to use TaxFundService"""
    from .sec_service import SECService

    sec = SECService(enable_cache=True)
    tax_service = TaxFundService(sec)

    try:
        # Get RMF funds
        print("=" * 60)
        print("Example 1: Get RMF Funds")
        print("=" * 60)

        rmf_funds = await tax_service.get_tax_funds(TaxFundCategory.RMF, limit=5)
        for fund in rmf_funds:
            print(f"  {fund['fund_code']}: {fund['fund_name_th']}")

        # Calculate tax savings
        print("\n" + "=" * 60)
        print("Example 2: Calculate Tax Savings")
        print("=" * 60)

        savings = tax_service.calculate_tax_savings(
            annual_income=1_200_000,
            rmf_investment=200_000,
            thai_esg_investment=100_000
        )

        print(f"  Tax saved: ฿{savings['tax_saved']:,.0f}")
        print(f"  Effective return: {savings['effective_return']:.1f}%")

        # Optimal allocation (ปี 2568 - ไม่รวม SSF)
        print("\n" + "=" * 60)
        print("Example 3: Optimal Allocation (RMF + ThaiESG)")
        print("=" * 60)

        allocation = tax_service.calculate_optimal_allocation(
            annual_income=1_200_000,
            available_budget=300_000,
            priority='balanced'
        )

        print(f"  Recommended:")
        print(f"    RMF: ฿{allocation['recommended_allocation']['rmf']:,.0f}")
        print(f"    ThaiESG: ฿{allocation['recommended_allocation']['thai_esg']:,.0f}")
        print(f"  Tax savings: ฿{allocation['tax_savings']:,.0f}")

    finally:
        await sec.close()


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(example_usage())
