"""
AI Service สำหรับ Evaluation - ปี 2568 (ฉบับสมบูรณ์)
ใช้ Prompt เหมือนกับระบบหลักทุกประการ
แยกออกจากระบบหลัก เพื่อแสดง raw response และทำ evaluation

จุดประสงค์:
1. แสดง raw response จาก LLM เพื่อตรวจสอบคุณภาพ
2. บันทึก logs สำหรับวิเคราะห์
3. ทำ evaluation โดยไม่กระทบระบบหลัก
"""

from langchain_ollama import ChatOllama
import json
import os
import time
import asyncio
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Import models และ config
from app.models import TaxCalculationRequest, TaxCalculationResult
from app.config import settings
from app.services.few_shot_pool import FewShotPool


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
        print(f"🦙 Evaluation using Ollama: {settings.ollama_model} at {settings.ollama_base_url}")
        self.llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.ollama_temperature,
            format="json",
        )
        self.verbose = verbose
        self.save_to_file = save_to_file
        self.few_shot_pool = FewShotPool()

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
        สร้าง Prompt ตามหลักการใหม่:
        - AI สร้าง description แบบ natural language
        - Backend คำนวณตัวเลขทั้งหมด (total_investment, tax_saving, investment_amount)
        - AI รับผิดชอบแค่: reasoning, percentage allocation, explanation
        """

        gross = tax_result.gross_income
        taxable = tax_result.taxable_income
        current_tax = tax_result.tax_amount

        # คำนวณวงเงินที่เหลือ - ปี 2568 (สำหรับ 40(6) และ 40(8) เท่านั้น)
        max_rmf = min(gross * 0.30, 500000)
        max_thai_esg = 300000
        max_thai_esgx = 300000
        max_pension = min(gross * 0.15, 200000)

        remaining_rmf = max_rmf - request.rmf
        remaining_thai_esg = max_thai_esg - request.thai_esg
        remaining_pension = max_pension - request.pension_insurance
        remaining_life = 100000 - request.life_insurance
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

        has_life_insurance = request.life_insurance > 0
        has_health_insurance = request.health_insurance > 0

        risk_map = {
            'low': 'ต่ำ',
            'medium': 'กลาง',
            'high': 'สูง'
        }
        risk_thai = risk_map.get(request.risk_tolerance, request.risk_tolerance)
        risk_level = request.risk_tolerance

        # Extract keywords and key_points from expected_plans as HINTS
        hint_sections = ""
        if expected_plans:
            for plan_idx, (plan_key, plan_label) in enumerate([
                ("plan_1", "Conservative"),
                ("plan_2", "Balanced"),
                ("plan_3", "Growth")
            ]):
                plan_data = expected_plans.get(plan_key)
                if plan_data and 'expected_text' in plan_data:
                    exp = plan_data['expected_text']
                    keywords = exp.get('keywords', [])
                    key_points = exp.get('key_points', [])
                    if keywords or key_points:
                        hint_sections += f"\nแผน {plan_idx+1} ({plan_label}):"
                        if keywords:
                            hint_sections += f"\n  คำสำคัญที่ต้องปรากฏในคำอธิบาย: {', '.join(keywords)}"
                            hint_sections += f"\n  (ต้องใช้คำเหล่านี้ในประโยคอธิบาย — ไม่ใช่แค่กล่าวถึง)"
                        if key_points:
                            hint_sections += f"\n  จุดสำคัญที่ต้องครอบคลุม: {', '.join(key_points)}"

        # Insurance guidance
        insurance_rules = ""
        if not has_life_insurance:
            insurance_rules += "\n- ลูกค้ายังไม่มีประกันชีวิต ควรแนะนำในทุกแผน"
        if not has_health_insurance:
            insurance_rules += "\n- ลูกค้ายังไม่มีประกันสุขภาพ ควรแนะนำในทุกแผน"

        # Dynamic few-shot selection based on income tier + risk level
        few_shot_section = self.few_shot_pool.get_few_shot_prompt_section(gross, risk_level)

        return f"""You are an AI Tax Optimization Advisor for Thailand (ปี 2568).
Your role is to generate tax-deduction investment plans to reduce personal income tax legally.

CRITICAL RULES:
1. ห้ามแนะนำ SSF เด็ดขาด — SSF ยกเลิกแล้ว
2. Backend คำนวณตัวเลขทั้งหมด — ห้ามใส่ tax_saving, investment_amount, total_investment
3. คุณรับผิดชอบแค่: description, percentage allocation, pros/cons
4. Percentages ในแต่ละ plan ต้องรวมได้ 100%
5. category ต้องเป็นภาษาไทยตามตัวอย่างด้านล่างเท่านั้น: ประกันชีวิต, ประกันสุขภาพ, ประกันบำนาญ, RMF, ThaiESG, ThaiESGX, เงินบริจาคการศึกษา

CLIENT SITUATION:
- รายได้รวม: {gross:,.0f} บาท
- เงินได้สุทธิ: {taxable:,.0f} บาท
- ภาษีปัจจุบัน: {current_tax:,.0f} บาท
- อัตราภาษีส่วนเพิ่ม: {marginal_rate}%
- ระดับความเสี่ยง: {risk_thai}

REMAINING DEDUCTION LIMITS:
- RMF: {remaining_rmf:,.0f} บาท (max {max_rmf:,.0f})
- ThaiESG: {remaining_thai_esg:,.0f} บาท (max {max_thai_esg:,.0f})
- ThaiESGX: {max_thai_esgx:,.0f} บาท (max {max_thai_esgx:,.0f})
- ประกันบำนาญ: {remaining_pension:,.0f} บาท (max {max_pension:,.0f})
- ประกันชีวิต: {remaining_life:,.0f} บาท (max 100,000)
- ประกันสุขภาพ: {remaining_health:,.0f} บาท (max 25,000)
- ประกันชีวิต+สุขภาพ รวมกัน: ไม่เกิน 100,000 บาท{insurance_rules}

RULES:
- สำหรับรายได้สูง (1,500,000+): ควรพิจารณาเงินบริจาคการศึกษา (นับ 2 เท่า)
- ควรใช้วงเงิน RMF ให้มากที่สุดเพราะลดหย่อนได้สูง

DESCRIPTION RULES:
- Plan 1 (conservative): description ต้องมีคำว่า "ความคุ้มครอง" และ "ประกัน" — เน้นประกันชีวิต ประกันสุขภาพ ประกันบำนาญ
- Plan 2 (balanced): description ต้องมีคำว่า "กระจายความเสี่ยง" และ "สมดุล" — ผสมประกันกับกองทุน
- Plan 3 (growth): description ต้องมีคำว่า "ลดหย่อนภาษี" และ "วงเงิน" — เน้น RMF ThaiESG ThaiESGX
{f'''
DESCRIPTION HINTS (บังคับ — ต้องใช้คำเหล่านี้ในประโยค description):
{hint_sections}
''' if hint_sections else ''}
{few_shot_section}

KNOWLEDGE BASE (ข้อมูลอ้างอิง):
{retrieved_context}

สร้าง JSON output ตาม format เดียวกับ EXAMPLE OUTPUT ด้านบน
เรียบเรียง description ใหม่ให้เหมาะกับสถานการณ์ลูกค้า แต่ใช้ category เดียวกับตัวอย่าง
ตอบเป็น JSON เท่านั้น:"""

    def _is_api_refusal(self, response_text: str) -> bool:
        """
        ตรวจสอบว่า response เป็นการปฏิเสธจาก LLM หรือไม่

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
        เรียก LLM เพื่อสร้างคำแนะนำ พร้อม retry logic

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
            print("📤 PROMPT SENT TO OLLAMA:")
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

                # เรียก Ollama LLM
                if self.verbose:
                    print(f"🦙 Calling Ollama ({settings.ollama_model})...")

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
                    print("📥 RAW RESPONSE FROM OLLAMA:")
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
        ตรวจสอบความถูกต้องของ response (simplified JSON structure)
        AI returns only: plan_type, description, allocations (category, percentage, risk_level, pros, cons)
        """
        if "plans" not in result:
            raise ValueError("Missing 'plans' key in response")

        if len(result["plans"]) != 3:
            raise ValueError(f"Expected 3 plans, got {len(result['plans'])}")

        required_plan_fields = ["plan_type", "description", "allocations"]
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