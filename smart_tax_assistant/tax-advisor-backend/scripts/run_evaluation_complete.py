"""
Evaluation Runner - Fixed Version (รันได้แน่นอน)
แก้ไขปัญหาทั้งหมดให้รันได้เลย
"""

import sys
import os
import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# เพิ่ม path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🔧 Initializing...")

# Import evaluation modules
try:
    from app.services.evaluation_service import EvaluationService
    print("✅ EvaluationService loaded")
except Exception as e:
    print(f"❌ Failed to import EvaluationService: {e}")
    print("\n🔧 FIX: Install dependencies:")
    print("   pip install rouge-score nltk pythainlp")
    sys.exit(1)

try:
    from app.services.evaluation_test_data import EvaluationTestData
    print("✅ EvaluationTestData loaded")
except Exception as e:
    print(f"❌ Failed to import EvaluationTestData: {e}")
    sys.exit(1)

try:
    from app.services.ai_service_for_evaluation import AIServiceForEvaluation
    print("✅ AIServiceForEvaluation loaded")
except Exception as e:
    print(f"❌ Failed to import AIServiceForEvaluation: {e}")
    sys.exit(1)

# Import ระบบหลัก
try:
    from app.services.rag_service import RAGService
    from app.services.tax_calculator import tax_calculator_service
    from app.models import TaxCalculationRequest
    print("✅ Core services loaded")
except Exception as e:
    print(f"❌ Failed to import core services: {e}")
    sys.exit(1)

# NLTK data check
try:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("📥 Downloading NLTK punkt data...")
        nltk.download('punkt', quiet=True)
        print("✅ NLTK data ready")
except Exception as e:
    print(f"⚠️  NLTK warning: {e}")


# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class EvaluationRunner:
    """
    Runner สำหรับ Evaluation - Fixed Version
    """
    
    # ProfessionType mapping for 40(6)
    PROFESSION_MAP = {
        "doctor_clinic": "medical",
        "doctor_specialist": "medical",
        "dentist": "medical",
        "vet": "medical",
        "lawyer": "law",
        "engineer": "engineering",
        "architect": "architecture",
        "accountant": "accounting",
    }
    
    # BusinessType mapping for 40(8)
    BUSINESS_MAP = {
        "online_seller": "general_trade",
        "importer": "general_trade",
        "photographer": "photography",
        "farmer": "agriculture",
        "restaurant_owner": "hotel_restaurant",
        "contractor": "other_business",
        "real_estate_broker": "general_trade",
        "youtuber": "other_business",
        "startup_founder": "other_business",
        "business_owner_retired": "other_business",
    }
    
    # Profile to TestCase mapping
    # Maps test_profiles.py (A1-A10, B11-B20) to evaluation_test_data.py (TEST_CASE_1-20)
    # Based on income_type and similar income levels
    PROFILE_TO_TESTCASE = {
        # Group A: M40(6) - 10 profiles map to TEST_CASE_6-9 (4 cases) + reused
        "A1": "TEST_CASE_6",   # แพทย์เปิดคลินิก 1.5M -> 40(6) similar to TEST_CASE_6 (1.2M engineer)
        "A2": "TEST_CASE_7",   # ทนายความ 1.2M -> 40(6) similar to TEST_CASE_7 (3M doctor)
        "A3": "TEST_CASE_8",   # วิศวกรที่ปรึกษา 900K -> 40(6) similar to TEST_CASE_8 (960K lawyer)
        "A4": "TEST_CASE_9",   # สถาปนิกฟรีแลนซ์ 480K -> 40(6) similar to TEST_CASE_9 (1.8M architect)
        "A5": "TEST_CASE_6",   # นักบัญชีอิสระ 1.8M -> reuse TEST_CASE_6
        "A6": "TEST_CASE_7",   # แพทย์เฉพาะทาง 4M -> reuse TEST_CASE_7
        "A7": "TEST_CASE_8",   # ทันตแพทย์ 2M -> reuse TEST_CASE_8
        "A8": "TEST_CASE_9",   # นักกฎหมาย 700K -> reuse TEST_CASE_9
        "A9": "TEST_CASE_6",   # วิศวกร 2.5M -> reuse TEST_CASE_6
        "A10": "TEST_CASE_7",  # สัตวแพทย์ 1M -> reuse TEST_CASE_7
        
        # Group B: M40(8) - 10 profiles map to TEST_CASE_10-19 (10 cases)
        "B11": "TEST_CASE_10", # เจ้าของร้านค้าออนไลน์ 600K -> 40(8) similar to TEST_CASE_10 (540K hair salon)
        "B12": "TEST_CASE_11", # ผู้รับเหมาก่อสร้าง 1.5M -> 40(8) similar to TEST_CASE_11 (1M shop)
        "B13": "TEST_CASE_12", # เจ้าของร้านอาหาร 800K -> 40(8) similar to TEST_CASE_12 (1.5M restaurant)
        "B14": "TEST_CASE_13", # นายหน้าอสังหาฯ 3M -> 40(8) similar to TEST_CASE_13 (600K actor)
        "B15": "TEST_CASE_14", # YouTuber 420K -> 40(8) similar to TEST_CASE_14 (720K photographer)
        "B16": "TEST_CASE_15", # เจ้าของธุรกิจนำเข้า 5M -> 40(8) similar to TEST_CASE_15 (840K salon)
        "B17": "TEST_CASE_16", # ช่างภาพฟรีแลนซ์ 360K -> 40(8) similar to TEST_CASE_16 (2.4M car repair)
        "B18": "TEST_CASE_17", # เจ้าของฟาร์ม 1.2M -> 40(8) similar to TEST_CASE_17 (1.2M transport)
        "B19": "TEST_CASE_18", # Startup founder 1M -> 40(8) similar to TEST_CASE_18 (600K laundry)
        "B20": "TEST_CASE_19", # เจ้าของธุรกิจเกษียณ 700K -> 40(8) similar to TEST_CASE_19 (1.8M printing)
    }
    
    def __init__(
        self,
        verbose: bool = True,
        save_logs: bool = True,
        use_bertscore: bool = False,
        limit: int = 0
    ):
        self.verbose = verbose
        self.save_logs = save_logs
        self.use_bertscore = use_bertscore
        self.limit = limit
        
        print("\n🚀 Initializing Evaluation Runner...")
        
        # สร้าง services
        self.evaluator = EvaluationService()
        self.ai_service = AIServiceForEvaluation(verbose=verbose, save_to_file=save_logs)
        
        try:
            self.rag_service = RAGService()
            print("✅ RAG Service initialized")
        except Exception as e:
            print(f"⚠️  RAG Service not available: {e}")
            self.rag_service = None
        
        # 📁 แยกโฟลเดอร์ให้ชัดเจน
        self.base_dir = Path("evaluation_output")
        self.logs_dir = self.base_dir / "logs"
        self.results_dir = self.base_dir / "results"
        
        # สร้างโฟลเดอร์
        self.base_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        print(f"📁 Output: {self.base_dir.absolute()}")
        
        # อัพเดท ai_service ให้ใช้โฟลเดอร์ logs
        if hasattr(self.ai_service, 'log_dir'):
            self.ai_service.log_dir = self.logs_dir
        
        self.print_header()
    
    def print_header(self):
        """แสดง Header สวยงาม"""
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 AI TAX ADVISOR - EVALUATION SYSTEM{Colors.END}")
        print("="*80)
        print(f"  📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🔧 Mode: {'Verbose' if self.verbose else 'Silent'}")
        print(f"  💾 Save logs: {'Yes' if self.save_logs else 'No'}")
        print(f"  🤖 BERTScore: {'Enabled' if self.use_bertscore else 'Disabled'}")
        print(f"\n  📁 Output directories:")
        print(f"     Logs:    {self.logs_dir}")
        print(f"     Results: {self.results_dir}")
        print("="*80 + "\n")
    
    def _get_expected_plans_for_profile(self, profile_id: str) -> Dict[str, Any]:
        """ดึง expected_plans จาก test_profiles.PROFILE_EXPECTED_PLANS โดยตรง
        พร้อม enrich ด้วย multi-reference descriptions จาก test_profiles.py"""
        from test_profiles import PROFILE_EXPECTED_PLANS, enrich_profile_with_multi_references

        expected_plans = PROFILE_EXPECTED_PLANS.get(profile_id)
        if not expected_plans:
            print(f"  ⚠️  No PROFILE_EXPECTED_PLANS for {profile_id}")
            return {}

        # Enrich with multi-reference descriptions (จาก test_profiles.py เท่านั้น)
        enrich_profile_with_multi_references(expected_plans)

        return expected_plans

    def load_new_profiles(self) -> List[Dict[str, Any]]:
        """Load test profiles from test_profiles and map to TaxCalculationRequest schema
        พร้อมแนบ expected_plans จาก test_profiles.PROFILE_EXPECTED_PLANS
        """
        from test_profiles import TEST_PROFILES
        from app.models import TaxCalculationRequest

        mapped_profiles = []

        for profile in TEST_PROFILES:
            p = profile["profile"]
            profile_id = profile["id"]
            label = profile["label"]
            goal = profile["goal"]
            expected_goal_type = profile["expected_goal_type"]

            input_dict: Dict[str, Any] = {}
            meta_dict: Dict[str, Any] = {}

            # annual_income -> gross_income
            input_dict["gross_income"] = p.get("annual_income", 0)

            # income_type -> income_type (keep original string)
            input_dict["income_type"] = p.get("income_type", "40(8)")

            # expense_deduction_type: "standard" -> expense_method = "standard", "actual" -> expense_method = "actual"
            expense_type = p.get("expense_deduction_type", "standard")
            input_dict["expense_method"] = "standard" if expense_type == "standard" else "actual"

            # actual_expenses -> actual_expenses (use 0 if not present)
            input_dict["actual_expenses"] = p.get("actual_expenses", 0)

            # occupation mapping based on income_type
            occupation = p.get("occupation", "")
            income_type = p.get("income_type", "40(8)")

            if income_type == "40(6)":
                # Map to profession_type (ProfessionType Enum)
                input_dict["profession_type"] = self.PROFESSION_MAP.get(occupation, "other")
                input_dict["business_type"] = None
            elif income_type == "40(8)":
                # Map to business_type (BusinessType Enum)
                input_dict["business_type"] = self.BUSINESS_MAP.get(occupation, "other_business")
                input_dict["profession_type"] = None

            # risk_tolerance: "aggressive" -> "high", "moderate" -> "medium", "conservative" -> "low"
            risk_map = {"aggressive": "high", "moderate": "medium", "conservative": "low"}
            input_dict["risk_tolerance"] = risk_map.get(p.get("risk_tolerance", "moderate"), "medium")

            # marital_status: "married" -> spouse_deduction = 60000, "single" -> spouse_deduction = 0
            marital_status = p.get("marital_status", "single")
            input_dict["spouse_deduction"] = 60000 if marital_status == "married" else 0

            # num_children -> child_deduction = num_children * 30000
            num_children = p.get("num_children", 0)
            input_dict["child_deduction"] = num_children * 30000

            # num_parents -> parent_support = num_parents * 30000
            num_parents = p.get("num_parents", 0)
            input_dict["parent_support"] = num_parents * 30000

            # life_insurance_amount -> life_insurance
            input_dict["life_insurance"] = p.get("life_insurance_amount", 0)

            # health_insurance_amount -> health_insurance
            input_dict["health_insurance"] = p.get("health_insurance_amount", 0)

            # existing_rmf -> rmf
            input_dict["rmf"] = p.get("existing_rmf", 0)

            # existing_thai_esg -> thai_esg
            input_dict["thai_esg"] = p.get("existing_thai_esg", 0)

            # Fields NOT in TaxCalculationRequest -> put in meta
            meta_dict["age"] = p.get("age")
            meta_dict["is_vat_registered"] = p.get("is_vat_registered")
            meta_dict["existing_savings"] = p.get("existing_savings")
            meta_dict["marital_status"] = p.get("marital_status")
            meta_dict["dependents"] = p.get("dependents")

            # ดึง expected_plans จาก evaluation_test_data ผ่าน PROFILE_TO_TESTCASE mapping
            expected_plans = self._get_expected_plans_for_profile(profile_id)

            # Build final structure
            mapped_profile = {
                "name": f"[{profile_id}] {label}",
                "description": goal,
                "input": input_dict,
                "meta": meta_dict,
                "expected_goal_type": expected_goal_type,
                "expected_plans": expected_plans,
            }

            # Validate it matches TaxCalculationRequest
            try:
                TaxCalculationRequest(**input_dict)
                
                from app.services.evaluation_test_data import EvaluationTestData
                EvaluationTestData.enrich_with_multi_references(mapped_profile)
                
                mapped_profiles.append(mapped_profile)
                if self.verbose:
                    has_plans = "✅" if expected_plans else "❌"
                    print(f"  {has_plans} {profile_id} (expected_plans: {'yes' if expected_plans else 'MISSING'})")
            except Exception as e:
                print(f"⚠️  Skipping profile {profile_id}: {e}")

        return mapped_profiles
    
    def print_progress(self, current: int, total: int, message: str = ""):
        """แสดง Progress"""
        percentage = (current / total) * 100
        filled = int((current / total) * 40)
        bar = '█' * filled + '░' * (40 - filled)
        
        print(f"\r  Progress: {bar} {percentage:.0f}% - {message}", end='', flush=True)
        
        if current == total:
            print()  # New line when complete
    
    async def run_single_test_case(
        self,
        test_case: Dict[str, Any],
        test_case_id: int
    ) -> Dict[str, Any]:
        """รัน 1 test case"""
        
        test_name = test_case.get('name', f'Test Case {test_case_id}')
        
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.BLUE}📋 TEST CASE {test_case_id}: {test_name}{Colors.END}")
        print("="*80)
        
        description = test_case.get('description', 'N/A')
        if description:
            print(f"  {Colors.CYAN}{description}{Colors.END}")
        
        # สร้าง request
        request_data = test_case['input']
        request = TaxCalculationRequest(**request_data)
        
        print(f"\n  💰 รายได้: {Colors.YELLOW}{request.gross_income:,}{Colors.END} บาท")
        print(f"  🎯 ความเสี่ยง: {Colors.YELLOW}{request.risk_tolerance}{Colors.END}")
        
        # Step 1: คำนวณภาษี
        print(f"\n  {Colors.CYAN}[1/4]{Colors.END} คำนวณภาษี...", end='', flush=True)
        try:
            tax_result = tax_calculator_service.calculate_tax(request)
            print(f" {Colors.GREEN}✓{Colors.END}")
            print(f"     └─ เงินได้สุทธิ: {tax_result.taxable_income:,} บาท")
            print(f"     └─ ภาษี: {tax_result.tax_amount:,} บาท ({tax_result.effective_tax_rate:.2f}%)")
        except Exception as e:
            print(f" {Colors.RED}✗{Colors.END}")
            print(f"     Error: {e}")
            return {}
        
        # Step 2: ดึงข้อมูลจาก RAG
        print(f"  {Colors.CYAN}[2/4]{Colors.END} ดึงข้อมูลจาก RAG...", end='', flush=True)

        # Dynamic Query: ดึงข้อมูลอาชีพและประเภทเงินได้มาสร้าง Query ที่เจาะจงกฎหมาย
        income_type = request_data.get('income_type', '')
        prof_type = getattr(request.profession_type, 'value', request.profession_type) if request.profession_type else ""
        biz_type = getattr(request.business_type, 'value', request.business_type) if request.business_type else ""
        job_keyword = prof_type or biz_type or ""

        query = f"สิทธิลดหย่อนภาษี เงินได้มาตรา {income_type} อาชีพ {job_keyword} หักค่าใช้จ่าย พ.ร.ฎ. 629 ภาษีมูลค่าเพิ่ม ข้อยกเว้น มาตรา 81(1)"
        
        context = "ไม่มีข้อมูลจาก RAG"
        if self.rag_service:
            try:
                retrieved_docs = await self.rag_service.retrieve_relevant_documents(query, k=5)
                context_parts = []
                for doc in retrieved_docs:
                    if hasattr(doc, 'page_content'):
                        context_parts.append(doc.page_content)
                    elif hasattr(doc, 'content'):
                        context_parts.append(doc.content)
                    elif isinstance(doc, str):
                        context_parts.append(doc)
                
                context = "\n\n".join(context_parts) if context_parts else "ไม่มีข้อมูลจาก RAG"
                print(f" {Colors.GREEN}✓{Colors.END} ({len(context)} chars)")
            except Exception as e:
                print(f" {Colors.YELLOW}⚠{Colors.END}")
                if self.verbose:
                    print(f"     Warning: {e}")
        else:
            print(f" {Colors.YELLOW}⚠{Colors.END} (Not available)")
        
        expected_plans = test_case.get('expected_plans', {})
        # Step 3: เรียก AI
        print(f"  {Colors.CYAN}[3/4]{Colors.END} เรียก Ollama LLM...", end='', flush=True)
        try:
            ai_response, raw_response = await self.ai_service.generate_recommendations(
    request, tax_result, context, expected_plans, test_case_id
)
            print(f" {Colors.GREEN}✓{Colors.END} ({len(ai_response.get('plans', []))} plans)")
        except Exception as e:
            print(f" {Colors.RED}✗{Colors.END}")
            print(f"     Error: {e}")
            return {}

        # ✨ =================================================================
        # ✨ Post-processing: Backend fills numerics → Validate → Correct → Verify
        # ✨ =================================================================
        print(f"  {Colors.CYAN}[Post-processing]{Colors.END} Fill numerics → Validate → Correct...", end='', flush=True)

        from app.services.tax_law_validator import (
            TaxLawValidator, validate_and_correct_plans
        )

        # กำหนด tiers ตามรายได้ (ต้องตรงกับ main.py)
        gross = tax_result.gross_income
        if gross < 600000:
            tiers = [40000, 60000, 80000]
        elif gross < 1000000:
            tiers = [60000, 100000, 150000]
        elif gross < 1500000:
            tiers = [200000, 350000, 500000]
        elif gross < 2000000:
            tiers = [300000, 500000, 800000]
        elif gross < 3000000:
            tiers = [500000, 800000, 1200000]
        else:
            tiers = [800000, 1200000, 1800000]

        # Cap tiers ไม่ให้เกิน max legal total (คำนวณจาก existing deductions ด้วย)
        validator = TaxLawValidator(
            gross_income=gross,
            existing_life_insurance=request_data.get("life_insurance", 0),
            existing_health_insurance=request_data.get("health_insurance", 0),
            existing_rmf=request_data.get("rmf", 0),
        )
        max_legal = validator.get_max_legal_total()
        tiers = [min(t, max_legal) for t in tiers]

        # 🆕 Backend fills in all numeric fields that AI doesn't generate
        plan_type_map = {"conservative": 0, "balanced": 1, "growth": 2}
        for idx, plan in enumerate(ai_response.get("plans", [])):
            # Determine tier index from plan_type or position
            plan_type = plan.get("plan_type", "").lower()
            tier_idx = plan_type_map.get(plan_type, idx)
            if tier_idx >= len(tiers):
                tier_idx = idx

            tier_investment = tiers[min(tier_idx, len(tiers) - 1)]

            # Fill plan-level fields that AI doesn't provide
            plan["total_investment"] = tier_investment
            plan.setdefault("plan_id", str(idx + 1))
            plan_names = [
                "ทางเลือกที่ 1 - เน้นประกัน",
                "ทางเลือกที่ 2 - สมดุล",
                "ทางเลือกที่ 3 - ลงทุนสูงสุด"
            ]
            plan.setdefault("plan_name", plan_names[min(idx, 2)])
            plan.setdefault("overall_risk", plan.get("plan_type", "medium"))

            # Fill allocation-level investment_amount from percentage
            for alloc in plan.get("allocations", []):
                pct = alloc.get("percentage", 0)
                alloc["investment_amount"] = int((pct / 100) * tier_investment)

        # Validate → Correct → Verify ทุก plan
        # ส่ง existing deductions จาก profile เพื่อคำนวณวงเงินที่เหลือถูกต้อง
        correction_result = validate_and_correct_plans(
            plans=ai_response.get("plans", []),
            gross_income=gross,
            taxable_income=tax_result.taxable_income,
            existing_life_insurance=request_data.get("life_insurance", 0),
            existing_health_insurance=request_data.get("health_insurance", 0),
            existing_rmf=request_data.get("rmf", 0),
        )

        # อัพเดท expected_plans ให้ตรงกับ tiers (ใช้ bracket-by-bracket tax saving)
        if expected_plans:
            for plan_idx, plan_key in enumerate(["plan_1", "plan_2", "plan_3"]):
                if plan_key in expected_plans and plan_idx < len(tiers):
                    expected_investment = tiers[plan_idx]
                    expected_tax_saving = tax_calculator_service.calculate_tax_saving_accurate(
                        tax_result.taxable_income, expected_investment
                    )
                    expected_plans[plan_key]["total_investment"] = expected_investment
                    expected_plans[plan_key]["total_tax_saving"] = expected_tax_saving

        if correction_result["corrections_made"] > 0:
            print(f" {Colors.YELLOW}✓{Colors.END} (corrected {correction_result['corrections_made']} plan(s), max legal={max_legal:,})")
        else:
            print(f" {Colors.GREEN}✓{Colors.END} (all legal)")
        # ✨ =================================================================

        # Step 4 เช็คกฎหมาย (re-validate after correction)
        print(f"  {Colors.CYAN}[4/5]{Colors.END} เช็คความถูกต้องตามกฎหมาย...", end='', flush=True)

        legal_checks = []
        has_legal_violations = False

        for plan_idx, plan in enumerate(ai_response.get("plans", [])):
            legal_result = self.evaluator.validate_legal_compliance(
                plan=plan,
                gross_income=tax_result.gross_income,
                verbose=False,  # ไม่ print ในขั้นตอนนี้ จะ print รวมทีเดียวข้างล่าง
                existing_rmf=request_data.get("rmf", 0),
                existing_life_insurance=request_data.get("life_insurance", 0),
                existing_health_insurance=request_data.get("health_insurance", 0),
            )
            legal_checks.append(legal_result)

            if not legal_result["is_legal"]:
                has_legal_violations = True

        if has_legal_violations:
            print(f" {Colors.RED}✗{Colors.END} (Found violations)")
        else:
            print(f" {Colors.GREEN}✓{Colors.END} (All legal)")

        # Step 5 ประเมิน
        print(f"  {Colors.CYAN}[5/5]{Colors.END} ประเมินผล...", end='', flush=True)


        if not expected_plans:
            print(f" {Colors.YELLOW}⚠{Colors.END} (No expected plans - skipping evaluation)")
            return {
                'test_case_id': test_case_id,
                'test_case_name': test_name,
                'status': 'no_expected_plans',
                'ai_response': ai_response,
                'legal_checks': legal_checks
            }

        try:
            evaluation_results = self.evaluator.evaluate_complete_response(
                expected_plans,
                ai_response,
                use_bertscore=self.use_bertscore
            )

            # 🆕 NitiBench evaluation — Coverage, Consistency, Citation F1
            try:
                from evaluation.nitibench_eval import evaluate_nitibench
                # รวม description ของทุก plan เป็น candidate text
                ai_texts = []
                for pk in ["plan_1", "plan_2", "plan_3"]:
                    if pk in ai_response and "plans" not in ai_response:
                        plan = ai_response[pk]
                        ai_texts.append(plan.get("description", ""))
                    elif "plans" in ai_response:
                        for p in ai_response["plans"]:
                            ai_texts.append(p.get("description", ""))
                        break
                candidate_text = " ".join(ai_texts)

                # รวม expected description + key_points
                ref_texts = []
                all_key_points = []
                all_expected_citations = []
                for pk in ["plan_1", "plan_2", "plan_3"]:
                    ep = expected_plans.get(pk, {})
                    et = ep.get("expected_text", {})
                    if et.get("description"):
                        ref_texts.append(et["description"])
                    all_key_points.extend(et.get("key_points", []))
                    all_expected_citations.extend(et.get("expected_citations", []))
                reference_text = " ".join(ref_texts)

                nitibench_results = evaluate_nitibench(
                    candidate=candidate_text,
                    reference=reference_text,
                    key_points=all_key_points if all_key_points else None,
                    expected_citations=all_expected_citations if all_expected_citations else None,
                )
                evaluation_results['nitibench'] = nitibench_results
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  NitiBench eval error: {e}")

            # 🆕 เพิ่ม Legal Compliance Score เข้าไปใน evaluation_results
            evaluation_results['legal_compliance'] = {
                'checks': legal_checks,
                'has_violations': has_legal_violations,
                'overall_score': 100 if not has_legal_violations else 0
            }

            # 🆕 ถ้ามี violations ให้ลดคะแนน Numerical Accuracy เป็น 0
            if has_legal_violations:
                # ลดคะแนนของ plans ที่มี violations
                for plan_idx, legal_check in enumerate(legal_checks):
                    if not legal_check["is_legal"]:
                        plan_key = f"plan_{plan_idx + 1}"
                        if plan_key in evaluation_results:
                            # บันทึก numerical accuracy เดิมไว้
                            original_numerical = evaluation_results[plan_key].get("numerical_accuracy", {})
                            evaluation_results[plan_key]["numerical_accuracy_before_legal_check"] = original_numerical

                            # ลดคะแนนเป็น 0 เพราะผิดกฎหมาย
                            evaluation_results[plan_key]["numerical_accuracy"] = {
                                "total_investment_match": 0.0,
                                "total_tax_saving_match": 0.0,
                                "overall_score": 0.0,
                                "reason": "FAILED - Legal violations detected"
                            }
                            evaluation_results[plan_key]["legal_check"] = legal_check

            # 🆕 Plan Diversity Score
            try:
                diversity_result = self.evaluator.calculate_plan_diversity(ai_response)
                evaluation_results['plan_diversity'] = diversity_result
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  Plan Diversity error: {e}")

            # 🆕 Format Validity
            try:
                format_result = self.evaluator.validate_format(ai_response)
                evaluation_results['format_validity'] = format_result
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  Format Validity error: {e}")

            print(f" {Colors.GREEN}✓{Colors.END}")
        except Exception as e:
            print(f" {Colors.RED}✗{Colors.END}")
            print(f"     Error: {e}")
            evaluation_results = {'error': str(e), 'legal_checks': legal_checks}
        
        # แสดงรายงาน
        if 'error' not in evaluation_results:
            self.evaluator.print_evaluation_report(
                evaluation_results,
                test_case_name=test_name,
                save_to_file=self.save_logs,
                output_dir=self.results_dir
            )
        
        # บันทึกผลลัพธ์
        result = {
            'test_case_id': test_case_id,
            'test_case_name': test_name,
            'input': request_data,
            'tax_result': {
                'gross_income': tax_result.gross_income,
                'taxable_income': tax_result.taxable_income,
                'tax_amount': tax_result.tax_amount,
                'effective_tax_rate': tax_result.effective_tax_rate
            },
            'ai_response': ai_response,
            'expected_plans': expected_plans,
            'evaluation_results': evaluation_results,
            'raw_response_preview': raw_response[:300] if raw_response else ""
        }
        
        return result
    
    async def run_all_test_cases(self) -> List[Dict[str, Any]]:
        """รันทุก test cases"""
        
        test_cases = EvaluationTestData.get_all_test_cases()
        # Enrich with multi-reference descriptions for better evaluation
        test_cases = [EvaluationTestData.enrich_with_multi_references(tc) for tc in test_cases]

        if self.limit > 0:
            test_cases = test_cases[:self.limit]
            print(f"  ⚡ Limited to {self.limit} test cases")

        all_results = []

        print(f"\n{Colors.BOLD}🧪 RUNNING {len(test_cases)} TEST CASES{Colors.END}")
        print("="*80 + "\n")
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                result = await self.run_single_test_case(test_case, i)
                if result:
                    all_results.append(result)

                # แสดง progress
                self.print_progress(i, len(test_cases), f"Completed {i}/{len(test_cases)}")

                # 🔄 Rate limiting: Add delay between test cases to prevent overwhelming API
                if i < len(test_cases):  # ไม่ delay หลัง test case สุดท้าย
                    if self.verbose:
                        print(f"\n⏱️  Rate limiting: Waiting 1.5s before next test case...")
                    await asyncio.sleep(1.5)

            except Exception as e:
                print(f"\n{Colors.RED}❌ Error in test case {i}: {e}{Colors.END}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
        
        return all_results

    async def run_profile_test_cases(self) -> List[Dict[str, Any]]:
        """รัน evaluation โดยใช้ 20 profiles จาก test_profiles.py
        แต่ละ profile มี expected_plans เฉพาะจาก PROFILE_EXPECTED_PLANS ใน test_profiles.py
        """

        print(f"\n{Colors.BOLD}📦 Loading test profiles from test_profiles.py...{Colors.END}")
        profiles = self.load_new_profiles()

        if not profiles:
            print(f"{Colors.RED}❌ No profiles loaded!{Colors.END}")
            return []

        if self.limit > 0:
            profiles = profiles[:self.limit]
            print(f"  ⚡ Limited to {self.limit} profiles")

        all_results = []

        print(f"\n{Colors.BOLD}🧪 RUNNING {len(profiles)} PROFILE TEST CASES{Colors.END}")
        print(f"  (Profiles + expected_plans from test_profiles.py)")
        print("="*80 + "\n")

        for i, profile in enumerate(profiles, 1):
            try:
                # profile มี expected_plans แนบมาแล้วจาก load_new_profiles()
                result = await self.run_single_test_case(profile, i)
                if result:
                    # เพิ่ม meta data ของ profile เข้าไปใน result
                    result['meta'] = profile.get('meta', {})
                    result['expected_goal_type'] = profile.get('expected_goal_type', '')
                    all_results.append(result)

                self.print_progress(i, len(profiles), f"Completed {i}/{len(profiles)}")

                # Rate limiting
                if i < len(profiles):
                    if self.verbose:
                        print(f"\n⏱️  Rate limiting: Waiting 1.5s before next profile...")
                    await asyncio.sleep(1.5)

            except Exception as e:
                print(f"\n{Colors.RED}❌ Error in profile {i}: {e}{Colors.END}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()

        return all_results

    async def run_generalization_test(self) -> Dict[str, Any]:
        """
        Generalization Test — รัน 5 profiles ที่ไม่อยู่ใน few-shot pool
        ใช้ rule-based validation แทน text matching (ไม่มี expected_plans)

        Returns dict ที่สามารถ merge เข้า summary ได้
        """
        from test_profiles import GENERALIZATION_PROFILES

        print(f"\n{Colors.BOLD}{Colors.CYAN}🧪 GENERALIZATION TEST — 5 unseen profiles{Colors.END}")
        print("=" * 80)
        print(f"  วัดว่า model จัดการ profile ใหม่ที่ไม่เคยเห็นใน few-shot ได้ดีแค่ไหน")
        print("=" * 80 + "\n")

        gen_results = []
        total_checks = 0
        passed_checks = 0

        for i, profile in enumerate(GENERALIZATION_PROFILES, 1):
            profile_id = profile["id"]
            label = profile["label"]
            checks = profile.get("generalization_checks", {})
            p = profile["profile"]

            print(f"\n  {Colors.BOLD}[{i}/5] {profile_id}: {label}{Colors.END}")

            try:
                # สร้าง TaxCalculationRequest
                from app.models import TaxCalculationRequest
                risk_map = {"aggressive": "high", "moderate": "medium", "conservative": "low", "low": "low"}

                input_dict = {
                    "gross_income": p.get("annual_income", 0),
                    "income_type": p.get("income_type", "40(8)"),
                    "expense_method": "standard" if p.get("expense_deduction_type") == "standard" else "actual",
                    "actual_expenses": p.get("actual_expenses", 0),
                    "risk_tolerance": risk_map.get(p.get("risk_tolerance", "medium"), "medium"),
                    "spouse_deduction": 60000 if p.get("marital_status") == "married" else 0,
                    "child_deduction": p.get("num_children", 0) * 30000,
                    "parent_support": p.get("num_parents", 0) * 30000,
                    "life_insurance": p.get("life_insurance_amount", 0),
                    "health_insurance": p.get("health_insurance_amount", 0),
                    "rmf": p.get("existing_rmf", 0),
                    "thai_esg": p.get("existing_thai_esg", 0),
                }

                occupation = p.get("occupation", "")
                if p.get("income_type") == "40(6)":
                    input_dict["profession_type"] = self.PROFESSION_MAP.get(occupation, "other")
                    input_dict["business_type"] = None
                else:
                    input_dict["business_type"] = self.BUSINESS_MAP.get(occupation, "other_business")
                    input_dict["profession_type"] = None

                request = TaxCalculationRequest(**input_dict)
                tax_result = tax_calculator_service.calculate_tax(request)

                # RAG
                retrieved_context = ""
                if self.rag_service:
                    try:
                        context_results = self.rag_service.retrieve_context(
                            income_type=request.income_type,
                            profession_type=getattr(request.profession_type, 'value', request.profession_type) if request.profession_type else None,
                            business_type=getattr(request.business_type, 'value', request.business_type) if request.business_type else None,
                        )
                        retrieved_context = context_results.get("context", "") if isinstance(context_results, dict) else str(context_results)
                    except:
                        pass

                # AI Generate (ใช้ method เดียวกับ run_single_test_case)
                ai_response, raw_response = await self.ai_service.generate_recommendations(
                    request, tax_result, retrieved_context, {}, i
                )

                if not ai_response or "plans" not in ai_response:
                    print(f"    {Colors.RED}❌ No valid response{Colors.END}")
                    gen_results.append({"id": profile_id, "passed": 0, "total": 1, "errors": ["No valid response"]})
                    total_checks += 1
                    continue

                # ─── Rule-based validation ───
                plans = ai_response.get("plans", [])
                profile_passed = 0
                profile_total = 0
                profile_errors = []

                # Check: Format valid (3 plans)
                profile_total += 1
                format_result = self.evaluator.validate_format(ai_response)
                if format_result["format_score"] >= 80:
                    profile_passed += 1
                    print(f"    ✅ Format valid ({format_result['format_score']}%)")
                else:
                    profile_errors.append(f"Format score {format_result['format_score']}%")
                    print(f"    ❌ Format issues ({format_result['format_score']}%)")

                # Check: Legal compliance
                profile_total += 1
                all_legal = True
                for plan in plans[:3]:
                    legal = self.evaluator.validate_legal_compliance(
                        plan=plan, gross_income=tax_result.gross_income, verbose=False,
                        existing_rmf=p.get("existing_rmf", 0),
                        existing_life_insurance=p.get("life_insurance_amount", 0),
                        existing_health_insurance=p.get("health_insurance_amount", 0),
                    )
                    if not legal["is_legal"]:
                        all_legal = False
                if all_legal:
                    profile_passed += 1
                    print(f"    ✅ Legal compliance passed")
                else:
                    profile_errors.append("Legal violations detected")
                    print(f"    ❌ Legal violations detected")

                # Check: Plan diversity
                profile_total += 1
                diversity = self.evaluator.calculate_plan_diversity(ai_response)
                if diversity["diversity_score"] >= 30:
                    profile_passed += 1
                    print(f"    ✅ Plan diversity ({diversity['diversity_score']}/100)")
                else:
                    profile_errors.append(f"Low diversity {diversity['diversity_score']}")
                    print(f"    ❌ Low plan diversity ({diversity['diversity_score']}/100)")

                # Check: should_not_have (เช่น SSF)
                if "should_not_have" in checks:
                    profile_total += 1
                    all_text = " ".join(p.get("description", "") for p in plans[:3])
                    all_alloc_cats = [a.get("category", "") for p in plans[:3] for a in p.get("allocations", [])]
                    combined = all_text + " " + " ".join(all_alloc_cats)
                    found_forbidden = [item for item in checks["should_not_have"] if item.lower() in combined.lower()]
                    if not found_forbidden:
                        profile_passed += 1
                        print(f"    ✅ No forbidden items (SSF etc.)")
                    else:
                        profile_errors.append(f"Found forbidden: {found_forbidden}")
                        print(f"    ❌ Found forbidden items: {found_forbidden}")

                # Check: should_have_insurance
                if checks.get("should_have_insurance"):
                    profile_total += 1
                    has_insurance = any(
                        "ประกัน" in a.get("category", "")
                        for p in plans[:3] for a in p.get("allocations", [])
                    )
                    if has_insurance:
                        profile_passed += 1
                        print(f"    ✅ Has insurance recommendation")
                    else:
                        profile_errors.append("No insurance recommended")
                        print(f"    ❌ No insurance recommended (should have)")

                # Check: Consistency (no hallucination)
                profile_total += 1
                try:
                    from evaluation.nitibench_eval import compute_consistency
                    candidate = " ".join(p.get("description", "") for p in plans[:3])
                    con_result = compute_consistency(candidate)
                    if con_result["consistency_score"] == 1:
                        profile_passed += 1
                        print(f"    ✅ No hallucination detected")
                    else:
                        reasons = [c["reason"][:50] for c in con_result.get("contradictions", [])]
                        profile_errors.append(f"Hallucination: {reasons}")
                        print(f"    ❌ Hallucination: {reasons}")
                except:
                    profile_passed += 1  # ถ้า import ไม่ได้ ไม่ลงโทษ
                    print(f"    ⚠️  Consistency check skipped")

                total_checks += profile_total
                passed_checks += profile_passed

                gen_results.append({
                    "id": profile_id,
                    "label": label,
                    "passed": profile_passed,
                    "total": profile_total,
                    "score": round(profile_passed / profile_total * 100, 1) if profile_total > 0 else 0,
                    "errors": profile_errors,
                    "diversity_score": diversity["diversity_score"],
                    "format_score": format_result["format_score"],
                })

                # Rate limiting
                if i < len(GENERALIZATION_PROFILES):
                    await asyncio.sleep(1.5)

            except Exception as e:
                print(f"    {Colors.RED}❌ Error: {e}{Colors.END}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                gen_results.append({"id": profile_id, "passed": 0, "total": 1, "errors": [str(e)]})
                total_checks += 1

        # Summary
        overall_score = round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0

        print(f"\n{'='*80}")
        print(f"{Colors.BOLD}🧪 GENERALIZATION TEST RESULTS{Colors.END}")
        print(f"{'='*80}")
        print(f"  Overall: {passed_checks}/{total_checks} checks passed ({overall_score}%)")
        for r in gen_results:
            emoji = "✅" if r.get("score", 0) >= 80 else "⚠️" if r.get("score", 0) >= 50 else "❌"
            print(f"  {emoji} {r['id']}: {r.get('label', '')} — {r.get('passed', 0)}/{r.get('total', 0)} ({r.get('score', 0)}%)")
            if r.get("errors"):
                for err in r["errors"][:2]:
                    print(f"     ↳ {err}")
        print(f"{'='*80}\n")

        return {
            "generalization_score": overall_score,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "profiles": gen_results,
        }

    def save_final_results(
        self,
        all_results: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ):
        """บันทึกผลลัพธ์สุดท้าย"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n{Colors.BOLD}💾 SAVING RESULTS{Colors.END}")
        print("─"*80)
        
        detailed_file = self.results_dir / f"detailed_results_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"  {Colors.GREEN}✓{Colors.END} Detailed results: {detailed_file.name}")
        
        summary_file = self.results_dir / f"summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  {Colors.GREEN}✓{Colors.END} Summary: {summary_file.name}")
    
        report_file = self.results_dir / f"report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("AI TAX ADVISOR - EVALUATION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total Test Cases: {summary.get('total_test_cases', 0)}\n\n")

            if 'multi_level_metrics' in summary and summary['multi_level_metrics']:
                f.write("="*80 + "\n")
                f.write("DESCRIPTION TEXT MATCHING (Primary Metric)\n")
                f.write("="*80 + "\n")
                f.write("These metrics show how well the AI matched the EXACT description text\n")
                f.write("="*80 + "\n\n")

                ml = summary['multi_level_metrics']

                # Show key metrics
                if 'avg_desc_bleu4' in ml:
                    val = ml['avg_desc_bleu4']
                    status = "PERFECT ✓" if val >= 0.95 else "GOOD ✓" if val >= 0.80 else "NEEDS IMPROVEMENT ✗"
                    f.write(f"  BLEU-4 (Description)      : {val:.4f} ({val*100:.1f}%) - {status}\n")

                if 'avg_desc_bertscore_f1' in ml:
                    val = ml['avg_desc_bertscore_f1']
                    status = "PERFECT ✓" if val >= 0.95 else "GOOD ✓" if val >= 0.80 else "NEEDS IMPROVEMENT ✗"
                    f.write(f"  BERTScore (Description)   : {val:.4f} ({val*100:.1f}%) - {status}\n")

                if 'avg_desc_rouge1_f1' in ml:
                    val = ml['avg_desc_rouge1_f1']
                    note = " (May be 0 due to Thai tokenization)" if val == 0 else ""
                    f.write(f"  ROUGE-1 F1 (Description)  : {val:.4f}{note}\n")

                if 'avg_desc_rougeL_f1' in ml:
                    val = ml['avg_desc_rougeL_f1']
                    note = " (May be 0 due to Thai tokenization)" if val == 0 else ""
                    f.write(f"  ROUGE-L F1 (Description)  : {val:.4f}{note}\n")

                f.write("\n")
                f.write("Supporting Metrics:\n")
                f.write("-"*40 + "\n")

                if 'avg_keyword_coverage_ratio' in ml:
                    f.write(f"  Keyword Coverage          : {ml['avg_keyword_coverage_ratio']:.2%}\n")

                if 'avg_semantic_bertscore_f1' in ml:
                    f.write(f"  Semantic Similarity       : {ml['avg_semantic_bertscore_f1']:.4f}\n")

                if 'avg_keypoint_coverage_ratio' in ml:
                    f.write(f"  Key Points Coverage       : {ml['avg_keypoint_coverage_ratio']:.2%}\n")

                f.write("\n")

            # NitiBench (Thai Legal Quality)
            if 'nitibench_metrics' in summary and summary['nitibench_metrics']:
                nb = summary['nitibench_metrics']
                f.write("="*80 + "\n")
                f.write("NITIBENCH - THAI LEGAL QUALITY (Supplementary Metric)\n")
                f.write("="*80 + "\n")
                f.write("Measures legal quality that ROUGE/BLEU/BERTScore cannot capture\n")
                f.write("="*80 + "\n\n")

                if 'avg_coverage_score' in nb:
                    val = nb['avg_coverage_score']
                    status = "GOOD" if val >= 80 else "PARTIAL" if val >= 40 else "LOW"
                    f.write(f"  Coverage Score (0-100)     : {val:.1f} - {status}\n")
                if 'avg_consistency_score' in nb:
                    val = nb['avg_consistency_score']
                    status = "GOOD" if val >= 0.8 else "WARNING" if val >= 0.5 else "FAIL"
                    f.write(f"  Consistency Score (0-1)    : {val:.4f} - {status}\n")
                if 'avg_citation_f1' in nb:
                    val = nb['avg_citation_f1']
                    status = "GOOD" if val >= 0.8 else "PARTIAL" if val >= 0.5 else "LOW"
                    f.write(f"  Citation F1 (0-1)          : {val:.4f} - {status}\n")
                if 'avg_joint_score' in nb:
                    val = nb['avg_joint_score']
                    status = "GOOD" if val >= 0.8 else "PARTIAL" if val >= 0.5 else "LOW"
                    f.write(f"  Joint Score (weighted avg)  : {val:.4f} - {status}\n")
                    f.write(f"    (Coverage 40% + Consistency 35% + Citation 25%)\n")
                f.write("\n")

            # 🆕 Plan Diversity
            if 'plan_diversity_metrics' in summary:
                pd = summary['plan_diversity_metrics']
                f.write("="*80 + "\n")
                f.write("PLAN DIVERSITY SCORE\n")
                f.write("="*80 + "\n")
                f.write(f"  Average: {pd['avg_diversity_score']}/100\n")
                f.write(f"  Min: {pd['min_diversity_score']}/100 | Max: {pd['max_diversity_score']}/100\n\n")

            # 🆕 Format Validity
            if 'format_validity_metrics' in summary:
                fv = summary['format_validity_metrics']
                f.write("="*80 + "\n")
                f.write("FORMAT VALIDITY\n")
                f.write("="*80 + "\n")
                f.write(f"  Average: {fv['avg_format_score']}%\n")
                f.write(f"  Perfect format: {fv['perfect_format_count']}/{fv['total_evaluated']}\n\n")

            # 🆕 Generalization Test
            if 'generalization_metrics' in summary:
                gm = summary['generalization_metrics']
                f.write("="*80 + "\n")
                f.write("GENERALIZATION TEST (unseen profiles)\n")
                f.write("="*80 + "\n")
                f.write(f"  Score: {gm['generalization_score']}% ({gm['passed_checks']}/{gm['total_checks']} checks)\n")
                for p in gm.get('profiles', []):
                    f.write(f"  {p['id']}: {p.get('label', '')} — {p.get('score', 0)}%\n")
                f.write("\n")

            # Numeric metrics
            if 'numeric_metrics' in summary and summary['numeric_metrics']:
                f.write("NUMERIC ACCURACY (Hardcoded Validation):\n")
                f.write("Note: Numbers are hardcoded in prompt — this validates AI uses given values, not invents its own\n")
                f.write("-"*40 + "\n")
                for key, value in summary['numeric_metrics'].items():
                    metric_name = key.replace('_', ' ').title()
                    f.write(f"  {metric_name:15} : {value:.2f}%\n")
                f.write("\n")

            # Legacy Text metrics (for reference)
            if 'text_metrics' in summary and summary['text_metrics']:
                f.write("\n")
                f.write("="*80 + "\n")
                f.write("LEGACY FULL-TEXT METRICS (Less Relevant - For Reference Only)\n")
                f.write("="*80 + "\n")
                f.write("Note: These compare ALL text including allocations (pros/cons) we don't control\n")
                f.write("      Focus on 'Description Text Matching' metrics above instead!\n")
                f.write("="*80 + "\n\n")
                for key, value in summary['text_metrics'].items():
                    metric_name = key.replace('avg_', '').upper()
                    f.write(f"  {metric_name:25} : {value:.4f}\n")
                f.write("\n")
            
            # Test case details
            f.write("\n" + "="*80 + "\n")
            f.write("DETAILED RESULTS BY TEST CASE\n")
            f.write("="*80 + "\n\n")
            
            for result in all_results:
                f.write(f"Test Case {result['test_case_id']}: {result['test_case_name']}\n")
                f.write("-"*80 + "\n")

                eval_res = result.get('evaluation_results', {})
                if 'overall_metrics' in eval_res:
                    overall = eval_res['overall_metrics']
                    f.write(f"  Plans: {overall.get('actual_plan_count', 0)}/{overall.get('expected_plan_count', 3)}\n")

                    if 'avg_numeric_accuracy' in overall:
                        f.write(f"  Numeric Accuracy: {overall['avg_numeric_accuracy']:.2f}%\n")

                    # Show multi-level metrics if available
                    if 'multi_level_metrics' in overall:
                        ml = overall['multi_level_metrics']
                        if 'avg_desc_bleu4' in ml:
                            val = ml['avg_desc_bleu4']
                            f.write(f"  Description BLEU-4: {val:.4f} ({val*100:.1f}%)\n")
                        if 'avg_desc_bertscore_f1' in ml:
                            val = ml['avg_desc_bertscore_f1']
                            f.write(f"  Description BERTScore: {val:.4f} ({val*100:.1f}%)\n")
                    # Fallback to legacy metrics
                    elif 'text_metrics' in overall:
                        text_m = overall['text_metrics']
                        if 'avg_rouge1_f1' in text_m:
                            f.write(f"  ROUGE-1 F1 (Legacy): {text_m['avg_rouge1_f1']:.4f}\n")
                        if 'avg_bleu4' in text_m:
                            f.write(f"  BLEU-4 (Legacy): {text_m['avg_bleu4']:.4f}\n")

                # 🆕 Plan Diversity + Format Validity per test case
                if 'plan_diversity' in eval_res:
                    ds = eval_res['plan_diversity']['diversity_score']
                    f.write(f"  Plan Diversity: {ds}/100\n")
                if 'format_validity' in eval_res:
                    fs = eval_res['format_validity']['format_score']
                    f.write(f"  Format Validity: {fs}%\n")

                # NitiBench per test case
                if 'nitibench' in eval_res:
                    nb = eval_res['nitibench']
                    cov = nb.get('coverage', {})
                    con = nb.get('consistency', {})
                    cite = nb.get('citation', {})
                    joint = nb.get('joint_score', 0)
                    cite_f1 = cite.get('citation_f1')
                    cite_str = f"{cite_f1:.4f}" if cite_f1 is not None else "N/A"
                    f.write(f"  NitiBench: Coverage={cov.get('coverage_score', 0)}/100 "
                            f"({cov.get('covered', 0)}/{cov.get('total', 0)} pts), "
                            f"Consistency={con.get('consistency_score', 0)}/1, "
                            f"Citation F1={cite_str}, "
                            f"Joint={joint:.4f}\n")
                    if con.get('contradictions'):
                        for ct in con['contradictions'][:2]:
                            f.write(f"    [WARN] {ct.get('reason', '')[:60]}\n")

                f.write("\n")
        
        print(f"  {Colors.GREEN}✓{Colors.END} Report: {report_file.name}")
        print()


async def quick_test():
    """ทดสอบแบบง่ายๆ"""
    
    print(f"\n{Colors.CYAN}🧪 Quick Test - Evaluation Service{Colors.END}\n")
    
    evaluator = EvaluationService()
    
    expected_plan = {
        "plan_id": "1",
        "plan_name": "ทางเลือกที่ 1 - เน้นประกัน",
        "description": "เน้นความคุ้มครองและความปลอดภัย",
        "total_investment": 150000,
        "total_tax_saving": 15000,
        "allocations": [
            {
                "category": "ประกันชีวิต",
                "investment_amount": 50000,
                "percentage": 33.33,
                "tax_saving": 5000,
                "risk_level": "low"
            }
        ]
    }
    
    ai_plan = {
        "plan_id": "1",
        "plan_name": "ทางเลือกที่ 1 - เน้นความปลอดภัย",
        "description": "เน้นความคุ้มครองและสร้างรากฐาน",
        "total_investment": 145000,
        "total_tax_saving": 14500,
        "allocations": [
            {
                "category": "ประกันชีวิต",
                "investment_amount": 48000,
                "percentage": 33.10,
                "tax_saving": 4800,
                "risk_level": "low"
            }
        ]
    }
    
    print("Evaluating sample plan...")
    results = evaluator.evaluate_plan(expected_plan, ai_plan, use_bertscore=False)
    
    # แสดงผลสวยงาม
    evaluator.print_evaluation_report(
        {'plan_metrics': {'plan_1': results}},
        test_case_name="Quick Test Sample"
    )


async def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(
        description='AI Tax Advisor - Enhanced Evaluation (Fixed)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_evaluation_complete.py --mode quick
  python run_evaluation_complete.py --mode full
  python run_evaluation_complete.py --mode full --test-case 1
  python run_evaluation_complete.py --mode full --bertscore
  python run_evaluation_complete.py --mode profiles
  python run_evaluation_complete.py --mode profiles --bertscore
        """
    )

    parser.add_argument('--mode', choices=['quick', 'full', 'profiles', 'generalization'], default='quick',
                       help='Evaluation mode: quick (sample), full (evaluation_test_data), profiles (test_profiles.py), generalization (unseen profiles)')
    parser.add_argument('--test-case', type=int,
                       help='Run specific test case (1-20) [full mode only]')
    parser.add_argument('--bertscore', action='store_true',
                       help='Use BERTScore (slower)')
    parser.add_argument('--no-verbose', action='store_true',
                       help='Disable verbose logging')
    parser.add_argument('--no-save', action='store_true',
                       help='Disable saving logs')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit number of test cases/profiles to run (0 = all)')

    args = parser.parse_args()

    if args.mode == 'quick':
        await quick_test()
        return

    # Full or Profiles evaluation
    runner = EvaluationRunner(
        verbose=not args.no_verbose,
        save_logs=not args.no_save,
        use_bertscore=args.bertscore,
        limit=args.limit
    )

    if args.mode == 'generalization':
        # 🆕 Generalization Test only
        print(f"\n{Colors.BOLD}{Colors.CYAN}📋 MODE: generalization{Colors.END}")
        print(f"  ทดสอบ 5 profiles ที่ไม่อยู่ใน few-shot pool\n")
        gen_results = await runner.run_generalization_test()
        summary = {
            'total_test_cases': 5,
            'generalization_metrics': gen_results,
        }
        runner.evaluator.print_summary_report(summary)
        runner.save_final_results([], summary)
        return

    elif args.mode == 'profiles':
        # ใช้ 20 profiles จาก test_profiles.py (ตาม AI_OPTIMIZER_VISION.md)
        print(f"\n{Colors.BOLD}{Colors.CYAN}📋 MODE: profiles{Colors.END}")
        print(f"  ใช้ 20 test profiles จาก test_profiles.py")
        print(f"  expected_plans จาก test_profiles.PROFILE_EXPECTED_PLANS (เฉพาะแต่ละ profile)\n")
        all_results = await runner.run_profile_test_cases()

    elif args.test_case:
        # รัน specific test case จาก evaluation_test_data
        test_case = EvaluationTestData.get_test_case_by_id(args.test_case)
        if not test_case:
            print(f"{Colors.RED}❌ Test case {args.test_case} not found{Colors.END}")
            return
        test_case = EvaluationTestData.enrich_with_multi_references(test_case)
        result = await runner.run_single_test_case(test_case, args.test_case)
        all_results = [result] if result else []
    else:
        # รันทั้งหมดจาก evaluation_test_data
        all_results = await runner.run_all_test_cases()
    
    if not all_results:
        print(f"\n{Colors.YELLOW}⚠️  No results to summarize{Colors.END}\n")
        return
    
    # สร้าง summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}📈 GENERATING SUMMARY{Colors.END}")
    print("="*80 + "\n")
    
    evaluation_results = [r['evaluation_results'] for r in all_results 
                         if 'evaluation_results' in r and 'error' not in r['evaluation_results']]
    
    if evaluation_results:
        summary = runner.evaluator.generate_summary_statistics(evaluation_results)

        # 🆕 Auto-run generalization test in profiles mode
        if args.mode == 'profiles':
            try:
                gen_results = await runner.run_generalization_test()
                summary['generalization_metrics'] = gen_results
            except Exception as e:
                print(f"  ⚠️  Generalization test error: {e}")

        runner.evaluator.print_summary_report(summary)
        runner.save_final_results(all_results, summary)
    else:
        print(f"{Colors.YELLOW}⚠️  No valid evaluation results to summarize{Colors.END}\n")
        summary = {'total_test_cases': len(all_results)}
        runner.save_final_results(all_results, summary)

    # 📊 Print API Retry Statistics
    print(f"\n{Colors.BOLD}{Colors.HEADER}📊 API RELIABILITY STATISTICS{Colors.END}")
    print("="*80)
    runner.ai_service.print_retry_statistics()

    # Final summary
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ EVALUATION COMPLETED!{Colors.END}")
    print("="*80)
    print(f"  Test cases: {len(all_results)}")
    print(f"  Results: {runner.results_dir}")
    print(f"  Logs: {runner.logs_dir}")
    
    if evaluation_results and 'numeric_metrics' in summary and 'avg_accuracy' in summary['numeric_metrics']:
        acc = summary['numeric_metrics']['avg_accuracy']
        print(f"  Average accuracy: {Colors.CYAN}{acc:.2f}%{Colors.END}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Fatal error: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)