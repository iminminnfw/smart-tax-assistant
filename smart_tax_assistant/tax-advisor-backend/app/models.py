"""
Pydantic Models
Version: ปี 2568 - อัปเดตตามกฎหมายใหม่
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# ===================================
# Enums for Income and Business Types
# ===================================

class IncomeType(str, Enum):
    """ประเภทเงินได้ตามมาตรา 40"""
    SECTION_40_1 = "40(1)"  # เงินเดือน ค่าจ้าง
    SECTION_40_2 = "40(2)"  # ค่าจ้างทำของ ค่าธรรมเนียม ค่านายหน้า
    SECTION_40_3 = "40(3)"  # ค่าแห่งกู๊ดวิลล์ ค่าลิขสิทธิ์
    SECTION_40_4 = "40(4)"  # ดอกเบี้ย เงินปันผล
    SECTION_40_5 = "40(5)"  # ค่าเช่าทรัพย์สิน
    SECTION_40_6 = "40(6)"  # วิชาชีพอิสระ
    SECTION_40_7 = "40(7)"  # การรับเหมา
    SECTION_40_8 = "40(8)"  # เงินได้อื่นๆ (ธุรกิจ)

class ProfessionType(str, Enum):
    """ประเภทวิชาชีพอิสระ มาตรา 40(6)"""
    MEDICAL = "medical"  # การประกอบโรคศิลปะ (หัก 60%)
    LAW = "law"  # กฎหมาย (หัก 30%)
    ENGINEERING = "engineering"  # วิศวกรรม (หัก 30%)
    ARCHITECTURE = "architecture"  # สถาปัตยกรรม (หัก 30%)
    ACCOUNTING = "accounting"  # การบัญชี (หัก 30%)
    FINE_ARTS = "fine_arts"  # ประณีตศิลปกรรม (หัก 30%)
    OTHER = "other"  # วิชาชีพอื่นๆ (หัก 30%)

class BusinessType(str, Enum):
    """ประเภทธุรกิจ มาตรา 40(8) - 43 ประเภทตามตาราง"""
    # Entertainment (60% for first 300k, 40% over 300k, max 600k combined)
    ENTERTAINMENT = "entertainment"  # นักแสดง นักร้อง นักกีฬา

    # Standard 60% deduction businesses
    LAND_SALE = "land_sale"  # ขายที่ดินเงินผ่อน
    GAMBLING = "gambling"  # เก็บค่าต๋ง ค่าเกม
    PHOTOGRAPHY = "photography"  # ถ่าย ล้าง อัดรูป
    BOAT_REPAIR = "boat_repair"  # คานเรือ อู่เรือ ซ่อมเรือ
    LEATHER_GOODS = "leather_goods"  # รองเท้า เครื่องหนัง
    TAILORING = "tailoring"  # ตัด เย็บ ถัก ปักเสื้อผ้า
    FURNITURE = "furniture"  # ทำเครื่องเรือน
    HOTEL_RESTAURANT = "hotel_restaurant"  # โรงแรม ภัตตาคาร
    HAIR_SALON = "hair_salon"  # ดัด ตัด แต่งผม
    COSMETICS = "cosmetics"  # สบู่ แชมพู เครื่องสำอาง
    WRITING = "writing"  # ทำวรรณกรรม
    JEWELRY = "jewelry"  # เครื่องเงิน ทอง เพชร พลอย
    HOSPITAL = "hospital"  # สถานพยาบาล (มีเตียง)
    STONE_CRUSHING = "stone_crushing"  # โม่ ย่อยหิน
    FORESTRY = "forestry"  # ป่าไม้ สวนยาง ไม้ยืนต้น
    TRANSPORTATION = "transportation"  # ขนส่ง รับจ้างด้วยยานพาหนะ
    PRINTING = "printing"  # บล็อก ตรา รับพิมพ์
    MINING = "mining"  # ทำเหมืองแร่
    BEVERAGE = "beverage"  # เครื่องดื่มตามกฎหมายสรรพสามิต
    CERAMICS = "ceramics"  # กระเบื้อง เครื่องเคลือบ ซีเมนต์
    ELECTRICITY = "electricity"  # ทำหรือจำหน่ายไฟฟ้า
    ICE = "ice"  # ทำน้ำแข็ง
    GLUE_STARCH = "glue_starch"  # กาว แป้งเปียก แป้งชนิดต่างๆ
    BALLOONS_PLASTIC = "balloons_plastic"  # ลูกโป่ง แก้ว พลาสติก ยาง
    LAUNDRY = "laundry"  # ซักรีด ย้อมสี
    GENERAL_TRADE = "general_trade"  # ขายของทั่วไป (ไม่ใช่ผู้ผลิต)
    HORSE_RACING = "horse_racing"  # รางวัลจากการส่งม้าแข่ง
    PAWN = "pawn"  # รับสินไถ่ทรัพย์สินขายฝาก
    RUBBER = "rubber"  # รมยาง ทำยางแผ่น
    TANNING = "tanning"  # ฟอกหนัง
    SUGAR = "sugar"  # ทำน้ำตาล น้ำเหลือง
    FISHING = "fishing"  # จับสัตว์น้ำ
    SAWMILL = "sawmill"  # โรงเลื่อย
    OIL_REFINERY = "oil_refinery"  # กลั่น หีบน้ำมัน
    HIRE_PURCHASE = "hire_purchase"  # ให้เช่าซื้อสังหาริมทรัพย์
    RICE_MILL = "rice_mill"  # โรงสีข้าว
    AGRICULTURE = "agriculture"  # เกษตรกรรมไม้ล้มลุก ธัญชาติ
    TOBACCO = "tobacco"  # อบ บ่มใบยาสูบ
    LIVESTOCK = "livestock"  # เลี้ยงสัตว์ทุกชนิด
    SLAUGHTERHOUSE = "slaughterhouse"  # ฆ่าสัตว์จำหน่าย
    SALT = "salt"  # ทำนาเกลือ
    SHIP_SALE = "ship_sale"  # ขายเรือ กำปั่น เรือกลไฟ แพ
    OTHER_BUSINESS = "other_business"  # ธุรกิจอื่นๆ ที่ไม่ระบุ

class ExpenseMethod(str, Enum):
    """วิธีการหักค่าใช้จ่าย"""
    STANDARD = "standard"  # หักค่าใช้จ่ายแบบเหมา (ตามอัตรา)
    ACTUAL = "actual"  # หักค่าใช้จ่ายตามจริง (ต้องมีเอกสาร)


# ===================================
# Request Models (จัดหมวดหมู่ปี 2568)
# ===================================

class TaxCalculationRequest(BaseModel):
    """ข้อมูลรายได้และค่าลดหย่อน ปี 2568"""

    # รายได้และประเภทเงินได้ (ใหม่ - สำคัญสำหรับการคำนวณภาษีที่ถูกต้อง)
    gross_income: int = Field(..., description="รายได้รวม", ge=0)
    income_type: IncomeType = Field(
        IncomeType.SECTION_40_8,
        description="ประเภทเงินได้ตามมาตรา 40 (ใช้สำหรับคำนวณค่าใช้จ่าย)"
    )

    # ประเภทวิชาชีพ/ธุรกิจ (ใช้เมื่อ income_type เป็น 40(6) หรือ 40(8))
    profession_type: Optional[ProfessionType] = Field(
        None,
        description="ประเภทวิชาชีพอิสระ (สำหรับ มาตรา 40(6))"
    )
    business_type: Optional[BusinessType] = Field(
        BusinessType.GENERAL_TRADE,
        description="ประเภทธุรกิจ (สำหรับ มาตรา 40(8))"
    )

    # วิธีการหักค่าใช้จ่าย (ใหม่ - ตามกฎหมายภาษี)
    expense_method: ExpenseMethod = Field(
        ExpenseMethod.STANDARD,
        description="วิธีหักค่าใช้จ่าย: standard (เหมา) หรือ actual (ตามจริง)"
    )
    actual_expenses: int = Field(
        0,
        description="ค่าใช้จ่ายจริง (ถ้าเลือก expense_method = actual)",
        ge=0
    )
    
    # กลุ่มลดหย่อนส่วนตัว/ครอบครัว
    personal_deduction: int = Field(60000, description="ค่าลดหย่อนส่วนตัว", ge=0)
    spouse_deduction: int = Field(0, description="ค่าลดหย่อนคู่สมรส (ไม่มีรายได้)", ge=0, le=60000)
    child_deduction: int = Field(0, description="ค่าเลี้ยงดูบุตร (คนละ 30,000 ไม่จำกัดจำนวน)", ge=0)
    parent_support: int = Field(0, description="ค่าอุปการะเลี้ยงดูบิดามารดา (คนละ 30,000 สูงสุด 4 คน)", ge=0, le=120000)
    disabled_support: int = Field(0, description="ค่าอุปการะคนพิการ/ทุพพลภาพ (คนละ 60,000 ไม่จำกัด)", ge=0)
    
    # กลุ่มประกันชีวิตและสุขภาพ
    life_insurance: int = Field(0, description="เบี้ยประกันชีวิต", ge=0, le=100000)
    life_insurance_pension: int = Field(0, description="ประกันชีวิตแบบบำนาญ", ge=0, le=10000)
    life_insurance_parents: int = Field(0, description="เบี้ยประกันชีวิตบิดามารดา", ge=0, le=60000)
    health_insurance: int = Field(0, description="เบี้ยประกันสุขภาพ", ge=0, le=25000)
    health_insurance_parents: int = Field(0, description="เบี้ยประกันสุขภาพบิดามารดา (สูงสุด 4 คน)", ge=0, le=60000)
    social_security: int = Field(0, description="ประกันสังคม", ge=0, le=9000)
    
    # กลุ่มกองทุนและการลงทุน
    pension_insurance: int = Field(0, description="เบี้ยประกันบำนาญ", ge=0, le=200000)
    provident_fund: int = Field(0, description="กองทุนสำรองเลี้ยงชีพ (PVD)", ge=0, le=500000)
    gpf: int = Field(0, description="กองทุนบำเหน็จบำนาญข้าราชการ (กบข.)", ge=0, le=500000)
    pvd_teacher: int = Field(0, description="กองทุนสงเคราะห์ครูโรงเรียนเอกชน", ge=0, le=500000)
    rmf: int = Field(0, description="RMF", ge=0, le=500000)
    
    # กลุ่มกองทุน ESG (ใหม่ปี 2568 - แทน SSF)
    thai_esg: int = Field(0, description="กองทุน ThaiESG", ge=0, le=300000)
    thai_esgx_new: int = Field(0, description="กองทุน ThaiESGX (เงินใหม่)", ge=0, le=300000)
    thai_esgx_ltf: int = Field(0, description="กองทุน ThaiESGX (สะสมจาก LTF)", ge=0, le=300000)
    
    # กลุ่มอื่นๆ (ใหม่ปี 2568)
    stock_investment: int = Field(0, description="ลงทุนหุ้นจดทะเบียนที่ออกใหม่", ge=0, le=100000)
    easy_e_receipt: int = Field(0, description="Easy e-Receipt", ge=0, le=50000)
    home_loan_interest: int = Field(0, description="ดอกเบี้ยเงินกู้ซื้อ/สร้างบ้าน (2567-2568)", ge=0, le=100000)
    nsf: int = Field(0, description="กองทุนการออมแห่งชาติ (กอช.)", ge=0, le=30000)
    
    # กลุ่มเงินบริจาค
    donation_general: int = Field(0, description="เงินบริจาคทั่วไป", ge=0)
    donation_education: int = Field(0, description="เงินบริจาคเพื่อการศึกษา (นับ 2 เท่า)", ge=0)
    donation_social_enterprise: int = Field(0, description="บริจาค Social Enterprise", ge=0, le=100000)
    donation_political: int = Field(0, description="บริจาคพรรคการเมือง", ge=0, le=10000)
    
    # ระดับความเสี่ยง
    risk_tolerance: str = Field("medium", description="ระดับความเสี่ยง: low, medium, high")


# ===================================
# Response Models
# ===================================

class TaxCalculationResult(BaseModel):
    """ผลการคำนวณภาษี"""
    gross_income: int
    taxable_income: int
    tax_amount: int
    effective_tax_rate: float


class AllocationItem(BaseModel):
    """รายการการจัดสรรในแต่ละแผน"""
    category: str = Field(..., description="ประเภทการลงทุน")
    investment_amount: Optional[int] = Field(None, description="จำนวนเงิน")
    percentage: float = Field(..., description="สัดส่วน %")
    tax_saving: Optional[int] = Field(None, description="ภาษีที่ประหยัด")
    risk_level: str = Field(..., description="ระดับความเสี่ยง")
    pros: List[str] = Field(..., description="ข้อดี")
    cons: List[str] = Field(..., description="ข้อเสีย")


class InvestmentPlan(BaseModel):
    """แผนการลงทุนแต่ละแผน"""
    plan_id: str = Field(..., description="รหัสแผน A, B, C")
    plan_name: str = Field(..., description="ชื่อแผน")
    plan_type: str = Field(..., description="ประเภทแผน: conservative, moderate, aggressive")
    description: str = Field(..., description="คำอธิบายแผน")
    total_investment: int = Field(..., description="เงินลงทุนรวม")
    total_tax_saving: int = Field(..., description="ภาษีที่ประหยัดรวม")
    overall_risk: str = Field(..., description="ความเสี่ยงโดยรวม")
    allocations: List[AllocationItem] = Field(..., description="รายการการจัดสรร")


class MultiplePlansResponse(BaseModel):
    """Response ที่มีหลายแผนการลงทุน"""
    plans: List[InvestmentPlan] = Field(..., description="แผนการลงทุนทั้งหมด")


class TaxCalculationResponse(BaseModel):
    """Response สำหรับ API"""
    tax_result: TaxCalculationResult = Field(..., description="ผลการคำนวณภาษี")
    investment_plans: MultiplePlansResponse = Field(..., description="แผนการลงทุนทั้งหมด")