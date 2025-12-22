"""
Tax Service สำหรับคำนวณภาษี
"""

from pydantic import BaseModel
from typing import Optional


class TaxCalculationRequest(BaseModel):
    """Request model"""
    gross_income: int
    personal_deduction: int = 60000
    life_insurance: int = 0
    health_insurance: int = 0
    provident_fund: int = 0
    rmf: int = 0
    ssf: int = 0
    pension_insurance: int = 0
    donation: int = 0
    risk_tolerance: str = 'medium'


class TaxCalculationResult:
    """Result model"""
    def __init__(self, gross_income: int, taxable_income: int, tax_amount: int, effective_tax_rate: float):
        self.gross_income = gross_income
        self.taxable_income = taxable_income
        self.tax_amount = tax_amount
        self.effective_tax_rate = effective_tax_rate


class TaxService:
    """
    Service สำหรับคำนวณภาษี
    """
    
    def calculate_tax(self, request: TaxCalculationRequest) -> TaxCalculationResult:
        """
        คำนวณภาษี
        
        Args:
            request: ข้อมูลรายได้และค่าลดหย่อน
            
        Returns:
            ผลการคำนวณภาษี
        """
        # คำนวณค่าลดหย่อนรวม
        total_deductions = (
            request.personal_deduction +
            request.life_insurance +
            request.health_insurance +
            request.provident_fund +
            request.rmf +
            request.ssf +
            request.pension_insurance +
            request.donation
        )
        
        # คำนวณเงินได้สุทธิ
        taxable_income = max(0, request.gross_income - total_deductions)
        
        # คำนวณภาษี
        tax_amount = self._calculate_progressive_tax(taxable_income)
        
        # คำนวณอัตราภาษีเฉลี่ย
        effective_tax_rate = (tax_amount / request.gross_income * 100) if request.gross_income > 0 else 0
        
        return TaxCalculationResult(
            gross_income=request.gross_income,
            taxable_income=taxable_income,
            tax_amount=tax_amount,
            effective_tax_rate=round(effective_tax_rate, 2)
        )
    
    def _calculate_progressive_tax(self, taxable_income: int) -> int:
        """
        คำนวณภาษีแบบขั้นบันได
        
        อัตราภาษี:
        0-150,000: 0%
        150,001-300,000: 5%
        300,001-500,000: 10%
        500,001-750,000: 15%
        750,001-1,000,000: 20%
        1,000,001-2,000,000: 25%
        2,000,001-5,000,000: 30%
        5,000,001+: 35%
        """
        if taxable_income <= 0:
            return 0
        
        tax = 0
        remaining = taxable_income
        
        # ชั้นที่ 1: 0-150,000 (0%)
        if remaining > 150000:
            remaining -= 150000
        else:
            return 0
        
        # ชั้นที่ 2: 150,001-300,000 (5%)
        if remaining > 150000:
            tax += 150000 * 0.05
            remaining -= 150000
        else:
            tax += remaining * 0.05
            return int(tax)
        
        # ชั้นที่ 3: 300,001-500,000 (10%)
        if remaining > 200000:
            tax += 200000 * 0.10
            remaining -= 200000
        else:
            tax += remaining * 0.10
            return int(tax)
        
        # ชั้นที่ 4: 500,001-750,000 (15%)
        if remaining > 250000:
            tax += 250000 * 0.15
            remaining -= 250000
        else:
            tax += remaining * 0.15
            return int(tax)
        
        # ชั้นที่ 5: 750,001-1,000,000 (20%)
        if remaining > 250000:
            tax += 250000 * 0.20
            remaining -= 250000
        else:
            tax += remaining * 0.20
            return int(tax)
        
        # ชั้นที่ 6: 1,000,001-2,000,000 (25%)
        if remaining > 1000000:
            tax += 1000000 * 0.25
            remaining -= 1000000
        else:
            tax += remaining * 0.25
            return int(tax)
        
        # ชั้นที่ 7: 2,000,001-5,000,000 (30%)
        if remaining > 3000000:
            tax += 3000000 * 0.30
            remaining -= 3000000
        else:
            tax += remaining * 0.30
            return int(tax)
        
        # ชั้นที่ 8: 5,000,001+ (35%)
        tax += remaining * 0.35
        
        return int(tax)