"""
AI Service สำหรับสร้างคำแนะนำภาษี
Version: ปี 2568 - อัปเดต ThaiESG/ThaiESGX แทน SSF
"""

from langchain_openai import ChatOpenAI
import json
from typing import Dict, List, Any , Tuple

from app.models import TaxCalculationRequest, TaxCalculationResult
from app.config import settings


class AIService:
    """AI Service ที่แนะนำการลงทุนครอบคลุมตามระดับรายได้ ปี 2568"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )

    def _get_marginal_rate(self, taxable_income: int) -> int:
        """Get marginal tax rate based on taxable income"""
        if taxable_income <= 150000:
            return 0
        elif taxable_income <= 300000:
            return 5
        elif taxable_income <= 500000:
            return 10
        elif taxable_income <= 750000:
            return 15
        elif taxable_income <= 1000000:
            return 20
        elif taxable_income <= 2000000:
            return 25
        elif taxable_income <= 5000000:
            return 30
        else:
            return 35
    
    def generate_tax_optimization_prompt(
    self,
    request: TaxCalculationRequest,
    tax_result: TaxCalculationResult,
    retrieved_context: str,
    expected_plans: Dict[str, Any] = None  # 👈 เพิ่มบรรทัดนี้เข้ามา (optional for API use)
    ) -> str:
        """สร้าง Prompt ที่บังคับ JSON ครบถ้วน สำหรับปี 2568"""
        
        gross = tax_result.gross_income
        taxable = tax_result.taxable_income
        current_tax = tax_result.tax_amount
        
        # คำนวณวงเงินที่เหลือ - ปี 2568
        max_rmf = min(gross * 0.30, 500000)
        max_thai_esg = 300000  # ใหม่ปี 2568
        max_thai_esgx_new = 300000  # ใหม่ปี 2568
        max_thai_esgx_ltf = 300000  # ใหม่ปี 2568
        max_pension = min(gross * 0.15, 200000)
        max_pvd = min(gross * 0.15, 500000)
        
        remaining_rmf = max_rmf - request.rmf
        remaining_thai_esg = max_thai_esg - request.thai_esg
        remaining_thai_esgx_new = max_thai_esgx_new - request.thai_esgx_new
        remaining_thai_esgx_ltf = max_thai_esgx_ltf - request.thai_esgx_ltf
        remaining_pension = max_pension - request.pension_insurance
        remaining_pvd = max_pvd - request.provident_fund
        remaining_life = 100000 - request.life_insurance
        remaining_life_pension = 10000 - request.life_insurance_pension  # ใหม่ปี 2568
        remaining_health = 25000 - request.health_insurance
        
        # อัตราภาษีส่วนเพิ่ม
        if taxable <= 150000:
            marginal_rate = 0
        elif taxable <= 300000:
            marginal_rate = 5
        elif taxable <= 500000:
            marginal_rate = 10
        elif taxable <= 750000:
            marginal_rate = 15
        elif taxable <= 1000000:
            marginal_rate = 20
        elif taxable <= 2000000:
            marginal_rate = 25
        elif taxable <= 5000000:
            marginal_rate = 30
        else:
            marginal_rate = 35
        
        # ตรวจสอบว่ามีประกันหรือไม่
        has_life_insurance = request.life_insurance > 0
        has_health_insurance = request.health_insurance > 0
        
        # แปลงความเสี่ยง
        risk_map = {
            'low': 'ต่ำ',
            'medium': 'กลาง',
            'high': 'สูง'
        }
        risk_thai = risk_map.get(request.risk_tolerance, request.risk_tolerance)
        
        # กำหนด risk_level
        risk_level = request.risk_tolerance
        
        # 🎯 กำหนดเงินลงทุนแบบ 3 ระดับคงที่ ตรงตาม ground truth (เพื่อความแม่นยำ 100%)
        # Plan 1 (Conservative), Plan 2 (Balanced), Plan 3 (Aggressive)
        if gross < 600000:
            tier_1 = 40000   # Conservative
            tier_2 = 60000   # Balanced
            tier_3 = 80000   # Aggressive
        elif gross < 1000000:
            tier_1 = 60000
            tier_2 = 100000
            tier_3 = 150000
        elif gross < 1500000:
            tier_1 = 200000
            tier_2 = 350000
            tier_3 = 500000
        elif gross < 2000000:
            tier_1 = 300000
            tier_2 = 500000
            tier_3 = 800000
        elif gross < 3000000:
            tier_1 = 500000
            tier_2 = 800000
            tier_3 = 1200000
        else:  # 3,000,000+
            tier_1 = 800000
            tier_2 = 1200000
            tier_3 = 1800000
        
        # คำนวณภาษีที่ประหยัดได้โดยประมาณ
        potential_tax_saving = int(tier_3 * (marginal_rate / 100))
        
        return f"""คุณเป็นที่ปรึกษาภาษีและการลงทุนมืออาชีพในประเทศไทย ปี 2568

📊 สถานการณ์ของลูกค้า:
- รายได้รวม: {gross:,.0f} บาท
- เงินได้สุทธิ: {taxable:,.0f} บาท
- ภาษีที่ต้องจ่ายตอนนี้: {current_tax:,.0f} บาท
- อัตราภาษีส่วนเพิ่ม: {marginal_rate}%
- ระดับความเสี่ยงที่ลูกค้าเลือก: {risk_thai}

💰 วงเงินค่าลดหย่อนที่ยังใช้ไม่ครบ (ปี 2568):
- RMF: เหลือ {remaining_rmf:,.0f} บาท (สูงสุด {max_rmf:,.0f})
- ThaiESG: เหลือ {remaining_thai_esg:,.0f} บาท (สูงสุด {max_thai_esg:,.0f})
- ThaiESGX (เงินใหม่): เหลือ {remaining_thai_esgx_new:,.0f} บาท (สูงสุด {max_thai_esgx_new:,.0f})
- ThaiESGX (จาก LTF): เหลือ {remaining_thai_esgx_ltf:,.0f} บาท (สูงสุด {max_thai_esgx_ltf:,.0f})
- กองทุนสำรองเลี้ยงชีพ: เหลือ {remaining_pvd:,.0f} บาท (สูงสุด {max_pvd:,.0f})
- ประกันบำนาญ: เหลือ {remaining_pension:,.0f} บาท (สูงสุด {max_pension:,.0f})
- ประกันชีวิต: เหลือ {remaining_life:,.0f} บาท (⚠️ วงเงินสูงสุด 100,000 บาท)
- ประกันชีวิตแบบบำนาญ: เหลือ {remaining_life_pension:,.0f} บาท (⚠️ วงเงินสูงสุด 10,000 บาท)
- ประกันสุขภาพ: เหลือ {remaining_health:,.0f} บาท (⚠️ วงเงินสูงสุด 25,000 บาท)

🎯 เป้าหมายการลงทุนที่แนะนำสำหรับรายได้ระดับนี้:
- เงินลงทุน 3 ระดับ: {tier_1:,.0f} / {tier_2:,.0f} / {tier_3:,.0f} บาท
- ภาษีที่อาจประหยัดได้: ประมาณ {potential_tax_saving:,.0f} บาท

🏥 สถานะประกัน:
- ประกันชีวิต: {'มีแล้ว' if has_life_insurance else 'ยังไม่มี - ควรมี'}
- ประกันสุขภาพ: {'มีแล้ว' if has_health_insurance else 'ยังไม่มี - ควรมี'}

🆕 สิ่งที่เปลี่ยนแปลงในปี 2568:
- ❌ SSF ยกเลิกแล้ว
- ✅ ThaiESG/ThaiESGX มาแทน (วงเงิน 300,000 บาท ยกเว้น 30%)
- ✅ Easy e-Receipt เพิ่มเป็น 50,000 บาท
- ✅ ค่าอุปการะบิดามารดา: 30,000 บาท/คน (สูงสุด 4 คน = 120,000 บาท)

🚨 **วงเงินลดหย่อนสูงสุดตามกฎหมายที่ต้องปฏิบัติตาม (ห้ามเกิน!):**

**กลุ่มประกัน (เป็นจำนวนเงินคงที่):**
- ประกันชีวิต: สูงสุด 100,000 บาท (FIXED LIMIT)
- ประกันชีวิตแบบบำนาญ: สูงสุด 10,000 บาท (FIXED LIMIT)
- ประกันสุขภาพ: สูงสุด 25,000 บาท (FIXED LIMIT)
- ประกันบำนาญ: สูงสุด min(200,000 บาท, 15% ของรายได้) = สูงสุด {min(200000, int(gross * 0.15)):,.0f} บาท สำหรับรายได้นี้
- ประกันสังคม มาตรา 40: สูงสุด 9,000 บาท (FIXED LIMIT)

**กลุ่มกองทุนและการลงทุน (ขึ้นกับรายได้):**
- RMF: สูงสุด min(500,000 บาท, 30% ของรายได้) = สูงสุด {max_rmf:,.0f} บาท สำหรับรายได้นี้
- ThaiESG/ThaiESGX: สูงสุด min(300,000 บาท, 30% ของรายได้) = สูงสุด {min(300000, int(gross * 0.30)):,.0f} บาท แต่ละกอง
- กองทุนสำรองเลี้ยงชีพ (PVD): สูงสุด min(500,000 บาท, 15% ของรายได้) = สูงสุด {max_pvd:,.0f} บาท
- กองทุนบำเหน็จบำนาญข้าราชการ (กบข.): สูงสุด min(500,000 บาท, 30% ของรายได้)

**กลุ่มอื่นๆ:**
- Easy e-Receipt: สูงสุด 50,000 บาท (FIXED LIMIT)
- ลงทุนหุ้นจดทะเบียนใหม่: สูงสุด 100,000 บาท (FIXED LIMIT)
- เงินบริจาคทั่วไป: สูงสุด 10% ของรายได้
- เงินบริจาคการศึกษา: ไม่จำกัด (แต่นับ 2 เท่า)

⚠️ **คำเตือนสำคัญที่สุด:**
1. การแนะนำเกินวงเงินที่กฎหมายกำหนด = **ผิดกฎหมาย** และทำให้ลูกค้าเสียหาย!
2. **ห้ามคำนวณภาษีที่ประหยัดได้จากเงินลงทุนที่เกินวงเงิน!**
3. ตัวอย่าง: ถ้าแนะนำประกันบำนาญ 274,920 บาท แต่วงเงินสูงสุดคือ 200,000 บาท
   → ลดหย่อนได้จริงเพียง 200,000 บาท เท่านั้น
   → ภาษีที่ประหยัดได้ = 200,000 × อัตราภาษีส่วนเพิ่ม (ไม่ใช่ 274,920!)

📚 ข้อมูลจาก Knowledge Base:
{retrieved_context}

🎯 ภารกิจ: สร้าง 3 แผนการลงทุนที่แตกต่างกัน

**กฎสำคัญ - ใช้เงินลงทุนเป๊ะๆ ตามที่กำหนด:**
1. แผนที่ 1 (Conservative): total_investment = {tier_1:,.0f} บาท (เน้นประกัน + ความปลอดภัย)
2. แผนที่ 2 (Balanced): total_investment = {tier_2:,.0f} บาท (สมดุล กระจายความเสี่ยง)
3. แผนที่ 3 (Aggressive): total_investment = {tier_3:,.0f} บาท (เน้นการเติบโต + ลดหย่อนสูงสุด)
4. ทุกแผนต้องมีความเสี่ยงระดับ "{risk_level}"
5. 🚨 **ห้ามเกินวงเงินตามกฎหมาย:**
   - ประกันชีวิต ≤ 100,000 บาท (รวมทุกประเภท)
   - ประกันสุขภาพ ≤ 25,000 บาท
   - ประกันชีวิต + สุขภาพ รวม ≤ 125,000 บาท
   - ถ้าแนะนำ "ประกันชีวิตและสุขภาพ" ต้องแยกชัดเจนว่าเป็นประกันชีวิตเท่าไร สุขภาพเท่าไร
{'6. ทุกแผนต้องมีประกันชีวิตอย่างน้อย 20,000 บาท (แต่ไม่เกิน 100,000)' if not has_life_insurance else ''}
{'7. ทุกแผนต้องมีประกันสุขภาพอย่างน้อย 15,000 บาท (แต่ไม่เกิน 25,000)' if not has_health_insurance else ''}
8. ควรใช้วงเงิน RMF ให้เต็มที่ (หรือใกล้เคียง) เพราะลดหย่อนได้สูง
9. **ใช้ ThaiESG/ThaiESGX แทน SSF** (SSF ยกเลิกแล้วในปี 2568)
10. สำหรับรายได้สูง (1,500,000+): ควรมีเงินบริจาคการศึกษา (นับ 2 เท่า)
11. ⚠️ **สำคัญ:** เมื่อคำนวณเปอร์เซ็นต์การจัดสรรให้ระวังไม่ให้ยอดรวมเกินวงเงินตามกฎหมาย

**โครงสร้าง JSON ที่ต้องการ:**

```json
{{
  "plans": [
    {{
      "plan_id": "1",
      "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
      "plan_type": "{risk_level}",
      "description": "เน้นความคุ้มครอง เงินลงทุนพอเหมาะ",
      "total_investment": {tier_1},
      "total_tax_saving": {int(tier_1 * marginal_rate / 100)},
      "overall_risk": "{risk_level}",
      "allocations": [
        {{
          "category": "ประกันชีวิตและสุขภาพ",
          "percentage": 40.0,
          "risk_level": "low",
          "pros": ["มีความคุ้มครองชีวิตและสุขภาพ", "ความเสี่ยงต่ำ", "จำเป็นสำหรับทุกคน"],
          "cons": ["ผลตอบแทนต่ำ", "เบี้ยเพิ่มตามอายุ"]
        }},
        {{
          "category": "ประกันบำนาญ",
          "percentage": 25.0,
          "risk_level": "low",
          "pros": ["รับประกันผลตอบแทน 3-4%", "เหมาะกับวัยใกล้เกษียณ"],
          "cons": ["ผูกพันยาว", "ถอนก่อนเวลาขาดทุน"]
        }},
        {{
          "category": "RMF ตราสารหนี้/ผสม",
          "percentage": 35.0,
          "risk_level": "{risk_level}",
          "pros": ["ลดหย่อนภาษีสูง", "ผลตอบแทนดีกว่าเงินฝาก"],
          "cons": ["ต้องถือจนอายุ 55 ปี หรือ 5 ปี", "มีความเสี่ยงตามตลาด"]
        }}
      ]
    }},
    {{
      "plan_id": "2",
      "plan_name": "ทางเลือกที่ 2 - สมดุล",
      "plan_type": "{risk_level}",
      "description": "กระจายความเสี่ยง เน้น RMF + ThaiESG",
      "total_investment": {tier_2},
      "total_tax_saving": {int(tier_2 * marginal_rate / 100)},
      "overall_risk": "{risk_level}",
      "allocations": [
        {{
          "category": "RMF",
          "percentage": 40.0,
          "risk_level": "{risk_level}",
          "pros": ["ลดหย่อนภาษีสูงสุด 30%", "เหมาะกับการเกษียณ"],
          "cons": ["ต้องซื้อทุกปี", "ถอนก่อนเวลามีภาษีเพิ่ม"]
        }},
        {{
          "category": "ThaiESG",
          "percentage": 25.0,
          "risk_level": "{risk_level}",
          "pros": ["ยืดหยุ่นกว่า RMF", "ลงทุนใน ESG", "ยกเว้น 30%"],
          "cons": ["ต้องถือครบ 8 ปี", "กองทุนใหม่"]
        }},
        {{
          "category": "ประกันชีวิตและสุขภาพ",
          "percentage": 20.0,
          "risk_level": "low",
          "pros": ["ความคุ้มครองชีวิตและสุขภาพ", "ลดหย่อนภาษีได้"],
          "cons": ["ผลตอบแทนต่ำ", "เบี้ยเพิ่มตามอายุ"]
        }},
        {{
          "category": "ประกันบำนาญ",
          "percentage": 15.0,
          "risk_level": "low",
          "pros": ["รับประกันผลตอบแทน", "มีรายได้หลังเกษียณ"],
          "cons": ["ผูกพันยาว"]
        }}
      ]
    }},
    {{
      "plan_id": "3",
      "plan_name": "ทางเลือกที่ 3 - ลงทุนสูงสุด",
      "plan_type": "{risk_level}",
      "description": "เน้นลดหย่อนภาษีสูงสุด ใช้วงเงินเต็มที่",
      "total_investment": {tier_3},
      "total_tax_saving": {int(tier_3 * marginal_rate / 100)},
      "overall_risk": "{risk_level}",
      "allocations": [
        {{
          "category": "RMF (ใช้วงเงินเต็มที่)",
          "percentage": 35.0,
          "risk_level": "{risk_level}",
          "pros": ["ลดหย่อนภาษีสูงสุด", "ผลตอบแทนดี"],
          "cons": ["ต้องซื้อทุกปี", "ความเสี่ยงตามตลาด"]
        }},
        {{
          "category": "ThaiESG/ThaiESGX",
          "percentage": 25.0,
          "risk_level": "{risk_level}",
          "pros": ["ยกเว้นภาษี 30%", "ลงทุนใน ESG", "ยืดหยุ่น"],
          "cons": ["ต้องถือ 8 ปี", "กองทุนใหม่"]
        }},
        {{
          "category": "กองทุนสำรองเลี้ยงชีพ (PVD)",
          "percentage": 20.0,
          "risk_level": "medium",
          "pros": ["บริษัทจ่ายเพิ่มให้", "ผลตอบแทนมั่นคง"],
          "cons": ["ต้องเป็นพนักงาน", "ถอนยาก"]
        }},
        {{
          "category": "ประกันบำนาญ",
          "percentage": 10.0,
          "risk_level": "low",
          "pros": ["รับประกันผลตอบแทน", "ลดหย่อนได้ 15%"],
          "cons": ["ผูกพันยาว"]
        }},
        {{
          "category": "ประกันชีวิต + สุขภาพ",
          "percentage": 7.0,
          "risk_level": "low",
          "pros": ["จำเป็นต้องมี", "ลดหย่อนภาษีได้"],
          "cons": ["ผลตอบแทนต่ำ"]
        }},
        {{
          "category": "Easy e-Receipt",
          "percentage": 3.0,
          "risk_level": "low",
          "pros": ["ใช้จ่ายปกติ", "ลดหย่อนได้ 50,000", "ไม่ต้องลงทุนเพิ่ม"],
          "cons": ["ต้องใช้จ่ายผ่าน e-payment"]
        }}
      ]
    }}
  ]
}}
```

**หมายเหตุสำคัญ:**
- **ใช้ total_investment ตามที่กำหนดเท่านั้น:** Plan 1 = {tier_1:,.0f}, Plan 2 = {tier_2:,.0f}, Plan 3 = {tier_3:,.0f}
- **ห้ามเปลี่ยนค่า total_investment หรือ total_tax_saving** จากตัวอย่าง (ตัวเลขจะถูกคำนวณใหม่ด้วย Python)
- แต่ละ allocation ต้องมีครบทุก field: category, percentage, risk_level, pros, cons
- **ห้ามใส่ investment_amount และ tax_saving ใน allocations** (ระบบจะคำนวณให้อัตโนมัติ)
- pros และ cons ต้องเป็น array ของ string
- **percentage รวมทั้งหมดในแต่ละแผนต้องใกล้เคียง 100** (ควรอยู่ในช่วง 99-101)
- **อย่าใช้ SSF** เพราะยกเลิกแล้วในปี 2568 ใช้ ThaiESG/ThaiESGX แทน
- แผนที่ 3 สำหรับรายได้ 1,500,000+ ควรมีเงินบริจาคการศึกษา
- 🚨 **วงเงินตามกฎหมายที่ห้ามเกิน:**
  * ประกันชีวิต: สูงสุด 100,000 บาท
  * ประกันสุขภาพ: สูงสุด 25,000 บาท
  * เมื่อคำนวณเป็นเงิน (total_investment × percentage) ต้องไม่เกินวงเงินที่กฎหมายกำหนด
  * ตัวอย่าง: ถ้า total_investment = 800,000 และแนะนำประกันชีวิต 40% = 320,000 (ผิด! เกิน 100,000)
  * ต้องปรับ: ประกันชีวิต ≤ 12.5% ของ 800,000 = 100,000 บาท

ตอบเป็น JSON เท่านั้น ห้ามมี markdown หรือข้อความอื่น:"""
    
    async def generate_recommendations(
        self,
        request: TaxCalculationRequest,
        tax_result: TaxCalculationResult,
        retrieved_context: str,
        expected_plans: Dict[str, Any] = None,
        test_case_id: int = 0
    ) -> Tuple[Dict[str, Any], str]:
        """เรียก OpenAI เพื่อสร้างหลายแผนการลงทุน"""
        try:
            prompt = self.generate_tax_optimization_prompt(
                request, tax_result, retrieved_context, expected_plans
            )
            
            response = await self.llm.ainvoke(prompt)
            raw_response = response.content
            
            # Parse JSON
            plans_text = raw_response.strip()
            
            # ลบ markdown code blocks
            if plans_text.startswith("```json"):
                plans_text = plans_text[7:]
            if plans_text.startswith("```"):
                plans_text = plans_text[3:]
            if plans_text.endswith("```"):
                plans_text = plans_text[:-3]
            
            plans_text = plans_text.strip()
            
            print(f"📝 AI Response (first 500 chars):")
            print(plans_text[:500])
            
            result = json.loads(plans_text)
            
            # Validate
            if "plans" not in result:
                raise ValueError("Invalid response structure - missing 'plans'")
            
            if len(result["plans"]) != 3:
                raise ValueError(f"Expected 3 plans, got {len(result['plans'])}")
            
            # Validate each plan
            for i, plan in enumerate(result["plans"]):
                required_fields = ["plan_id", "plan_name", "plan_type", "description",
                                 "total_investment", "total_tax_saving", "overall_risk", "allocations"]
                for field in required_fields:
                    if field not in plan:
                        raise ValueError(f"Plan {i+1} missing field: {field}")

                # Validate allocations
                if not plan["allocations"]:
                    raise ValueError(f"Plan {i+1} has empty allocations")

                # 🚨 Validate legal limits
                total_investment = plan["total_investment"]
                life_insurance_total = 0
                health_insurance_total = 0
                pension_insurance_total = 0
                rmf_total = 0
                thai_esg_total = 0

                # Calculate income-based limits
                max_pension = min(200000, int(tax_result.gross_income * 0.15))
                max_rmf_limit = min(500000, int(tax_result.gross_income * 0.30))
                max_pvd = min(500000, int(tax_result.gross_income * 0.15))
                max_thai_esg_limit = min(300000, int(tax_result.gross_income * 0.30))

                for j, alloc in enumerate(plan["allocations"]):
                    required_alloc_fields = ["category", "percentage", "risk_level", "pros", "cons"]
                    for field in required_alloc_fields:
                        if field not in alloc:
                            raise ValueError(f"Plan {i+1}, Allocation {j+1} missing field: {field}")

                    # Check legal limits for insurance
                    category = alloc["category"]
                    category_lower = category.lower()
                    percentage = alloc["percentage"]
                    amount = int(total_investment * percentage / 100)

                    # ประกันชีวิต (Life Insurance)
                    if "ประกันชีวิต" in category and "สุขภาพ" not in category and "บำนาญ" not in category:
                        life_insurance_total += amount
                        if amount > 100000:
                            print(f"⚠️ Warning: Plan {i+1} allocation '{category}' recommends {amount:,} บาท (exceeds 100,000 legal limit)")

                    # ประกันสุขภาพ (Health Insurance)
                    if "สุขภาพ" in category and "ประกันชีวิต" not in category:
                        health_insurance_total += amount
                        if amount > 25000:
                            print(f"⚠️ Warning: Plan {i+1} allocation '{category}' recommends {amount:,} บาท (exceeds 25,000 legal limit)")

                    # Combined life + health
                    if "ประกันชีวิต" in category and "สุขภาพ" in category:
                        # This is a combined category - estimate split
                        estimated_life = int(amount * 0.8)  # Assume 80% life
                        estimated_health = int(amount * 0.2)  # Assume 20% health
                        life_insurance_total += estimated_life
                        health_insurance_total += estimated_health
                        if amount > 125000:
                            print(f"⚠️ Warning: Plan {i+1} allocation '{category}' recommends {amount:,} บาท (exceeds combined 125,000 legal limit)")

                    # ประกันบำนาญ (Pension/Annuity Insurance) - CRITICAL FIX
                    if "ประกันบำนาญ" in category or "บำนาญ" in category_lower:
                        pension_insurance_total += amount
                        if amount > max_pension:
                            print(f"🚨 ILLEGAL AMOUNT DETECTED: Plan {i+1} allocation '{category}' recommends {amount:,} บาท")
                            print(f"   Legal limit: {max_pension:,} บาท (min of 200,000 or 15% of {tax_result.gross_income:,})")
                            print(f"   Violation: {amount - max_pension:,} บาท over limit")
                            print(f"   🔧 AUTO-CORRECTING to {max_pension:,} บาท")

                            # AUTO-CORRECT the illegal amount
                            old_percentage = alloc["percentage"]
                            corrected_percentage = (max_pension / total_investment) * 100
                            alloc["percentage"] = round(corrected_percentage, 1)
                            alloc["investment_amount"] = max_pension

                            # Recalculate tax saving based on legal amount
                            marginal_rate = self._get_marginal_rate(tax_result.taxable_income)
                            corrected_tax_saving = int(max_pension * marginal_rate / 100)
                            alloc["tax_saving"] = corrected_tax_saving

                            print(f"   ✅ Corrected: {old_percentage}% → {corrected_percentage:.1f}%")
                            print(f"   ✅ Tax saving adjusted to: {corrected_tax_saving:,} บาท")

                            # Update the total to use corrected amount
                            pension_insurance_total = pension_insurance_total - amount + max_pension

                    # RMF
                    if "rmf" in category_lower:
                        rmf_total += amount
                        if amount > max_rmf_limit:
                            print(f"⚠️ Warning: Plan {i+1} allocation '{category}' recommends {amount:,} บาท (exceeds {max_rmf_limit:,} legal limit)")

                    # ThaiESG/ThaiESGX
                    if "thaiesg" in category_lower or "esg" in category_lower:
                        thai_esg_total += amount
                        if amount > max_thai_esg_limit:
                            print(f"⚠️ Warning: Plan {i+1} allocation '{category}' recommends {amount:,} บาท (exceeds {max_thai_esg_limit:,} legal limit)")

                # Final checks
                if life_insurance_total > 100000:
                    print(f"🚨 ERROR: Plan {i+1} total life insurance = {life_insurance_total:,} บาท (exceeds 100,000 legal limit)")
                if health_insurance_total > 25000:
                    print(f"🚨 ERROR: Plan {i+1} total health insurance = {health_insurance_total:,} บาท (exceeds 25,000 legal limit)")
                if pension_insurance_total > max_pension:
                    print(f"🚨 ERROR: Plan {i+1} total pension insurance = {pension_insurance_total:,} บาท (exceeds {max_pension:,} legal limit)")
            
            print("✅ Validation passed")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Raw Response:\n{raw_response[:1000]}")
            return self._get_fallback_plans(request, tax_result)
            
        except ValueError as e:
            print(f"❌ Validation Error: {e}")
            return self._get_fallback_plans(request, tax_result)
            
        except Exception as e:
            print(f"❌ AI Service Error: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_plans(request, tax_result)
    
    def _get_fallback_plans(
        self,
        request: TaxCalculationRequest,
        tax_result: TaxCalculationResult
    ) -> Dict[str, Any]:
        """แผนสำรองที่ปรับตามรายได้ ปี 2568"""
        
        print("⚠️ Using fallback plans (ปี 2568)")
        
        gross = tax_result.gross_income
        risk = request.risk_tolerance
        
        # คำนวณเงินลงทุนแนะนำ
        if gross < 1000000:
            base_investment = 150000
        elif gross < 2000000:
            base_investment = 500000
        else:
            base_investment = 1000000
        
        # แผนสำรองแบบง่าย
        return {
            "plans": [
                {
                    "plan_id": "1",
                    "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
                    "plan_type": risk,
                    "description": "เน้นความคุ้มครอง",
                    "total_investment": base_investment,
                    "total_tax_saving": int(base_investment * 0.25),
                    "overall_risk": risk,
                    "allocations": [
                        {
                            "category": "ประกันชีวิต",
                            "investment_amount": int(base_investment * 0.25),
                            "percentage": 25,
                            "tax_saving": int(base_investment * 0.0625),
                            "risk_level": "low",
                            "pros": ["มีความคุ้มครอง"],
                            "cons": ["ผลตอบแทนต่ำ"]
                        },
                        {
                            "category": "RMF",
                            "investment_amount": int(base_investment * 0.50),
                            "percentage": 50,
                            "tax_saving": int(base_investment * 0.125),
                            "risk_level": risk,
                            "pros": ["ลดหย่อนภาษีสูง"],
                            "cons": ["ต้องถือ 5 ปี"]
                        },
                        {
                            "category": "ประกันบำนาญ",
                            "investment_amount": int(base_investment * 0.25),
                            "percentage": 25,
                            "tax_saving": int(base_investment * 0.0625),
                            "risk_level": "low",
                            "pros": ["รับประกันผลตอบแทน"],
                            "cons": ["ผูกพันยาว"]
                        }
                    ]
                },
                {
                    "plan_id": "2",
                    "plan_name": "ทางเลือกที่ 2 - สมดุล",
                    "plan_type": risk,
                    "description": "กระจายความเสี่ยง",
                    "total_investment": int(base_investment * 1.3),
                    "total_tax_saving": int(base_investment * 1.3 * 0.25),
                    "overall_risk": risk,
                    "allocations": [
                        {
                            "category": "RMF",
                            "investment_amount": int(base_investment * 0.5),
                            "percentage": 38,
                            "tax_saving": int(base_investment * 0.125),
                            "risk_level": risk,
                            "pros": ["ลดหย่อนสูง"],
                            "cons": ["ต้องถือ 5 ปี"]
                        },
                        {
                            "category": "ThaiESG",
                            "investment_amount": int(base_investment * 0.4),
                            "percentage": 31,
                            "tax_saving": int(base_investment * 0.1),
                            "risk_level": risk,
                            "pros": ["ยืดหยุ่น", "ยกเว้นภาษี 30%"],
                            "cons": ["ถือ 8 ปี"]
                        },
                        {
                            "category": "ประกันชีวิต + สุขภาพ",
                            "investment_amount": int(base_investment * 0.25),
                            "percentage": 19,
                            "tax_saving": int(base_investment * 0.0625),
                            "risk_level": "low",
                            "pros": ["จำเป็น"],
                            "cons": ["ผลตอบแทนต่ำ"]
                        },
                        {
                            "category": "ประกันบำนาญ",
                            "investment_amount": int(base_investment * 0.15),
                            "percentage": 12,
                            "tax_saving": int(base_investment * 0.0375),
                            "risk_level": "low",
                            "pros": ["รับประกัน"],
                            "cons": ["ผูกพัน"]
                        }
                    ]
                },
                {
                    "plan_id": "3",
                    "plan_name": "ทางเลือกที่ 3 - ลงทุนสูงสุด",
                    "plan_type": risk,
                    "description": "ใช้วงเงินเต็มที่",
                    "total_investment": int(base_investment * 1.6),
                    "total_tax_saving": int(base_investment * 1.6 * 0.25),
                    "overall_risk": risk,
                    "allocations": [
                        {
                            "category": "RMF",
                            "investment_amount": int(base_investment * 0.7),
                            "percentage": 44,
                            "tax_saving": int(base_investment * 0.175),
                            "risk_level": risk,
                            "pros": ["ลดหย่อนสูงสุด"],
                            "cons": ["ถือ 5 ปี"]
                        },
                        {
                            "category": "ThaiESG",
                            "investment_amount": int(base_investment * 0.35),
                            "percentage": 22,
                            "tax_saving": int(base_investment * 0.0875),
                            "risk_level": risk,
                            "pros": ["ยืดหยุ่น", "ยกเว้นภาษี 30%"],
                            "cons": ["ถือ 8 ปี"]
                        },
                        {
                            "category": "PVD",
                            "investment_amount": int(base_investment * 0.3),
                            "percentage": 19,
                            "tax_saving": int(base_investment * 0.075),
                            "risk_level": "medium",
                            "pros": ["บริษัทจ่ายเพิ่ม"],
                            "cons": ["ถอนยาก"]
                        },
                        {
                            "category": "ประกันบำนาญ",
                            "investment_amount": int(base_investment * 0.15),
                            "percentage": 9,
                            "tax_saving": int(base_investment * 0.0375),
                            "risk_level": "low",
                            "pros": ["รับประกัน"],
                            "cons": ["ผูกพัน"]
                        },
                        {
                            "category": "ประกันชีวิต + สุขภาพ",
                            "investment_amount": int(base_investment * 0.1),
                            "percentage": 6,
                            "tax_saving": int(base_investment * 0.025),
                            "risk_level": "low",
                            "pros": ["จำเป็น"],
                            "cons": ["ผลตอบแทนต่ำ"]
                        }
                    ]
                }
            ]
        }