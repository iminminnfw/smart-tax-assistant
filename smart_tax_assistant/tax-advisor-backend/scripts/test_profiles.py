"""
20 Test Profiles สำหรับ Evaluation
ครอบคลุมทุกกลุ่มเป้าหมาย: อายุ, รายได้, อาชีพ, สถานะสมรส, ความเสี่ยง

Profile Design Rationale:
- 4 ระดับรายได้: ต่ำ (<500K), กลาง (500K-1M), สูง (1M-3M), สูงมาก (>3M)
- 3 ช่วงอายุ: หนุ่มสาว (22-30), วัยทำงาน (31-45), ใกล้เกษียณ (46-60)
- 3 ระดับความเสี่ยง: conservative, moderate, aggressive
- สถานะหลากหลาย: โสด, แต่งงาน, มีบุตร, ดูแลพ่อแม่
"""

from typing import List, Dict, Any

# =============================================================================
# 20 TEST PROFILES FOR M40(6) AND M40(8)
# =============================================================================

TEST_PROFILES: List[Dict[str, Any]] = [
    # =========================================================================
    # Group A: M40(6) - วิชาชีพอิสระ (10 Profiles)
    # =========================================================================
    {
        "id": "A1",
        "label": "แพทย์เปิดคลินิก โสด หักเหมา",
        "profile": {
            "income_type": "40(6)",
            "occupation": "doctor_clinic", # ประกอบโรคศิลปะ
            "age": 32,
            "annual_income": 1500000,
            "expense_deduction_type": "standard", # หักเหมา 60%
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 500000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "ต้องการประหยัดภาษีสูงสุด",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "A2",
        "label": "ทนายความ แต่งงาน มีลูก 1 หักเหมา",
        "profile": {
            "income_type": "40(6)",
            "occupation": "lawyer", # กฎหมาย
            "age": 38,
            "annual_income": 1200000,
            "expense_deduction_type": "standard", # หักเหมา 30%
            "is_vat_registered": False,
            "marital_status": "married",
            "dependents": 1,
            "num_children": 1,
            "num_parents": 0,
            "existing_savings": 800000,
            "risk_tolerance": "moderate",
            "existing_rmf": 50000,
            "existing_thai_esg": 0,
            "life_insurance_amount": 30000,
            "health_insurance_amount": 10000,
        },
        "goal": "สมดุลภาษี และเก็บเงินสดไว้เลี้ยงลูก",
        "expected_goal_type": "HYBRID",
    },
    {
        "id": "A3",
        "label": "วิศวกรที่ปรึกษา ดูแลพ่อแม่ 2 คน หักตามจริง",
        "profile": {
            "income_type": "40(6)",
            "occupation": "engineer", # วิศวกรรม
            "age": 35,
            "annual_income": 900000,
            "expense_deduction_type": "actual", 
            "actual_expenses": 400000, # ค่าใช้จ่ายตามจริง
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 2,
            "existing_savings": 300000,
            "risk_tolerance": "moderate",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 50000,
            "health_insurance_amount": 0,
        },
        "goal": "ลดภาษีด้วยบิลตามจริง แต่ต้องรักษาสภาพคล่องดูแลพ่อแม่",
        "expected_goal_type": "CASH_FLOW",
    },
    {
        "id": "A4",
        "label": "สถาปนิกฟรีแลนซ์ จบใหม่ หักเหมา",
        "profile": {
            "income_type": "40(6)",
            "occupation": "architect", # สถาปัตยกรรม
            "age": 26,
            "annual_income": 480000,
            "expense_deduction_type": "standard", # หักเหมา 30%
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 100000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "เริ่มต้นวางแผนภาษีครั้งแรก",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "A5",
        "label": "นักบัญชีอิสระ ใกล้เกษียณ หักตามจริง",
        "profile": {
            "income_type": "40(6)",
            "occupation": "accountant", # บัญชี
            "age": 56,
            "annual_income": 1800000,
            "expense_deduction_type": "actual",
            "actual_expenses": 500000,
            "is_vat_registered": False, # ปริ่ม 1.8M สมมติยังไม่เกิน
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 4000000,
            "risk_tolerance": "conservative",
            "existing_rmf": 300000,
            "existing_thai_esg": 0,
            "life_insurance_amount": 100000,
            "health_insurance_amount": 25000,
        },
        "goal": "เกษียณอีก 4 ปี ต้องการลดเสี่ยงและหักภาษีตามจริง",
        "expected_goal_type": "RETIREMENT",
    },
    {
        "id": "A6",
        "label": "แพทย์เฉพาะทาง รายได้สูงมาก จด VAT",
        "profile": {
            "income_type": "40(6)",
            "occupation": "doctor_specialist",
            "age": 45,
            "annual_income": 4000000, # ไม่รวม VAT
            "expense_deduction_type": "actual",
            "actual_expenses": 1500000,
            "is_vat_registered": True, # เกิน 1.8M
            "marital_status": "married",
            "dependents": 1,
            "num_children": 1,
            "num_parents": 0,
            "existing_savings": 8000000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 200000,
            "existing_thai_esg": 100000,
            "life_insurance_amount": 100000,
            "health_insurance_amount": 25000,
        },
        "goal": "วางแผนภาษีขั้นสูง จัดการเรื่อง VAT และเกษียณตอน 55",
        "expected_goal_type": "HYBRID",
    },
    {
        "id": "A7",
        "label": "ทันตแพทย์ แต่งงาน มีลูก 2 จด VAT หักเหมา",
        "profile": {
            "income_type": "40(6)",
            "occupation": "dentist",
            "age": 40,
            "annual_income": 2000000,
            "expense_deduction_type": "standard", # หักเหมา 60%
            "is_vat_registered": True, # เกิน 1.8M
            "marital_status": "married",
            "dependents": 2,
            "num_children": 2,
            "num_parents": 0,
            "existing_savings": 1500000,
            "risk_tolerance": "moderate",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 50000,
            "health_insurance_amount": 20000,
        },
        "goal": "ประหยัดภาษีพร้อมเก็บเงินดาวน์บ้าน 2 ล้าน",
        "expected_goal_type": "LIFE_EVENT",
    },
    {
        "id": "A8",
        "label": "นักกฎหมาย รายได้ปานกลาง อนุรักษ์นิยม",
        "profile": {
            "income_type": "40(6)",
            "occupation": "lawyer",
            "age": 30,
            "annual_income": 700000,
            "expense_deduction_type": "standard",
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 300000,
            "risk_tolerance": "conservative",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 20000,
            "health_insurance_amount": 0,
        },
        "goal": "ไม่อยากลงทุนเสี่ยง แต่อยากได้สิทธิลดหย่อนภาษี",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "A9",
        "label": "วิศวกร ลดหย่อนเกือบเต็มสิทธิแล้ว จด VAT",
        "profile": {
            "income_type": "40(6)",
            "occupation": "engineer",
            "age": 42,
            "annual_income": 2500000,
            "expense_deduction_type": "actual",
            "actual_expenses": 800000,
            "is_vat_registered": True,
            "marital_status": "married",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 2,
            "existing_savings": 3000000,
            "risk_tolerance": "moderate",
            "existing_rmf": 400000,
            "existing_thai_esg": 200000,
            "life_insurance_amount": 100000,
            "health_insurance_amount": 25000,
        },
        "goal": "ลงทุนลดหย่อนไปเยอะแล้ว อยากรู้ว่ายังเหลือสิทธิอะไรอีกบ้าง",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "A10",
        "label": "สัตวแพทย์ เปิดคลินิก เงินสำรองต่ำ",
        "profile": {
            "income_type": "40(6)",
            "occupation": "vet", # จัดเป็นประกอบโรคศิลปะหรือไม่ขึ้นกับการตีความ แต่ให้เป็นตัวแทน 40(6)
            "age": 29,
            "annual_income": 1000000,
            "expense_deduction_type": "standard",
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 50000, # EF ต่ำ
            "risk_tolerance": "aggressive",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "รายได้ดีแต่ไม่เคยวางแผนและเงินเก็บน้อย เริ่มต้นอย่างไรดี",
        "expected_goal_type": "TAX_SAVING",
    },

    # =========================================================================
    # Group B: M40(8) - ธุรกิจ/พาณิชย์ (10 Profiles)
    # =========================================================================
    {
        "id": "B11",
        "label": "เจ้าของร้านค้าออนไลน์ โสด",
        "profile": {
            "income_type": "40(8)",
            "occupation": "online_seller", # ขายของ
            "age": 27,
            "annual_income": 600000,
            "expense_deduction_type": "standard", # เหมา 60%
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 200000,
            "risk_tolerance": "moderate",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "วางแผนภาษีครั้งแรกสำหรับธุรกิจ",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "B12",
        "label": "ผู้รับเหมาก่อสร้าง แต่งงาน มีลูก 2 จด VAT",
        "profile": {
            "income_type": "40(8)",
            "occupation": "contractor", # รับเหมา
            "age": 43,
            "annual_income": 1500000, # ถ้ารวม VAT จะเกิน แต่สมมติยอดนี้จด VAT แล้วเพื่อเทส
            "expense_deduction_type": "actual",
            "actual_expenses": 1000000,
            "is_vat_registered": True, 
            "marital_status": "married",
            "dependents": 2,
            "num_children": 2,
            "num_parents": 0,
            "existing_savings": 600000,
            "risk_tolerance": "moderate",
            "existing_rmf": 100000,
            "existing_thai_esg": 0,
            "life_insurance_amount": 50000,
            "health_insurance_amount": 25000,
        },
        "goal": "สมดุลระหว่างภาษีธุรกิจและภาษีบุคคลธรรมดา",
        "expected_goal_type": "HYBRID",
    },
    {
        "id": "B13",
        "label": "เจ้าของร้านอาหาร รายได้ผันผวน",
        "profile": {
            "income_type": "40(8)",
            "occupation": "restaurant_owner",
            "age": 36,
            "annual_income": 800000,
            "expense_deduction_type": "actual",
            "actual_expenses": 500000,
            "is_vat_registered": False, # สมมติยอดนี้จด VAT เพื่อเทส edge case หรือให้เป็น False ตามเงื่อนไขคุณ
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 150000,
            "risk_tolerance": "conservative",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 20000,
            "health_insurance_amount": 10000,
        },
        "goal": "เงินหมุนเวียนสำคัญกว่า แต่ก็อยากลดภาษี",
        "expected_goal_type": "CASH_FLOW",
    },
    {
        "id": "B14",
        "label": "นายหน้าอสังหาฯ รายได้สูง จด VAT",
        "profile": {
            "income_type": "40(8)", # นายหน้าทั่วไป 40(2) แต่นี่ตีเป็นรูปแบบบริษัท/จัดตั้ง
            "occupation": "real_estate_broker", 
            "age": 38,
            "annual_income": 3000000,
            "expense_deduction_type": "standard", # สมมติเหมาได้ตามเงื่อนไขธุรกิจ
            "is_vat_registered": True,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 2000000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 200000,
            "existing_thai_esg": 100000,
            "life_insurance_amount": 100000,
            "health_insurance_amount": 0,
        },
        "goal": "ต้องการอัดลดหย่อนภาษีให้สูงสุด",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "B15",
        "label": "YouTuber/Content Creator วัยรุ่น",
        "profile": {
            "income_type": "40(8)",
            "occupation": "youtuber",
            "age": 24,
            "annual_income": 420000,
            "expense_deduction_type": "standard", # หักเหมา 60% (ตามการตีความบางกรณี)
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 100000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "รายได้น้อยแต่เติบโตเร็ว เริ่มวางแผนภาษี",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "B16",
        "label": "เจ้าของธุรกิจนำเข้า รายได้สูงมาก จด VAT",
        "profile": {
            "income_type": "40(8)",
            "occupation": "importer",
            "age": 50,
            "annual_income": 5000000,
            "expense_deduction_type": "actual",
            "actual_expenses": 3000000,
            "is_vat_registered": True,
            "marital_status": "married",
            "dependents": 1,
            "num_children": 1,
            "num_parents": 2,
            "existing_savings": 5000000,
            "risk_tolerance": "moderate",
            "existing_rmf": 500000, # เต็มเพดาน
            "existing_thai_esg": 300000, # เต็มเพดาน
            "life_insurance_amount": 100000,
            "health_insurance_amount": 25000,
        },
        "goal": "เตรียมเกษียณและจัดการภาษีธุรกิจที่รายได้สูง",
        "expected_goal_type": "HYBRID",
    },
    {
        "id": "B17",
        "label": "ช่างภาพฟรีแลนซ์ รายได้น้อย",
        "profile": {
            "income_type": "40(8)", # สมมติเปิดหน้าร้าน/สตูดิโอ
            "occupation": "photographer",
            "age": 25,
            "annual_income": 360000,
            "expense_deduction_type": "standard",
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 50000,
            "risk_tolerance": "moderate",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "รายได้แค่นี้จำเป็นต้องหาตัวลดหย่อนไหม",
        "expected_goal_type": "TAX_SAVING",
    },
    {
        "id": "B18",
        "label": "เจ้าของฟาร์ม (เกษตร) ภาระเยอะ",
        "profile": {
            "income_type": "40(8)",
            "occupation": "farmer",
            "age": 48,
            "annual_income": 1200000,
            "expense_deduction_type": "actual",
            "actual_expenses": 700000,
            "is_vat_registered": False, # สินค้าเกษตรมักยกเว้น VAT
            "marital_status": "married",
            "dependents": 2,
            "num_children": 2,
            "num_parents": 4, # ดูแลพ่อแม่ 4 คน
            "existing_savings": 300000,
            "risk_tolerance": "conservative",
            "existing_rmf": 50000,
            "existing_thai_esg": 0,
            "life_insurance_amount": 40000,
            "health_insurance_amount": 0,
        },
        "goal": "ภาระครอบครัวเยอะ เน้นสภาพคล่อง ไม่เน้นลงทุนล็อคเงิน",
        "expected_goal_type": "CASH_FLOW",
    },
    {
        "id": "B19",
        "label": "Startup founder รายได้ผันผวน",
        "profile": {
            "income_type": "40(8)",
            "occupation": "startup_founder",
            "age": 29,
            "annual_income": 1000000,
            "expense_deduction_type": "standard",
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 400000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 0,
            "existing_thai_esg": 50000,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "ลงทุนเชิงรุกพร้อมได้สิทธิประโยชน์ทางภาษี",
        "expected_goal_type": "HYBRID",
    },
    {
        "id": "B20",
        "label": "เจ้าของธุรกิจ เกษียณแล้วแต่ยังมีรายได้",
        "profile": {
            "income_type": "40(8)",
            "occupation": "business_owner_retired",
            "age": 63,
            "annual_income": 700000,
            "expense_deduction_type": "actual",
            "actual_expenses": 300000,
            "is_vat_registered": False,
            "marital_status": "married",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 5000000,
            "risk_tolerance": "conservative",
            "existing_rmf": 0, # อายุเกินเกณฑ์ซื้อ RMF ใหม่แล้ว
            "existing_thai_esg": 0,
            "life_insurance_amount": 50000,
            "health_insurance_amount": 25000,
        },
        "goal": "อายุเกิน 60 แล้ว จัดการภาษีจากรายได้ธุรกิจอย่างไรดี",
        "expected_goal_type": "TAX_SAVING",
    },
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_profile_by_id(profile_id: str) -> Dict[str, Any]:
    for p in TEST_PROFILES:
        if p["id"] == profile_id:
            return p
    return {}

def print_profile_summary():
    print(f"\n{'='*110}")
    print(f"{'ID':<4} {'Label':<40} {'Type':<6} {'Income':>10} {'Age':>4} {'Expense':<10} {'VAT':<6} {'Goal':<12}")
    print(f"{'='*110}")
    for p in TEST_PROFILES:
        prof = p['profile']
        vat_status = "Yes" if prof.get('is_vat_registered') else "No"
        expense_type = "Standard" if prof['expense_deduction_type'] == 'standard' else "Actual"
        print(
            f"{p['id']:<4} "
            f"{p['label'][:38]:<40} "
            f"{prof['income_type']:<6} "
            f"{prof['annual_income']:>10,.0f} "
            f"{prof['age']:>4} "
            f"{expense_type:<10} "
            f"{vat_status:<6} "
            f"{p['expected_goal_type']:<12}"
        )
    print(f"{'='*110}")
    print(f"Total: {len(TEST_PROFILES)} profiles configured.")

if __name__ == "__main__":
    print_profile_summary()