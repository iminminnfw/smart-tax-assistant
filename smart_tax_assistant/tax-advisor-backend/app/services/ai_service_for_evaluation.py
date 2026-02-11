"""
AI Service สำหรับ Evaluation - ปี 2568 (ฉบับสมบูรณ์)
ใช้ Prompt เหมือนกับระบบหลักทุกประการ
แยกออกจากระบบหลัก เพื่อแสดง raw response และทำ evaluation

จุดประสงค์:
1. แสดง raw response จาก OpenAI เพื่อตรวจสอบคุณภาพ
2. บันทึก logs สำหรับวิเคราะห์
3. ทำ evaluation โดยไม่กระทบระบบหลัก
"""

from langchain_openai import ChatOpenAI
import json
import os
import time
import asyncio
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Import models และ config
from app.models import TaxCalculationRequest, TaxCalculationResult
from app.config import settings


class AIServiceForEvaluation:
    """
    AI Service แยกสำหรับ Evaluation
    
    ความแตกต่างจากระบบหลัก:
    - แสดง raw response
    - บันทึก logs
    - Verbose logging
    - ไม่กระทบระบบหลัก
    """
    
    def __init__(self, verbose: bool = True, save_to_file: bool = True):
        """
        Args:
            verbose: แสดงข้อความ debug
            save_to_file: บันทึก logs ลงไฟล์
        """
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # ใช้ค่าเดียวกับระบบหลัก
            openai_api_key=settings.openai_api_key
        )
        self.verbose = verbose
        self.save_to_file = save_to_file

        # 📊 Retry statistics tracking
        self.retry_stats = {
            "total_calls": 0,
            "successful_first_try": 0,
            "retries_needed": 0,
            "total_retries": 0,
            "fallback_used": 0,
            "refusal_detected": 0
        }

        # สร้างโฟลเดอร์สำหรับเก็บ logs
        if self.save_to_file:
            self.log_dir = Path(__file__).parent.parent.parent / "evaluation_logs"
            self.log_dir.mkdir(exist_ok=True)
            if self.verbose:
                print(f"📂 Log directory: {self.log_dir}")
    
    def generate_tax_optimization_prompt(
        self, 
        request: TaxCalculationRequest,
        tax_result: TaxCalculationResult,
        retrieved_context: str,
        expected_plans: Dict[str, Any]
    ) -> str:
        """
        สร้าง Prompt ที่เหมือนกับระบบหลักทุกประการ
        
        🔥 CRITICAL: Prompt นี้ต้องเหมือนกับ ai_service.py ในระบบหลัก
        """
        
        gross = tax_result.gross_income
        taxable = tax_result.taxable_income
        current_tax = tax_result.tax_amount
        
        # คำนวณวงเงินที่เหลือ - ปี 2568 (สำหรับ 40(6) และ 40(8) เท่านั้น)
        # หมายเหตุ: PVD/กบข./กบศ. ลบออกแล้ว (ใช้ได้เฉพาะ 40(1) เงินเดือน)
        max_rmf = min(gross * 0.30, 500000)
        max_thai_esg = 300000  # ใหม่ปี 2568
        max_thai_esgx_new = 300000  # ใหม่ปี 2568
        max_thai_esgx_ltf = 300000  # ใหม่ปี 2568
        max_pension = min(gross * 0.15, 200000)

        remaining_rmf = max_rmf - request.rmf
        remaining_thai_esg = max_thai_esg - request.thai_esg
        remaining_thai_esgx_new = max_thai_esgx_new - request.thai_esgx_new
        remaining_thai_esgx_ltf = max_thai_esgx_ltf - request.thai_esgx_ltf
        remaining_pension = max_pension - request.pension_insurance
        remaining_life = 100000 - request.life_insurance
        remaining_life_pension = 10000 - request.life_insurance_pension
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

        potential_tax_saving = int(tier_3 * (marginal_rate / 100))

        # 🎯 Define comprehensive pros/cons for all allocation categories
        ALLOCATION_PROS_CONS = {
            "RMF": {
                "pros": [
                    "ลดหย่อนภาษีได้สูงถึง 30% ของรายได้",
                    "ผลตอบแทนระยะยาวจากการลงทุนในตลาดทุน",
                    "เหมาะสำหรับการวางแผนเกษียณ"
                ],
                "cons": [
                    "ต้องถือจนอายุ 55 ปีหรือครบ 5 ปี",
                    "ต้องลงทุนต่อเนื่องทุกปี",
                    "มีความเสี่ยงจากตลาดหุ้น"
                ]
            },
            "SSF": {
                "pros": [
                    "ลดหย่อนภาษีได้สูง",
                    "ผลตอบแทนที่ดีจากการลงทุนระยะยาว",
                    "เหมาะสำหรับสะสมความมั่งคั่ง"
                ],
                "cons": [
                    "ต้องถือครองอย่างน้อย 10 ปี",
                    "มีความเสี่ยงจากตลาดหุ้น",
                    "ไม่สามารถถอนก่อนกำหนดได้"
                ]
            },
            "ThaiESG": {
                "pros": [
                    "ลดหย่อนภาษีได้ 30% สูงสุด 300,000 บาท",
                    "ลงทุนในบริษัทที่คำนึงถึงความยั่งยืน",
                    "ผลตอบแทนดีจากกองทุนหุ้นคุณภาพ"
                ],
                "cons": [
                    "ต้องถือครองอย่างน้อย 8 ปี",
                    "มีความเสี่ยงจากตลาดหุ้น",
                    "ทางเลือกกองทุนจำกัด"
                ]
            },
            "ThaiESGX": {
                "pros": [
                    "ลดหย่อนภาษีได้ 30% สูงสุด 300,000 บาท",
                    "รองรับเงินจาก LTF เดิม",
                    "ลงทุนในหุ้นที่มีความยั่งยืน"
                ],
                "cons": [
                    "ต้องถือครองอย่างน้อย 8 ปี",
                    "มีความเสี่ยงจากตลาดหุ้น",
                    "เป็นกองทุนใหม่ ข้อมูลผลตอบแทนในอดีตจำกัด"
                ]
            },
            "ประกันชีวิต": {
                "pros": [
                    "ให้ความคุ้มครองชีวิตและครอบครัว",
                    "ลดหย่อนภาษีได้สูงสุด 100,000 บาท",
                    "สร้างความมั่นใจทางการเงิน"
                ],
                "cons": [
                    "ผลตอบแทนจากการลงทุนต่ำ",
                    "ต้องจ่ายเบี้ยประกันต่อเนื่อง",
                    "ไม่เหมาะสำหรับการเติบโตของเงิน"
                ]
            },
            "ประกันสุขภาพ": {
                "pros": [
                    "คุ้มครองค่ารักษาพยาบาล",
                    "ลดหย่อนภาษีได้สูงสุด 25,000 บาท",
                    "จำเป็นสำหรับความปลอดภัยทางสุขภาพ"
                ],
                "cons": [
                    "เบี้ยประกันสูงขึ้นตามอายุ",
                    "ไม่ได้ผลตอบแทนจากการลงทุน",
                    "มีเงื่อนไขการรับประกัน"
                ]
            },
            "ประกันบำนาญ": {
                "pros": [
                    "รับประกันรายได้หลังเกษียณ",
                    "ลดหย่อนภาษีได้สูงสุด 15% หรือ 200,000 บาท",
                    "ผลตอบแทนที่แน่นอน"
                ],
                "cons": [
                    "ต้องถือครองจนถึงอายุที่กำหนด",
                    "ผลตอบแทนต่ำกว่าการลงทุนในตลาดทุน",
                    "สภาพคล่องต่ำ"
                ]
            },
            # หมายเหตุ: PVD/กบข./กบศ. ลบออกแล้ว (ใช้ได้เฉพาะ 40(1) เงินเดือน)
            # โปรเจกต์นี้เน้น 40(6) และ 40(8) เท่านั้น
            "เงินบริจาคทั่วไป": {
                "pros": [
                    "ลดหย่อนภาษีได้ 10% ของรายได้",
                    "ช่วยเหลือสังคม",
                    "สร้างบุญ"
                ],
                "cons": [
                    "ไม่ได้รับผลตอบแทน",
                    "วงเงินจำกัด",
                    "ต้องมีใบเสร็จรับเงิน"
                ]
            },
            "เงินบริจาคการศึกษา": {
                "pros": [
                    "ลดหย่อนภาษีได้ 2 เท่า",
                    "สนับสนุนการศึกษา",
                    "คุ้มค่าที่สุดสำหรับการบริจาค"
                ],
                "cons": [
                    "ต้องบริจาคผ่านสถาบันที่กำหนด",
                    "ไม่ได้รับผลตอบแทน",
                    "วงเงินรวมไม่เกิน 10% ของรายได้"
                ]
            },
            "ลงทุนหุ้น": {
                "pros": [
                    "ผลตอบแทนสูงในระยะยาว",
                    "สภาพคล่องสูง",
                    "ยกเว้นภาษีเงินปันผล"
                ],
                "cons": [
                    "ความเสี่ยงสูงจากความผันผวนของตลาด",
                    "ต้องมีความรู้ในการวิเคราะห์",
                    "อาจขาดทุนได้"
                ]
            }
        }

        # 🎯 Extract ground truth text from expected_plans
        expected_text_plan_1 = ""
        expected_text_plan_2 = ""
        expected_text_plan_3 = ""
        allocations_guide = ""

        if expected_plans:
            # Check if it's the old format (plan_1, plan_2, plan_3) or new format (plans array)
            plan1 = expected_plans.get('plan_1', None)
            plan2 = expected_plans.get('plan_2', None)
            plan3 = expected_plans.get('plan_3', None)

            if plan1 and 'expected_text' in plan1:
                # Plan 1 - Extract from expected_text
                exp_text = plan1['expected_text']
                desc = exp_text.get('description', '')
                keywords = exp_text.get('keywords', [])
                key_points = exp_text.get('key_points', [])

                expected_text_plan_1 = f"""
                description: "{desc}"
                คำสำคัญ: {', '.join(keywords)}
                จุดเด่น:
                {chr(10).join(['  - ' + point for point in key_points])}
                """

            if plan2 and 'expected_text' in plan2:
                # Plan 2 - Extract from expected_text
                exp_text = plan2['expected_text']
                desc = exp_text.get('description', '')
                keywords = exp_text.get('keywords', [])
                key_points = exp_text.get('key_points', [])

                expected_text_plan_2 = f"""
                description: "{desc}"
                คำสำคัญ: {', '.join(keywords)}
                จุดเด่น:
                {chr(10).join(['  - ' + point for point in key_points])}
                """

            if plan3 and 'expected_text' in plan3:
                # Plan 3 - Extract from expected_text
                exp_text = plan3['expected_text']
                desc = exp_text.get('description', '')
                keywords = exp_text.get('keywords', [])
                key_points = exp_text.get('key_points', [])

                expected_text_plan_3 = f"""
                description: "{desc}"
                คำสำคัญ: {', '.join(keywords)}
                จุดเด่น:
                {chr(10).join(['  - ' + point for point in key_points])}
                """

        # 🔒 Build comprehensive allocations guide from the dictionary
        allocations_guide = "\n\n🔒 **MANDATORY PROS/CONS FOR EACH ALLOCATION CATEGORY:**\n"
        allocations_guide += "**You MUST use these exact pros/cons for each category. DO NOT create new ones!**\n"
        allocations_guide += "=" * 80 + "\n\n"

        for category, data in ALLOCATION_PROS_CONS.items():
            allocations_guide += f"**{category}:**\n"
            allocations_guide += f"  Pros (ใช้ตรงตัว): {json.dumps(data['pros'], ensure_ascii=False)}\n"
            allocations_guide += f"  Cons (ใช้ตรงตัว): {json.dumps(data['cons'], ensure_ascii=False)}\n\n"

        # 🔥 PROMPT ที่บังคับใช้ Ground Truth Text
        return f"""คุณเป็นที่ปรึกษาภาษีและการลงทุนมืออาชีพในประเทศไทย ปี 2568

📊 สถานการณ์ของลูกค้า:
- รายได้รวม: {gross:,.0f} บาท
- เงินได้สุทธิ: {taxable:,.0f} บาท
- ภาษีที่ต้องจ่ายตอนนี้: {current_tax:,.0f} บาท
- อัตราภาษีส่วนเพิ่ม: {marginal_rate}%
- ระดับความเสี่ยงที่ลูกค้าเลือก: {risk_thai}

💰 วงเงินค่าลดหย่อนที่ยังใช้ไม่ครบ (ปี 2568 - สำหรับ 40(6) และ 40(8)):
- RMF: เหลือ {remaining_rmf:,.0f} บาท (สูงสุด {max_rmf:,.0f})
- ThaiESG: เหลือ {remaining_thai_esg:,.0f} บาท (สูงสุด {max_thai_esg:,.0f})
- ThaiESGX (เงินใหม่): เหลือ {remaining_thai_esgx_new:,.0f} บาท (สูงสุด {max_thai_esgx_new:,.0f})
- ThaiESGX (จาก LTF): เหลือ {remaining_thai_esgx_ltf:,.0f} บาท (สูงสุด {max_thai_esgx_ltf:,.0f})
- ประกันบำนาญ: เหลือ {remaining_pension:,.0f} บาท (สูงสุด {max_pension:,.0f})
(หมายเหตุ: PVD/กบข./กบศ. ไม่รวมเพราะใช้ได้เฉพาะ 40(1) เงินเดือน)
- ประกันชีวิต: เหลือ {remaining_life:,.0f} บาท
- ประกันชีวิตแบบบำนาญ: เหลือ {remaining_life_pension:,.0f} บาท
- ประกันสุขภาพ: เหลือ {remaining_health:,.0f} บาท

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

📚 ข้อมูลจาก Knowledge Base:
{retrieved_context}

🎯 ภารกิจ: สร้าง 3 แผนการลงทุนที่แตกต่างกัน

🔒 **กฎทองคำ - คุณต้องใช้ description ที่กำหนดไว้เท่านั้น:**

**แผนที่ 1 (Conservative) - description ที่ต้องใช้:**{expected_text_plan_1}

**แผนที่ 2 (Balanced) - description ที่ต้องใช้:**{expected_text_plan_2}

**แผนที่ 3 (Aggressive) - description ที่ต้องใช้:**{expected_text_plan_3}

**กฎสำคัญ - ใช้เงินลงทุนและข้อความเป๊ะๆ ตามที่กำหนด:**

📌 **การใช้ description:**
1. แผนที่ 1 (Conservative): total_investment = {tier_1:,.0f} บาท (เน้นประกัน + ความปลอดภัย)
2. แผนที่ 2 (Balanced): total_investment = {tier_2:,.0f} บาท (สมดุล กระจายความเสี่ยง)
3. แผนที่ 3 (Aggressive): total_investment = {tier_3:,.0f} บาท (เน้นการเติบโต + ลดหย่อนสูงสุด)
4. **🚫 ห้ามเปลี่ยน description - คัดลอกตรงตัวจาก description ที่กำหนดไว้ด้านบน**
5. **🚫 ห้ามเขียน description ใหม่ - ใช้เนื้อหาจาก description ที่กำหนดไว้เท่านั้น**
6. **🚫 description ต้องตรงตัวกับที่กำหนด - ห้ามแต่งเติมหรือตัดออก**

📌 **การใช้ Pros/Cons ใน allocations:**
7. **🔒 CRITICAL: ทุก allocation ต้องใช้ pros และ cons จากคู่มือด้านบนเท่านั้น**
8. **🔒 ห้ามเขียน pros/cons ใหม่ - คัดลอกตรงตัวจากคู่มือตามชื่อ category**
9. **🔒 ถ้าใช้ category "RMF" ต้องใช้ pros/cons ของ RMF จากคู่มือเท่านั้น**
10. **🔒 ถ้าใช้ category "ประกันชีวิต" ต้องใช้ pros/cons ของประกันชีวิตจากคู่มือเท่านั้น**
11. **🔒 pros และ cons ต้องเป็น array เหมือนในคู่มือ ไม่ต้องเปลี่ยนแปลงใดๆ**

📌 **กฎทั่วไป:**
12. ทุกแผนต้องมีความเสี่ยงระดับ "{risk_level}"
13. ใช้คำสำคัญ (keywords) และจุดเด่น (key_points) เป็นแนวทางในการเลือก allocations
{'14. ทุกแผนต้องมีประกันชีวิตอย่างน้อย 20,000 บาท' if not has_life_insurance else ''}
{'15. ทุกแผนต้องมีประกันสุขภาพอย่างน้อย 15,000 บาท' if not has_health_insurance else ''}
16. ควรใช้วงเงิน RMF ให้เต็มที่ (หรือใกล้เคียง) เพราะลดหย่อนได้สูง
17. **ใช้ ThaiESG/ThaiESGX แทน SSF** (SSF ยกเลิกแล้วในปี 2568)
18. สำหรับรายได้สูง (1,500,000+): ควรมีเงินบริจาคการศึกษา (นับ 2 เท่า)

**ตัวอย่างการใช้ pros/cons จากคู่มือ:**

หาก allocation ของคุณคือ "RMF" คุณต้องใช้:
```json
{{
  "category": "RMF",
  "percentage": 50,
  "risk_level": "medium",
  "pros": {json.dumps(ALLOCATION_PROS_CONS.get("RMF", {}).get("pros", []), ensure_ascii=False)},
  "cons": {json.dumps(ALLOCATION_PROS_CONS.get("RMF", {}).get("cons", []), ensure_ascii=False)}
}}
```

หาก allocation ของคุณคือ "ประกันชีวิต" คุณต้องใช้:
```json
{{
  "category": "ประกันชีวิต",
  "percentage": 30,
  "risk_level": "low",
  "pros": {json.dumps(ALLOCATION_PROS_CONS.get("ประกันชีวิต", {}).get("pros", []), ensure_ascii=False)},
  "cons": {json.dumps(ALLOCATION_PROS_CONS.get("ประกันชีวิต", {}).get("cons", []), ensure_ascii=False)}
}}
```

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
      "allocations": [...]
    }},
    {{
      "plan_id": "2",
      "plan_name": "ทางเลือกที่ 2 - สมดุล",
      "plan_type": "{risk_level}",
      "description": "กระจายความเสี่ยง เน้น RMF + ThaiESG",
      "total_investment": {tier_2},
      "total_tax_saving": {int(tier_2 * marginal_rate / 100)},
      "overall_risk": "{risk_level}",
      "allocations": [...]
    }},
    {{
      "plan_id": "3",
      "plan_name": "ทางเลือกที่ 3 - ลงทุนสูงสุด",
      "plan_type": "{risk_level}",
      "description": "เน้นลดหย่อนภาษีสูงสุด ใช้วงเงินเต็มที่",
      "total_investment": {tier_3},
      "total_tax_saving": {int(tier_3 * marginal_rate / 100)},
      "overall_risk": "{risk_level}",
      "allocations": [...]
    }}
  ]
}}
```

**หมายเหตุสำคัญ:**

📌 **สำหรับ description:**
- **🔒 🔒 🔒 CRITICAL: ใช้ description ตรงตัวจากที่กำหนดไว้ด้านบน**
- **🔒 คัดลอกข้อความหลังคำว่า "description:" มาใส่ใน field "description" ของแต่ละแผน**
- **🔒 ห้ามเปลี่ยนแปลง แต่งเติม หรือตัดทอน description - ใช้ตรงตัวเท่านั้น**

📌 **สำหรับ pros/cons ใน allocations:**
- **🔒 🔒 🔒 CRITICAL: ใช้ pros และ cons จากคู่มือด้านบนเท่านั้น**
- **🔒 ค้นหา category ที่ตรงกัน (เช่น "RMF", "ประกันชีวิต") แล้วคัดลอก pros/cons มาใช้ตรงตัว**
- **🔒 ห้ามเขียน pros/cons ใหม่ - ห้ามแก้ไข - ห้ามตัดทอน - คัดลอกเท่านั้น!**
- **🔒 pros และ cons ต้องเป็น array ของ string เหมือนในคู่มือทุกประการ**

📌 **สำหรับตัวเลข:**
- **ใช้ total_investment ตามที่กำหนดเท่านั้น:** Plan 1 = {tier_1:,.0f}, Plan 2 = {tier_2:,.0f}, Plan 3 = {tier_3:,.0f}
- **ห้ามเปลี่ยนค่า total_investment หรือ total_tax_saving** (ตัวเลขจะถูกคำนวณใหม่ด้วย Python)
- **ห้ามใส่ investment_amount และ tax_saving ใน allocations** (ระบบคำนวณให้อัตโนมัติ)

📌 **ข้อกำหนดทั่วไป:**
- แต่ละ allocation ต้องมีครบทุก field: category, percentage, risk_level, pros, cons
- **percentage รวมทั้งหมดในแต่ละแผนต้องใกล้เคียง 100** (ควรอยู่ในช่วง 99-101)
- **อย่าใช้ SSF** เพราะยกเลิกแล้วในปี 2568 ใช้ ThaiESG/ThaiESGX แทน

⚠️ **คำเตือนสุดท้าย:**
- **description ต้องตรงตัว 100% กับที่กำหนดไว้ - อย่าสร้างใหม่!**
- **pros/cons ต้องตรงตัว 100% กับคู่มือ - อย่าสร้างใหม่!**
- **หาก category ตรงกัน ต้องใช้ pros/cons ตรงตัวจากคู่มือเท่านั้น!**

ตอบเป็น JSON เท่านั้น ห้ามมี markdown หรือข้อความอื่น:"""

    def _is_api_refusal(self, response_text: str) -> bool:
        """
        ตรวจสอบว่า response เป็นการปฏิเสธจาก OpenAI หรือไม่

        Returns:
            True ถ้าเป็นการปฏิเสธ, False ถ้าเป็น response ปกติ
        """
        refusal_patterns = [
            "I'm sorry, I can't assist",
            "I cannot assist",
            "I'm unable to assist",
            "I can't help with that",
            "I'm not able to help",
            "I apologize, but I cannot",
            "I'm sorry, but I cannot"
        ]

        response_lower = response_text.lower().strip()

        for pattern in refusal_patterns:
            if pattern.lower() in response_lower:
                return True

        # ตรวจสอบว่า response สั้นเกินไป (น้อยกว่า 100 ตัวอักษร) และไม่มี JSON
        if len(response_text) < 100 and "{" not in response_text:
            return True

        return False

    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        ดึงสถิติการ retry

        Returns:
            Dictionary ที่มีสถิติการ retry
        """
        stats = self.retry_stats.copy()

        # คำนวณ success rate
        if stats["total_calls"] > 0:
            stats["success_rate"] = (stats["successful_first_try"] / stats["total_calls"]) * 100
            stats["retry_rate"] = (stats["retries_needed"] / stats["total_calls"]) * 100
            stats["fallback_rate"] = (stats["fallback_used"] / stats["total_calls"]) * 100
        else:
            stats["success_rate"] = 0.0
            stats["retry_rate"] = 0.0
            stats["fallback_rate"] = 0.0

        # คำนวณค่าเฉลี่ย retries ต่อครั้งที่ต้อง retry
        if stats["retries_needed"] > 0:
            stats["avg_retries_when_needed"] = stats["total_retries"] / stats["retries_needed"]
        else:
            stats["avg_retries_when_needed"] = 0.0

        return stats

    def print_retry_statistics(self):
        """
        พิมพ์สถิติการ retry ในรูปแบบที่อ่านง่าย
        """
        stats = self.get_retry_statistics()

        print("\n" + "=" * 80)
        print("📊 API RETRY STATISTICS")
        print("=" * 80)
        print(f"Total API Calls:           {stats['total_calls']}")
        print(f"✅ Successful (1st try):    {stats['successful_first_try']} ({stats['success_rate']:.1f}%)")
        print(f"🔄 Needed Retries:          {stats['retries_needed']} ({stats['retry_rate']:.1f}%)")
        print(f"📈 Total Retry Attempts:    {stats['total_retries']}")
        print(f"⚠️  Fallback Used:           {stats['fallback_used']} ({stats['fallback_rate']:.1f}%)")
        print(f"🚫 API Refusals Detected:   {stats['refusal_detected']}")

        if stats['retries_needed'] > 0:
            print(f"📊 Avg Retries (when needed): {stats['avg_retries_when_needed']:.2f}")

        print("=" * 80 + "\n")

    async def generate_recommendations(
        self,
        request: TaxCalculationRequest,
        tax_result: TaxCalculationResult,
        retrieved_context: str,
        expected_plans: Dict[str, Any],
        test_case_id: int = 0,
        max_retries: int = 3
    ) -> Tuple[Dict[str, Any], str]:
        """
        เรียก OpenAI เพื่อสร้างคำแนะนำ พร้อม retry logic

        Args:
            max_retries: จำนวนครั้งสูงสุดที่จะพยายามใหม่ (default = 3)

        Returns:
            (parsed_result, raw_response)
        """
        # Track statistics
        self.retry_stats["total_calls"] += 1

        # สร้าง Prompt (นอก loop เพราะไม่ต้องสร้างใหม่ทุกครั้ง)
        prompt = self.generate_tax_optimization_prompt(
            request, tax_result, retrieved_context, expected_plans
        )

        # แสดง Prompt (ถ้า verbose)
        if self.verbose:
            print("\n" + "=" * 80)
            print("📤 PROMPT SENT TO OPENAI:")
            print("=" * 80)
            print(prompt[:1500] + "...[truncated]" if len(prompt) > 1500 else prompt)
            print("=" * 80 + "\n")

        # บันทึก Prompt ลงไฟล์
        if self.save_to_file:
            prompt_file = self.log_dir / f"prompt_test_case_{test_case_id}.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            if self.verbose:
                print(f"💾 Saved prompt to: {prompt_file}\n")

        # 🔄 RETRY LOOP with exponential backoff
        for attempt in range(max_retries + 1):  # +1 เพราะครั้งแรกไม่ใช่ retry
            try:
                # แสดงสถานะการ retry
                if attempt > 0:
                    if self.verbose:
                        print(f"\n🔄 Retry attempt {attempt}/{max_retries}...")
                    self.retry_stats["total_retries"] += 1

                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** (attempt - 1)
                    if self.verbose:
                        print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)

                # เรียก OpenAI
                if self.verbose:
                    print("🤖 Calling OpenAI API...")

                response = await self.llm.ainvoke(prompt)
                raw_response = response.content

                # 🚫 ตรวจสอบว่าเป็น API refusal หรือไม่
                if self._is_api_refusal(raw_response):
                    self.retry_stats["refusal_detected"] += 1

                    if self.verbose:
                        print("\n" + "=" * 80)
                        print("🚫 API REFUSAL DETECTED:")
                        print("=" * 80)
                        print(raw_response[:500])
                        print("=" * 80 + "\n")

                    # บันทึก refusal
                    if self.save_to_file:
                        refusal_file = self.log_dir / f"refusal_test_case_{test_case_id}_attempt_{attempt}.txt"
                        with open(refusal_file, 'w', encoding='utf-8') as f:
                            f.write(f"API Refusal detected on attempt {attempt}\n\n")
                            f.write(raw_response)
                        if self.verbose:
                            print(f"💾 Saved refusal to: {refusal_file}\n")

                    # ถ้ายังมีโอกาส retry ให้ลองใหม่
                    if attempt < max_retries:
                        if self.verbose:
                            print(f"⚠️  API refused request, will retry... ({attempt + 1}/{max_retries})")
                        continue
                    else:
                        # หมด retry แล้ว ใช้ fallback
                        if self.verbose:
                            print("⚠️  All retries exhausted, using fallback response")
                        self.retry_stats["fallback_used"] += 1
                        if attempt > 0:
                            self.retry_stats["retries_needed"] += 1
                        return self._get_fallback_response(request, tax_result), raw_response

                # แสดง Raw Response
                if self.verbose:
                    print("\n" + "=" * 80)
                    print("📥 RAW RESPONSE FROM OPENAI:")
                    print("=" * 80)
                    print(raw_response[:2000] if len(raw_response) > 2000 else raw_response)
                    if len(raw_response) > 2000:
                        print(f"...[truncated, total {len(raw_response)} characters]")
                    print("=" * 80 + "\n")

                # บันทึก Raw Response ลงไฟล์
                if self.save_to_file:
                    response_file = self.log_dir / f"raw_response_test_case_{test_case_id}.txt"
                    with open(response_file, 'w', encoding='utf-8') as f:
                        f.write(raw_response)
                    if self.verbose:
                        print(f"💾 Saved raw response to: {response_file}\n")

                # Parse JSON
                plans_text = raw_response.strip()

                # ลบ markdown code blocks ถ้ามี
                if plans_text.startswith("```json"):
                    plans_text = plans_text[7:]
                    if self.verbose:
                        print("🔧 Removed ```json prefix")
                if plans_text.startswith("```"):
                    plans_text = plans_text[3:]
                    if self.verbose:
                        print("🔧 Removed ``` prefix")
                if plans_text.endswith("```"):
                    plans_text = plans_text[:-3]
                    if self.verbose:
                        print("🔧 Removed ``` suffix")

                plans_text = plans_text.strip()
                result = json.loads(plans_text)

                # แสดง Parsed Result
                if self.verbose:
                    print("\n" + "=" * 80)
                    print("📊 PARSED RESULT:")
                    print("=" * 80)
                    print(json.dumps(result, indent=2, ensure_ascii=False)[:1500])
                    print("=" * 80 + "\n")
                    print(f"✅ Successfully parsed {len(result.get('plans', []))} plans\n")

                # บันทึก Parsed Result ลงไฟล์
                if self.save_to_file:
                    parsed_file = self.log_dir / f"parsed_result_test_case_{test_case_id}.json"
                    with open(parsed_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    if self.verbose:
                        print(f"💾 Saved parsed result to: {parsed_file}\n")

                # Validate
                self._validate_response(result)

                # ✅ สำเร็จ!
                if attempt == 0:
                    self.retry_stats["successful_first_try"] += 1
                else:
                    self.retry_stats["retries_needed"] += 1
                    if self.verbose:
                        print(f"✅ Success after {attempt} retry/retries\n")

                return result, raw_response

            except json.JSONDecodeError as e:
                print(f"\n❌ JSON Parse Error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"\n📄 Raw Response was:")
                print("=" * 80)
                print(raw_response[:1000] if 'raw_response' in locals() else "No response")
                print("=" * 80)

                # ถ้ายังมีโอกาส retry ให้ลองใหม่
                if attempt < max_retries:
                    if self.verbose:
                        print(f"⚠️  JSON parse failed, will retry... ({attempt + 1}/{max_retries})")
                    continue
                else:
                    # หมด retry แล้ว ใช้ fallback
                    if self.save_to_file:
                        error_file = self.log_dir / f"error_test_case_{test_case_id}.txt"
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(f"JSON Parse Error after {max_retries} retries: {e}\n\n")
                            f.write("Raw Response:\n")
                            f.write(raw_response if 'raw_response' in locals() else "No response")
                        print(f"\n💾 Saved error to: {error_file}\n")

                    self.retry_stats["fallback_used"] += 1
                    if attempt > 0:
                        self.retry_stats["retries_needed"] += 1
                    return self._get_fallback_response(request, tax_result), raw_response if 'raw_response' in locals() else ""

            except Exception as e:
                print(f"\n❌ Error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                import traceback
                traceback.print_exc()

                # ถ้ายังมีโอกาส retry ให้ลองใหม่
                if attempt < max_retries:
                    if self.verbose:
                        print(f"⚠️  Error occurred, will retry... ({attempt + 1}/{max_retries})")
                    continue
                else:
                    # หมด retry แล้ว ใช้ fallback
                    if self.save_to_file:
                        error_file = self.log_dir / f"error_test_case_{test_case_id}.txt"
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(f"Error after {max_retries} retries: {e}\n\n")
                            f.write(traceback.format_exc())
                        print(f"\n💾 Saved error to: {error_file}\n")

                    self.retry_stats["fallback_used"] += 1
                    if attempt > 0:
                        self.retry_stats["retries_needed"] += 1
                    return self._get_fallback_response(request, tax_result), ""

        # ไม่ควรมาถึงจุดนี้ แต่เผื่อกรณี
        self.retry_stats["fallback_used"] += 1
        return self._get_fallback_response(request, tax_result), ""
    
    def _validate_response(self, result: Dict[str, Any]):
        """
        ตรวจสอบความถูกต้องของ response
        """
        if "plans" not in result:
            raise ValueError("Missing 'plans' key in response")
        
        if len(result["plans"]) != 3:
            raise ValueError(f"Expected 3 plans, got {len(result['plans'])}")
        
        required_plan_fields = ["plan_id", "plan_name", "plan_type", "description",
                               "total_investment", "total_tax_saving", "overall_risk", "allocations"]
        required_alloc_fields = ["category", "percentage", "risk_level", "pros", "cons"]
        
        for i, plan in enumerate(result["plans"]):
            for field in required_plan_fields:
                if field not in plan:
                    raise ValueError(f"Plan {i+1} missing field: {field}")
            
            if not plan["allocations"]:
                raise ValueError(f"Plan {i+1} has empty allocations")
            
            for j, alloc in enumerate(plan["allocations"]):
                for field in required_alloc_fields:
                    if field not in alloc:
                        raise ValueError(f"Plan {i+1}, Allocation {j+1} missing field: {field}")
        
        if self.verbose:
            print("✅ Response validation passed")
    
    def _get_fallback_response(
        self,
        request: TaxCalculationRequest,
        tax_result: TaxCalculationResult
    ) -> Dict[str, Any]:
        """
        คำตอบสำรองกรณี AI ล้มเหลว
        """
        if self.verbose:
            print("\n⚠️  Using fallback response...\n")
        
        gross = tax_result.gross_income
        risk = request.risk_tolerance
        
        # คำนวณเงินลงทุนแนะนำ
        if gross < 1000000:
            base_investment = 150000
        elif gross < 2000000:
            base_investment = 500000
        else:
            base_investment = 1000000
        
        return {
            "plans": [
                {
                    "plan_id": "1",
                    "plan_name": "ทางเลือกที่ 1 - เน้นประกัน (Fallback)",
                    "plan_type": risk,
                    "description": "แผนสำรอง - เน้นความคุ้มครอง",
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
                            "pros": ["มีความคุ้มครอง", "จำเป็น"],
                            "cons": ["ผลตอบแทนต่ำ"]
                        },
                        {
                            "category": "RMF",
                            "investment_amount": int(base_investment * 0.50),
                            "percentage": 50,
                            "tax_saving": int(base_investment * 0.125),
                            "risk_level": risk,
                            "pros": ["ลดหย่อนภาษีสูง", "ผลตอบแทนดี"],
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
                    "plan_name": "ทางเลือกที่ 2 - สมดุล (Fallback)",
                    "plan_type": risk,
                    "description": "แผนสำรอง - กระจายความเสี่ยง",
                    "total_investment": int(base_investment * 1.3),
                    "total_tax_saving": int(base_investment * 1.3 * 0.25),
                    "overall_risk": risk,
                    "allocations": []  # Simplified
                },
                {
                    "plan_id": "3",
                    "plan_name": "ทางเลือกที่ 3 - ลงทุนสูงสุด (Fallback)",
                    "plan_type": risk,
                    "description": "แผนสำรอง - ใช้วงเงินเต็มที่",
                    "total_investment": int(base_investment * 1.6),
                    "total_tax_saving": int(base_investment * 1.6 * 0.25),
                    "overall_risk": risk,
                    "allocations": []  # Simplified
                }
            ]
        }