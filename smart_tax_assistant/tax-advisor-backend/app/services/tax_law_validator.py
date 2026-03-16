"""
Tax Law Validator & Plan Corrector
ตรวจสอบและแก้ไขแผนภาษีให้ถูกต้องตามกฎหมายภาษีไทย ปี 2568

Architecture: Validate → Correct → Verify
- TaxLawValidator: ตรวจสอบว่าแผนถูกกฎหมายหรือไม่
- PlanCorrector: แก้ไขแผนที่ผิดกฎหมายโดยอัตโนมัติ

กฎหมายที่ครอบคลุม:
- ประกันชีวิต + สุขภาพ รวมกัน ≤ 100,000 บาท
- ประกันบำนาญ: min(15% รายได้, 200,000) + spillover จากโควตาประกันชีวิตทั่วไป
- กลุ่มเกษียณ (RMF + ประกันบำนาญ + PVD + กบข. + กอช. + กองทุนครูฯ) ≤ 500,000 บาท
- SSF ยกเลิกแล้ว (สิ้นปี 2567) — ห้ามนำมารวม
"""

from typing import Dict, List, Any, Optional, Tuple
from app.services.tax_calculator import tax_calculator_service


# =============================================================================
# Category Matching Utility
# =============================================================================

def classify_category(category_name: str) -> Optional[str]:
    """จับคู่ชื่อ category กับ legal limit key

    Returns: key เช่น 'rmf', 'life_insurance', etc. หรือ None ถ้าไม่มี limit
    """
    cat_lower = category_name.lower()

    if "ประกันบำนาญ" in category_name or "บำนาญ" in cat_lower:
        return "pension_insurance"
    if "ประกันสุขภาพ" in category_name or (
        "สุขภาพ" in category_name and "ประกันชีวิต" not in category_name
    ):
        return "health_insurance"
    if "ประกันชีวิต" in category_name and "สุขภาพ" not in category_name and "บำนาญ" not in category_name:
        return "life_insurance"
    if "rmf" in cat_lower:
        return "rmf"
    if "thaiesgx" in cat_lower or "esgx" in cat_lower:
        return "thai_esgx"
    if "thaiesg" in cat_lower or "esg" in cat_lower:
        return "thai_esg"

    return None


# =============================================================================
# TaxLawValidator
# =============================================================================

class TaxLawValidator:
    """ตรวจสอบแผนการลงทุนตามกฎหมายภาษีไทย 2568 (Holistic View)

    Individual Limits:
    - RMF: min(30% of assessable_income, 500,000)
    - ThaiESG: min(30% of assessable_income, 300,000)
    - ThaiESGX: min(30% of assessable_income, 300,000)
    - Pension Insurance: min(15% of assessable_income, 200,000)
      + Spillover: ถ้าโควตาประกันชีวิตทั่วไปยังเหลือ สามารถนำบำนาญไปเติมได้
    - Life Insurance: 100,000
    - Health Insurance: 25,000

    Combined Limits:
    - Combined Insurance (life + health): ≤ 100,000
    - Retirement Group (RMF + pension + PVD + กบข. + กอช. + กองทุนครูฯ): ≤ 500,000
      (SSF ยกเลิกแล้ว ไม่รวม)
    """

    RETIREMENT_CAP = 500_000

    def __init__(
        self,
        gross_income: int,
        existing_life_insurance: int = 0,
        existing_health_insurance: int = 0,
        existing_rmf: int = 0,
        existing_pvd: int = 0,
        existing_gpf: int = 0,       # กบข.
        existing_nsf: int = 0,       # กอช.
        existing_teacher_fund: int = 0,  # กองทุนสงเคราะห์ครูฯ
    ):
        self.gross_income = gross_income

        # Existing deductions (from profile / other income sources)
        self.existing_life_insurance = existing_life_insurance
        self.existing_health_insurance = existing_health_insurance
        self.existing_rmf = existing_rmf
        self.existing_pvd = existing_pvd
        self.existing_gpf = existing_gpf
        self.existing_nsf = existing_nsf
        self.existing_teacher_fund = existing_teacher_fund

        self.limits = self._compute_limits()

    def _compute_limits(self) -> Dict[str, int]:
        g = self.gross_income

        # --- Individual limits ---
        rmf_limit = min(int(g * 0.30), 500_000)
        thai_esg_limit = min(int(g * 0.30), 300_000)
        thai_esgx_limit = min(int(g * 0.30), 300_000)
        pension_base_limit = min(int(g * 0.15), 200_000)
        life_insurance_limit = 100_000
        health_insurance_limit = 25_000
        combined_insurance_limit = 100_000  # life + health ≤ 100K

        # --- Remaining limits (after existing deductions) ---
        remaining_rmf = max(0, rmf_limit - self.existing_rmf)
        remaining_life = max(0, life_insurance_limit - self.existing_life_insurance)
        remaining_health = max(0, health_insurance_limit - self.existing_health_insurance)

        # Combined insurance remaining
        existing_combined = self.existing_life_insurance + self.existing_health_insurance
        remaining_combined = max(0, combined_insurance_limit - existing_combined)
        # Cap remaining life/health to not exceed combined remaining
        remaining_life = min(remaining_life, remaining_combined)
        remaining_health = min(remaining_health, max(0, remaining_combined - remaining_life))

        # --- Pension Insurance with Spillover ---
        # ถ้าโควตาประกันชีวิตทั่วไปยังเหลือ สามารถนำเบี้ยบำนาญไปเติมได้
        remaining_life_quota = max(0, life_insurance_limit - self.existing_life_insurance)
        # Spillover: เบี้ยบำนาญที่ไปอยู่ในโควตาประกันชีวิตทั่วไป (ยังไม่ใช้ตอน validate)
        # เก็บไว้เป็นข้อมูลเพิ่มเติม
        self.pension_life_spillover_available = remaining_life_quota

        # --- Retirement Group Cap ---
        # Used retirement quota from existing sources (not from new plan)
        used_retirement = (
            self.existing_rmf
            + self.existing_pvd
            + self.existing_gpf
            + self.existing_nsf
            + self.existing_teacher_fund
        )
        remaining_retirement_cap = max(0, self.RETIREMENT_CAP - used_retirement)

        # Pension limit is further constrained by retirement group cap
        # (RMF from new plan also eats into retirement cap, but we handle that in validate)
        remaining_pension = min(pension_base_limit, remaining_retirement_cap)

        return {
            "rmf": remaining_rmf,
            "thai_esg": thai_esg_limit,
            "thai_esgx": thai_esgx_limit,
            "pension_insurance": remaining_pension,
            "life_insurance": remaining_life,
            "health_insurance": remaining_health,
            "combined_insurance": remaining_combined,
            # Store base limits for reference
            "_rmf_base": rmf_limit,
            "_pension_base": pension_base_limit,
            "_retirement_cap": self.RETIREMENT_CAP,
            "_used_retirement": used_retirement,
            "_remaining_retirement_cap": remaining_retirement_cap,
        }

    def get_max_legal_total(self) -> int:
        """คำนวณยอดลงทุนสูงสุดที่ถูกกฎหมาย

        ต้องพิจารณา:
        1. Individual limits ของแต่ละ category
        2. Combined insurance limit (life + health ≤ 100K)
        3. Retirement group cap (RMF + pension ≤ remaining_retirement_cap)
        """
        lim = self.limits
        remaining_ret = lim["_remaining_retirement_cap"]

        # RMF + Pension ต้องไม่เกิน remaining_retirement_cap
        rmf_for_calc = min(lim["rmf"], remaining_ret)
        pension_for_calc = min(lim["pension_insurance"], max(0, remaining_ret - rmf_for_calc))

        return (
            rmf_for_calc
            + lim["thai_esg"]
            + lim["thai_esgx"]
            + pension_for_calc
            + lim["combined_insurance"]  # life + health รวมกัน ≤ 100k
        )

    def get_limit_for(self, category_key: str) -> Optional[int]:
        """ดึง limit ของ category"""
        return self.limits.get(category_key)

    def validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """ตรวจสอบแผนเดียว

        ตรวจ 3 ระดับ:
        1. Individual limits (แต่ละ category)
        2. Combined insurance (life + health ≤ 100,000)
        3. Retirement group cap (RMF + pension ≤ remaining retirement cap)

        Returns:
            {
                "is_legal": bool,
                "violations": [...],
                "category_totals": {...},
                "limits": {...}
            }
        """
        violations = []
        allocations = plan.get("allocations", [])
        total_investment = plan.get("total_investment", 0)

        # รวมยอดตาม category
        category_totals: Dict[str, int] = {}
        for alloc in allocations:
            cat_name = alloc.get("category", "")
            cat_key = classify_category(cat_name)
            if cat_key is None:
                continue

            amount = alloc.get("investment_amount")
            if amount is None and total_investment > 0:
                pct = alloc.get("percentage", 0)
                amount = int(total_investment * pct / 100)

            if amount is None or amount <= 0:
                continue

            category_totals[cat_key] = category_totals.get(cat_key, 0) + amount

        # --- Check 1: Individual limits ---
        for cat_key, total_amount in category_totals.items():
            limit = self.limits.get(cat_key)
            if limit is not None and not cat_key.startswith("_") and total_amount > limit:
                violations.append({
                    "type": "individual",
                    "category_key": cat_key,
                    "amount": total_amount,
                    "limit": limit,
                    "excess": total_amount - limit,
                })

        # --- Check 2: Combined insurance (life + health ≤ 100,000) ---
        combined_ins = (
            category_totals.get("life_insurance", 0)
            + category_totals.get("health_insurance", 0)
        )
        if combined_ins > self.limits["combined_insurance"]:
            violations.append({
                "type": "combined_insurance",
                "category_key": "combined_insurance",
                "amount": combined_ins,
                "limit": self.limits["combined_insurance"],
                "excess": combined_ins - self.limits["combined_insurance"],
            })

        # --- Check 3: Retirement group cap ---
        # New plan's RMF + pension must fit within remaining retirement cap
        new_rmf = category_totals.get("rmf", 0)
        new_pension = category_totals.get("pension_insurance", 0)
        new_retirement_total = new_rmf + new_pension
        remaining_ret = self.limits["_remaining_retirement_cap"]

        if new_retirement_total > remaining_ret:
            violations.append({
                "type": "retirement_group_cap",
                "category_key": "retirement_group",
                "amount": self.limits["_used_retirement"] + new_retirement_total,
                "limit": self.RETIREMENT_CAP,
                "excess": new_retirement_total - remaining_ret,
                "detail": f"New RMF({new_rmf:,}) + Pension({new_pension:,}) = {new_retirement_total:,} > remaining cap {remaining_ret:,}",
            })

        return {
            "is_legal": len(violations) == 0,
            "violations": violations,
            "category_totals": category_totals,
            "limits": self.limits,
        }


# =============================================================================
# PlanCorrector
# =============================================================================

class PlanCorrector:
    """แก้ไขแผนที่ผิดกฎหมายโดยอัตโนมัติ

    Strategy:
    1. Cap แต่ละ allocation ตาม individual legal limit
    2. Enforce combined insurance limit (ลด life ก่อน เพราะ health สำคัญกว่า)
    3. Enforce retirement group cap (ลด pension ก่อน RMF เพราะ RMF limit สูงกว่า)
    4. Redistribute: ถ้า total หลัง cap < target, พยายามกระจายส่วนเกินไป category ที่ยังมี headroom
    5. ถ้า target > max legal total, ลด total ลงเป็น max legal
    6. Recalculate tax saving ด้วย bracket-by-bracket (calculate_tax_saving_accurate)
    """

    def __init__(self, validator: TaxLawValidator, taxable_income: int):
        self.validator = validator
        self.taxable_income = taxable_income

    def correct_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """แก้ไขแผนให้ถูกกฎหมาย + คำนวณ tax saving ที่ถูกต้อง

        Returns: corrected plan (mutated in-place + returned)
        """
        allocations = plan.get("allocations", [])
        target_total = plan.get("total_investment", 0)
        max_legal = self.validator.get_max_legal_total()

        # Step 1: Cap target ถ้าเกิน max legal
        if target_total > max_legal:
            target_total = max_legal
            plan["total_investment"] = target_total

        # Step 2: คำนวณ investment_amount จาก percentage แล้ว cap ตาม legal limit
        for alloc in allocations:
            pct = alloc.get("percentage", 0)
            raw_amount = int((pct / 100) * target_total)

            cat_key = classify_category(alloc.get("category", ""))
            if cat_key is not None:
                limit = self.validator.get_limit_for(cat_key)
                if limit is not None:
                    raw_amount = min(raw_amount, limit)

            alloc["investment_amount"] = raw_amount

        # Step 3: Enforce combined insurance limit
        self._enforce_combined_insurance(allocations)

        # Step 4: Enforce retirement group cap
        self._enforce_retirement_cap(allocations)

        # Step 5: Redistribute — try to fill up to target_total
        capped_total = sum(a.get("investment_amount", 0) for a in allocations)
        if capped_total < target_total:
            self._redistribute_excess(allocations, target_total - capped_total)

        # Step 6: Recalculate final totals
        final_total = sum(a.get("investment_amount", 0) for a in allocations)
        plan["total_investment"] = final_total

        # Step 7: Recalculate tax saving with bracket-by-bracket
        plan["total_tax_saving"] = tax_calculator_service.calculate_tax_saving_accurate(
            self.taxable_income, final_total
        )

        # Step 8: Recalculate per-allocation tax saving proportionally
        for alloc in allocations:
            amt = alloc.get("investment_amount", 0)
            if final_total > 0:
                proportion = amt / final_total
            else:
                proportion = 0
            alloc["tax_saving"] = int(proportion * plan["total_tax_saving"])

        # Step 9: Update percentages to match actual amounts
        for alloc in allocations:
            amt = alloc.get("investment_amount", 0)
            if final_total > 0:
                alloc["percentage"] = round((amt / final_total) * 100, 1)
            else:
                alloc["percentage"] = 0

        return plan

    def _enforce_combined_insurance(self, allocations: List[Dict[str, Any]]):
        """Enforce life + health ≤ combined_insurance limit (ลด life ก่อน health)"""
        combined_limit = self.validator.limits["combined_insurance"]
        life_allocs = []
        health_allocs = []

        for alloc in allocations:
            cat_key = classify_category(alloc.get("category", ""))
            if cat_key == "life_insurance":
                life_allocs.append(alloc)
            elif cat_key == "health_insurance":
                health_allocs.append(alloc)

        total_life = sum(a.get("investment_amount", 0) for a in life_allocs)
        total_health = sum(a.get("investment_amount", 0) for a in health_allocs)
        combined = total_life + total_health

        if combined <= combined_limit:
            return

        excess = combined - combined_limit
        # ลด life insurance ก่อน (health สำคัญกว่า)
        for alloc in life_allocs:
            if excess <= 0:
                break
            current = alloc.get("investment_amount", 0)
            reduction = min(current, excess)
            alloc["investment_amount"] = current - reduction
            excess -= reduction

        # ถ้ายังเกินอยู่ ลด health
        for alloc in health_allocs:
            if excess <= 0:
                break
            current = alloc.get("investment_amount", 0)
            reduction = min(current, excess)
            alloc["investment_amount"] = current - reduction
            excess -= reduction

    def _enforce_retirement_cap(self, allocations: List[Dict[str, Any]]):
        """Enforce retirement group cap: new RMF + new pension ≤ remaining retirement cap
        ลด pension ก่อน RMF (เพราะ RMF มี limit สูงกว่าและสำคัญกว่า)
        """
        remaining_ret = self.validator.limits["_remaining_retirement_cap"]

        rmf_allocs = []
        pension_allocs = []
        for alloc in allocations:
            cat_key = classify_category(alloc.get("category", ""))
            if cat_key == "rmf":
                rmf_allocs.append(alloc)
            elif cat_key == "pension_insurance":
                pension_allocs.append(alloc)

        total_rmf = sum(a.get("investment_amount", 0) for a in rmf_allocs)
        total_pension = sum(a.get("investment_amount", 0) for a in pension_allocs)
        combined = total_rmf + total_pension

        if combined <= remaining_ret:
            return

        excess = combined - remaining_ret
        # ลด pension ก่อน (RMF สำคัญกว่า)
        for alloc in pension_allocs:
            if excess <= 0:
                break
            current = alloc.get("investment_amount", 0)
            reduction = min(current, excess)
            alloc["investment_amount"] = current - reduction
            excess -= reduction

        # ถ้ายังเกินอยู่ ลด RMF
        for alloc in rmf_allocs:
            if excess <= 0:
                break
            current = alloc.get("investment_amount", 0)
            reduction = min(current, excess)
            alloc["investment_amount"] = current - reduction
            excess -= reduction

    def _redistribute_excess(self, allocations: List[Dict[str, Any]], shortfall: int):
        """กระจาย shortfall ไปที่ category ที่ยังมี headroom

        ลำดับความสำคัญ: RMF > ThaiESG > ThaiESGX > Pension > Life > Health
        ต้องเช็ค retirement group cap สำหรับ RMF และ Pension ด้วย
        """
        priority_order = [
            "rmf", "thai_esg", "thai_esgx",
            "pension_insurance", "life_insurance", "health_insurance"
        ]

        # สร้าง map ของ current totals per category
        cat_totals: Dict[str, int] = {}
        cat_allocs: Dict[str, List[Dict[str, Any]]] = {}
        for alloc in allocations:
            cat_key = classify_category(alloc.get("category", ""))
            if cat_key is None:
                continue
            cat_totals[cat_key] = cat_totals.get(cat_key, 0) + alloc.get("investment_amount", 0)
            cat_allocs.setdefault(cat_key, []).append(alloc)

        # Track retirement group usage for redistribution
        current_retirement_used = cat_totals.get("rmf", 0) + cat_totals.get("pension_insurance", 0)
        remaining_ret = self.validator.limits["_remaining_retirement_cap"]

        remaining = shortfall
        for cat_key in priority_order:
            if remaining <= 0:
                break

            limit = self.validator.get_limit_for(cat_key)
            if limit is None:
                continue

            current = cat_totals.get(cat_key, 0)
            headroom = limit - current
            if headroom <= 0:
                continue

            # สำหรับ RMF และ Pension ต้องเช็ค retirement cap ด้วย
            if cat_key in ("rmf", "pension_insurance"):
                retirement_headroom = max(0, remaining_ret - current_retirement_used)
                headroom = min(headroom, retirement_headroom)
                if headroom <= 0:
                    continue

            add_amount = min(remaining, headroom)

            # เพิ่มไปที่ allocation แรกของ category นี้
            if cat_key in cat_allocs and cat_allocs[cat_key]:
                cat_allocs[cat_key][0]["investment_amount"] += add_amount
            else:
                # ไม่มี allocation ของ category นี้ — เพิ่มใหม่
                allocations.append({
                    "category": self._key_to_thai_name(cat_key),
                    "investment_amount": add_amount,
                    "percentage": 0,  # จะคำนวณใหม่ใน correct_plan
                    "risk_level": "medium",
                    "pros": [],
                    "cons": [],
                })

            remaining -= add_amount
            cat_totals[cat_key] = current + add_amount

            # อัปเดต retirement usage
            if cat_key in ("rmf", "pension_insurance"):
                current_retirement_used += add_amount

    @staticmethod
    def _key_to_thai_name(cat_key: str) -> str:
        """แปลง category key กลับเป็นชื่อไทย"""
        mapping = {
            "rmf": "RMF",
            "thai_esg": "ThaiESG",
            "thai_esgx": "ThaiESGX",
            "pension_insurance": "ประกันบำนาญ",
            "life_insurance": "ประกันชีวิต",
            "health_insurance": "ประกันสุขภาพ",
        }
        return mapping.get(cat_key, cat_key)


# =============================================================================
# High-level convenience function
# =============================================================================

def validate_and_correct_plans(
    plans: List[Dict[str, Any]],
    gross_income: int,
    taxable_income: int,
    existing_life_insurance: int = 0,
    existing_health_insurance: int = 0,
    existing_rmf: int = 0,
    existing_pvd: int = 0,
    existing_gpf: int = 0,
    existing_nsf: int = 0,
    existing_teacher_fund: int = 0,
) -> Dict[str, Any]:
    """Validate → Correct → Verify loop สำหรับทุก plan

    Args:
        plans: แผนการลงทุนจาก AI
        gross_income: รายได้รวม (เงินได้พึงประเมิน)
        taxable_income: เงินได้สุทธิ
        existing_*: ยอดลดหย่อนที่มีอยู่แล้ว (จาก profile หรือรายได้อื่น)

    Returns:
        {
            "plans": [...],            # corrected plans
            "all_legal": bool,
            "corrections_made": int,    # จำนวน plan ที่ต้องแก้ไข
            "details": [...]            # per-plan validation details
        }
    """
    validator = TaxLawValidator(
        gross_income=gross_income,
        existing_life_insurance=existing_life_insurance,
        existing_health_insurance=existing_health_insurance,
        existing_rmf=existing_rmf,
        existing_pvd=existing_pvd,
        existing_gpf=existing_gpf,
        existing_nsf=existing_nsf,
        existing_teacher_fund=existing_teacher_fund,
    )
    corrector = PlanCorrector(validator, taxable_income)

    corrections_made = 0
    details = []

    for plan in plans:
        # Step 1: Validate
        result = validator.validate_plan(plan)

        if not result["is_legal"]:
            # Step 2: Correct (cap + redistribute + recalc)
            corrector.correct_plan(plan)
            corrections_made += 1

            # Step 3: Verify
            result = validator.validate_plan(plan)
        else:
            # Plan is legal but still recalculate tax_saving with accurate formula
            # (AI may have used wrong formula like marginal_rate × investment)
            total_inv = plan.get("total_investment", 0)
            plan["total_tax_saving"] = tax_calculator_service.calculate_tax_saving_accurate(
                taxable_income, total_inv
            )
            # Recalculate per-allocation tax saving proportionally
            for alloc in plan.get("allocations", []):
                amt = alloc.get("investment_amount", 0)
                if total_inv > 0:
                    alloc["tax_saving"] = int((amt / total_inv) * plan["total_tax_saving"])

        details.append(result)

    all_legal = all(d["is_legal"] for d in details)

    return {
        "plans": plans,
        "all_legal": all_legal,
        "corrections_made": corrections_made,
        "max_legal_total": validator.get_max_legal_total(),
        "details": details,
    }
