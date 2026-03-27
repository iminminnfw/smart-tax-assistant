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
# GENERALIZATION TEST PROFILES (G1-G5)
# Profile ที่ไม่อยู่ใน few-shot pool — วัดความสามารถจริงของ model
# ไม่มี expected_plans (ใช้ rule-based validation แทน text matching)
# =============================================================================

GENERALIZATION_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "G1",
        "label": "นักดนตรี/ศิลปิน รายได้ไม่สม่ำเสมอ",
        "profile": {
            "income_type": "40(8)",
            "occupation": "other_business",  # ไม่ตรงกับ few-shot pool ที่มี
            "age": 28,
            "annual_income": 480000,
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
        "goal": "รายได้ไม่แน่นอน อยากวางแผนภาษีให้มั่นคง",
        "expected_goal_type": "TAX_SAVING",
        # Generalization checks (rule-based, ไม่ใช่ text matching)
        "generalization_checks": {
            "should_have_insurance": True,  # ยังไม่มีประกัน → ควรแนะนำ
            "max_tier_1_investment": 80000,  # รายได้ต่ำ tier ควรต่ำ
            "should_not_have": ["SSF"],  # SSF ยกเลิกแล้ว
            "income_type_should_be": "40(8)",  # ไม่ใช่ 40(6)
        },
    },
    {
        "id": "G2",
        "label": "โปรแกรมเมอร์ฟรีแลนซ์ + ขายของออนไลน์ (รายได้ 2 ทาง)",
        "profile": {
            "income_type": "40(8)",
            "occupation": "other_business",
            "age": 30,
            "annual_income": 1800000,
            "expense_deduction_type": "standard",
            "is_vat_registered": True,  # เกิน 1.8M → VAT
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 2,
            "existing_savings": 300000,
            "risk_tolerance": "aggressive",
            "existing_rmf": 50000,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "รายได้เกิน 1.8 ล้าน ต้องจด VAT ไหม และลดหย่อนอะไรได้บ้าง",
        "expected_goal_type": "HYBRID",
        "generalization_checks": {
            "should_have_insurance": True,
            "should_consider_vat": True,  # รายได้ > 1.8M
            "rmf_should_account_existing": True,  # มี existing RMF 50K
            "should_not_have": ["SSF"],
            "income_type_should_be": "40(8)",
        },
    },
    {
        "id": "G3",
        "label": "ทันตแพทย์ + เปิดร้านกาแฟ (40(6) เป็นหลัก)",
        "profile": {
            "income_type": "40(6)",
            "occupation": "dentist",
            "age": 42,
            "annual_income": 2500000,
            "expense_deduction_type": "standard",
            "is_vat_registered": True,  # เกิน 1.8M
            "marital_status": "married",
            "dependents": 1,
            "num_children": 1,
            "num_parents": 2,
            "existing_savings": 1500000,
            "risk_tolerance": "moderate",
            "existing_rmf": 100000,
            "existing_thai_esg": 0,
            "life_insurance_amount": 50000,
            "health_insurance_amount": 15000,
        },
        "goal": "มีรายได้หลายทาง ลดหย่อนยังไงให้คุ้มที่สุด",
        "expected_goal_type": "HYBRID",
        "generalization_checks": {
            "should_have_insurance": False,  # มีประกันอยู่แล้ว
            "should_consider_vat": True,
            "rmf_should_account_existing": True,  # มี existing RMF 100K
            "life_insurance_remaining": 50000,  # เหลือ 100K - 50K
            "health_insurance_remaining": 10000,  # เหลือ 25K - 15K
            "should_not_have": ["SSF"],
            "income_type_should_be": "40(6)",
        },
    },
    {
        "id": "G4",
        "label": "ผู้สูงอายุ 63 ปี มีรายได้จากดอกเบี้ยและเงินปันผล",
        "profile": {
            "income_type": "40(8)",
            "occupation": "business_owner_retired",
            "age": 63,
            "annual_income": 900000,
            "expense_deduction_type": "standard",
            "is_vat_registered": False,
            "marital_status": "married",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 8000000,
            "risk_tolerance": "conservative",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 80000,
            "health_insurance_amount": 25000,
        },
        "goal": "อายุมาก ไม่อยากเสี่ยง แต่อยากลดภาษีให้ได้บ้าง",
        "expected_goal_type": "RETIREMENT",
        "generalization_checks": {
            "should_have_insurance": False,  # มีเกือบเต็มแล้ว
            "should_emphasize_low_risk": True,  # conservative + อายุ 63
            "should_not_have_long_lock": True,  # ไม่ควรแนะนำ ThaiESG 8 ปี (อายุ 63+8=71)
            "life_insurance_remaining": 20000,  # เหลือ 100K - 80K
            "health_insurance_remaining": 0,  # เต็มแล้ว
            "should_not_have": ["SSF"],
            "income_type_should_be": "40(8)",
        },
    },
    {
        "id": "G5",
        "label": "คนรายได้น้อยมาก (200K/ปี) พนักงานรับจ้างทั่วไป",
        "profile": {
            "income_type": "40(8)",
            "occupation": "other_business",
            "age": 25,
            "annual_income": 200000,
            "expense_deduction_type": "standard",
            "is_vat_registered": False,
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "existing_savings": 20000,
            "risk_tolerance": "low",
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
        },
        "goal": "รายได้น้อยมาก ต้องเสียภาษีไหม",
        "expected_goal_type": "TAX_SAVING",
        "generalization_checks": {
            "should_have_insurance": True,  # ไม่มีเลย
            "should_be_minimal_investment": True,  # รายได้น้อย tier ต่ำสุด
            "taxable_income_may_be_zero": True,  # 200K - 60% - 60K personal ≈ 20K → ภาษี 0
            "should_not_have": ["SSF", "ThaiESGX"],
            "income_type_should_be": "40(8)",
        },
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

# =============================================================================
# COMMON ALLOCATION PROS/CONS TEMPLATES
# =============================================================================

_ALLOC_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "ประกันชีวิต": {
        "category": "ประกันชีวิต",
        "pros": ["ให้ความคุ้มครองชีวิตและครอบครัว", "ลดหย่อนภาษีได้สูงสุด 100,000 บาท", "สร้างความมั่นใจทางการเงิน"],
        "cons": ["ผลตอบแทนจากการลงทุนต่ำ", "ต้องจ่ายเบี้ยประกันต่อเนื่อง", "ไม่เหมาะสำหรับการเติบโตของเงิน"],
    },
    "ประกันสุขภาพ": {
        "category": "ประกันสุขภาพ",
        "pros": ["ให้ความคุ้มครองค่ารักษาพยาบาล", "ลดหย่อนภาษีได้สูงสุด 25,000 บาท", "ช่วยลดภาระค่าใช้จ่ายทางการแพทย์"],
        "cons": ["ไม่มีผลตอบแทนจากการลงทุน", "ต้องจ่ายเบี้ยประกันต่อเนื่อง", "ไม่เหมาะสำหรับการเติบโตของเงิน"],
    },
    "ประกันบำนาญ": {
        "category": "ประกันบำนาญ",
        "pros": ["รับประกันรายได้หลังเกษียณ", "ลดหย่อนภาษีได้สูงสุด 200,000 บาท", "ผลตอบแทนที่แน่นอนและมั่นคง"],
        "cons": ["ต้องถือครองจนถึงอายุที่กำหนด", "ผลตอบแทนต่ำกว่าการลงทุนในตลาดทุน", "สภาพคล่องต่ำ"],
    },
    "RMF": {
        "category": "RMF",
        "pros": ["ลดหย่อนภาษีได้สูงถึง 30% ของรายได้", "ผลตอบแทนระยะยาวจากการลงทุนในตลาดทุน", "เหมาะสำหรับการวางแผนเกษียณ"],
        "cons": ["ต้องถือจนอายุ 55 ปีหรือครบ 5 ปี", "ต้องลงทุนต่อเนื่องทุกปี", "มีความเสี่ยงจากตลาดหุ้น"],
    },
    "ThaiESG": {
        "category": "ThaiESG",
        "pros": ["ลดหย่อนภาษีได้สูงสุด 300,000 บาท", "ลงทุนในบริษัทที่คำนึงถึงความยั่งยืน", "ผลตอบแทนดีจากกองทุนหุ้นคุณภาพ"],
        "cons": ["ต้องถือครองอย่างน้อย 8 ปี", "มีความเสี่ยงจากตลาดหุ้น", "ทางเลือกกองทุนจำกัด"],
    },
    "เงินบริจาค": {
        "category": "เงินบริจาค",
        "pros": ["ลดหย่อนภาษีได้ทันที", "บริจาคการศึกษาลดหย่อนได้ 1 เท่า (ตั้งแต่ปี 2568)", "ไม่ต้องถือครองหรือล็อคเงิน"],
        "cons": ["ไม่มีผลตอบแทนจากการลงทุน", "เป็นค่าใช้จ่ายที่ไม่ได้คืน", "วงเงินลดหย่อนจำกัดตามกฎหมาย"],
    },
    "Solar_Rooftop": {
        "category": "Solar Rooftop",
        "pros": ["ลดหย่อนภาษีได้ตามจริงสูงสุด 200,000 บาท", "ประหยัดค่าไฟในระยะยาว", "สนับสนุนพลังงานสะอาดตามนโยบายรัฐ"],
        "cons": ["ใช้เงินลงทุนก้อนใหญ่ในครั้งแรก", "ใช้สิทธิลดหย่อนได้เพียง 1 ครั้งตลอดโครงการ"],
    },
    "ThaiESGX": {
        "category": "ThaiESGX",
        "pros": ["ได้วงเงินพิเศษแยกต่างหากสูงสุด 300,000 บาท (เฉพาะปี 2568)", "สามารถโอนสับเปลี่ยนจาก LTF เดิมได้", "ลงทุนในหุ้น ESG ไทยที่ยั่งยืน"],
        "cons": ["ต้องถือครองตามเงื่อนไขที่กำหนด", "วงเงินพิเศษจำกัดเฉพาะปีภาษี 2568"],
    },
}


def _alloc(cat: str) -> Dict[str, Any]:
    """Return standard pros/cons template for a category"""
    return _ALLOC_TEMPLATES[cat].copy()


# =============================================================================
# PROFILE_EXPECTED_PLANS - 20 profiles × 3 plans
# expected_text descriptions ที่สอดคล้องกับแต่ละ profile
# total_investment / total_tax_saving จะถูก overwrite โดย backend
# =============================================================================

PROFILE_EXPECTED_PLANS: Dict[str, Dict[str, Any]] = {
    # =====================================================================
    # A1: แพทย์เปิดคลินิก 1.5M | no existing | aggressive | TAX_SAVING
    # Insurance remaining: 100K | RMF remaining: 450K | Pension: 200K
    # =====================================================================
    "A1": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นสร้างความคุ้มครองพื้นฐานด้วยประกันชีวิตและสุขภาพ เหมาะสำหรับแพทย์ที่เริ่มต้นวางแผนภาษีและยังไม่มีประกัน",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["ความคุ้มครอง", "ประกันชีวิต", "ประกันสุขภาพ", "แพทย์", "ลดหย่อนภาษี"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายการลงทุนระหว่างประกันและกองทุนรวม สร้างสมดุลระหว่างความคุ้มครองและผลตอบแทน",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "กระจายความเสี่ยง", "กองทุน", "ประกัน", "ผลตอบแทน"],
                "key_points": ["กองทุน", "ประกัน", "กระจายความเสี่ยง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลดหย่อนภาษีสูงสุดด้วย RMF และ ThaiESG ใช้สิทธิลดหย่อนเต็มวงเงินสำหรับรายได้สูง",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["ลดหย่อนสูงสุด", "RMF", "ThaiESG", "ผลตอบแทน", "เติบโต"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี", "ผลตอบแทนสูง"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A2: ทนายความ 1.2M | life=30K health=10K RMF=50K | moderate | HYBRID
    # Insurance remaining: 60K | RMF remaining: 310K | Pension: 180K
    # =====================================================================
    "A2": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มความคุ้มครองครอบครัวด้วยประกันชีวิตและสุขภาพเพิ่มเติม เหมาะกับครอบครัวที่มีลูกเล็ก",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["ความคุ้มครอง", "ครอบครัว", "ประกันชีวิต", "ประกันสุขภาพ", "ลูก"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครองครอบครัว"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างความคุ้มครองและการลงทุน เพิ่ม RMF ต่อยอดจากที่มีอยู่พร้อมรักษาสภาพคล่อง",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "RMF", "ประกัน", "สภาพคล่อง", "ครอบครัว"],
                "key_points": ["RMF", "ประกัน", "สมดุล"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นการลงทุนเพื่อผลตอบแทนระยะยาวพร้อมสิทธิประโยชน์ทางภาษี เพิ่ม RMF และ ThaiESG",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["ผลตอบแทน", "RMF", "ThaiESG", "ลดหย่อน", "ระยะยาว"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A3: วิศวกรที่ปรึกษา 900K | life=50K | moderate | CASH_FLOW
    # Insurance remaining: 50K | RMF remaining: 270K | Pension: 135K
    # =====================================================================
    "A3": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นสภาพคล่องและความคุ้มครองพื้นฐาน เพิ่มประกันสุขภาพเพื่อรองรับค่าใช้จ่ายดูแลพ่อแม่",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["สภาพคล่อง", "คุ้มครอง", "ประกันสุขภาพ", "ดูแลพ่อแม่", "ประกัน"],
                "key_points": ["ประกันสุขภาพ", "สภาพคล่อง", "ดูแลพ่อแม่"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างสภาพคล่องและการลดหย่อนภาษี กระจายเงินในประกันและกองทุนรวม",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "สภาพคล่อง", "ลดหย่อน", "กองทุน", "ประกัน"],
                "key_points": ["กองทุน", "ประกัน", "สภาพคล่อง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มการลดหย่อนภาษีด้วย RMF และ ThaiESG โดยยังรักษาสภาพคล่องสำหรับดูแลพ่อแม่",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อน", "สภาพคล่อง", "ดูแลพ่อแม่"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A4: สถาปนิกฟรีแลนซ์ 480K | no existing | aggressive | TAX_SAVING
    # Insurance remaining: 100K | RMF remaining: 144K | Pension: 72K
    # =====================================================================
    "A4": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เริ่มต้นวางแผนภาษีด้วยประกันชีวิตและสุขภาพ สร้างความคุ้มครองพื้นฐานสำหรับสถาปนิกจบใหม่",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["เริ่มต้น", "ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "วางแผนภาษี"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "เริ่มต้นวางแผน"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายการลงทุนระหว่างประกันและกองทุนรวม เหมาะสำหรับผู้เริ่มต้นวางแผนภาษี",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["กระจาย", "กองทุน", "ประกัน", "เริ่มต้น", "สมดุล"],
                "key_points": ["กองทุน", "ประกัน", "กระจายความเสี่ยง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลดหย่อนภาษีสูงสุดด้วยกองทุน RMF และ ThaiESG สำหรับรายได้ระดับเริ่มต้น",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["ลดหย่อนสูงสุด", "RMF", "ThaiESG", "เติบโต", "รายได้"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A5: นักบัญชีอิสระ 1.8M | life=100K health=25K RMF=300K | conservative | RETIREMENT
    # Insurance FULL (combined>100K) | RMF remaining: 200K | Pension: 200K
    # Retirement cap remaining: 500K - 300K = 200K
    # =====================================================================
    "A5": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นความมั่นคงหลังเกษียณด้วยประกันบำนาญ เพิ่มความมั่นใจสำหรับเกษียณใน 4 ปี",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["เกษียณ", "ประกันบำนาญ", "มั่นคง", "ความปลอดภัย", "รายได้หลังเกษียณ"],
                "key_points": ["ประกันบำนาญ", "เกษียณ", "ความมั่นคง"],
                "expected_allocations": [_alloc("ประกันบำนาญ"), _alloc("RMF")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่าง RMF เพิ่มเติมและ ThaiESG เตรียมพร้อมสำหรับเกษียณอีก 4 ปี",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "RMF", "ThaiESG", "เกษียณ", "เตรียมพร้อม"],
                "key_points": ["RMF", "ThaiESG", "เกษียณ"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่ม RMF และ ThaiESG เพื่อลดหย่อนภาษีสูงสุดก่อนเกษียณ ใช้สิทธิที่เหลืออยู่ให้คุ้มค่า",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อนสูงสุด", "เกษียณ", "คุ้มค่า"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี", "เกษียณ"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A6: แพทย์เฉพาะทาง 4M | life=100K health=25K RMF=200K ThaiESG=100K | aggressive | HYBRID
    # Insurance FULL | RMF remaining: 300K | ThaiESG remaining: 200K | Pension: 200K
    # Retirement cap remaining: 500K - 200K = 300K
    # =====================================================================
    "A6": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่ม RMF ต่อยอดจากที่มีอยู่ พร้อมประกันบำนาญเพื่อวางแผนเกษียณตอน 55",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["RMF", "ประกันบำนาญ", "เกษียณ", "ต่อยอด", "แพทย์"],
                "key_points": ["RMF", "ประกันบำนาญ", "เกษียณตอน 55"],
                "expected_allocations": [_alloc("ประกันบำนาญ"), _alloc("RMF")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายการลงทุนใน RMF ThaiESG และประกันบำนาญ เพื่อใช้สิทธิลดหย่อนอย่างครบถ้วน",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["กระจาย", "RMF", "ThaiESG", "ประกันบำนาญ", "ลดหย่อน"],
                "key_points": ["RMF", "ThaiESG", "ประกันบำนาญ"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลงทุนเต็มวงเงินใน RMF และ ThaiESG พร้อมเงินบริจาคการศึกษาเพื่อลดหย่อนสูงสุด",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "เงินบริจาค", "ลดหย่อนสูงสุด", "เติบโต"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษีสูงสุด"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("เงินบริจาค")],
            },
        },
    },

    # =====================================================================
    # A7: ทันตแพทย์ 2M | life=50K health=20K | moderate | LIFE_EVENT
    # Insurance remaining: 30K | RMF remaining: 500K | Pension: 200K
    # =====================================================================
    "A7": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มความคุ้มครองครอบครัวด้วยประกันชีวิตเพิ่มเติม เตรียมเงินสำหรับดาวน์บ้าน",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["คุ้มครอง", "ครอบครัว", "ประกันชีวิต", "ดาวน์บ้าน", "ประกัน"],
                "key_points": ["ประกันชีวิต", "คุ้มครองครอบครัว", "ดาวน์บ้าน"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างประกันและกองทุนรวม สร้างเงินออมเพื่อเป้าหมายดาวน์บ้านพร้อมลดหย่อนภาษี",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "กองทุน", "ดาวน์บ้าน", "เงินออม", "ลดหย่อน"],
                "key_points": ["กองทุน", "ประกัน", "ดาวน์บ้าน"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นการลงทุนใน RMF และ ThaiESG เพื่อลดหย่อนภาษีสูงสุดและเพิ่มเงินออมสำหรับเป้าหมาย",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อนสูงสุด", "เงินออม", "เป้าหมาย"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A8: นักกฎหมาย 700K | life=20K | conservative | TAX_SAVING
    # Insurance remaining: 80K | RMF remaining: 210K | Pension: 105K
    # =====================================================================
    "A8": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นประกันชีวิตและสุขภาพเพิ่มเติม เหมาะกับผู้ที่ไม่อยากเสี่ยงลงทุนแต่ต้องการลดหย่อนภาษี",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["ประกันชีวิต", "ประกันสุขภาพ", "ไม่เสี่ยง", "ลดหย่อน", "ปลอดภัย"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "ปลอดภัย"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างประกันและกองทุนความเสี่ยงต่ำ ลดหย่อนภาษีอย่างปลอดภัย",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "ความเสี่ยงต่ำ", "ประกัน", "กองทุน", "ลดหย่อน"],
                "key_points": ["กองทุน", "ประกัน", "ความเสี่ยงต่ำ"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มการลดหย่อนด้วย RMF ความเสี่ยงต่ำและประกันบำนาญ เหมาะกับผู้ที่ต้องการความมั่นคง",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ประกันบำนาญ", "ความเสี่ยงต่ำ", "มั่นคง", "ลดหย่อน"],
                "key_points": ["RMF", "ประกันบำนาญ", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A9: วิศวกร 2.5M | life=100K health=25K RMF=400K ThaiESG=200K | moderate | TAX_SAVING
    # Insurance FULL | RMF remaining: 100K | ThaiESG remaining: 100K | Pension: 200K
    # Retirement cap remaining: 500K - 400K = 100K
    # =====================================================================
    "A9": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่ม RMF อีกเล็กน้อยเพื่อเติมเต็มวงเงิน พร้อมประกันบำนาญสำหรับสิทธิที่เหลือ",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["RMF", "ประกันบำนาญ", "เติมเต็ม", "สิทธิที่เหลือ", "วงเงิน"],
                "key_points": ["RMF", "ประกันบำนาญ", "สิทธิที่เหลือ"],
                "expected_allocations": [_alloc("ประกันบำนาญ"), _alloc("RMF")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่ม ThaiESG อีก 100,000 บาทและ RMF เพื่อใช้สิทธิลดหย่อนที่เหลืออยู่อย่างสมดุล",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["ThaiESG", "RMF", "สมดุล", "สิทธิลดหย่อน", "เพิ่ม"],
                "key_points": ["ThaiESG", "RMF", "สิทธิที่เหลือ"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เติมเต็มทั้ง RMF และ ThaiESG ให้เต็มเพดาน พร้อมประกันบำนาญเพื่อลดหย่อนสูงสุด",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "เต็มเพดาน", "ลดหย่อนสูงสุด", "ประกันบำนาญ"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี", "เต็มวงเงิน"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # A10: สัตวแพทย์ 1M | no existing | aggressive | TAX_SAVING | low savings
    # Insurance remaining: 100K | RMF remaining: 300K | Pension: 150K
    # =====================================================================
    "A10": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เริ่มต้นด้วยประกันชีวิตและสุขภาพ สร้างความคุ้มครองพื้นฐานก่อนลงทุนเพิ่ม",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["เริ่มต้น", "ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "พื้นฐาน"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "เริ่มต้นวางแผน"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายระหว่างประกันและกองทุน เริ่มต้นวางแผนภาษีอย่างเป็นระบบแม้เงินสำรองน้อย",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["กระจาย", "ประกัน", "กองทุน", "วางแผน", "เงินสำรอง"],
                "key_points": ["กองทุน", "ประกัน", "วางแผนภาษี"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลดหย่อนภาษีสูงสุดด้วย RMF และ ThaiESG สำหรับสัตวแพทย์ที่มีรายได้ดี",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อนสูงสุด", "เติบโต", "รายได้ดี"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B11: เจ้าของร้านค้าออนไลน์ 600K | no existing | moderate | TAX_SAVING
    # Insurance remaining: 100K | RMF remaining: 180K | Pension: 90K
    # =====================================================================
    "B11": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เริ่มต้นด้วยประกันชีวิตและสุขภาพ สร้างความคุ้มครองสำหรับเจ้าของธุรกิจออนไลน์",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "ธุรกิจ", "เริ่มต้น"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครองธุรกิจ"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างประกันและกองทุนรวม กระจายความเสี่ยงสำหรับธุรกิจออนไลน์",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "กระจายความเสี่ยง", "กองทุน", "ประกัน", "ธุรกิจ"],
                "key_points": ["กองทุน", "ประกัน", "กระจายความเสี่ยง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลดหย่อนภาษีด้วย RMF และ ThaiESG สำหรับรายได้ระดับกลางจากธุรกิจ",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อน", "ธุรกิจ", "เติบโต"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B12: ผู้รับเหมาก่อสร้าง 1.5M | life=50K health=25K RMF=100K | moderate | HYBRID
    # Insurance remaining: 25K (combined=75K) | RMF remaining: 350K | Pension: 200K
    # =====================================================================
    "B12": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มความคุ้มครองครอบครัวด้วยประกันชีวิตเพิ่มเติม สมดุลภาษีธุรกิจและบุคคลธรรมดา",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["คุ้มครอง", "ครอบครัว", "ประกันชีวิต", "ธุรกิจ", "ภาษี"],
                "key_points": ["ประกันชีวิต", "คุ้มครองครอบครัว", "สมดุลภาษี"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันบำนาญ"), _alloc("RMF")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างประกันและกองทุน เพิ่ม RMF ต่อยอดจากที่มีอยู่เพื่อลดหย่อนเพิ่ม",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "RMF", "ประกัน", "ต่อยอด", "ลดหย่อน"],
                "key_points": ["RMF", "ประกัน", "สมดุล"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลงทุนใน RMF และ ThaiESG เพื่อลดหย่อนภาษีสูงสุดสำหรับผู้รับเหมา",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อนสูงสุด", "ผู้รับเหมา", "ลงทุน"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B13: เจ้าของร้านอาหาร 800K | life=20K health=10K | conservative | CASH_FLOW
    # Insurance remaining: 70K (combined=30K) | RMF remaining: 240K | Pension: 120K
    # =====================================================================
    "B13": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นสภาพคล่องและเพิ่มความคุ้มครองด้วยประกันชีวิตและสุขภาพเพิ่มเติม",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["สภาพคล่อง", "คุ้มครอง", "ประกันชีวิต", "ประกันสุขภาพ", "ร้านอาหาร"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "สภาพคล่อง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างสภาพคล่องและการลดหย่อน เหมาะกับธุรกิจร้านอาหารที่รายได้ผันผวน",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "สภาพคล่อง", "ลดหย่อน", "ผันผวน", "ร้านอาหาร"],
                "key_points": ["กองทุน", "ประกัน", "สภาพคล่อง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มการลดหย่อนด้วยกองทุนความเสี่ยงต่ำ โดยรักษาเงินหมุนเวียนธุรกิจร้านอาหาร",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["กองทุน", "ลดหย่อน", "ความเสี่ยงต่ำ", "เงินหมุนเวียน", "ธุรกิจ"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B14: นายหน้าอสังหาฯ 3M | life=100K RMF=200K ThaiESG=100K | aggressive | TAX_SAVING
    # Insurance FULL (life=100K) | RMF remaining: 300K | ThaiESG remaining: 200K | Pension: 200K
    # Retirement cap remaining: 500K - 200K = 300K
    # =====================================================================
    "B14": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่ม RMF ต่อยอดจาก 200,000 บาทที่มีอยู่ พร้อมประกันบำนาญเพิ่มความมั่นคง",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["RMF", "ประกันบำนาญ", "ต่อยอด", "มั่นคง", "นายหน้า"],
                "key_points": ["RMF", "ประกันบำนาญ", "ต่อยอด"],
                "expected_allocations": [_alloc("ประกันบำนาญ"), _alloc("RMF")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายการลงทุนใน RMF และ ThaiESG ต่อยอดจากที่มีอยู่เพื่อใช้สิทธิลดหย่อนเพิ่ม",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["RMF", "ThaiESG", "กระจาย", "สิทธิลดหย่อน", "ต่อยอด"],
                "key_points": ["RMF", "ThaiESG", "สิทธิลดหย่อน"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลงทุนเต็มวงเงินใน RMF และ ThaiESG พร้อม Thai ESGX วงเงินพิเศษปี 2568 เพื่อลดหย่อนสูงสุด",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ThaiESGX", "ลดหย่อนสูงสุด", "เต็มวงเงิน"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษีสูงสุด"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ThaiESGX")],
            },
        },
    },

    # =====================================================================
    # B15: YouTuber 420K | no existing | aggressive | TAX_SAVING
    # Insurance remaining: 100K | RMF remaining: 126K | Pension: 63K
    # =====================================================================
    "B15": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เริ่มต้นด้วยประกันชีวิตและสุขภาพ สร้างความคุ้มครองสำหรับรายได้ที่เติบโตเร็ว",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["เริ่มต้น", "ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "เติบโต"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "เริ่มต้นวางแผน"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายระหว่างประกันและกองทุนรวม เหมาะกับคนรุ่นใหม่ที่เริ่มต้นวางแผนภาษี",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["กระจาย", "กองทุน", "ประกัน", "คนรุ่นใหม่", "วางแผน"],
                "key_points": ["กองทุน", "ประกัน", "กระจายความเสี่ยง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้น RMF และ ThaiESG เพื่อลดหย่อนภาษีสูงสุดสำหรับรายได้ระดับเริ่มต้น",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อนสูงสุด", "รายได้", "เติบโต"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B16: ธุรกิจนำเข้า 5M | life=100K health=25K RMF=500K ThaiESG=300K | moderate | HYBRID
    # Insurance FULL | RMF FULL | ThaiESG FULL | Retirement cap FULL (500K-500K=0)
    # Almost no deductions left — edge case profile
    # =====================================================================
    "B16": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "ท่านใช้สิทธิลดหย่อนกองทุนเต็มวงเงินแล้ว แนะนำติดตั้งระบบ Solar Rooftop เพื่อรับสิทธิลดหย่อนพิเศษสูงสุด 200,000 บาท",
                "plan_name": "ทางเลือกที่ 1 - เน้นโครงสร้างพื้นฐาน",
                "keywords": ["เต็มวงเงิน", "Solar Rooftop", "พลังงานสะอาด", "ลดหย่อน", "พิเศษ"],
                "key_points": ["Solar Rooftop", "สิทธิเต็มวงเงิน", "พลังงานสะอาด"],
                "expected_allocations": [_alloc("Solar_Rooftop")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "จัดการสินทรัพย์เดิมโดยพิจารณาโอนสับเปลี่ยน LTF ที่ครบกำหนดมายังกองทุน Thai ESGX เพื่อรับสิทธิลดหย่อนเพิ่มสูงสุด 300,000 บาท",
                "plan_name": "ทางเลือกที่ 2 - จัดการสินทรัพย์เดิม",
                "keywords": ["จัดการสินทรัพย์", "LTF", "Thai ESGX", "สับเปลี่ยน", "วงเงินพิเศษ"],
                "key_points": ["Thai ESGX", "โอนสับเปลี่ยน LTF", "วงเงินพิเศษ"],
                "expected_allocations": [_alloc("ThaiESGX")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "ใช้สิทธิประโยชน์สูงสุดของปี 2568 ด้วยการผสานวงเงินพิเศษจาก Thai ESGX ควบคู่กับการลดหย่อน Solar Rooftop",
                "plan_name": "ทางเลือกที่ 3 - ใช้สิทธิปี 2568 เต็มพิกัด",
                "keywords": ["สิทธิประโยชน์", "ปี 2568", "Thai ESGX", "Solar Rooftop", "สูงสุด"],
                "key_points": ["Thai ESGX", "Solar Rooftop", "ลดหย่อนภาษีปี 2568"],
                "expected_allocations": [_alloc("ThaiESGX"), _alloc("Solar_Rooftop")],
            },
        },
    },

    # =====================================================================
    # B17: ช่างภาพฟรีแลนซ์ 360K | no existing | moderate | TAX_SAVING
    # Insurance remaining: 100K | RMF remaining: 108K | Pension: 54K
    # =====================================================================
    "B17": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เริ่มต้นด้วยประกันชีวิตและสุขภาพ สร้างความคุ้มครองพื้นฐานสำหรับฟรีแลนซ์รายได้น้อย",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["เริ่มต้น", "ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "ฟรีแลนซ์"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายระหว่างประกันและกองทุนรวม เหมาะสำหรับช่างภาพที่ต้องการเริ่มต้นลดหย่อนภาษี",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["กระจาย", "ประกัน", "กองทุน", "ช่างภาพ", "ลดหย่อน"],
                "key_points": ["กองทุน", "ประกัน", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้น RMF และ ThaiESG เพื่อลดหย่อนภาษีให้มากที่สุดตามวงเงินรายได้",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อน", "วงเงิน", "รายได้"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B18: เจ้าของฟาร์ม 1.2M | life=40K RMF=50K | conservative | CASH_FLOW
    # Insurance remaining: 60K (combined=40K) | RMF remaining: 310K | Pension: 180K
    # =====================================================================
    "B18": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นสภาพคล่องและเพิ่มประกันชีวิตและสุขภาพ สำหรับครอบครัวที่มีภาระดูแลเยอะ",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["สภาพคล่อง", "ประกันชีวิต", "ประกันสุขภาพ", "ครอบครัว", "ภาระ"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "สภาพคล่อง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างสภาพคล่องและการลดหย่อน เน้นประกันและกองทุนความเสี่ยงต่ำ",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "สภาพคล่อง", "ลดหย่อน", "ประกัน", "ความเสี่ยงต่ำ"],
                "key_points": ["กองทุน", "ประกัน", "สภาพคล่อง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มการลดหย่อนด้วย RMF ต่อยอดและ ThaiESG โดยยังรักษาสภาพคล่องสำหรับครอบครัว",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อน", "สภาพคล่อง", "ครอบครัว"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B19: Startup founder 1M | ThaiESG=50K | aggressive | HYBRID
    # Insurance remaining: 100K | RMF remaining: 300K | ThaiESG remaining: 250K | Pension: 150K
    # =====================================================================
    "B19": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เริ่มต้นด้วยประกันชีวิตและสุขภาพ สร้างความคุ้มครองสำหรับ Startup founder",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง", "Startup", "เริ่มต้น"],
                "key_points": ["ประกันชีวิต", "ประกันสุขภาพ", "คุ้มครอง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันสุขภาพ"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "กระจายระหว่างประกันและกองทุน เพิ่ม ThaiESG ต่อยอดจากที่มีอยู่พร้อม RMF",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["กระจาย", "ThaiESG", "RMF", "ต่อยอด", "กองทุน"],
                "key_points": ["ThaiESG", "RMF", "กระจายความเสี่ยง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ThaiESG")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เน้นลงทุนเชิงรุกใน RMF และ ThaiESG เพื่อผลตอบแทนและลดหย่อนภาษีสูงสุด",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "เชิงรุก", "ผลตอบแทน", "ลดหย่อนสูงสุด"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี", "ผลตอบแทนสูง"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },

    # =====================================================================
    # B20: เจ้าของธุรกิจเกษียณ 700K | life=50K health=25K | conservative | TAX_SAVING
    # Insurance remaining: 25K (combined=75K) | RMF remaining: 210K | Pension: 105K
    # Age 63 - limited investment horizon
    # =====================================================================
    "B20": {
        "plan_1": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มประกันชีวิตเล็กน้อยและประกันบำนาญ เหมาะกับผู้ที่อายุเกิน 60 ปีต้องการความมั่นคง",
                "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                "keywords": ["ประกันชีวิต", "ประกันบำนาญ", "มั่นคง", "อายุเกิน 60", "ปลอดภัย"],
                "key_points": ["ประกันชีวิต", "ประกันบำนาญ", "ความมั่นคง"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("ประกันบำนาญ"), _alloc("RMF")],
            },
        },
        "plan_2": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "สมดุลระหว่างประกันและกองทุนความเสี่ยงต่ำ จัดการภาษีจากรายได้ธุรกิจหลังเกษียณ",
                "plan_name": "ทางเลือกที่ 2 - สมดุล",
                "keywords": ["สมดุล", "ความเสี่ยงต่ำ", "ภาษี", "ธุรกิจ", "หลังเกษียณ"],
                "key_points": ["กองทุน", "ประกัน", "ความเสี่ยงต่ำ"],
                "expected_allocations": [_alloc("ประกันชีวิต"), _alloc("RMF"), _alloc("ประกันบำนาญ")],
            },
        },
        "plan_3": {
            "total_investment": 0,
            "total_tax_saving": 0,
            "expected_text": {
                "description": "เพิ่มการลดหย่อนด้วย RMF และ ThaiESG ความเสี่ยงต่ำ สำหรับรายได้หลังเกษียณ",
                "plan_name": "ทางเลือกที่ 3 - เน้นการเติบโต",
                "keywords": ["RMF", "ThaiESG", "ลดหย่อน", "ความเสี่ยงต่ำ", "หลังเกษียณ"],
                "key_points": ["RMF", "ThaiESG", "ลดหย่อนภาษี"],
                "expected_allocations": [_alloc("RMF"), _alloc("ThaiESG"), _alloc("ประกันบำนาญ")],
            },
        },
    },
}


# =============================================================================
# EXPECTED CITATIONS PER PROFILE
# อ้างอิงจากเอกสาร "ปรับปรุงเอกสารภาษีบุคคลธรรมดา 2568-2569.pdf"
#
# มาตรากฎหมายที่คำตอบ LLM ควรอ้างอิง เพื่อวัด Citation F1 ใน NitiBench
# - มาตรา 40(6): เงินได้พึงประเมินจากวิชาชีพอิสระ (แพทย์ ทนาย วิศวกร สถาปนิก บัญชี ฯลฯ)
# - มาตรา 40(8): เงินได้พึงประเมินจากธุรกิจ/พาณิชย์ (catch-all provision)
# - พ.ร.ฎ. 629: พระราชกฤษฎีกาฉบับที่ 629 — ปรับอัตราหักค่าใช้จ่ายเหมา
#   บังคับเพดานสูงสุด 60% สำหรับทุกประเภทกิจการตามมาตรา 40(8)
#   และคงอัตราเดิมสำหรับ 40(6): แพทย์ 60%, อื่นๆ 30%
# - มาตรา 81(1): ยกเว้นภาษีมูลค่าเพิ่ม (VAT) สำหรับวิชาชีพอิสระบางประเภท
#   และกิจการบางประเภทตาม 40(8) — เกี่ยวข้องเมื่อรายรับเกิน 1.8 ล้านบาท/ปี
# - ภ.ง.ด. 94: แบบแสดงรายการภาษีครึ่งปี สำหรับผู้มีเงินได้ตามมาตรา 40(5)-40(8)
# =============================================================================

_PROFILE_CITATIONS: Dict[str, List[str]] = {
    # Group A: มาตรา 40(6) — วิชาชีพอิสระ
    "A1":  ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # แพทย์เปิดคลินิก หักเหมา 60%
    "A2":  ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # ทนายความ หักเหมา 30%
    "A3":  ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # วิศวกรที่ปรึกษา หักตามจริง
    "A4":  ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # สถาปนิกฟรีแลนซ์ หักเหมา 30%
    "A5":  ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # นักบัญชีอิสระ หักตามจริง
    "A6":  ["มาตรา 40(6)", "พ.ร.ฎ. 629", "มาตรา 81(1)"],  # แพทย์เฉพาะทาง จด VAT (>1.8M)
    "A7":  ["มาตรา 40(6)", "พ.ร.ฎ. 629", "มาตรา 81(1)"],  # ทันตแพทย์ จด VAT (>1.8M)
    "A8":  ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # นักกฎหมาย หักเหมา 30%
    "A9":  ["มาตรา 40(6)", "พ.ร.ฎ. 629", "มาตรา 81(1)"],  # วิศวกร จด VAT (>1.8M)
    "A10": ["มาตรา 40(6)", "พ.ร.ฎ. 629"],              # สัตวแพทย์ หักเหมา

    # Group B: มาตรา 40(8) — ธุรกิจ/พาณิชย์
    # พ.ร.ฎ. 629 บังคับหักเหมาสูงสุด 60% ทุกประเภทกิจการ (เดิมบางประเภทสูงถึง 85%)
    "B11": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # ร้านค้าออนไลน์
    "B12": ["มาตรา 40(8)", "พ.ร.ฎ. 629", "มาตรา 81(1)"],  # ผู้รับเหมาก่อสร้าง จด VAT
    "B13": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # ร้านอาหาร
    "B14": ["มาตรา 40(8)", "พ.ร.ฎ. 629", "มาตรา 81(1)"],  # นายหน้าอสังหาฯ จด VAT
    "B15": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # YouTuber/Content Creator
    "B16": ["มาตรา 40(8)", "พ.ร.ฎ. 629", "มาตรา 81(1)"],  # ธุรกิจนำเข้า จด VAT
    "B17": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # ช่างภาพฟรีแลนซ์
    "B18": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # เจ้าของฟาร์ม (เกษตร ยกเว้น VAT ตาม ม.81)
    "B19": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # Startup founder
    "B20": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],              # เจ้าของธุรกิจเกษียณ
}


def _inject_expected_citations() -> None:
    """เพิ่ม expected_citations ให้ทุก plan ใน PROFILE_EXPECTED_PLANS จาก _PROFILE_CITATIONS

    ทำ inject อัตโนมัติเพื่อไม่ต้องเขียนซ้ำใน 60 plans (20 profiles × 3 plans)
    Citations เหมือนกันทุก plan ของ profile เดียวกัน เพราะอ้างอิงมาตราเดียวกัน
    """
    for profile_id, plans in PROFILE_EXPECTED_PLANS.items():
        citations = _PROFILE_CITATIONS.get(profile_id, [])
        for plan_key in ['plan_1', 'plan_2', 'plan_3']:
            plan = plans.get(plan_key)
            if plan and 'expected_text' in plan:
                plan['expected_text']['expected_citations'] = citations


# Auto-inject citations on module load
_inject_expected_citations()


def get_expected_plans_by_profile_id(profile_id: str) -> Dict[str, Any]:
    """ดึง expected_plans สำหรับ profile ที่ระบุ"""
    return PROFILE_EXPECTED_PLANS.get(profile_id, {})


# =============================================================================
# AUTO-GENERATE MULTI-REFERENCE DESCRIPTIONS
# สร้าง paraphrased descriptions อัตโนมัติจาก description + keywords ของแต่ละ plan
# Academic Justification: Multi-Reference Evaluation (Papineni et al., 2002)
# =============================================================================

# Thai synonym/paraphrase patterns for auto-generation
_PARAPHRASE_PATTERNS = {
    # Conservative plan patterns
    "เน้นความคุ้มครอง": ["เน้นด้านความคุ้มครอง", "ให้ความสำคัญกับความคุ้มครอง", "เน้นประกันและความคุ้มครอง"],
    "เน้นสร้างความคุ้มครอง": ["สร้างฐานความคุ้มครอง", "เริ่มจากความคุ้มครอง", "เน้นความคุ้มครองเป็นหลัก"],
    "เพิ่มความคุ้มครอง": ["เสริมความคุ้มครอง", "เพิ่มการคุ้มครอง", "ขยายความคุ้มครอง"],
    "เน้นสภาพคล่อง": ["ให้ความสำคัญกับสภาพคล่อง", "รักษาสภาพคล่อง", "เน้นความคล่องตัวทางการเงิน"],
    # Balanced plan patterns
    "กระจายความเสี่ยง": ["กระจายการลงทุน", "แบ่งการลงทุน", "กระจายเงินลงทุน"],
    "กระจายการลงทุน": ["กระจายความเสี่ยง", "แบ่งเงินลงทุน", "จัดสรรเงินลงทุน"],
    "สมดุลระหว่าง": ["สร้างสมดุลระหว่าง", "ผสมผสานระหว่าง", "จัดสรรอย่างสมดุลระหว่าง"],
    "กระจายระหว่าง": ["จัดสรรระหว่าง", "แบ่งระหว่าง", "สมดุลระหว่าง"],
    # Growth plan patterns
    "เน้นลดหย่อนภาษีสูงสุด": ["ลดหย่อนภาษีให้มากที่สุด", "ใช้สิทธิลดหย่อนเต็มที่", "เน้นสิทธิประโยชน์ทางภาษีสูงสุด"],
    "เน้นลงทุนเต็มวงเงิน": ["ลงทุนเต็มเพดาน", "ใช้วงเงินลงทุนสูงสุด", "เติมเต็มวงเงินลงทุน"],
    "เพิ่มการลดหย่อน": ["เพิ่มสิทธิลดหย่อน", "ขยายการลดหย่อนภาษี", "ใช้สิทธิลดหย่อนเพิ่ม"],
    "เน้นการลงทุน": ["เน้นลงทุน", "ให้ความสำคัญกับการลงทุน", "เน้นผลตอบแทนจากการลงทุน"],
    # Product-specific
    "ประกันชีวิตและสุขภาพ": ["ประกันชีวิตรวมสุขภาพ", "ประกันทั้งชีวิตและสุขภาพ", "ประกันครอบคลุมชีวิตและสุขภาพ"],
    "RMF และ ThaiESG": ["กองทุน RMF กับ ThaiESG", "RMF ร่วมกับ ThaiESG", "กองทุน RMF และ ThaiESG"],
    "ประกันและกองทุน": ["ประกันร่วมกับกองทุน", "ประกันกับกองทุนรวม", "ประกันและกองทุนรวม"],
    "ประกันและกองทุนรวม": ["ประกันร่วมกับกองทุน", "ประกันกับกองทุน", "ประกันรวมกับกองทุนรวม"],
}


def _generate_paraphrase(description: str) -> str:
    """สร้าง paraphrase จาก description โดยใช้ pattern matching"""
    import random
    result = description
    for pattern, replacements in _PARAPHRASE_PATTERNS.items():
        if pattern in result:
            replacement = random.choice(replacements)
            result = result.replace(pattern, replacement, 1)
            break  # Replace only 1 pattern per paraphrase to keep it natural
    return result


def _generate_keyword_based_description(description: str, keywords: list) -> str:
    """สร้าง description ทางเลือกจาก keywords"""
    if not keywords:
        return description
    # Build a sentence from keywords
    kw_text = " ".join(keywords[:4])
    # Detect plan type from description
    if any(w in description for w in ["คุ้มครอง", "ประกัน", "ปลอดภัย", "มั่นคง"]):
        return f"เน้นด้าน {kw_text} สร้างความมั่นคงทางการเงิน"
    elif any(w in description for w in ["สมดุล", "กระจาย", "ผสม"]):
        return f"สมดุลระหว่าง {kw_text} เพื่อกระจายความเสี่ยง"
    elif any(w in description for w in ["ลดหย่อน", "ภาษี", "วงเงิน", "สูงสุด", "เติบโต"]):
        return f"เน้น {kw_text} เพื่อผลประโยชน์ทางภาษีสูงสุด"
    return f"{kw_text} สำหรับการวางแผนภาษีที่เหมาะสม"


def enrich_profile_with_multi_references(expected_plans: Dict[str, Any]) -> Dict[str, Any]:
    """
    เพิ่ม descriptions (multi-reference) ให้ expected_plans ของแต่ละ profile
    ใช้ auto-paraphrase จาก description เดิม + keyword-based description
    """
    import random
    random.seed(42)  # Reproducible results

    for plan_key in ['plan_1', 'plan_2', 'plan_3']:
        plan = expected_plans.get(plan_key, {})
        exp_text = plan.get('expected_text', {})
        desc = exp_text.get('description', '')
        keywords = exp_text.get('keywords', [])

        if desc and 'descriptions' not in exp_text:
            paraphrase1 = _generate_paraphrase(desc)
            paraphrase2 = _generate_keyword_based_description(desc, keywords)

            # Ensure all 3 are unique
            descriptions = [desc]
            if paraphrase1 != desc:
                descriptions.append(paraphrase1)
            if paraphrase2 != desc and paraphrase2 != paraphrase1:
                descriptions.append(paraphrase2)

            exp_text['descriptions'] = descriptions

    return expected_plans


if __name__ == "__main__":
    print_profile_summary()
    print(f"\n📋 PROFILE_EXPECTED_PLANS: {len(PROFILE_EXPECTED_PLANS)} profiles configured.")