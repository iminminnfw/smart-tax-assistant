"""
Tax Fund Service
Filters SEC fund data for tax-saving funds (RMF, SSF, ThaiESG)
and provides tax optimization calculations
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum

from .sec_service import SECService

logger = logging.getLogger(__name__)


class TaxFundCategory(str, Enum):
    """Tax-saving fund categories in Thailand"""
    RMF = "RMF"           # Retirement Mutual Fund - 30% of income, max 500K
    SSF = "SSF"           # Super Saving Fund - max 200K (combined with RMF max 500K)
    THAI_ESG = "ThaiESG"  # Thai ESG Fund - max 300K


@dataclass
class TaxDeductionLimits:
    """Thai tax deduction limits for 2567-2568"""
    RMF_PERCENT = 0.30          # 30% of assessable income
    RMF_MAX = 500_000           # Max 500,000 THB
    SSF_MAX = 200_000           # Max 200,000 THB
    SSF_RMF_COMBINED_MAX = 500_000  # Combined max 500,000 THB
    THAI_ESG_MAX = 300_000      # Max 300,000 THB (valid until 2032)

    # Tax brackets 2567
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
    Service for filtering and recommending tax-saving funds

    Features:
    - Filter funds by tax category (RMF, SSF, ThaiESG)
    - Calculate tax savings potential
    - Get fund recommendations with NAV data
    - Calculate optimal allocation

    Usage:
        service = TaxFundService(sec_service)
        rmf_funds = await service.get_tax_funds('RMF')
        savings = service.calculate_tax_savings(income=1_200_000, rmf=200_000)
    """

    # Keywords for fund classification
    FUND_KEYWORDS = {
        TaxFundCategory.RMF: [
            'RMF', 'RETIREMENT', 'เพื่อการเลี้ยงชีพ', 'กองทุนรวมเพื่อการเลี้ยงชีพ'
        ],
        TaxFundCategory.SSF: [
            'SSF', 'SUPER SAVING', 'ซูเปอร์เซฟวิ่ง'
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
        Get tax-saving funds filtered by category

        Args:
            category: Filter by RMF, SSF, or ThaiESG (None for all)
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

    def calculate_tax_bracket(self, annual_income: float) -> Dict[str, Any]:
        """
        Calculate tax bracket and rate for given income

        Args:
            annual_income: Annual assessable income

        Returns:
            Tax bracket info with rate and tax amount
        """
        # Standard personal deduction
        personal_deduction = 60_000
        expense_deduction = min(annual_income * 0.5, 100_000)

        taxable_income = max(0, annual_income - personal_deduction - expense_deduction)

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
        Calculate maximum deduction limits for each category

        Args:
            annual_income: Annual assessable income

        Returns:
            Dict with max deduction for each category
        """
        rmf_limit = min(
            annual_income * self.limits.RMF_PERCENT,
            self.limits.RMF_MAX
        )

        return {
            'rmf_max': rmf_limit,
            'ssf_max': self.limits.SSF_MAX,
            'ssf_rmf_combined_max': self.limits.SSF_RMF_COMBINED_MAX,
            'thai_esg_max': self.limits.THAI_ESG_MAX,
            'total_potential': rmf_limit + self.limits.THAI_ESG_MAX
        }

    def calculate_tax_savings(
        self,
        annual_income: float,
        rmf_investment: float = 0,
        ssf_investment: float = 0,
        thai_esg_investment: float = 0,
        existing_deductions: float = 0
    ) -> Dict[str, Any]:
        """
        Calculate tax savings from tax fund investments

        Args:
            annual_income: Annual assessable income
            rmf_investment: Amount invested in RMF
            ssf_investment: Amount invested in SSF
            thai_esg_investment: Amount invested in ThaiESG
            existing_deductions: Other existing deductions

        Returns:
            Detailed tax savings breakdown
        """
        limits = self.calculate_deduction_limits(annual_income)

        # Apply limits
        actual_rmf = min(rmf_investment, limits['rmf_max'])
        actual_ssf = min(ssf_investment, limits['ssf_max'])

        # Combined SSF+RMF limit
        combined = actual_rmf + actual_ssf
        if combined > limits['ssf_rmf_combined_max']:
            excess = combined - limits['ssf_rmf_combined_max']
            actual_ssf = max(0, actual_ssf - excess)

        actual_thai_esg = min(thai_esg_investment, limits['thai_esg_max'])

        total_deduction = actual_rmf + actual_ssf + actual_thai_esg

        # Calculate tax without deductions
        tax_without = self.calculate_tax_bracket(annual_income)

        # Calculate tax with deductions (reduce taxable income)
        effective_income = annual_income - total_deduction
        tax_with = self.calculate_tax_bracket(effective_income)

        # Tax savings
        tax_saved = tax_without['total_tax'] - tax_with['total_tax']

        return {
            'investments': {
                'rmf': rmf_investment,
                'ssf': ssf_investment,
                'thai_esg': thai_esg_investment,
                'total': rmf_investment + ssf_investment + thai_esg_investment
            },
            'actual_deductions': {
                'rmf': actual_rmf,
                'ssf': actual_ssf,
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
        existing_ssf: float = 0,
        existing_thai_esg: float = 0,
        priority: str = 'balanced'
    ) -> Dict[str, Any]:
        """
        Calculate optimal allocation across tax fund categories

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
        ssf_remaining = max(0, limits['ssf_max'] - existing_ssf)
        thai_esg_remaining = max(0, limits['thai_esg_max'] - existing_thai_esg)

        # Combined limit check
        combined_remaining = limits['ssf_rmf_combined_max'] - existing_rmf - existing_ssf
        ssf_remaining = min(ssf_remaining, combined_remaining)

        total_remaining = rmf_remaining + ssf_remaining + thai_esg_remaining
        budget = min(available_budget, total_remaining)

        # Allocation strategy
        allocation = {'rmf': 0, 'ssf': 0, 'thai_esg': 0}
        remaining_budget = budget

        if priority == 'tax_max':
            # Maximize deductions: RMF first, then ThaiESG, then SSF
            allocation['rmf'] = min(remaining_budget, rmf_remaining)
            remaining_budget -= allocation['rmf']

            allocation['thai_esg'] = min(remaining_budget, thai_esg_remaining)
            remaining_budget -= allocation['thai_esg']

            allocation['ssf'] = min(remaining_budget, ssf_remaining)

        elif priority == 'balanced':
            # Balanced: distribute proportionally
            if total_remaining > 0:
                rmf_ratio = rmf_remaining / total_remaining
                ssf_ratio = ssf_remaining / total_remaining
                esg_ratio = thai_esg_remaining / total_remaining

                allocation['rmf'] = min(budget * rmf_ratio, rmf_remaining)
                allocation['ssf'] = min(budget * ssf_ratio, ssf_remaining)
                allocation['thai_esg'] = min(budget * esg_ratio, thai_esg_remaining)

        else:  # conservative
            # ThaiESG first (newer, more flexible), then SSF, then RMF
            allocation['thai_esg'] = min(remaining_budget, thai_esg_remaining)
            remaining_budget -= allocation['thai_esg']

            allocation['ssf'] = min(remaining_budget, ssf_remaining)
            remaining_budget -= allocation['ssf']

            allocation['rmf'] = min(remaining_budget, rmf_remaining)

        # Calculate savings with this allocation
        savings = self.calculate_tax_savings(
            annual_income,
            rmf_investment=existing_rmf + allocation['rmf'],
            ssf_investment=existing_ssf + allocation['ssf'],
            thai_esg_investment=existing_thai_esg + allocation['thai_esg']
        )

        return {
            'recommended_allocation': allocation,
            'total_investment': sum(allocation.values()),
            'remaining_budget': available_budget - sum(allocation.values()),
            'remaining_quota': {
                'rmf': rmf_remaining - allocation['rmf'],
                'ssf': ssf_remaining - allocation['ssf'],
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
        Get statistics about available tax funds

        Returns:
            Count and breakdown by category
        """
        all_funds = await self.get_tax_funds(limit=1000)

        stats = {
            'total': len(all_funds),
            'by_category': {
                'RMF': 0,
                'SSF': 0,
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

        # Optimal allocation
        print("\n" + "=" * 60)
        print("Example 3: Optimal Allocation")
        print("=" * 60)

        allocation = tax_service.calculate_optimal_allocation(
            annual_income=1_200_000,
            available_budget=300_000,
            priority='balanced'
        )

        print(f"  Recommended:")
        print(f"    RMF: ฿{allocation['recommended_allocation']['rmf']:,.0f}")
        print(f"    SSF: ฿{allocation['recommended_allocation']['ssf']:,.0f}")
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
