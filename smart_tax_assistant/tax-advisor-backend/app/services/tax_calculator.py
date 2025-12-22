"""
Tax Calculator Service
Version: Support All Deduction Categories - ปี 2568
Updated: Added Section 40(6)/40(8) expense deduction and Alternative Minimum Tax (AMT)
"""

from typing import Dict, Tuple
from app.models import (
    TaxCalculationRequest,
    TaxCalculationResult,
    IncomeType,
    ProfessionType,
    BusinessType,
    ExpenseMethod
)


class TaxCalculatorService:
    """Service สำหรับคำนวณภาษีเงินได้บุคคลธรรมดา ปี 2568

    เพิ่มการคำนวณตามกฎหมายจริง:
    1. หักค่าใช้จ่ายตามประเภทเงินได้ มาตรา 40(6) และ 40(8)
    2. คำนวณภาษีทั้ง 2 วิธี (จากเงินได้สุทธิ และ 0.5% ของเงินได้รวม)
    3. เสียภาษีตามจำนวนที่สูงกว่า
    """
#ขั้นบันได
    TAX_BRACKETS = [
        (150000, 0),
        (300000, 5),
        (500000, 10),
        (750000, 15),
        (1000000, 20),
        (2000000, 25),
        (5000000, 30),
        (float('inf'), 35)
    ]

    def _calculate_expense_deduction(self, request: TaxCalculationRequest) -> int:
        """คำนวณค่าใช้จ่ายที่หักได้ตามมาตรา 40(6) หรือ 40(8)

        ตาม guideline50_50.pdf หน้า 12-15:
        - วิธีที่ 1: หักค่าใช้จ่ายจริง (ต้องมีเอกสาร)
        - วิธีที่ 2: หักค่าใช้จ่ายเหมา (ตามอัตรา %)
        """
        gross_income = request.gross_income
        income_type = request.income_type
        expense_method = request.expense_method

        # ถ้าเลือกหักค่าใช้จ่ายจริง
        if expense_method == ExpenseMethod.ACTUAL:
            return request.actual_expenses

        # ถ้าเลือกหักค่าใช้จ่ายเหมา (standard deduction)
        # กรณี 40(1) - เงินเดือน ค่าจ้าง (หน้า 11-12)
        if income_type == IncomeType.SECTION_40_1:
            return min(int(gross_income * 0.50), 100000)  # 50% สูงสุด 100,000 บาท

        # กรณีเงินได้ที่ไม่มีค่าใช้จ่าย (40(2), 40(4))
        if income_type in [IncomeType.SECTION_40_2, IncomeType.SECTION_40_4]:
            return 0  # ไม่มีค่าใช้จ่ายให้หัก

        # กรณี 40(3) - ค่าแห่งกู๊ดวิลล์ ค่าลิขสิทธิ์ (หน้า 12)
        if income_type == IncomeType.SECTION_40_3:
            return min(int(gross_income * 0.50), 100000)  # 50% สูงสุด 100,000 บาท

        # กรณี 40(5) - ค่าเช่าทรัพย์สิน (หน้า 12)
        # ค่า default = 30% (ทรัพย์สินอื่น) เนื่องจากไม่มีข้อมูลประเภททรัพย์สิน
        if income_type == IncomeType.SECTION_40_5:
            return int(gross_income * 0.30)  # 30% (ค่า default)

        # 40(6) อิสระ
        if income_type == IncomeType.SECTION_40_6:
            profession = request.profession_type
            if profession == ProfessionType.MEDICAL:
                return int(gross_income * 0.60)  # การประกอบโรคศิลปะ 60%
            else:
                return int(gross_income * 0.30)  # วิชาชีพอื่นๆ 30%

        # กรณี 40(7) - การรับเหมา (หน้า 13)
        if income_type == IncomeType.SECTION_40_7:
            return int(gross_income * 0.60)  # 60%

        # กรณี 40(8) - เงินได้อื่นๆ (ธุรกิจ) (หน้า 13-15)
        if income_type == IncomeType.SECTION_40_8:
            business = request.business_type

            # กรณีพิเศษ: นักแสดง นักร้อง (entertainment)
            if business == BusinessType.ENTERTAINMENT:
                # 60% สำหรับ 300,000 แรก + 40% สำหรับส่วนเกิน (สูงสุดรวม 600,000)
                if gross_income <= 300000:
                    return int(gross_income * 0.60)
                else:
                    first_part = int(300000 * 0.60)  # 180,000
                    excess = gross_income - 300000
                    second_part = int(excess * 0.40)
                    return min(first_part + second_part, 600000)

            # ธุรกิจอื่นๆ ส่วนใหญ่ = 60% (ตารางหน้า 14-15)
            return int(gross_income * 0.60)

        # Default: ไม่มีค่าใช้จ่าย
        return 0

    def _validate_percentage_limits(self, request: TaxCalculationRequest) -> None:
        """ตรวจสอบขีดจำกัดตามเปอร์เซ็นต์ของรายได้

        ตาม tax_deductions_update280168.pdf:
        - ประกันบำนาญ: สูงสุด 15% หรือ 200,000 (item 13)
        - RMF: สูงสุด 30% หรือ 500,000 (item 12)
        - ThaiESG: สูงสุด 30% หรือ 300,000 (item 21)
        - PVD/กบข./ครู: มีขีดจำกัดตามเปอร์เซ็นต์
        """
        gross_income = request.gross_income

        # ประกันบำนาญ: สูงสุด 15% หรือ 200,000
        max_pension = min(int(gross_income * 0.15), 200000)
        if request.pension_insurance > max_pension:
            raise ValueError(
                f"ประกันบำนาญเกินขีดจำกัด: ระบุ {request.pension_insurance:,} บาท "
                f"แต่สูงสุดได้ {max_pension:,} บาท (15% ของรายได้ {gross_income:,} หรือ 200,000)"
            )

        # RMF: สูงสุด 30% หรือ 500,000
        max_rmf = min(int(gross_income * 0.30), 500000)
        if request.rmf > max_rmf:
            raise ValueError(
                f"RMF เกินขีดจำกัด: ระบุ {request.rmf:,} บาท "
                f"แต่สูงสุดได้ {max_rmf:,} บาท (30% ของรายได้ {gross_income:,} หรือ 500,000)"
            )

        # ThaiESG: สูงสุด 30% หรือ 300,000
        max_thai_esg = min(int(gross_income * 0.30), 300000)
        if request.thai_esg > max_thai_esg:
            raise ValueError(
                f"ThaiESG เกินขีดจำกัด: ระบุ {request.thai_esg:,} บาท "
                f"แต่สูงสุดได้ {max_thai_esg:,} บาท (30% ของรายได้ {gross_income:,} หรือ 300,000)"
            )

        # ThaiESGX (เงินใหม่): สูงสุด 30% หรือ 300,000
        if request.thai_esgx_new > max_thai_esg:
            raise ValueError(
                f"ThaiESGX (เงินใหม่) เกินขีดจำกัด: ระบุ {request.thai_esgx_new:,} บาท "
                f"แต่สูงสุดได้ {max_thai_esg:,} บาท (30% ของรายได้ {gross_income:,} หรือ 300,000)"
            )

        # PVD: สูงสุด 15% หรือ 500,000
        max_pvd = min(int(gross_income * 0.15), 500000)
        if request.provident_fund > max_pvd:
            raise ValueError(
                f"PVD เกินขีดจำกัด: ระบุ {request.provident_fund:,} บาท "
                f"แต่สูงสุดได้ {max_pvd:,} บาท (15% ของรายได้ {gross_income:,} หรือ 500,000)"
            )

        # กบข.: สูงสุด 30% หรือ 500,000
        max_gpf = min(int(gross_income * 0.30), 500000)
        if request.gpf > max_gpf:
            raise ValueError(
                f"กบข. เกินขีดจำกัด: ระบุ {request.gpf:,} บาท "
                f"แต่สูงสุดได้ {max_gpf:,} บาท (30% ของรายได้ {gross_income:,} หรือ 500,000)"
            )

        # กองทุนสงเคราะห์ครู: สูงสุด 15% หรือ 500,000
        if request.pvd_teacher > max_pvd:
            raise ValueError(
                f"กองทุนสงเคราะห์ครู เกินขีดจำกัด: ระบุ {request.pvd_teacher:,} บาท "
                f"แต่สูงสุดได้ {max_pvd:,} บาท (15% ของรายได้ {gross_income:,} หรือ 500,000)"
            )

        # เงินบริจาคทั่วไป: สูงสุด 10% ของรายได้หลังหักค่าใช้จ่าย
        # (จะคำนวณหลังหักค่าใช้จ่ายและค่าลดหย่อนแล้ว)

    def calculate_tax(self, request: TaxCalculationRequest) -> TaxCalculationResult:
        """คำนวณภาษีเงินได้ ปี 2568

        ตาม guideline50_50.pdf หน้า 20:
        - วิธีที่ 1: คำนวณจากเงินได้สุทธิ (Progressive Tax)
        - วิธีที่ 2: คำนวณจากเงินได้พึงประเมิน (0.5% ของเงินได้ มาตรา 40(5)-(8))
        - เสียภาษีตามจำนวนที่สูงกว่า (ยกเว้น วิธีที่ 2 ≤ 5,000 ให้เสียตามวิธีที่ 1)
        """

        gross_income = request.gross_income

        # 🆕 ตรวจสอบขีดจำกัดตามเปอร์เซ็นต์ก่อนคำนวณภาษี
        self._validate_percentage_limits(request)

        # 🆕 ขั้นตอนที่ 1: คำนวณค่าใช้จ่ายตามประเภทเงินได้และวิธีที่เลือก
        expense_deduction = self._calculate_expense_deduction(request)

        # รวมค่าลดหย่อนทั้งหมด ปี 2568
        total_allowances = (
            # กลุ่มส่วนตัว/ครอบครัว
            request.personal_deduction +
            request.spouse_deduction +
            request.child_deduction +
            request.parent_support +
            request.disabled_support +

            # กลุ่มประกันชีวิตและสุขภาพ
            request.life_insurance +
            request.life_insurance_pension +
            request.life_insurance_parents +
            request.health_insurance +
            request.health_insurance_parents +
            request.social_security +

            # กลุ่มกองทุนและการลงทุน
            request.pension_insurance +
            request.provident_fund +
            request.gpf +
            request.pvd_teacher +
            request.rmf +

            # กลุ่มกองทุน ESG (ใหม่ปี 2568 - แทน SSF)
            request.thai_esg +
            request.thai_esgx_new +
            request.thai_esgx_ltf +

            # กลุ่มอื่นๆ (ใหม่ปี 2568)
            request.stock_investment +
            request.easy_e_receipt +
            request.home_loan_interest +
            request.nsf +

            # กลุ่มเงินบริจาค
            request.donation_general +
            (request.donation_education * 2) +  # นับ 2 เท่า
            request.donation_social_enterprise +
            request.donation_political
        )

        # เงินได้สุทธิ = รายได้รวม - ค่าใช้จ่าย - ค่าลดหย่อน
        taxable_income = max(0, gross_income - expense_deduction - total_allowances)

        # 🆕 วิธีที่ 1: คำนวณภาษีจากเงินได้สุทธิ (Progressive Tax)
        tax_method_1 = self._calculate_progressive_tax(taxable_income)

        # 🆕 วิธีที่ 2: คำนวณภาษีจากเงินได้พึงประเมิน (Alternative Minimum Tax)
        # ตาม guideline50_50.pdf หน้า 5 และหน้า 20:
        # - PND 94 (ครึ่งปี): เฉพาะ มาตรา 40(5), 40(6), 40(7), 40(8)
        # - PND 90 (ทั้งปี): ใช้กับ มาตรา 40(2), 40(3), 40(5), 40(6), 40(7), 40(8)
        #   (ยกเว้น 40(1) เงินเดือน และ 40(4) ดอกเบี้ย/เงินปันผล)
        tax_method_2 = 0
        if request.income_type in [
            IncomeType.SECTION_40_2,  # ✨ เพิ่มสำหรับ PND 90
            IncomeType.SECTION_40_3,  # ✨ เพิ่มสำหรับ PND 90
            IncomeType.SECTION_40_5,
            IncomeType.SECTION_40_6,
            IncomeType.SECTION_40_7,
            IncomeType.SECTION_40_8
        ]:
            # 0.5% ของเงินได้รวม (ไม่หักค่าใช้จ่าย)
            tax_method_2 = int(gross_income * 0.005)

        # 🆕 เลือกภาษีที่สูงกว่า (ตามกฎหมาย)
        # ยกเว้น: ถ้า tax_method_2 ≤ 5,000 บาท ให้ใช้ tax_method_1
        if tax_method_2 > 0 and tax_method_2 > 5000:
            tax_amount = max(tax_method_1, tax_method_2)
        else:
            tax_amount = tax_method_1

        # อัตราภาษีเฉลี่ย
        effective_tax_rate = (tax_amount / gross_income * 100) if gross_income > 0 else 0

        print(f"💰 Tax Calculation Summary:")
        print(f"   - Gross Income: {gross_income:,} บาท")
        print(f"   - Expense Deduction: {expense_deduction:,} บาท")
        print(f"   - Total Allowances: {total_allowances:,} บาท")
        print(f"   - Taxable Income: {taxable_income:,} บาท")
        print(f"   - Tax (Method 1 - Progressive): {tax_method_1:,} บาท")
        print(f"   - Tax (Method 2 - AMT 0.5%): {tax_method_2:,} บาท")
        print(f"   - Final Tax Amount: {tax_amount:,} บาท")

        return TaxCalculationResult(
            gross_income=gross_income,
            taxable_income=taxable_income,
            tax_amount=tax_amount,
            effective_tax_rate=round(effective_tax_rate, 2)
        )
    
    def _calculate_progressive_tax(self, taxable_income: int) -> int:
        """คำนวณภาษีแบบขั้นบันได"""
        if taxable_income <= 0:
            return 0
        
        tax = 0
        previous_bracket = 0
        
        for bracket_limit, rate in self.TAX_BRACKETS:
            if taxable_income <= bracket_limit:
                taxable_in_bracket = taxable_income - previous_bracket
                tax += taxable_in_bracket * rate / 100
                break
            else:
                taxable_in_bracket = bracket_limit - previous_bracket
                tax += taxable_in_bracket * rate / 100
                previous_bracket = bracket_limit
        
        return int(tax)
    
    def get_marginal_tax_rate(self, taxable_income: int) -> int:
        """หาอัตราภาษีส่วนเพิ่ม"""
        for bracket_limit, rate in self.TAX_BRACKETS:
            if taxable_income <= bracket_limit:
                return rate
        return 35

    def calculate_tax_saving_accurate(self, taxable_base: int, investment: int) -> int:
        """
        คำนวณ Tax Saving อย่างถูกต้องด้วย Multi-Bracket Calculation

        สูตรที่ถูกต้อง:
        Tax Saving = ภาษีก่อนลงทุน - ภาษีหลังลงทุน

        ไม่ใช่สูตรที่ผิด: investment × marginal_rate (ผิดเพราะไม่คำนึงถึงการข้าม bracket)

        Args:
            taxable_base: รายได้สุทธิที่ต้องเสียภาษี (ก่อนหักค่าลงทุน)
            investment: จำนวนเงินลงทุนที่จะหักลดหย่อน

        Returns:
            int: จำนวนภาษีที่ลดได้ (Tax Saving)

        Example:
            >>> calculate_tax_saving_accurate(316000, 60000)
            3800  # ไม่ใช่ 6000 (60k × 10%)
        """
        # คำนวณจำนวนเงินที่สามารถหักลดหย่อนได้จริง
        # (ไม่เกิน taxable_base เพราะไม่สามารถหักจนติดลบได้)
        actual_deduction = min(investment, taxable_base)

        # คำนวณภาษีก่อนลงทุน
        tax_before = self._calculate_progressive_tax(taxable_base)

        # คำนวณภาษีหลังลงทุน (taxable_base ลดลง)
        tax_after = self._calculate_progressive_tax(taxable_base - actual_deduction)

        # Tax Saving = ภาษีที่ลดลงได้
        tax_saving = tax_before - tax_after

        return tax_saving


# Export singleton
tax_calculator_service = TaxCalculatorService()