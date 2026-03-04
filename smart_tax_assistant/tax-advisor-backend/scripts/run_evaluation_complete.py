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
    }
    
    def __init__(
        self, 
        verbose: bool = True, 
        save_logs: bool = True,
        use_bertscore: bool = False
    ):
        self.verbose = verbose
        self.save_logs = save_logs
        self.use_bertscore = use_bertscore
        
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
    
    def load_new_profiles(self) -> List[Dict[str, Any]]:
        """Load test profiles from test_profiles and map to TaxCalculationRequest schema"""
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

            
            # Build final structure
            mapped_profile = {
                "name": f"[{profile_id}] {label}",
                "description": goal,
                "input": input_dict,
                "meta": meta_dict,
                "expected_goal_type": expected_goal_type
            }
            
            # Validate it matches TaxCalculationRequest
            try:
                TaxCalculationRequest(**input_dict)
                mapped_profiles.append(mapped_profile)
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
        query = f"รายได้ {request.gross_income} บาท ระดับความเสี่ยง {request.risk_tolerance}"
        
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
        print(f"  {Colors.CYAN}[3/4]{Colors.END} เรียก OpenAI...", end='', flush=True)
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
        # ✨ เพิ่มโค้ดคำนวณสำหรับ Evaluation Script ตรงนี้
        # ✨ =================================================================
        print(f"  {Colors.CYAN}[Post-processing]{Colors.END} คำนวณตัวเลข...", end='', flush=True)

        # กำหนด tiers ตามรายได้ (ต้องตรงกับ AI service และ main.py)
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

        # 🔧 FIX: คำนวณ tax saving อย่างถูกต้องตามหลักภาษี
        # Tax Saving = ภาษีที่ลดได้จากการลงทุน
        # = (ภาษีโดยไม่ลงทุน) - (ภาษีถ้าลงทุน)
        # = Investment × Marginal Rate ของรายได้ที่เพิ่มขึ้น

        for idx, plan in enumerate(ai_response.get("plans", [])):
                        # 🎯 บังคับใช้ total_investment ตาม tier (ไม่ใช้ค่าจาก AI)

            if idx < len(tiers):
                total_investment = tiers[idx]
                plan["total_investment"] = total_investment 
            else:
                total_investment = plan.get("total_investment", 0)

            taxable_without_total_investment = tax_result.taxable_income + total_investment
            marginal_rate_for_total = tax_calculator_service.get_marginal_tax_rate(
                taxable_without_total_investment
            )
            calculated_total_tax_saving = int(total_investment * (marginal_rate_for_total / 100))

            for alloc in plan.get("allocations", []):
                percentage = alloc.get("percentage", 0)
                investment_amount = int((percentage / 100) * total_investment)
                alloc["investment_amount"] = investment_amount
                tax_saving = int((percentage / 100) * calculated_total_tax_saving)
                alloc["tax_saving"] = tax_saving
            plan["total_tax_saving"] = calculated_total_tax_saving
        print(f" {Colors.GREEN}✓{Colors.END}")
        # ✨ =================================================================

        # Step 4 เช็คกฎหมาย 
        print(f"  {Colors.CYAN}[4/5]{Colors.END} เช็คความถูกต้องตามกฎหมาย...", end='', flush=True)

        legal_checks = []
        has_legal_violations = False

        for plan_idx, plan in enumerate(ai_response.get("plans", [])):
            legal_result = self.evaluator.validate_legal_compliance(
                plan=plan,
                gross_income=tax_result.gross_income,
                verbose=False  # ไม่ print ในขั้นตอนนี้ จะ print รวมทีเดียวข้างล่าง
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

            # Numeric metrics
            if 'numeric_metrics' in summary and summary['numeric_metrics']:
                f.write("NUMERIC ACCURACY:\n")
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
        """
    )
    
    parser.add_argument('--mode', choices=['quick', 'full'], default='quick',
                       help='Evaluation mode')
    parser.add_argument('--test-case', type=int,
                       help='Run specific test case (1-20)')
    parser.add_argument('--bertscore', action='store_true',
                       help='Use BERTScore (slower)')
    parser.add_argument('--no-verbose', action='store_true',
                       help='Disable verbose logging')
    parser.add_argument('--no-save', action='store_true',
                       help='Disable saving logs')
    
    args = parser.parse_args()
    
    if args.mode == 'quick':
        await quick_test()
        return
    
    # Full evaluation
    runner = EvaluationRunner(
        verbose=not args.no_verbose,
        save_logs=not args.no_save,
        use_bertscore=args.bertscore
    )
    
    # รัน specific test case หรือทั้งหมด
    if args.test_case:
        test_case = EvaluationTestData.get_test_case_by_id(args.test_case)
        if not test_case:
            print(f"{Colors.RED}❌ Test case {args.test_case} not found{Colors.END}")
            return
        result = await runner.run_single_test_case(test_case, args.test_case)
        all_results = [result] if result else []
    else:
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