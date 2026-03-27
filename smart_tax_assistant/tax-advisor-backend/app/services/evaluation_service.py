"""
Evaluation Service - Enhanced Version
ปรับปรุงให้แสดงผลสวยงาม อ่านง่าย และจัดโฟลเดอร์เป็นระเบียบ
รองรับ ROUGE, BLEU, BERTScore เต็มรูปแบบ
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# ROUGE
from rouge_score import rouge_scorer, tokenizers

# BLEU
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# BERTScore
try:
    from bert_score import BERTScorer
    BERTSCORE_AVAILABLE = True
except:
    BERTSCORE_AVAILABLE = False
    print("⚠️  BERTScore not available. Install with: pip install bert-score")

# Thai tokenizer
try:
    from pythainlp.tokenize import word_tokenize
    THAI_TOKENIZER_AVAILABLE = True
except:
    THAI_TOKENIZER_AVAILABLE = False
    print("⚠️  PyThaiNLP not available. Install with: pip install pythainlp")


class Colors:
    """ANSI Color codes สำหรับ terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SimpleTokenizer(tokenizers.Tokenizer):
    """Custom tokenizer using PyThaiNLP for proper Thai word segmentation"""
    def tokenize(self, text):
        if THAI_TOKENIZER_AVAILABLE:
            tokens = word_tokenize(text, engine='newmm')
            return [t for t in tokens if t.strip()]
        return text.split()


class EvaluationService:
    """
    Service สำหรับประเมินคุณภาพคำตอบ AI Tax Advisor
    Enhanced Version - แสดงผลสวยงามและอ่านง่าย
    รองรับ ROUGE, BLEU, BERTScore with Thai language support
    """

    def __init__(self):
        # ROUGE scorer with custom tokenizer for Thai support
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'],
            use_stemmer=False,
            tokenizer=SimpleTokenizer()
        )

        # BLEU smoothing
        self.smoothing = SmoothingFunction().method1

        status = f"{Colors.GREEN}✅ Evaluation Service initialized{Colors.END}"
        status += f" {Colors.CYAN}(with Legal Compliance Check){Colors.END}"
        if BERTSCORE_AVAILABLE:
            status += f" (BERTScore: {Colors.GREEN}available{Colors.END})"
        else:
            status += f" (BERTScore: {Colors.YELLOW}not available{Colors.END})"

        print(status)

    def validate_legal_compliance(
        self,
        plan: Dict[str, Any],
        gross_income: int,
        verbose: bool = True,
        existing_rmf: int = 0,
        existing_life_insurance: int = 0,
        existing_health_insurance: int = 0,
    ) -> Dict[str, Any]:
        """
        ตรวจสอบว่าแผนการลงทุนถูกต้องตามกฎหมายหรือไม่
        โดยรวมยอดที่มีอยู่แล้ว (existing) + ยอดที่ AI แนะนำ เทียบกับเพดานกฎหมาย

        ตรวจสอบ (สำหรับ 40(6) และ 40(8) เท่านั้น):
        1. ประกันบำนาญ: ≤ min(15% of income, 200,000)
        2. RMF: existing_rmf + recommended ≤ min(30% of income, 500,000)
        3. ThaiESG/ThaiESGX: ≤ min(30% of income, 300,000)
        4. Life Insurance: existing_life + recommended ≤ 100,000
        5. Health Insurance: existing_health + recommended ≤ 25,000
        6. Combined Life + Health: (existing + recommended) รวมกัน ≤ 100,000

        หมายเหตุ: PVD/กบข./กบศ. ไม่รวมเพราะใช้ได้เฉพาะ 40(1) เงินเดือน

        Returns:
            {
                "is_legal": True/False,
                "violations": [...],
                "legal_compliance_score": 0-100,
                "details": {...}
            }
        """
        violations = []
        warnings = []

        # เพดานตามกฎหมาย (absolute limits)
        abs_limits = {
            "pension_insurance": min(int(gross_income * 0.15), 200000),
            "rmf": min(int(gross_income * 0.30), 500000),
            "thai_esg": min(int(gross_income * 0.30), 300000),
            "thai_esgx": min(int(gross_income * 0.30), 300000),
            "life_insurance": 100000,
            "health_insurance": 25000,
            "combined_insurance": 100000
        }

        # วงเงินคงเหลือ (remaining limits = absolute - existing)
        existing_combined = existing_life_insurance + existing_health_insurance
        limits = {
            "pension_insurance": abs_limits["pension_insurance"],
            "rmf": max(0, abs_limits["rmf"] - existing_rmf),
            "thai_esg": abs_limits["thai_esg"],
            "thai_esgx": abs_limits["thai_esgx"],
            "life_insurance": max(0, abs_limits["life_insurance"] - existing_life_insurance),
            "health_insurance": max(0, abs_limits["health_insurance"] - existing_health_insurance),
            "combined_insurance": max(0, abs_limits["combined_insurance"] - existing_combined),
        }

        total_investment = plan.get("total_investment", 0)
        allocations = plan.get("allocations", [])

        # ติดตามยอดรวม (เฉพาะที่ AI แนะนำใหม่)
        totals = {
            "pension_insurance": 0,
            "rmf": 0,
            "thai_esg": 0,
            "life_insurance": 0,
            "health_insurance": 0
        }

        # ตรวจสอบแต่ละรายการ
        for idx, allocation in enumerate(allocations):
            category = allocation.get("category", "")
            category_lower = category.lower()
            percentage = allocation.get("percentage", 0)
            amount = allocation.get("investment_amount")

            # ถ้าไม่มี investment_amount ให้คำนวณจาก percentage
            if amount is None and total_investment > 0:
                amount = int(total_investment * percentage / 100)

            if amount is None or amount <= 0:
                continue

            # ตรวจสอบ ประกันบำนาญ
            if "ประกันบำนาญ" in category or "บำนาญ" in category_lower:
                totals["pension_insurance"] += amount
                if amount > limits["pension_insurance"]:
                    violations.append({
                        "category": "ประกันบำนาญ",
                        "allocation_index": idx,
                        "recommended_amount": amount,
                        "legal_max": limits["pension_insurance"],
                        "excess": amount - limits["pension_insurance"],
                        "violation_percentage": ((amount - limits["pension_insurance"]) / limits["pension_insurance"]) * 100 if limits["pension_insurance"] > 0 else 100,
                        "reason": f"เกินขีดจำกัด 15% ของรายได้ ({int(gross_income * 0.15):,}) หรือ 200,000 บาท",
                        "law_reference": "tax_deductions_update280168.pdf, Page 2, Item 13"
                    })

            # ตรวจสอบ RMF (existing + recommended ≤ limit)
            if "rmf" in category_lower:
                totals["rmf"] += amount
                if amount > limits["rmf"]:
                    total_with_existing = amount + existing_rmf
                    violations.append({
                        "category": "RMF",
                        "allocation_index": idx,
                        "recommended_amount": amount,
                        "existing_amount": existing_rmf,
                        "total_with_existing": total_with_existing,
                        "legal_max": abs_limits["rmf"],
                        "remaining_quota": limits["rmf"],
                        "excess": amount - limits["rmf"],
                        "violation_percentage": ((amount - limits["rmf"]) / limits["rmf"]) * 100 if limits["rmf"] > 0 else 100,
                        "reason": f"existing ({existing_rmf:,}) + แนะนำ ({amount:,}) = {total_with_existing:,} > เพดาน {abs_limits['rmf']:,} บาท (30% ของรายได้ หรือ 500,000)",
                        "law_reference": "tax_deductions_update280168.pdf, Page 1, Item 12"
                    })

            # ตรวจสอบ ThaiESG/ThaiESGX
            if "thaiesg" in category_lower or "esg" in category_lower:
                totals["thai_esg"] += amount
                if amount > limits["thai_esg"]:
                    violations.append({
                        "category": "ThaiESG/ThaiESGX",
                        "allocation_index": idx,
                        "recommended_amount": amount,
                        "legal_max": abs_limits["thai_esg"],
                        "remaining_quota": limits["thai_esg"],
                        "excess": amount - limits["thai_esg"],
                        "violation_percentage": ((amount - limits["thai_esg"]) / limits["thai_esg"]) * 100 if limits["thai_esg"] > 0 else 100,
                        "reason": f"เกินขีดจำกัด 30% ของรายได้ ({int(gross_income * 0.30):,}) หรือ 300,000 บาท",
                        "law_reference": "tax_deductions_update280168.pdf, Page 2, Item 21"
                    })

            # ตรวจสอบ ประกันชีวิต (existing + recommended ≤ 100,000)
            if "ประกันชีวิต" in category and "สุขภาพ" not in category and "บำนาญ" not in category:
                totals["life_insurance"] += amount
                if amount > limits["life_insurance"]:
                    total_with_existing = amount + existing_life_insurance
                    violations.append({
                        "category": "ประกันชีวิต",
                        "allocation_index": idx,
                        "recommended_amount": amount,
                        "existing_amount": existing_life_insurance,
                        "total_with_existing": total_with_existing,
                        "legal_max": abs_limits["life_insurance"],
                        "remaining_quota": limits["life_insurance"],
                        "excess": amount - limits["life_insurance"],
                        "violation_percentage": ((amount - limits["life_insurance"]) / limits["life_insurance"]) * 100 if limits["life_insurance"] > 0 else 100,
                        "reason": f"existing ({existing_life_insurance:,}) + แนะนำ ({amount:,}) = {total_with_existing:,} > เพดาน {abs_limits['life_insurance']:,} บาท",
                        "law_reference": "tax_deductions_update280168.pdf, Page 1, Item 8"
                    })

            # ตรวจสอบ ประกันสุขภาพ (existing + recommended ≤ 25,000)
            if "ประกันสุขภาพ" in category or ("สุขภาพ" in category and "ประกันชีวิต" not in category):
                totals["health_insurance"] += amount
                if amount > limits["health_insurance"]:
                    total_with_existing = amount + existing_health_insurance
                    violations.append({
                        "category": "ประกันสุขภาพ",
                        "allocation_index": idx,
                        "recommended_amount": amount,
                        "existing_amount": existing_health_insurance,
                        "total_with_existing": total_with_existing,
                        "legal_max": abs_limits["health_insurance"],
                        "remaining_quota": limits["health_insurance"],
                        "excess": amount - limits["health_insurance"],
                        "violation_percentage": ((amount - limits["health_insurance"]) / limits["health_insurance"]) * 100 if limits["health_insurance"] > 0 else 100,
                        "reason": f"existing ({existing_health_insurance:,}) + แนะนำ ({amount:,}) = {total_with_existing:,} > เพดาน {abs_limits['health_insurance']:,} บาท",
                        "law_reference": "tax_deductions_update280168.pdf, Page 1, Item 9"
                    })

            # Combined (ประกันชีวิตและสุขภาพ)
            if "ประกันชีวิต" in category and "สุขภาพ" in category:
                estimated_life = int(amount * 0.8)
                estimated_health = int(amount * 0.2)
                totals["life_insurance"] += estimated_life
                totals["health_insurance"] += estimated_health

        # เช็ครวม Life + Health Insurance (existing + recommended ≤ 100,000)
        new_combined = totals["life_insurance"] + totals["health_insurance"]
        total_combined = new_combined + existing_combined
        if total_combined > abs_limits["combined_insurance"]:
            violations.append({
                "category": "รวมประกันชีวิต + สุขภาพ",
                "recommended_combined": new_combined,
                "existing_combined": existing_combined,
                "total_amount": total_combined,
                "legal_max": abs_limits["combined_insurance"],
                "excess": total_combined - abs_limits["combined_insurance"],
                "violation_percentage": ((total_combined - abs_limits["combined_insurance"]) / abs_limits["combined_insurance"]) * 100,
                "reason": f"existing ({existing_combined:,}) + แนะนำ ({new_combined:,}) = {total_combined:,} > เพดาน 100,000 บาท",
                "law_reference": "tax_deductions_update280168.pdf, Page 1, Item 8-9"
            })

        # คำนวณคะแนน Legal Compliance
        is_legal = len(violations) == 0
        legal_compliance_score = 100 if is_legal else 0

        # แสดงผลถ้า verbose
        if verbose and violations:
            print(f"\n{Colors.RED}🚨 LEGAL VIOLATIONS DETECTED in Plan {plan.get('plan_id', '?')}{Colors.END}")
            for v in violations:
                amount_display = v.get('recommended_amount') or v.get('total_amount', 0)
                print(f"   {Colors.RED}❌{Colors.END} {v['category']}: {amount_display:,} บาท")
                print(f"      Legal Max: {v['legal_max']:,} บาท")
                print(f"      Excess: {v['excess']:,} บาท ({v['violation_percentage']:.1f}% over)")
                print(f"      Reason: {v['reason']}")

        return {
            "is_legal": is_legal,
            "violations": violations,
            "warnings": warnings,
            "legal_compliance_score": legal_compliance_score,
            "totals": totals,
            "limits": limits,
            "abs_limits": abs_limits,
            "details": {
                "gross_income": gross_income,
                "existing_rmf": existing_rmf,
                "existing_life_insurance": existing_life_insurance,
                "existing_health_insurance": existing_health_insurance,
                "total_violations": len(violations),
                "total_warnings": len(warnings)
            }
        }
    
    def tokenize_thai(self, text: str) -> List[str]:
        """Tokenize ภาษาไทย"""
        if THAI_TOKENIZER_AVAILABLE:
            tokens = word_tokenize(text, engine='newmm')
            # Filter out whitespace tokens
            return [token for token in tokens if token.strip()]
        else:
            return text.split()
    
    def calculate_rouge(self, reference: str, hypothesis: str) -> Dict[str, float]:
        """คำนวณ ROUGE scores - รองรับภาษาไทยด้วย SimpleTokenizer ที่ใช้ PyThaiNLP โดยตรง"""
        # Let SimpleTokenizer handle Thai tokenization directly
        # (ไม่ต้อง pre-tokenize แล้ว join ด้วย space อีกต่อไป — แก้ปัญหา double-tokenization)
        scores = self.rouge_scorer.score(reference, hypothesis)

        return {
            'rouge1_precision': scores['rouge1'].precision,
            'rouge1_recall': scores['rouge1'].recall,
            'rouge1_f1': scores['rouge1'].fmeasure,
            'rouge2_precision': scores['rouge2'].precision,
            'rouge2_recall': scores['rouge2'].recall,
            'rouge2_f1': scores['rouge2'].fmeasure,
            'rougeL_precision': scores['rougeL'].precision,
            'rougeL_recall': scores['rougeL'].recall,
            'rougeL_f1': scores['rougeL'].fmeasure,
        }
    
    def calculate_bleu(self, reference: str, hypothesis: str) -> Dict[str, float]:
        """คำนวณ BLEU score"""
        ref_tokens = self.tokenize_thai(reference)
        hyp_tokens = self.tokenize_thai(hypothesis)
        
        bleu1 = sentence_bleu([ref_tokens], hyp_tokens, weights=(1, 0, 0, 0), smoothing_function=self.smoothing)
        bleu2 = sentence_bleu([ref_tokens], hyp_tokens, weights=(0.5, 0.5, 0, 0), smoothing_function=self.smoothing)
        bleu3 = sentence_bleu([ref_tokens], hyp_tokens, weights=(0.33, 0.33, 0.33, 0), smoothing_function=self.smoothing)
        bleu4 = sentence_bleu([ref_tokens], hyp_tokens, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=self.smoothing)
        
        return {
            'bleu1': bleu1,
            'bleu2': bleu2,
            'bleu3': bleu3,
            'bleu4': bleu4,
        }
    
    def calculate_keypoint_coverage(self, key_points: List[str], ai_full_text: str, use_bertscore: bool = False) -> Dict[str, Any]:
        """
        Calculate key points coverage - checks if each key point is semantically present in AI text

        Args:
            key_points: List of expected key points
            ai_full_text: Full AI generated text (description + plan details)
            use_bertscore: If True, use BERTScore for semantic matching; otherwise use substring matching

        Returns:
            Dictionary with coverage metrics
        """
        if not key_points:
            return {'coverage_ratio': 0.0, 'covered_points': 0, 'total_points': 0}

        covered_points = 0
        point_scores = []

        for key_point in key_points:
            if use_bertscore and BERTSCORE_AVAILABLE:
                # Semantic matching using BERTScore (reuse singleton scorer)
                try:
                    if EvaluationService._bertscore_scorer is None:
                        self.calculate_bertscore("", "")  # trigger lazy init
                    _, _, F1 = EvaluationService._bertscore_scorer.score([ai_full_text], [key_point])
                    score = F1.mean().item()
                    # Threshold: consider covered if BERTScore F1 > 0.7
                    is_covered = score > 0.7
                    point_scores.append(score)
                except:
                    # Fallback to substring matching
                    is_covered = key_point.lower() in ai_full_text.lower()
                    point_scores.append(1.0 if is_covered else 0.0)
            else:
                # Simple substring matching (faster but less accurate)
                is_covered = key_point.lower() in ai_full_text.lower()
                point_scores.append(1.0 if is_covered else 0.0)

            if is_covered:
                covered_points += 1

        coverage_ratio = covered_points / len(key_points) if key_points else 0.0
        avg_score = np.mean(point_scores) if point_scores else 0.0

        return {
            'coverage_ratio': coverage_ratio,
            'covered_points': covered_points,
            'total_points': len(key_points),
            'average_score': avg_score,
            'individual_scores': point_scores
        }

    def evaluate_multi_reference(self, references: List[str], hypothesis: str, use_bertscore: bool = False) -> Dict[str, float]:
        """
        Evaluate against multiple references, take best score per metric.
        Multi-reference evaluation เป็น standard practice ใน MT (Papineni et al., 2002)
        ช่วยลด penalty จากการ paraphrase ที่ถูกต้องแต่ต่างจาก single reference
        """
        best_scores = {}
        for ref in references:
            rouge = self.calculate_rouge(ref, hypothesis)
            bleu = self.calculate_bleu(ref, hypothesis)
            combined = {**rouge, **bleu}
            if use_bertscore:
                bert = self.calculate_bertscore(ref, hypothesis)
                combined.update(bert)
            for key, value in combined.items():
                if isinstance(value, (int, float)):
                    best_scores[key] = max(best_scores.get(key, 0), value)
        return best_scores

    # WangchanBERTa: โมเดลตระกูล RoBERTa-base ที่ถูกฝึกฝนด้วยชุดข้อมูลภาษาไทย 78.5GB
    # ลด Unknown Token จาก 46-52% (mBERT) และเพิ่มความแม่นยำเชิงความหมายสำหรับศัพท์กฎหมายภาษี
    BERTSCORE_MODEL = "airesearch/wangchanberta-base-att-spm-uncased"

    _bertscore_scorer = None  # Singleton — โหลดโมเดลครั้งเดียว

    def calculate_bertscore(self, reference: str, hypothesis: str) -> Dict[str, float]:
        """คำนวณ BERTScore ด้วย WangchanBERTa backbone (แทน mBERT)

        WangchanBERTa ให้ผลดีกว่า mBERT สำหรับภาษาไทยอย่างมีนัยสำคัญ
        เนื่องจากถูก pretrain ด้วยข้อมูลภาษาไทย 78.5GB โดยเฉพาะ
        ref: arxiv.org/abs/2101.09635

        ใช้ BERTScorer class แทน score() function เพื่อ:
        1. patch tokenizer.model_max_length (WangchanBERTa = 1e30 → overflow)
        2. โหลดโมเดลครั้งเดียว (singleton) — ไม่ต้องโหลดใหม่ทุกครั้ง
        """
        if not BERTSCORE_AVAILABLE:
            return {}

        try:
            # Lazy init — โหลดโมเดลครั้งแรกเท่านั้น
            if EvaluationService._bertscore_scorer is None:
                scorer = BERTScorer(
                    model_type=self.BERTSCORE_MODEL,
                    num_layers=9,
                    lang='th',
                )
                # Patch: WangchanBERTa tokenizer มี model_max_length = 1e30
                # ทำให้ tokenizers library OverflowError → ตั้งเป็น 512
                if scorer._tokenizer.model_max_length > 100_000:
                    scorer._tokenizer.model_max_length = 512
                EvaluationService._bertscore_scorer = scorer

            P, R, F1 = EvaluationService._bertscore_scorer.score(
                [hypothesis], [reference],
            )
            return {
                'bertscore_precision': P.mean().item(),
                'bertscore_recall': R.mean().item(),
                'bertscore_f1': F1.mean().item()
            }
        except Exception as e:
            print(f"  {Colors.YELLOW}⚠️  BERTScore error: {e}{Colors.END}")
            return {}
    
    def calculate_numeric_accuracy(self, expected_value: float, actual_value: float, tolerance: float = 0.1) -> Tuple[float, bool]:
        """คำนวณความแม่นยำของตัวเลข"""
        if expected_value == 0:
            return (100.0, actual_value == 0)
        
        error_percentage = abs(expected_value - actual_value) / expected_value
        accuracy = max(0, (1 - error_percentage) * 100)
        is_within_tolerance = error_percentage <= tolerance
        
        return (accuracy, is_within_tolerance)
    
    def get_score_color(self, score, metric_type: str = 'general') -> str:
        """เลือกสีตามคะแนน"""
        if score is None:
            return Colors.YELLOW
        if metric_type == 'accuracy':
            if score >= 90:
                return Colors.GREEN
            elif score >= 75:
                return Colors.YELLOW
            else:
                return Colors.RED
        else:  # text metrics
            if score >= 0.4:
                return Colors.GREEN
            elif score >= 0.25:
                return Colors.YELLOW
            else:
                return Colors.RED
    
    def get_score_emoji(self, score, metric_type: str = 'general') -> str:
        """เลือก emoji ตามคะแนน"""
        if score is None:
            return "➖"
        if metric_type == 'accuracy':
            if score >= 90:
                return "🎯"
            elif score >= 75:
                return "✅"
            else:
                return "⚠️"
        else:  # text metrics
            if score >= 0.4:
                return "🎯"
            elif score >= 0.25:
                return "✅"
            else:
                return "⚠️"
    
    def print_progress_bar(self, value: float, max_value: float = 100, width: int = 30):
        """แสดง progress bar"""
        percentage = (value / max_value) * 100
        filled = int((value / max_value) * width)
        bar = '█' * filled + '░' * (width - filled)
        
        color = self.get_score_color(percentage, 'accuracy')
        emoji = self.get_score_emoji(percentage, 'accuracy')
        
        return f"{emoji} {color}{bar}{Colors.END} {percentage:.1f}%"
    
    #ประเมินแบบหลายชั้น ไม่ดูแค่ข้อความเดียว
    def evaluate_plan(self, expected_plan: Dict[str, Any], ai_plan: Dict[str, Any], use_bertscore: bool = False) -> Dict[str, Any]:
        """
        ประเมิน 1 แผนการลงทุนแบบ Multi-Level Evaluation

        Level 1: Description Similarity (ROUGE, BLEU, BERTScore)
        Level 2: Keyword Coverage
        Level 3: Semantic Similarity (BERTScore)
        Level 4: Key Points Coverage
        """
        results = {
            'text_metrics': {},
            'numeric_metrics': {},
            'structural_metrics': {},
            'multi_level_metrics': {}  # NEW: Separate multi-level scores
        }

        # Extract expected text structure
        expected_text_data = expected_plan.get('expected_text', {})

        # Get AI generated text
        ai_description = ai_plan.get('description', '')
        ai_plan_name = ai_plan.get('plan_name', '')

        # Construct full AI text for key points coverage
        ai_allocations_text = ' '.join([
            f"{alloc.get('category', '')} {' '.join(alloc.get('pros', []))} {' '.join(alloc.get('cons', []))}"
            for alloc in ai_plan.get('allocations', [])
        ])
        ai_full_text = f"{ai_description} {ai_plan_name} {ai_allocations_text}"

        if expected_text_data:
            # ========================================
            # MULTI-LEVEL EVALUATION (Option 3)
            # ========================================

            expected_description = expected_text_data.get('description', '')
            expected_descriptions = expected_text_data.get('descriptions', [])
            expected_keywords = expected_text_data.get('keywords', [])
            expected_key_points = expected_text_data.get('key_points', [])

            # Build references list: use multi-reference if available, fallback to single
            references = expected_descriptions if expected_descriptions else ([expected_description] if expected_description else [])

            # -----------------------------------------
            # LEVEL 1: Description-Only Similarity
            # (Multi-Reference: best score across all references)
            # -----------------------------------------
            if references and ai_description.strip():
                if len(references) > 1:
                    # Multi-reference evaluation — take best score per metric
                    best_scores = self.evaluate_multi_reference(references, ai_description, use_bertscore)
                    for key, value in best_scores.items():
                        results['multi_level_metrics'][f'desc_{key}'] = value
                else:
                    # Single reference — original behavior
                    ref = references[0]
                    rouge_scores = self.calculate_rouge(ref, ai_description)
                    for key, value in rouge_scores.items():
                        results['multi_level_metrics'][f'desc_{key}'] = value

                    bleu_scores = self.calculate_bleu(ref, ai_description)
                    for key, value in bleu_scores.items():
                        results['multi_level_metrics'][f'desc_{key}'] = value

                    if use_bertscore:
                        bert_scores = self.calculate_bertscore(ref, ai_description)
                        for key, value in bert_scores.items():
                            results['multi_level_metrics'][f'desc_{key}'] = value

            # -----------------------------------------
            # LEVEL 2: Keyword Coverage
            # -----------------------------------------
            if expected_keywords:
                keyword_match_count = sum(1 for kw in expected_keywords if kw.lower() in ai_full_text.lower())
                keyword_match_ratio = keyword_match_count / len(expected_keywords)
                results['multi_level_metrics']['keyword_coverage_ratio'] = keyword_match_ratio
                results['multi_level_metrics']['keywords_matched'] = keyword_match_count
                results['multi_level_metrics']['keywords_total'] = len(expected_keywords)

            # -----------------------------------------
            # LEVEL 3: Semantic Similarity (Full Text)
            # -----------------------------------------
            if use_bertscore and ai_full_text.strip():
                expected_full = f"{expected_description} {' '.join(expected_keywords)} {' '.join(expected_key_points)}"
                semantic_scores = self.calculate_bertscore(expected_full, ai_full_text)
                for key, value in semantic_scores.items():
                    results['multi_level_metrics'][f'semantic_{key}'] = value

            # -----------------------------------------
            # LEVEL 4: Key Points Coverage
            # -----------------------------------------
            if expected_key_points:
                keypoint_coverage = self.calculate_keypoint_coverage(
                    expected_key_points,
                    ai_full_text,
                    use_bertscore=False  # Use substring matching for speed
                )
                results['multi_level_metrics']['keypoint_coverage_ratio'] = keypoint_coverage['coverage_ratio']
                results['multi_level_metrics']['keypoints_covered'] = keypoint_coverage['covered_points']
                results['multi_level_metrics']['keypoints_total'] = keypoint_coverage['total_points']
                results['multi_level_metrics']['keypoint_avg_score'] = keypoint_coverage['average_score']

            # ========================================
            # LEGACY METRICS (for backward compatibility)
            # ========================================
            # Get expected plan_name
            expected_plan_name = expected_text_data.get('plan_name', '')

            # Build expected allocations text
            expected_allocs_text = ""
            if 'expected_allocations' in expected_text_data:
                for alloc in expected_text_data['expected_allocations']:
                    cat = alloc.get('category', '')
                    pros = ' '.join(alloc.get('pros', []))
                    cons = ' '.join(alloc.get('cons', []))
                    expected_allocs_text += f" {cat} {pros} {cons}"

            # Build AI allocations text
            ai_allocs_text = ""
            for alloc in ai_plan.get('allocations', []):
                cat = alloc.get('category', '')
                pros = ' '.join(alloc.get('pros', []))
                cons = ' '.join(alloc.get('cons', []))
                ai_allocs_text += f" {cat} {pros} {cons}"

            # Include plan_name and allocations in legacy comparison
            ai_text_legacy = f"{ai_description} {ai_plan_name} {ai_allocs_text}"
            expected_text_legacy = f"{expected_description} {expected_plan_name} {' '.join(expected_keywords)} {' '.join(expected_key_points)} {expected_allocs_text}"

            if expected_text_legacy.strip() and ai_text_legacy.strip():
                rouge_legacy = self.calculate_rouge(expected_text_legacy, ai_text_legacy)
                results['text_metrics'].update(rouge_legacy)

                bleu_legacy = self.calculate_bleu(expected_text_legacy, ai_text_legacy)
                results['text_metrics'].update(bleu_legacy)

                if use_bertscore:
                    bert_legacy = self.calculate_bertscore(expected_text_legacy, ai_text_legacy)
                    results['text_metrics'].update(bert_legacy)

                if expected_keywords:
                    keyword_match_count = sum(1 for kw in expected_keywords if kw.lower() in ai_text_legacy.lower())
                    keyword_match_ratio = keyword_match_count / len(expected_keywords)
                    results['text_metrics']['keyword_match_ratio'] = keyword_match_ratio

        else:
            # Legacy: fallback to old structure (no expected_text)
            expected_text = f"{expected_plan.get('description', '')} {expected_plan.get('plan_name', '')}"
            ai_text = f"{ai_description} {ai_plan_name}"

            if expected_text.strip() and ai_text.strip():
                rouge_scores = self.calculate_rouge(expected_text, ai_text)
                results['text_metrics'].update(rouge_scores)

                bleu_scores = self.calculate_bleu(expected_text, ai_text)
                results['text_metrics'].update(bleu_scores)

                if use_bertscore:
                    bert_scores = self.calculate_bertscore(expected_text, ai_text)
                    results['text_metrics'].update(bert_scores)
        
        # 2. ประเมินข้อความ allocation categories
        expected_allocs = expected_plan.get('allocations', [])
        ai_allocs = ai_plan.get('allocations', [])
        
        allocation_text_scores = []
        for exp_alloc, ai_alloc in zip(expected_allocs, ai_allocs[:len(expected_allocs)]):
            exp_cat = exp_alloc.get('category', '')
            ai_cat = ai_alloc.get('category', '')
            
            if exp_cat and ai_cat:
                rouge = self.calculate_rouge(exp_cat, ai_cat)
                allocation_text_scores.append(rouge.get('rouge1_f1', 0))
        
        if allocation_text_scores:
            results['text_metrics']['avg_allocation_text_similarity'] = np.mean(allocation_text_scores)
        
        # 3. ประเมินตัวเลข
        numeric_fields = ['total_investment', 'total_tax_saving']
        for field in numeric_fields:
            expected_val = expected_plan.get(field, 0)
            ai_val = ai_plan.get(field, 0)
            
            if expected_val > 0:
                accuracy, within_tolerance = self.calculate_numeric_accuracy(expected_val, ai_val, tolerance=0.15)
                
                results['numeric_metrics'][field] = {
                    'expected': expected_val,
                    'actual': ai_val,
                    'accuracy': accuracy,
                    'within_tolerance': within_tolerance,
                    'error_percentage': abs(expected_val - ai_val) / expected_val * 100 if expected_val > 0 else 0
                }
        
        # 4. ประเมินโครงสร้าง
        results['structural_metrics'] = {
            'expected_allocation_count': len(expected_allocs),
            'actual_allocation_count': len(ai_allocs),
            'has_correct_structure': 'allocations' in ai_plan and len(ai_allocs) > 0
        }
        
        # 5. ประเมิน allocations
        allocation_scores = []
        for i, (exp_alloc, ai_alloc) in enumerate(zip(expected_allocs, ai_allocs[:len(expected_allocs)])):
            alloc_score = self.evaluate_allocation(exp_alloc, ai_alloc)
            allocation_scores.append(alloc_score)
        
        if allocation_scores:
            results['allocation_metrics'] = {
                'individual_scores': allocation_scores,
                'average_investment_accuracy': np.mean([s.get('investment_accuracy', 0) for s in allocation_scores]),
                'average_tax_saving_accuracy': np.mean([s.get('tax_saving_accuracy', 0) for s in allocation_scores])
            }
        
        return results
    
    def evaluate_allocation(self, expected_alloc: Dict[str, Any], ai_alloc: Dict[str, Any]) -> Dict[str, float]:
        """ประเมิน 1 allocation item"""
        results = {}
        
        # Investment amount accuracy
        exp_inv = expected_alloc.get('investment_amount', 0)
        ai_inv = ai_alloc.get('investment_amount', 0)
        if exp_inv > 0:
            inv_accuracy, _ = self.calculate_numeric_accuracy(exp_inv, ai_inv, tolerance=0.2)
            results['investment_accuracy'] = inv_accuracy
        
        # Tax saving accuracy
        exp_tax = expected_alloc.get('tax_saving', 0)
        ai_tax = ai_alloc.get('tax_saving', 0)
        if exp_tax > 0:
            tax_accuracy, _ = self.calculate_numeric_accuracy(exp_tax, ai_tax, tolerance=0.2)
            results['tax_saving_accuracy'] = tax_accuracy
        
        # Category match
        results['category_match'] = expected_alloc.get('category', '').lower() in ai_alloc.get('category', '').lower()
        
        return results
    
    # =========================================================================
    # NEW METRICS: Plan Diversity Score + Format Validity
    # =========================================================================

    def calculate_plan_diversity(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        วัดว่า 3 แผนต่างกันจริงไหม — ผู้ใช้ได้ตัวเลือกที่มีความหมาย

        วัด 3 มิติ:
        1. Category Diversity  — แต่ละแผนใช้ category ต่างกันแค่ไหน
        2. Allocation Diversity — สัดส่วน % ต่างกันแค่ไหน
        3. Risk Profile Diversity — conservative ≠ balanced ≠ growth จริงไหม

        Returns:
            {
                "diversity_score": 0-100,
                "category_diversity": 0-1,
                "allocation_diversity": 0-1,
                "risk_profile_diversity": 0-1,
                "details": {...}
            }
        """
        plans = ai_response.get("plans", [])
        if len(plans) < 2:
            return {
                "diversity_score": 0,
                "category_diversity": 0,
                "allocation_diversity": 0,
                "risk_profile_diversity": 0,
                "details": {"reason": "ไม่ถึง 2 แผน"}
            }

        # ─── 1. Category Diversity (Jaccard distance ระหว่างคู่แผน) ───
        plan_categories = []
        for plan in plans[:3]:
            cats = set()
            for alloc in plan.get("allocations", []):
                cat = alloc.get("category", "").strip()
                if cat:
                    cats.add(cat)
            plan_categories.append(cats)

        jaccard_distances = []
        for i in range(len(plan_categories)):
            for j in range(i + 1, len(plan_categories)):
                a, b = plan_categories[i], plan_categories[j]
                if a or b:
                    union = a | b
                    intersection = a & b
                    # Jaccard distance = 1 - (intersection / union)
                    jaccard_dist = 1 - (len(intersection) / len(union)) if union else 0
                    jaccard_distances.append(jaccard_dist)

        category_diversity = np.mean(jaccard_distances) if jaccard_distances else 0

        # ─── 2. Allocation Diversity (ค่าเฉลี่ย absolute % difference) ───
        plan_vectors = []
        all_cats_ordered = sorted(set().union(*plan_categories))

        for plan in plans[:3]:
            alloc_map = {}
            for alloc in plan.get("allocations", []):
                cat = alloc.get("category", "").strip()
                pct = alloc.get("percentage", 0)
                if cat:
                    alloc_map[cat] = pct
            vector = [alloc_map.get(c, 0) for c in all_cats_ordered]
            plan_vectors.append(vector)

        pct_diffs = []
        for i in range(len(plan_vectors)):
            for j in range(i + 1, len(plan_vectors)):
                diff = np.mean(np.abs(np.array(plan_vectors[i]) - np.array(plan_vectors[j])))
                pct_diffs.append(diff)

        # Normalize: diff of 10+ percentage points = good diversity
        avg_pct_diff = np.mean(pct_diffs) if pct_diffs else 0
        allocation_diversity = min(1.0, avg_pct_diff / 15.0)

        # ─── 3. Risk Profile Diversity ───
        # ตรวจว่า conservative เน้นประกัน, growth เน้นกองทุน
        insurance_cats = {"ประกันชีวิต", "ประกันสุขภาพ", "ประกันบำนาญ", "ประกันชีวิตและสุขภาพ"}
        fund_cats = {"RMF", "ThaiESG", "ThaiESGX", "Thai ESGX"}

        plan_insurance_pcts = []
        for plan in plans[:3]:
            ins_pct = 0
            for alloc in plan.get("allocations", []):
                cat = alloc.get("category", "").strip()
                pct = alloc.get("percentage", 0)
                # ตรวจว่าเป็นหมวดประกันหรือไม่
                is_insurance = any(ic in cat for ic in insurance_cats)
                if is_insurance:
                    ins_pct += pct
            plan_insurance_pcts.append(ins_pct)

        # Conservative (plan 1) ควรมี insurance% สูงกว่า Growth (plan 3)
        risk_profile_diversity = 0.0
        if len(plan_insurance_pcts) >= 3:
            # ถ้า plan1 insurance > plan3 insurance = ดี (progression ถูกทิศ)
            if plan_insurance_pcts[0] > plan_insurance_pcts[2]:
                risk_profile_diversity = 1.0
            elif plan_insurance_pcts[0] > plan_insurance_pcts[1]:
                risk_profile_diversity = 0.5
            else:
                # ตรวจว่ามี total_investment ต่างกันไหม (fallback)
                investments = [p.get("total_investment", 0) for p in plans[:3]]
                if len(set(investments)) >= 2:
                    risk_profile_diversity = 0.3
                else:
                    risk_profile_diversity = 0.0

        # ─── รวมคะแนน (weighted) ───
        diversity_score = (
            category_diversity * 35 +
            allocation_diversity * 35 +
            risk_profile_diversity * 30
        )

        return {
            "diversity_score": round(diversity_score, 1),
            "category_diversity": round(category_diversity, 4),
            "allocation_diversity": round(allocation_diversity, 4),
            "risk_profile_diversity": round(risk_profile_diversity, 4),
            "details": {
                "plan_categories": [sorted(list(cats)) for cats in plan_categories],
                "plan_insurance_pcts": plan_insurance_pcts,
                "avg_pct_diff": round(avg_pct_diff, 2),
            }
        }

    def validate_format(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        ตรวจว่า AI output มี format ที่ Frontend ใช้งานได้จริง

        ตรวจ:
        1. มี plans array ที่มี 3 แผน
        2. แต่ละ plan มี required fields ครบ + data type ถูก
        3. แต่ละ allocation มี required fields ครบ
        4. Percentage รวม ~100%
        5. ไม่มี placeholder text เช่น [ระบุ...]

        Returns:
            {
                "format_score": 0-100,
                "is_valid": True/False,
                "checks": {...},
                "errors": [...]
            }
        """
        errors = []
        checks = {}
        total_checks = 0
        passed_checks = 0

        # ─── Check 1: plans array exists ───
        total_checks += 1
        plans = ai_response.get("plans", [])
        if isinstance(plans, list) and len(plans) > 0:
            passed_checks += 1
            checks["has_plans_array"] = True
        else:
            errors.append("ไม่มี plans array หรือว่างเปล่า")
            checks["has_plans_array"] = False

        # ─── Check 2: มี 3 แผน ───
        total_checks += 1
        if len(plans) >= 3:
            passed_checks += 1
            checks["has_3_plans"] = True
        else:
            errors.append(f"มีเพียง {len(plans)} แผน (ต้องการ 3)")
            checks["has_3_plans"] = False

        # ─── Check 3-5: แต่ละ plan มี required fields ───
        PLAN_REQUIRED = {
            "plan_id": str,
            "plan_name": str,
            "plan_type": str,
            "description": str,
            "total_investment": (int, float),
            "total_tax_saving": (int, float),
            "overall_risk": str,
            "allocations": list,
        }

        ALLOC_REQUIRED = {
            "category": str,
            "percentage": (int, float),
            "risk_level": str,
            "pros": list,
            "cons": list,
        }

        for idx, plan in enumerate(plans[:3]):
            plan_label = f"Plan {idx + 1}"

            # Plan-level fields
            for field, expected_type in PLAN_REQUIRED.items():
                total_checks += 1
                value = plan.get(field)
                if value is None:
                    errors.append(f"{plan_label}: ไม่มี field '{field}'")
                elif not isinstance(value, expected_type):
                    errors.append(f"{plan_label}: '{field}' ควรเป็น {expected_type.__name__ if isinstance(expected_type, type) else expected_type} แต่ได้ {type(value).__name__}")
                else:
                    passed_checks += 1

            # Description ไม่ว่าง
            total_checks += 1
            desc = plan.get("description", "")
            if isinstance(desc, str) and len(desc.strip()) > 10:
                passed_checks += 1
            else:
                errors.append(f"{plan_label}: description ว่างหรือสั้นเกินไป")

            # Allocations
            allocs = plan.get("allocations", [])
            total_checks += 1
            if len(allocs) >= 2:
                passed_checks += 1
            else:
                errors.append(f"{plan_label}: allocations น้อยกว่า 2 รายการ")

            for alloc_idx, alloc in enumerate(allocs):
                for field, expected_type in ALLOC_REQUIRED.items():
                    total_checks += 1
                    value = alloc.get(field)
                    if value is None:
                        errors.append(f"{plan_label} Alloc {alloc_idx + 1}: ไม่มี '{field}'")
                    elif not isinstance(value, expected_type):
                        errors.append(f"{plan_label} Alloc {alloc_idx + 1}: '{field}' type ผิด")
                    else:
                        passed_checks += 1

            # Percentage sum ~100%
            total_checks += 1
            pct_sum = sum(a.get("percentage", 0) for a in allocs)
            if 95 <= pct_sum <= 105:
                passed_checks += 1
                checks[f"plan_{idx+1}_pct_sum"] = round(pct_sum, 1)
            else:
                errors.append(f"{plan_label}: percentage รวม = {pct_sum:.1f}% (ควร 95-105%)")
                checks[f"plan_{idx+1}_pct_sum"] = round(pct_sum, 1)

        # ─── Check: placeholder detection ───
        total_checks += 1
        placeholder_patterns = ["[ระบุ", "[ใส่", "ระบุเลข", "[fill", "[TODO"]
        has_placeholder = False
        for plan in plans[:3]:
            desc = plan.get("description", "")
            if any(p in desc for p in placeholder_patterns):
                has_placeholder = True
                break
        if not has_placeholder:
            passed_checks += 1
            checks["no_placeholders"] = True
        else:
            errors.append("พบ placeholder text ใน description (เช่น [ระบุเลขมาตรา])")
            checks["no_placeholders"] = False

        format_score = round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0

        return {
            "format_score": format_score,
            "is_valid": len(errors) == 0,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "checks": checks,
            "errors": errors[:10],  # จำกัด 10 errors
        }

    #รวม3แผน
    def evaluate_complete_response(self, expected_plans: Dict[str, Dict], ai_response: Dict[str, Any], use_bertscore: bool = False) -> Dict[str, Any]:
        """ประเมินคำตอบทั้งหมด (3 แผน)"""
        results = {
            'overall_metrics': {},
            'plan_metrics': {}
        }
        
        ai_plans = ai_response.get('plans', [])
        
        results['overall_metrics']['expected_plan_count'] = 3
        results['overall_metrics']['actual_plan_count'] = len(ai_plans)
        results['overall_metrics']['has_all_plans'] = len(ai_plans) >= 3
        
        plan_keys = ['plan_1', 'plan_2', 'plan_3']
        all_text_scores = []
        all_numeric_scores = []
        all_multi_level_scores = []  # NEW: Track multi-level metrics

        for i, (plan_key, ai_plan) in enumerate(zip(plan_keys, ai_plans[:3])):
            expected_plan = expected_plans.get(plan_key, {})

            if expected_plan:
                plan_results = self.evaluate_plan(expected_plan, ai_plan, use_bertscore)
                results['plan_metrics'][f'plan_{i+1}'] = plan_results

                if 'text_metrics' in plan_results:
                    all_text_scores.append(plan_results['text_metrics'])
                if 'numeric_metrics' in plan_results:
                    all_numeric_scores.append(plan_results['numeric_metrics'])
                if 'multi_level_metrics' in plan_results:  # NEW: Collect multi-level metrics
                    all_multi_level_scores.append(plan_results['multi_level_metrics'])

        # คำนวณค่าเฉลี่ย text metrics
        if all_text_scores:
            avg_text_metrics = {}
            for key in all_text_scores[0].keys():
                values = [s[key] for s in all_text_scores if key in s]
                if values:
                    avg_text_metrics[f'avg_{key}'] = np.mean(values)
            results['overall_metrics']['text_metrics'] = avg_text_metrics

        # NEW: คำนวณค่าเฉลี่ย multi-level metrics
        if all_multi_level_scores:
            avg_multi_level_metrics = {}
            for key in all_multi_level_scores[0].keys():
                values = [s[key] for s in all_multi_level_scores if key in s and s[key] is not None]
                if values:
                    avg_multi_level_metrics[f'avg_{key}'] = np.mean(values)
            results['overall_metrics']['multi_level_metrics'] = avg_multi_level_metrics

        # คำนวณค่าเฉลี่ย numeric metrics
        if all_numeric_scores:
            all_accuracies = []
            for plan_numerics in all_numeric_scores:
                for field, data in plan_numerics.items():
                    if isinstance(data, dict) and 'accuracy' in data:
                        all_accuracies.append(data['accuracy'])

            if all_accuracies:
                results['overall_metrics']['avg_numeric_accuracy'] = np.mean(all_accuracies)

        return results
    
    def print_evaluation_report(self, results: Dict[str, Any], test_case_name: str = "", save_to_file: bool = False, output_dir: Path = None):
        """แสดงรายงานที่สวยงามและอ่านง่าย"""
        
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.CYAN}📊 EVALUATION REPORT{Colors.END}")
        if test_case_name:
            print(f"{Colors.YELLOW}Test Case: {test_case_name}{Colors.END}")
        print("="*80 + "\n")

        # 🆕 Legal Compliance Summary (แสดงก่อนเป็นอันดับแรก)
        if 'legal_compliance' in results:
            legal = results['legal_compliance']
            has_violations = legal.get('has_violations', False)
            overall_legal_score = legal.get('overall_score', 100)

            print(f"{Colors.BOLD}⚖️  LEGAL COMPLIANCE CHECK{Colors.END}")
            print("─" * 80)

            if has_violations:
                print(f"  Status: {Colors.RED}❌ FAILED{Colors.END}")
                print(f"  Score:  {Colors.RED}{overall_legal_score}%{Colors.END}")
                print(f"\n  {Colors.RED}🚨 Legal Violations Detected:{Colors.END}\n")

                for idx, check in enumerate(legal.get('checks', []), 1):
                    if not check['is_legal']:
                        print(f"  {Colors.RED}Plan {idx}:{Colors.END}")
                        for violation in check['violations']:
                            v_amount = violation.get('recommended_amount') or violation.get('total_amount', 0)
                            print(f"    {Colors.RED}❌{Colors.END} {violation['category']}: {v_amount:,} บาท")
                            print(f"       Legal Max: {violation['legal_max']:,} บาท")
                            print(f"       Excess: {violation['excess']:,} บาท ({violation['violation_percentage']:.1f}% over)")
                            print(f"       Reason: {violation['reason']}")
                            print(f"       Law: {violation['law_reference']}")
                            print()
            else:
                print(f"  Status: {Colors.GREEN}✅ PASSED{Colors.END}")
                print(f"  Score:  {Colors.GREEN}{overall_legal_score}%{Colors.END}")
                print(f"  {Colors.GREEN}All plans comply with Thai Tax Law 2568{Colors.END}")

            print()

        # Overall Summary
        if 'overall_metrics' in results:
            overall = results['overall_metrics']
            
            print(f"{Colors.BOLD}🎯 OVERALL SUMMARY{Colors.END}")
            print("─" * 80)
            
            # Plans count
            plan_count = overall.get('actual_plan_count', 0)
            expected_count = overall.get('expected_plan_count', 3)
            has_all = overall.get('has_all_plans', False)
            
            status_emoji = "✅" if has_all else "❌"
            status_color = Colors.GREEN if has_all else Colors.RED
            
            print(f"  Plans Generated: {status_color}{plan_count}/{expected_count} {status_emoji}{Colors.END}")
            
            # Numeric Accuracy
            if 'avg_numeric_accuracy' in overall:
                acc = overall['avg_numeric_accuracy']
                print(f"\n  💰 Numeric Accuracy:")
                print(f"     {self.print_progress_bar(acc, 100, 40)}")
                print(f"     Value: {acc:.2f}%")
            
            # Text Similarity
            if 'text_metrics' in overall:
                text_m = overall['text_metrics']
                print(f"\n  📝 Text Similarity:")
                
                if 'avg_rouge1_f1' in text_m:
                    score = text_m['avg_rouge1_f1']
                    color = self.get_score_color(score, 'general')
                    emoji = self.get_score_emoji(score, 'general')
                    print(f"     {emoji} ROUGE-1 F1: {color}{score:.4f}{Colors.END}")
                
                if 'avg_rouge2_f1' in text_m:
                    score = text_m['avg_rouge2_f1']
                    color = self.get_score_color(score, 'general')
                    emoji = self.get_score_emoji(score, 'general')
                    print(f"     {emoji} ROUGE-2 F1: {color}{score:.4f}{Colors.END}")
                
                if 'avg_rougeL_f1' in text_m:
                    score = text_m['avg_rougeL_f1']
                    color = self.get_score_color(score, 'general')
                    emoji = self.get_score_emoji(score, 'general')
                    print(f"     {emoji} ROUGE-L F1: {color}{score:.4f}{Colors.END}")
                
                if 'avg_bleu4' in text_m:
                    score = text_m['avg_bleu4']
                    color = self.get_score_color(score, 'general')
                    emoji = self.get_score_emoji(score, 'general')
                    print(f"     {emoji} BLEU-4:     {color}{score:.4f}{Colors.END}")
                
                if 'avg_bertscore_f1' in text_m:
                    score = text_m['avg_bertscore_f1']
                    color = self.get_score_color(score, 'general')
                    emoji = self.get_score_emoji(score, 'general')
                    print(f"     {emoji} BERTScore:  {color}{score:.4f}{Colors.END}")

            # NitiBench (Thai Legal Quality)
            if 'nitibench' in results:
                nb = results['nitibench']
                print(f"\n  ⚖️  NitiBench (Thai Legal Quality):")

                # Coverage
                cov = nb.get('coverage', {})
                cov_score = cov.get('coverage_score', 0)
                cov_ratio = cov.get('coverage_ratio', 0)
                cov_color = Colors.GREEN if cov_score == 100 else Colors.YELLOW if cov_score == 50 else Colors.RED
                cov_emoji = "✅" if cov_score == 100 else "⚠️" if cov_score == 50 else "❌"
                print(f"     {cov_emoji} Coverage:      {cov_color}{cov_score}/100{Colors.END} ({cov.get('covered', 0)}/{cov.get('total', 0)} key points, ratio={cov_ratio:.2%})")

                # Consistency
                con = nb.get('consistency', {})
                con_score = con.get('consistency_score', 0)
                con_color = Colors.GREEN if con_score == 1 else Colors.RED
                con_emoji = "✅" if con_score == 1 else "❌"
                con_detail = ""
                if con.get('contradictions'):
                    reasons = [ct['reason'][:50] for ct in con['contradictions'][:2]]
                    con_detail = f" — {'; '.join(reasons)}"
                print(f"     {con_emoji} Consistency:   {con_color}{con_score}/1{Colors.END}{con_detail}")

                # Citation F1
                cite = nb.get('citation', {})
                cite_f1 = cite.get('citation_f1')
                cite_color = self.get_score_color(cite_f1, 'general')
                cite_emoji = self.get_score_emoji(cite_f1, 'general')
                cite_detail = ""
                if cite.get('missing'):
                    cite_detail = f" (missing: {', '.join(cite['missing'][:3])})"
                cite_str = f"{cite_f1:.4f}" if cite_f1 is not None else "N/A"
                print(f"     {cite_emoji} Citation F1:   {cite_color}{cite_str}{Colors.END}{cite_detail}")

                # Joint Score
                joint = nb.get('joint_score', 0)
                joint_color = self.get_score_color(joint, 'general')
                joint_emoji = self.get_score_emoji(joint, 'general')
                print(f"     {joint_emoji} Joint Score:   {joint_color}{joint:.4f}{Colors.END} (Coverage 40% + Consistency 35% + Citation 25%)")

            print()
        
        # Plan by Plan
        if 'plan_metrics' in results:
            print(f"\n{Colors.BOLD}📋 DETAILED RESULTS BY PLAN{Colors.END}")
            print("="*80 + "\n")
            
            for plan_key, plan_results in results['plan_metrics'].items():
                plan_num = plan_key.split('_')[1]
                print(f"{Colors.BOLD}{Colors.BLUE}▶ Plan {plan_num}{Colors.END}")
                print("─" * 80)
                
                # Numeric metrics
                if 'numeric_metrics' in plan_results:
                    num_m = plan_results['numeric_metrics']
                    
                    for field, data in num_m.items():
                        if isinstance(data, dict):
                            acc = data['accuracy']
                            expected = data['expected']
                            actual = data['actual']
                            within = data['within_tolerance']
                            
                            status = "✅" if within else "⚠️"
                            color = Colors.GREEN if within else Colors.YELLOW
                            
                            field_display = field.replace('_', ' ').title()
                            
                            print(f"\n  {Colors.BOLD}{field_display}:{Colors.END} {status}")
                            print(f"    Expected: {expected:>12,.0f} บาท")
                            print(f"    Actual:   {actual:>12,.0f} บาท")
                            print(f"    Accuracy: {color}{acc:.1f}%{Colors.END}")
                
                # Text metrics
                if 'text_metrics' in plan_results:
                    text_m = plan_results['text_metrics']
                    print(f"\n  {Colors.BOLD}Text Similarity:{Colors.END}")
                    
                    if 'rouge1_f1' in text_m:
                        print(f"    ROUGE-1 F1: {text_m['rouge1_f1']:.4f}")
                    if 'bleu4' in text_m:
                        print(f"    BLEU-4:     {text_m['bleu4']:.4f}")
                    if 'bertscore_f1' in text_m:
                        print(f"    BERTScore:  {text_m['bertscore_f1']:.4f}")
                
                # Allocation metrics
                if 'allocation_metrics' in plan_results:
                    alloc_m = plan_results['allocation_metrics']
                    print(f"\n  {Colors.BOLD}Allocation Accuracy:{Colors.END}")
                    
                    inv_acc = alloc_m['average_investment_accuracy']
                    tax_acc = alloc_m['average_tax_saving_accuracy']
                    
                    print(f"    Investment: {self.print_progress_bar(inv_acc, 100, 30)}")
                    print(f"    Tax Saving: {self.print_progress_bar(tax_acc, 100, 30)}")
                
                print()
        
        print("="*80 + "\n")
        
        # Save to file
        if save_to_file and output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            safe_name = test_case_name.replace(' ', '_').replace('/', '_')
            report_file = output_dir / f"report_{safe_name}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"{Colors.GREEN}💾 Report saved to: {report_file}{Colors.END}\n")
    ##ผลรวม 20 testcase
    def generate_summary_statistics(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """สร้างสถิติสรุป - รวม Multi-Level Metrics"""
        summary = {
            'total_test_cases': len(all_results),
            'text_metrics': {},  # Legacy metrics
            'numeric_metrics': {},
            'multi_level_metrics': {},  # NEW: Multi-level evaluation summary
            'nitibench_metrics': {},  # NitiBench Thai Legal Quality
        }

        # Legacy metrics
        all_rouge1 = []
        all_rouge2 = []
        all_rougeL = []
        all_bleu4 = []
        all_bertscore = []
        all_keyword_match = []
        all_numeric_acc = []

        # Multi-level metrics
        all_desc_rouge1_f1 = []
        all_desc_rougeL_f1 = []
        all_desc_bleu4 = []
        all_desc_bertscore_f1 = []
        all_keyword_coverage = []
        all_semantic_bertscore_f1 = []
        all_keypoint_coverage = []

        # NitiBench metrics
        all_nb_coverage = []
        all_nb_consistency = []
        all_nb_citation_f1 = []
        all_nb_joint = []

        # 🆕 New metrics
        all_diversity_scores = []
        all_format_scores = []

        for result in all_results:
            if 'overall_metrics' in result:
                overall = result['overall_metrics']

                # Legacy text metrics
                if 'text_metrics' in overall:
                    text_m = overall['text_metrics']
                    if 'avg_rouge1_f1' in text_m:
                        all_rouge1.append(text_m['avg_rouge1_f1'])
                    if 'avg_rouge2_f1' in text_m:
                        all_rouge2.append(text_m['avg_rouge2_f1'])
                    if 'avg_rougeL_f1' in text_m:
                        all_rougeL.append(text_m['avg_rougeL_f1'])
                    if 'avg_bleu4' in text_m:
                        all_bleu4.append(text_m['avg_bleu4'])
                    if 'avg_bertscore_f1' in text_m:
                        all_bertscore.append(text_m['avg_bertscore_f1'])
                    if 'avg_keyword_match_ratio' in text_m:
                        all_keyword_match.append(text_m['avg_keyword_match_ratio'])

                # Multi-level metrics
                if 'multi_level_metrics' in overall:
                    ml_m = overall['multi_level_metrics']
                    if 'avg_desc_rouge1_f1' in ml_m:
                        all_desc_rouge1_f1.append(ml_m['avg_desc_rouge1_f1'])
                    if 'avg_desc_rougeL_f1' in ml_m:
                        all_desc_rougeL_f1.append(ml_m['avg_desc_rougeL_f1'])
                    if 'avg_desc_bleu4' in ml_m:
                        all_desc_bleu4.append(ml_m['avg_desc_bleu4'])
                    if 'avg_desc_bertscore_f1' in ml_m:
                        all_desc_bertscore_f1.append(ml_m['avg_desc_bertscore_f1'])
                    if 'avg_keyword_coverage_ratio' in ml_m:
                        all_keyword_coverage.append(ml_m['avg_keyword_coverage_ratio'])
                    if 'avg_semantic_bertscore_f1' in ml_m:
                        all_semantic_bertscore_f1.append(ml_m['avg_semantic_bertscore_f1'])
                    if 'avg_keypoint_coverage_ratio' in ml_m:
                        all_keypoint_coverage.append(ml_m['avg_keypoint_coverage_ratio'])

                if 'avg_numeric_accuracy' in overall:
                    all_numeric_acc.append(overall['avg_numeric_accuracy'])

            # NitiBench metrics (stored at top level of result, not in overall_metrics)
            if 'nitibench' in result:
                nb = result['nitibench']
                if 'coverage' in nb:
                    all_nb_coverage.append(nb['coverage']['coverage_score'])
                if 'consistency' in nb:
                    all_nb_consistency.append(nb['consistency']['consistency_score'])
                if 'citation' in nb:
                    cite_f1 = nb['citation']['citation_f1']
                    if cite_f1 is not None:  # ข้าม cases ที่ไม่มี expected citations
                        all_nb_citation_f1.append(cite_f1)
                if 'joint_score' in nb:
                    all_nb_joint.append(nb['joint_score'])

            # 🆕 Plan Diversity
            if 'plan_diversity' in result:
                ds = result['plan_diversity'].get('diversity_score')
                if ds is not None:
                    all_diversity_scores.append(ds)

            # 🆕 Format Validity
            if 'format_validity' in result:
                fs = result['format_validity'].get('format_score')
                if fs is not None:
                    all_format_scores.append(fs)

        # Legacy metrics aggregation
        if all_rouge1:
            summary['text_metrics']['avg_rouge1_f1'] = np.mean(all_rouge1)
        if all_rouge2:
            summary['text_metrics']['avg_rouge2_f1'] = np.mean(all_rouge2)
        if all_rougeL:
            summary['text_metrics']['avg_rougeL_f1'] = np.mean(all_rougeL)
        if all_bleu4:
            summary['text_metrics']['avg_bleu4'] = np.mean(all_bleu4)
        if all_bertscore:
            summary['text_metrics']['avg_bertscore_f1'] = np.mean(all_bertscore)
        if all_keyword_match:
            summary['text_metrics']['avg_keyword_match_ratio'] = np.mean(all_keyword_match)

        # Multi-level metrics aggregation
        if all_desc_rouge1_f1:
            summary['multi_level_metrics']['avg_desc_rouge1_f1'] = np.mean(all_desc_rouge1_f1)
        if all_desc_rougeL_f1:
            summary['multi_level_metrics']['avg_desc_rougeL_f1'] = np.mean(all_desc_rougeL_f1)
        if all_desc_bleu4:
            summary['multi_level_metrics']['avg_desc_bleu4'] = np.mean(all_desc_bleu4)
        if all_desc_bertscore_f1:
            summary['multi_level_metrics']['avg_desc_bertscore_f1'] = np.mean(all_desc_bertscore_f1)
        if all_keyword_coverage:
            summary['multi_level_metrics']['avg_keyword_coverage_ratio'] = np.mean(all_keyword_coverage)
        if all_semantic_bertscore_f1:
            summary['multi_level_metrics']['avg_semantic_bertscore_f1'] = np.mean(all_semantic_bertscore_f1)
        if all_keypoint_coverage:
            summary['multi_level_metrics']['avg_keypoint_coverage_ratio'] = np.mean(all_keypoint_coverage)

        # Numeric metrics
        if all_numeric_acc:
            summary['numeric_metrics']['avg_accuracy'] = np.mean(all_numeric_acc)
            summary['numeric_metrics']['min_accuracy'] = np.min(all_numeric_acc)
            summary['numeric_metrics']['max_accuracy'] = np.max(all_numeric_acc)

        # NitiBench metrics aggregation
        if all_nb_coverage:
            summary['nitibench_metrics']['avg_coverage_score'] = np.mean(all_nb_coverage)
        if all_nb_consistency:
            summary['nitibench_metrics']['avg_consistency_score'] = np.mean(all_nb_consistency)
        if all_nb_citation_f1:
            summary['nitibench_metrics']['avg_citation_f1'] = np.mean(all_nb_citation_f1)
        if all_nb_joint:
            summary['nitibench_metrics']['avg_joint_score'] = np.mean(all_nb_joint)

        # 🆕 New metrics aggregation
        if all_diversity_scores:
            summary['plan_diversity_metrics'] = {
                'avg_diversity_score': round(float(np.mean(all_diversity_scores)), 1),
                'min_diversity_score': round(float(np.min(all_diversity_scores)), 1),
                'max_diversity_score': round(float(np.max(all_diversity_scores)), 1),
            }
        if all_format_scores:
            summary['format_validity_metrics'] = {
                'avg_format_score': round(float(np.mean(all_format_scores)), 1),
                'min_format_score': round(float(np.min(all_format_scores)), 1),
                'perfect_format_count': sum(1 for s in all_format_scores if s == 100.0),
                'total_evaluated': len(all_format_scores),
            }

        return summary
    
    def print_summary_report(self, summary: Dict[str, Any]):
        """แสดงรายงานสรุปแบบสวยงาม"""
        
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.HEADER}📈 FINAL SUMMARY STATISTICS{Colors.END}")
        print("="*80 + "\n")
        
        total = summary.get('total_test_cases', 0)
        print(f"{Colors.BOLD}Total Test Cases:{Colors.END} {Colors.CYAN}{total}{Colors.END}\n")
        
        # Multi-Level Metrics (PRIMARY METRICS - MOST IMPORTANT!)
        if 'multi_level_metrics' in summary and summary['multi_level_metrics']:
            print(f"{Colors.BOLD}{Colors.CYAN}🎯 DESCRIPTION TEXT MATCHING (Primary Metric):{Colors.END}")
            print("=" * 80)
            print(f"{Colors.CYAN}✨ These metrics show how well the AI matched the EXACT description text ✨{Colors.END}")
            print("=" * 80)

            ml = summary['multi_level_metrics']

            # Show BLEU-4 prominently (most important)
            if 'avg_desc_bleu4' in ml:
                val = ml['avg_desc_bleu4']
                color = Colors.GREEN if val >= 0.9 else Colors.YELLOW if val >= 0.7 else Colors.RED
                emoji = "✅" if val >= 0.9 else "⚠️" if val >= 0.7 else "❌"
                print(f"\n  {emoji} {Colors.BOLD}BLEU-4 (Description Text)    : {color}{val:.4f} = {val*100:.1f}%{Colors.END}")

            # Show BERTScore
            if 'avg_desc_bertscore_f1' in ml:
                val = ml['avg_desc_bertscore_f1']
                color = Colors.GREEN if val >= 0.9 else Colors.YELLOW if val >= 0.7 else Colors.RED
                emoji = "✅" if val >= 0.9 else "⚠️" if val >= 0.7 else "❌"
                print(f"  {emoji} {Colors.BOLD}BERTScore (Description Text) : {color}{val:.4f} = {val*100:.1f}%{Colors.END}")

            # Show ROUGE scores with note
            if 'avg_desc_rouge1_f1' in ml:
                val = ml['avg_desc_rouge1_f1']
                color = Colors.GREEN if val >= 0.7 else Colors.YELLOW if val >= 0.5 else Colors.RED
                emoji = "✅" if val >= 0.7 else "⚠️" if val >= 0.5 else "⚠️"
                note = f" {Colors.YELLOW}(Note: May be 0 due to Thai tokenization){Colors.END}" if val == 0 else ""
                print(f"  {emoji} ROUGE-1 F1 (Description)     : {color}{val:.4f}{Colors.END}{note}")

            if 'avg_desc_rougeL_f1' in ml:
                val = ml['avg_desc_rougeL_f1']
                color = Colors.GREEN if val >= 0.7 else Colors.YELLOW if val >= 0.5 else Colors.RED
                emoji = "✅" if val >= 0.7 else "⚠️" if val >= 0.5 else "⚠️"
                note = f" {Colors.YELLOW}(Note: May be 0 due to Thai tokenization){Colors.END}" if val == 0 else ""
                print(f"  {emoji} ROUGE-L F1 (Description)     : {color}{val:.4f}{Colors.END}{note}")

            print(f"\n{Colors.BOLD}📊 Supporting Metrics:{Colors.END}")
            print("─" * 80)

            if 'avg_keyword_coverage_ratio' in ml:
                val = ml['avg_keyword_coverage_ratio']
                color = self.get_score_color(val, 'general')
                emoji = self.get_score_emoji(val, 'general')
                print(f"  {emoji} Keyword Coverage          : {color}{val:.2%}{Colors.END}")

            if 'avg_semantic_bertscore_f1' in ml:
                val = ml['avg_semantic_bertscore_f1']
                color = self.get_score_color(val, 'general')
                emoji = self.get_score_emoji(val, 'general')
                print(f"  {emoji} Semantic Similarity       : {color}{val:.4f}{Colors.END}")

            if 'avg_keypoint_coverage_ratio' in ml:
                val = ml['avg_keypoint_coverage_ratio']
                color = self.get_score_color(val, 'general')
                emoji = self.get_score_emoji(val, 'general')
                print(f"  {emoji} Key Points Coverage       : {color}{val:.2%}{Colors.END}")
            print()

        # Legacy Text Metrics (LESS RELEVANT - Shown for reference only)
        if 'text_metrics' in summary and summary['text_metrics']:
            print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  Legacy Full-Text Metrics (Less Relevant - For Reference Only):{Colors.END}")
            print("─" * 80)
            print(f"{Colors.YELLOW}Note: These compare ALL text including allocations (pros/cons) that we don't control{Colors.END}")
            print(f"{Colors.YELLOW}      Focus on the 'Description Text Matching' metrics above instead!{Colors.END}")
            print("─" * 80)

            for key, value in summary['text_metrics'].items():
                metric_name = key.replace('avg_', '').replace('_', '-').upper()
                color = self.get_score_color(value, 'general')
                emoji = self.get_score_emoji(value, 'general')
                print(f"  {emoji} {metric_name:25} : {color}{value:.4f}{Colors.END}")
            print()

        # NitiBench (Thai Legal Quality)
        if 'nitibench_metrics' in summary and summary['nitibench_metrics']:
            print(f"{Colors.BOLD}{Colors.CYAN}⚖️  NitiBench — Thai Legal Quality (Supplementary Metric):{Colors.END}")
            print("=" * 80)
            print(f"{Colors.CYAN}ใช้ควบคู่กับ ROUGE/BLEU/BERTScore — วัดคุณภาพเชิงกฎหมายที่ text metrics วัดไม่ได้{Colors.END}")
            print("=" * 80)

            nb = summary['nitibench_metrics']

            if 'avg_coverage_score' in nb:
                val = nb['avg_coverage_score']
                color = Colors.GREEN if val >= 80 else Colors.YELLOW if val >= 40 else Colors.RED
                emoji = "✅" if val >= 80 else "⚠️" if val >= 40 else "❌"
                print(f"\n  {emoji} {Colors.BOLD}Coverage Score (0-100)     : {color}{val:.1f}{Colors.END}")

            if 'avg_consistency_score' in nb:
                val = nb['avg_consistency_score']
                color = Colors.GREEN if val >= 0.8 else Colors.YELLOW if val >= 0.5 else Colors.RED
                emoji = "✅" if val >= 0.8 else "⚠️" if val >= 0.5 else "❌"
                print(f"  {emoji} {Colors.BOLD}Consistency Score (0-1)    : {color}{val:.4f}{Colors.END}")

            if 'avg_citation_f1' in nb:
                val = nb['avg_citation_f1']
                color = self.get_score_color(val, 'general')
                emoji = self.get_score_emoji(val, 'general')
                print(f"  {emoji} {Colors.BOLD}Citation F1 (0-1)          : {color}{val:.4f}{Colors.END}")

            if 'avg_joint_score' in nb:
                val = nb['avg_joint_score']
                color = self.get_score_color(val, 'general')
                emoji = self.get_score_emoji(val, 'general')
                print(f"  {emoji} {Colors.BOLD}Joint Score (weighted avg)  : {color}{val:.4f}{Colors.END}")
                print(f"     (Coverage 40% + Consistency 35% + Citation 25%)")
            print()

        # 🆕 Plan Diversity
        if 'plan_diversity_metrics' in summary:
            pd = summary['plan_diversity_metrics']
            print(f"{Colors.BOLD}🎲 Plan Diversity Score:{Colors.END}")
            print("─" * 80)
            val = pd['avg_diversity_score']
            color = Colors.GREEN if val >= 50 else Colors.YELLOW if val >= 30 else Colors.RED
            emoji = "✅" if val >= 50 else "⚠️" if val >= 30 else "❌"
            print(f"  {emoji} Average: {color}{val}/100{Colors.END}")
            print(f"     Min: {pd['min_diversity_score']}/100 | Max: {pd['max_diversity_score']}/100")
            print()

        # 🆕 Format Validity
        if 'format_validity_metrics' in summary:
            fv = summary['format_validity_metrics']
            print(f"{Colors.BOLD}📋 Format Validity:{Colors.END}")
            print("─" * 80)
            val = fv['avg_format_score']
            color = Colors.GREEN if val >= 90 else Colors.YELLOW if val >= 70 else Colors.RED
            emoji = "✅" if val >= 90 else "⚠️" if val >= 70 else "❌"
            print(f"  {emoji} Average: {color}{val}%{Colors.END}")
            print(f"     Perfect format: {fv['perfect_format_count']}/{fv['total_evaluated']}")
            print()

        # 🆕 Generalization Test (ถ้ามี — จะถูก inject จาก runner)
        if 'generalization_metrics' in summary:
            gm = summary['generalization_metrics']
            print(f"{Colors.BOLD}🧪 Generalization Test (unseen profiles):{Colors.END}")
            print("=" * 80)
            val = gm['generalization_score']
            color = Colors.GREEN if val >= 70 else Colors.YELLOW if val >= 50 else Colors.RED
            emoji = "✅" if val >= 70 else "⚠️" if val >= 50 else "❌"
            print(f"  {emoji} Score: {color}{val}%{Colors.END} ({gm['passed_checks']}/{gm['total_checks']} checks)")
            if 'profiles' in gm:
                for p in gm['profiles']:
                    p_emoji = "✅" if p.get("score", 0) >= 80 else "⚠️" if p.get("score", 0) >= 50 else "❌"
                    print(f"  {p_emoji} {p['id']}: {p.get('label', '')} — {p.get('score', 0)}%")
            print()

        # Numeric Metrics
        if 'numeric_metrics' in summary and summary['numeric_metrics']:
            print(f"{Colors.BOLD}💰 Numeric Accuracy (Hardcoded Validation):{Colors.END}")
            print("─" * 80)
            print(f"  {Colors.CYAN}ℹ️  ตัวเลขถูก hardcode ไว้ใน prompt — metric นี้ยืนยันว่า AI ใช้ค่าที่กำหนด ไม่คิดเอง{Colors.END}")

            for key, value in summary['numeric_metrics'].items():
                metric_name = key.replace('_', ' ').title()
                color = self.get_score_color(value, 'accuracy')
                emoji = self.get_score_emoji(value, 'accuracy')
                print(f"  {emoji} {metric_name:15} : {color}{value:.2f}%{Colors.END}")
            print()

        print("="*80 + "\n")