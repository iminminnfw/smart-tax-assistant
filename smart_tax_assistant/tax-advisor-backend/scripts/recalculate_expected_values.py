"""
Script to recalculate expected values for test cases 8-19 with correct tier assignments.
"""
from typing import List, Tuple

def get_tier_for_gross_income(gross: int) -> List[int]:
    """Get investment tiers based on gross income (must match main.py logic)"""
    if gross < 600000:
        return [40000, 60000, 80000]
    elif gross < 1000000:
        return [60000, 100000, 150000]
    elif gross < 1500000:
        return [200000, 350000, 500000]
    elif gross < 2000000:
        return [300000, 500000, 800000]
    elif gross < 3000000:
        return [500000, 800000, 1200000]
    else:
        return [800000, 1200000, 1800000]

def calculate_progressive_tax(taxable: int) -> int:
    """Calculate progressive tax"""
    brackets = [
        (150000, 0.00),
        (300000, 0.05),
        (500000, 0.10),
        (750000, 0.15),
        (1000000, 0.20),
        (2000000, 0.25),
        (5000000, 0.30),
        (float('inf'), 0.35)
    ]

    tax = 0
    remaining = taxable
    prev_limit = 0

    for limit, rate in brackets:
        if remaining <= 0:
            break
        taxable_in_bracket = min(remaining, limit - prev_limit)
        tax += int(taxable_in_bracket * rate)
        remaining -= taxable_in_bracket
        prev_limit = limit

    return tax

def get_marginal_rate(taxable_with_investment: int) -> float:
    """Get marginal tax rate for the given taxable income"""
    if taxable_with_investment <= 150000:
        return 0.00
    elif taxable_with_investment <= 300000:
        return 0.05
    elif taxable_with_investment <= 500000:
        return 0.10
    elif taxable_with_investment <= 750000:
        return 0.15
    elif taxable_with_investment <= 1000000:
        return 0.20
    elif taxable_with_investment <= 2000000:
        return 0.25
    elif taxable_with_investment <= 5000000:
        return 0.30
    else:
        return 0.35

def calculate_expense_deduction(gross: int, income_type: str, profession_type: str = None, business_type: str = None) -> int:
    """Calculate expense deduction based on income type"""
    if income_type == "40(1)":  # Salary
        return min(int(gross * 0.50), 100000)
    elif income_type == "40(6)":  # Independent professions
        if profession_type in ["medical", "dentistry"]:
            return int(gross * 0.60)
        elif profession_type in ["law", "architecture", "engineering", "accounting"]:
            return int(gross * 0.30)
    elif income_type == "40(8)":  # Business
        if business_type == "entertainment":
            # Special rule: 60% for first 300K, 40% for excess (max 600K total deduction)
            first_part = min(gross, 300000) * 0.60
            if gross > 300000:
                second_part = min(gross - 300000, 300000) * 0.40
                return min(int(first_part + second_part), 600000)
            else:
                return int(first_part)
        else:
            return int(gross * 0.60)
    return 0

def calculate_expected_values(
    gross: int,
    income_type: str,
    profession_type: str = None,
    business_type: str = None,
    total_allowances: int = 335000  # Standard: personal 60K + spouse 60K + child 90K + parent 60K + disabled 65K
) -> Tuple[List[int], List[int]]:
    """
    Calculate expected investment and tax saving for a test case.
    Returns: (investments, tax_savings)
    """
    # 1. Calculate expense deduction
    expense = calculate_expense_deduction(gross, income_type, profession_type, business_type)

    # 2. Calculate base taxable income (without investment)
    taxable_base = max(0, gross - expense - total_allowances)

    # 3. Get tiers based on gross income
    tiers = get_tier_for_gross_income(gross)

    # 4. Calculate tax saving for each tier
    tax_savings = []
    for investment in tiers:
        # Taxable income with investment (investment reduces taxable income)
        taxable_with_investment = max(0, taxable_base - investment)

        # Marginal rate = rate at (taxable_base) position
        marginal_rate = get_marginal_rate(taxable_base)

        # Tax saving = investment × marginal rate
        tax_saving = int(investment * marginal_rate)
        tax_savings.append(tax_saving)

    return tiers, tax_savings

# Test cases 8-19 data
test_cases = [
    # Test Case 8: Lawyer 960K
    {
        "case": 8,
        "name": "ทนายความ 960K",
        "gross": 960000,
        "income_type": "40(6)",
        "profession_type": "law",
        "allowances": 335000
    },
    # Test Case 9: Architect 1.8M
    {
        "case": 9,
        "name": "สถาปนิก 1.8M",
        "gross": 1800000,
        "income_type": "40(6)",
        "profession_type": "architecture",
        "allowances": 335000
    },
    # Test Case 10: Hair salon 540K
    {
        "case": 10,
        "name": "ร้านตัดผม 540K",
        "gross": 540000,
        "income_type": "40(8)",
        "business_type": "hair_salon",
        "allowances": 275000  # Lower allowances
    },
    # Test Case 11: General trade 1M
    {
        "case": 11,
        "name": "การค้าทั่วไป 1M",
        "gross": 1000000,
        "income_type": "40(8)",
        "business_type": "general_trade",
        "allowances": 335000
    },
    # Test Case 12: Restaurant 1.5M
    {
        "case": 12,
        "name": "ร้านอาหาร 1.5M",
        "gross": 1500000,
        "income_type": "40(8)",
        "business_type": "restaurant",
        "allowances": 335000
    },
    # Test Case 13: Entertainment 600K
    {
        "case": 13,
        "name": "นักแสดง 600K",
        "gross": 600000,
        "income_type": "40(8)",
        "business_type": "entertainment",
        "allowances": 335000
    },
    # Test Case 14: Photography 720K
    {
        "case": 14,
        "name": "ช่างภาพ 720K",
        "gross": 720000,
        "income_type": "40(8)",
        "business_type": "photography",
        "allowances": 275000
    },
    # Test Case 15: Cosmetics 840K
    {
        "case": 15,
        "name": "ร้านเสริมสวย 840K",
        "gross": 840000,
        "income_type": "40(8)",
        "business_type": "cosmetics",
        "allowances": 335000
    },
    # Test Case 16: Vehicle repair 2.4M
    {
        "case": 16,
        "name": "โรงซ่อมรถ 2.4M",
        "gross": 2400000,
        "income_type": "40(8)",
        "business_type": "vehicle_repair",
        "allowances": 395000
    },
    # Test Case 17: Transportation 1.2M
    {
        "case": 17,
        "name": "ขนส่ง 1.2M",
        "gross": 1200000,
        "income_type": "40(8)",
        "business_type": "transportation",
        "allowances": 335000
    },
    # Test Case 18: Laundry 600K
    {
        "case": 18,
        "name": "โรงซักรีด 600K",
        "gross": 600000,
        "income_type": "40(8)",
        "business_type": "laundry",
        "allowances": 275000
    },
    # Test Case 19: Printing 1.8M
    {
        "case": 19,
        "name": "โรงพิมพ์ 1.8M",
        "gross": 1800000,
        "income_type": "40(8)",
        "business_type": "printing",
        "allowances": 395000
    },
]

print("="*80)
print("RECALCULATED EXPECTED VALUES FOR TEST CASES 8-19")
print("="*80)
print()

for tc in test_cases:
    tiers, tax_savings = calculate_expected_values(
        tc["gross"],
        tc["income_type"],
        tc.get("profession_type"),
        tc.get("business_type"),
        tc["allowances"]
    )

    # Calculate intermediate values for verification
    expense = calculate_expense_deduction(
        tc["gross"],
        tc["income_type"],
        tc.get("profession_type"),
        tc.get("business_type")
    )
    taxable_base = max(0, tc["gross"] - expense - tc["allowances"])
    marginal_rate = get_marginal_rate(taxable_base)

    print(f"Test Case {tc['case']}: {tc['name']}")
    print(f"  Gross: {tc['gross']:,}")
    print(f"  Expense: {expense:,}")
    print(f"  Allowances: {tc['allowances']:,}")
    print(f"  Taxable (base): {taxable_base:,}")
    print(f"  Marginal Rate: {marginal_rate:.1%}")
    print(f"  Tiers: {tiers}")
    print(f"  Tax Savings: {tax_savings}")
    print(f"  Expected plan_1: investment={tiers[0]:,}, tax_saving={tax_savings[0]:,}")
    print(f"  Expected plan_2: investment={tiers[1]:,}, tax_saving={tax_savings[1]:,}")
    print(f"  Expected plan_3: investment={tiers[2]:,}, tax_saving={tax_savings[2]:,}")
    print()
