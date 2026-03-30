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
            if profession in [ProfessionType.MEDICAL, ProfessionType.FINE_ARTS]:
                return int(gross_income * 0.60)  # การประกอบโรคศิลปะ และ ประณีตศิลปกรรม 60%
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
        """Auto-cap ค่าลดหย่อนที่เกินขีดจำกัดตามกฎหมาย (ไม่ throw error — cap แล้วคำนวณต่อ)

        ตาม tax_deductions_update280168.pdf:
        - ประกันบำนาญ: สูงสุด 15% หรือ 200,000 (item 13)
        - RMF: สูงสุด 30% หรือ 500,000 (item 12)
        - ThaiESG: สูงสุด 30% หรือ 300,000 (item 21)

        หมายเหตุ: PVD/กบข./กบศ. ลบออกแล้ว เพราะใช้ได้เฉพาะ 40(1) เงินเดือน
        โปรเจกต์นี้เน้น 40(6) และ 40(8) เท่านั้น
        """
        gross_income = request.gross_income

        # ประกันชีวิตแบบบำนาญ: สูงสุด 15% ของรายได้
        # cap สูงสุด = 200,000 + ส่วนที่เหลือจากประกันชีวิตทั่วไป (สูงสุดรวม 300,000)
        life_insurance_used = min(request.life_insurance, 100000)
        max_pension = min(int(gross_income * 0.15), 200000 + (100000 - life_insurance_used))
        if request.pension_insurance > max_pension:
            print(f"⚠️ Auto-cap pension_insurance: {request.pension_insurance:,} → {max_pension:,} บาท")
            request.pension_insurance = max_pension

        # RMF: สูงสุด 30% หรือ 500,000
        max_rmf = min(int(gross_income * 0.30), 500000)
        if request.rmf > max_rmf:
            print(f"⚠️ Auto-cap RMF: {request.rmf:,} → {max_rmf:,} บาท")
            request.rmf = max_rmf

        # ThaiESG: สูงสุด 30% หรือ 300,000
        max_thai_esg = min(int(gross_income * 0.30), 300000)
        if request.thai_esg > max_thai_esg:
            print(f"⚠️ Auto-cap ThaiESG: {request.thai_esg:,} → {max_thai_esg:,} บาท")
            request.thai_esg = max_thai_esg

        # ThaiESGX (เงินใหม่): สูงสุด 30% หรือ 300,000 (วงเงินแยกจาก ThaiESG)
        if request.thai_esgx_new > max_thai_esg:
            print(f"⚠️ Auto-cap ThaiESGX (เงินใหม่): {request.thai_esgx_new:,} → {max_thai_esg:,} บาท")
            request.thai_esgx_new = max_thai_esg

        # ThaiESGX (สับเปลี่ยนจาก LTF): สูงสุด 30% หรือ 300,000 สำหรับปี 2568
        if request.thai_esgx_ltf > max_thai_esg:
            print(f"⚠️ Auto-cap ThaiESGX (จาก LTF): {request.thai_esgx_ltf:,} → {max_thai_esg:,} บาท")
            request.thai_esgx_ltf = max_thai_esg

        # กอช.: สูงสุด 30,000
        if request.nsf > 30000:
            print(f"⚠️ Auto-cap กอช.: {request.nsf:,} → 30,000 บาท")
            request.nsf = 30000

        # ประกันสังคม: cap ตามมาตรา
        ss_cap_map = {'33': 9000, '39': 5184, '40': 3600, 'none': 0}
        ss_cap = ss_cap_map.get(request.social_security_type, 9000)
        if request.social_security > ss_cap:
            print(f"⚠️ Auto-cap ประกันสังคม: {request.social_security:,} → {ss_cap:,} บาท")
            request.social_security = ss_cap

        # Combined cap เกษียณ: RMF + กอช. + ประกันบำนาญ ≤ 500,000
        total_retirement = request.rmf + request.nsf + request.pension_insurance
        if total_retirement > 500000:
            print(f"⚠️ Auto-cap retirement combined: {total_retirement:,} → scale down to 500,000 บาท")
            scale = 500000 / total_retirement
            request.rmf            = int(request.rmf            * scale)
            request.nsf            = int(request.nsf            * scale)
            request.pension_insurance = int(request.pension_insurance * scale)

        # หมายเหตุ: PVD/กบข./กบศ. ลบออกแล้ว (ใช้ได้เฉพาะ 40(1) เงินเดือน)

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

        # รวมค่าลดหย่อนยกเว้นบริจาค (ใช้คำนวณ cap 10%)
        non_donation_allowances = (
            # กลุ่มส่วนตัว/ครอบครัว
            request.personal_deduction +
            request.spouse_deduction +
            request.child_deduction +
            request.parent_support +
            request.disabled_support +

            # กลุ่มประกันชีวิตและสุขภาพ
            min(request.life_insurance + request.health_insurance, 100000) +
            request.health_insurance_parents_own +
            request.health_insurance_parents_spouse +
            request.social_security +

            # กลุ่มกองทุนและการลงทุน (สำหรับ 40(6) และ 40(8))
            request.pension_insurance +
            request.rmf +

            # กลุ่มกองทุน ESG (ใหม่ปี 2568)
            request.thai_esg +
            request.thai_esgx_new +
            request.thai_esgx_ltf +

            # กลุ่มอื่นๆ (ใหม่ปี 2568)
            request.social_enterprise_investment +
            request.easy_e_receipt +
            request.home_loan_interest +
            request.new_house_construction +
            request.nsf +
            request.maternity_expense
        )

        # cap บริจาค = 10% ของเงินได้หลังหักค่าใช้จ่ายและค่าลดหย่อนอื่น
        income_after_non_donation = max(0, gross_income - expense_deduction - non_donation_allowances)
        max_donation = int(income_after_non_donation * 0.10)

        actual_donation_general = min(request.donation_general, max_donation)
        actual_donation_education_2x = min(request.donation_education * 2, max_donation)

        # รวมค่าลดหย่อนทั้งหมด
        total_allowances = (
            non_donation_allowances +
            actual_donation_general +
            actual_donation_education_2x +
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

    # ─────────────────────────────────────────────────────────
    # Smart Redistribution: cap เงินเกิน cap แล้วเติมตาม priority
    # ─────────────────────────────────────────────────────────
    def redistribute_plan_allocations(
        self,
        allocations: list,
        total_investment: int,
        gross_income: int,
        request: "TaxCalculationRequest",
    ) -> list:
        """
        1. Cap แต่ละ allocation ตาม legal limit (รวม combined caps)
        2. เก็บ excess ที่เกิน cap
        3. Redistribute excess ไปยัง category ที่ยังมีช่องว่าง ตาม priority:
           health → life → pension → rmf → esg → esgx_new → esgx_ltf
        """
        import copy
        allocs = copy.deepcopy(allocations)

        # ── existing deductions (user already has) ──
        ex_life     = request.life_insurance
        ex_health   = request.health_insurance
        ex_pension  = request.pension_insurance
        ex_rmf      = request.rmf
        ex_esg      = request.thai_esg
        ex_esgx_new = request.thai_esgx_new
        ex_esgx_ltf = request.thai_esgx_ltf

        max_pension = min(200000, int(gross_income * 0.15))
        max_rmf     = min(500000, int(gross_income * 0.30))
        max_esg     = min(300000, int(gross_income * 0.30))

        # ── detect category from AI's category string ──
        def detect(cat: str) -> str:
            c = cat.lower()
            if "rmf" in c:                          return "rmf"
            if "esgx" in c and "ltf" in c:          return "esgx_ltf"
            if "esgx" in c:                         return "esgx_new"
            if "esg" in c:                          return "esg"
            if "บำนาญ" in c:                        return "pension"
            if "สุขภาพ" in c:                       return "health"
            if "ชีวิต" in c:                        return "life"
            return "other"

        # ── annotate + sort by priority (health first เพราะ cap เล็ก) ──
        PRIORITY = ["health", "life", "pension", "rmf", "esg", "esgx_new", "esgx_ltf"]
        pri = {c: i for i, c in enumerate(PRIORITY)}
        for a in allocs:
            a["_cat"]    = detect(a.get("category", ""))
            a["_raw"]    = int((a.get("percentage", 0) / 100) * total_investment)
            a["_capped"] = 0
        allocs_sorted = sorted(allocs, key=lambda a: pri.get(a["_cat"], 99))

        # ── helper: remaining space accounting for combined caps ──
        plan = {c: 0 for c in PRIORITY}  # in-plan usage after capping

        def avail(cat: str) -> int:
            if cat == "health":
                return max(0, min(
                    25000 - ex_health,
                    100000 - ex_life - ex_health - plan["life"] - plan["health"]
                ))
            if cat == "life":
                return max(0, 100000 - ex_life - ex_health - plan["life"] - plan["health"])
            if cat == "pension":
                return max(0, min(
                    max_pension - ex_pension,
                    500000 - ex_pension - ex_rmf - plan["pension"] - plan["rmf"]
                ))
            if cat == "rmf":
                return max(0, min(
                    max_rmf - ex_rmf,
                    500000 - ex_pension - ex_rmf - plan["pension"] - plan["rmf"]
                ))
            if cat == "esg":      return max(0, max_esg - ex_esg      - plan["esg"])
            if cat == "esgx_new": return max(0, max_esg - ex_esgx_new - plan["esgx_new"])
            if cat == "esgx_ltf": return max(0, max_esg - ex_esgx_ltf - plan["esgx_ltf"])
            return 0

        # ── Pass 1: cap, collect excess ──
        excess = 0
        for a in allocs_sorted:
            cat = a["_cat"]
            raw = a["_raw"]
            cap = avail(cat) if cat in PRIORITY else raw
            capped = min(raw, cap)
            excess += raw - capped
            a["_capped"] = capped
            if cat in plan:
                plan[cat] += capped

        # ── Pass 2: redistribute excess by priority ──
        LABELS = {
            "health":   "ประกันสุขภาพ",
            "life":     "ประกันชีวิต",
            "pension":  "ประกันบำนาญ",
            "rmf":      "RMF",
            "esg":      "ThaiESG",
            "esgx_new": "ThaiESGX (เงินใหม่)",
            "esgx_ltf": "ThaiESGX (จาก LTF)",
        }
        # map category → first alloc with that category
        cat_alloc: dict = {}
        for a in allocs:
            if a["_cat"] not in cat_alloc and a["_cat"] != "other":
                cat_alloc[a["_cat"]] = a

        remaining = excess
        for cat in PRIORITY:
            if remaining <= 0:
                break
            space = avail(cat)
            if space <= 0:
                continue
            add = min(remaining, space)
            remaining -= add
            plan[cat] += add

            if cat in cat_alloc:
                cat_alloc[cat]["_capped"] += add
            else:
                # เพิ่ม allocation ใหม่สำหรับ category ที่ AI ไม่ได้แนะนำ
                new_a = {
                    "category":          LABELS[cat],
                    "percentage":        0,
                    "investment_amount": 0,
                    "tax_saving":        0,
                    "risk_level":        "low" if cat in ("life", "health") else "medium",
                    "pros":              [],
                    "cons":              [],
                    "_cat":              cat,
                    "_raw":              0,
                    "_capped":           add,
                }
                allocs.append(new_a)
                cat_alloc[cat] = new_a

        # ── Final: update fields, drop helper keys ──
        result = []
        for a in allocs:
            capped = a.pop("_capped", 0)
            a.pop("_cat", None)
            a.pop("_raw", None)
            if capped > 0:
                a["investment_amount"] = capped
                a["percentage"] = round((capped / total_investment * 100), 1) if total_investment > 0 else 0
                result.append(a)

        return result


# Export singleton
tax_calculator_service = TaxCalculatorService()