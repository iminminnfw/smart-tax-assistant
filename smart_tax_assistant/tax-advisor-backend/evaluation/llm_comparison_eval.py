"""
LLM Explanation Quality Evaluation
====================================
เปรียบเทียบคุณภาพการอธิบายของ 3 models:
  - qwen2.5:14b
  - llama3.1:8b
  - deepseek-r1:14b

Flow เหมือน production /optimize endpoint:
  1. calculate_allocation()  ← code คำนวณ (ไม่ให้ LLM คำนวณ)
  2. RAGService.retrieve_relevant_documents()  ← ดึง context กฎหมายภาษี
  3. generate_recommendation_explanation()  ← LLM อธิบาย
  4. วัดคุณภาพด้วย ROUGE-L + Thai Keyword Coverage

วิธีรัน (จาก tax-advisor-backend/):
  python -m evaluation.llm_comparison_eval

หรือ:
  cd tax-advisor-backend
  python evaluation/llm_comparison_eval.py
"""

import asyncio
import json
import time
import sys
import os

# fix emoji/Thai output บน Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# ── path setup (รันจาก tax-advisor-backend/) ──────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tax_fund_service import TaxFundService
from app.services.rag_service import RAGService
from app.services.ai_tax_advisor import AITaxAdvisor, UserProfile
from app.routers.ai_optimizer import calculate_allocation, _calculate_family_deductions, _calculate_3year_breakdown

# ROUGE-L (pip install rouge-score)
from rouge_score import rouge_scorer as rouge_scorer_module

# Thai tokenizer (pip install pythainlp)
try:
    from pythainlp.tokenize import word_tokenize
    THAI_NLP = True
except ImportError:
    THAI_NLP = False
    print("⚠️  pythainlp ไม่ได้ติดตั้ง — ใช้ character-level แทน")

# ─────────────────────────────────────────────────────────────────────────────
# Models ที่ต้องการเปรียบเทียบ
# ─────────────────────────────────────────────────────────────────────────────
MODELS = ["qwen2.5:14b", "llama3.1:8b", "deepseek-r1:14b"]

# ─────────────────────────────────────────────────────────────────────────────
# 5 Test Cases  (ครอบคลุม scenario หลักของระบบ)
# ─────────────────────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "TC1",
        "desc": "พนักงานหนุ่ม เป้าหมายเกษียณ ความเสี่ยงปานกลาง",
        "profile_kwargs": {
            "age": 28,
            "annual_income": 600_000,
            "monthly_expenses": 20_000,
            "risk_tolerance": "moderate",
            "occupation": "employee",
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 0,
            "life_insurance_amount": 0,
            "health_insurance_amount": 0,
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "existing_insurance": 0,
        },
        "money_goal": "retirement",
        "monthly_budget": 8_000,
        "income_growth_rate": 5.0,
        # reference: คำอธิบายคุณภาพสูงที่ครอบคลุม keywords สำคัญ
        "reference": (
            "อายุ 28 ปี เหลือเวลาถึง 27 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF ควรลงทุน RMF "
            "เพื่อประหยัดภาษีและเกษียณ ThaiESG ล็อค 5 ปี ถอนได้ปี 2574 "
            "ระดับความเสี่ยงปานกลาง กองทุน RMF กองทุน ThaiESG ลดหย่อนภาษี "
            "งบลงทุน 8000 บาทต่อเดือน 96000 บาทต่อปี ประหยัดภาษีได้ "
            "อัตราภาษีสูงสุด marginal rate เปอร์เซ็นต์ "
            "DCA ลงทุนรายเดือน สม่ำเสมอทุกเดือน ประหยัดภาษีสะสม 3 ปี "
            "ถอน RMF ได้เมื่ออายุ 55 ปีและถือครองไม่น้อยกว่า 5 ปี "
            "ควรซื้อก่อนสิ้นปีภาษีเพื่อใช้สิทธิ์ลดหย่อน "
            "รายได้เพิ่มขึ้น 5 เปอร์เซ็นต์ต่อปีควรเพิ่มวงเงินลงทุน"
        ),
    },
    {
        "id": "TC2",
        "desc": "ฟรีแลนซ์รายได้สูง ความเสี่ยงก้าวร้าว TESGX",
        "profile_kwargs": {
            "age": 35,
            "annual_income": 1_500_000,
            "monthly_expenses": 50_000,
            "risk_tolerance": "aggressive",
            "occupation": "freelance",
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 2,
            "life_insurance_amount": 50_000,
            "health_insurance_amount": 20_000,
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "existing_insurance": 0,
        },
        "money_goal": "retirement",
        "monthly_budget": 20_000,
        "income_growth_rate": 10.0,
        "reference": (
            "อายุ 35 ปี เหลือ 20 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF "
            "ความเสี่ยงก้าวร้าว aggressive TESGX ThaiESG "
            "TESGX ต่างจาก ThaiESG ทั่วไปอย่างไร ลงทุนในบริษัทที่เน้น ESG ความยั่งยืน "
            "สัดส่วน ThaiESG 60 เปอร์เซ็นต์ TESGX 40 เปอร์เซ็นต์ "
            "กองทุน RMF กองทุน ThaiESG กองทุน TESGX ลดหย่อนภาษี "
            "รายได้ 1500000 บาท โควตา RMF สูงสุด 500000 ThaiESG สูงสุด 300000 TESGX 300000 "
            "งบลงทุน 20000 บาทต่อเดือน ประหยัดภาษีได้ "
            "อัตราภาษีสูงสุด 35 เปอร์เซ็นต์ marginal rate "
            "ฟรีแลนซ์ต้องวางแผนภาษีเป็นพิเศษ ประกันชีวิต ประกันสุขภาพลดหย่อน "
            "รายได้เพิ่มขึ้น 10 เปอร์เซ็นต์ต่อปีควรเพิ่มวงเงินลงทุน"
        ),
    },
    {
        "id": "TC3",
        "desc": "มีครอบครัว ลูก 2 คน ระยะกลาง ความเสี่ยงปานกลาง",
        "profile_kwargs": {
            "age": 40,
            "annual_income": 840_000,
            "monthly_expenses": 40_000,
            "risk_tolerance": "moderate",
            "occupation": "employee",
            "marital_status": "married",
            "dependents": 2,
            "num_children": 2,
            "num_parents": 2,
            "life_insurance_amount": 80_000,
            "health_insurance_amount": 25_000,
            "existing_rmf": 50_000,
            "existing_thai_esg": 30_000,
            "existing_insurance": 0,
        },
        "money_goal": "mid_term",
        "monthly_budget": 10_000,
        "income_growth_rate": 3.0,
        "reference": (
            "อายุ 40 ปี เหลือ 15 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF "
            "เป้าหมายระยะกลาง 5 ถึง 10 ปี mid_term "
            "มีลูก 2 คน ลดหย่อนบุตร สามีภรรยา ลดหย่อนคู่สมรส "
            "ประกันชีวิต ประกันสุขภาพ ลดหย่อนภาษีได้ "
            "ลงทุน RMF อยู่แล้ว 50000 ThaiESG 30000 สิทธิ์คงเหลือ "
            "กองทุน RMF กองทุน ThaiESG ลดหย่อนภาษี "
            "งบลงทุน 10000 บาทต่อเดือน ประหยัดภาษีได้ "
            "ThaiESG ล็อค 5 ปี ถอนได้ เงินทุนสำรองฉุกเฉิน "
            "ความเสี่ยงปานกลาง moderate ครอบครัวมีภาระ "
            "ควรมีเงินสำรองฉุกเฉิน 6 เดือนก่อนลงทุน DCA รายเดือน"
        ),
    },
    {
        "id": "TC4",
        "desc": "ใกล้เกษียณ อายุมาก ความเสี่ยงต่ำ",
        "profile_kwargs": {
            "age": 50,
            "annual_income": 1_200_000,
            "monthly_expenses": 45_000,
            "risk_tolerance": "conservative",
            "occupation": "employee",
            "marital_status": "married",
            "dependents": 1,
            "num_children": 1,
            "num_parents": 0,
            "life_insurance_amount": 100_000,
            "health_insurance_amount": 25_000,
            "existing_rmf": 200_000,
            "existing_thai_esg": 100_000,
            "existing_insurance": 0,
        },
        "money_goal": "retirement",
        "monthly_budget": 25_000,
        "income_growth_rate": 2.0,
        "reference": (
            "อายุ 50 ปี เหลือเพียง 5 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF "
            "ใกล้เกษียณต้องรีบเพิ่มสัดส่วน RMF ให้สูงขึ้น "
            "ความเสี่ยงต่ำ conservative ไม่ลงทุน TESGX "
            "ThaiESG ล็อค 5 ปี ถอนได้ปี 2574 ปีที่ถอนได้จริง "
            "กองทุน RMF กองทุน ThaiESG ลดหย่อนภาษี "
            "ลงทุน RMF อยู่แล้ว 200000 ThaiESG 100000 สิทธิ์คงเหลือ "
            "งบลงทุน 25000 บาทต่อเดือน 300000 บาทต่อปี ประหยัดภาษีได้ "
            "รายได้ 1200000 อัตราภาษีสูงสุด 35 เปอร์เซ็นต์ marginal rate "
            "ควรซื้อก่อนสิ้นปีภาษี lump sum ช่วงปลายปี "
            "ถอน RMF ได้เมื่ออายุ 55 ปีหรือหลังจากนั้น"
        ),
    },
    {
        "id": "TC5",
        "desc": "รายได้น้อย เป้าหมายระยะสั้น ความเสี่ยงต่ำ",
        "profile_kwargs": {
            "age": 32,
            "annual_income": 360_000,
            "monthly_expenses": 22_000,
            "risk_tolerance": "conservative",
            "occupation": "employee",
            "marital_status": "single",
            "dependents": 0,
            "num_children": 0,
            "num_parents": 1,
            "life_insurance_amount": 30_000,
            "health_insurance_amount": 10_000,
            "existing_rmf": 0,
            "existing_thai_esg": 0,
            "existing_insurance": 0,
        },
        "money_goal": "short_term",
        "monthly_budget": 3_000,
        "income_growth_rate": 4.0,
        "reference": (
            "อายุ 32 ปี เป้าหมายระยะสั้น short_term ต้องใช้เงินภายใน 5 ปี "
            "ความเสี่ยงต่ำ conservative ไม่เหมาะลงทุน RMF ล็อคนาน "
            "ThaiESG ล็อค 5 ปี เหมาะกว่า RMF สำหรับระยะสั้น "
            "กองทุน ThaiESG ลดหย่อนภาษี "
            "งบลงทุน 3000 บาทต่อเดือน 36000 บาทต่อปี "
            "รายได้ 360000 บาท โควตาสิทธิ์ ThaiESG "
            "ประหยัดภาษีได้แม้งบน้อย อัตราภาษีสูงสุด marginal rate "
            "ระวังเงินล็อคถ้าต้องการสภาพคล่อง ควรมีเงินสำรองก่อน "
            "ดูแลพ่อแม่ ลดหย่อนบิดามารดา อายุ 60 ปีขึ้นไป"
        ),
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Thai tax-domain keywords สำหรับวัด Keyword Coverage
# ─────────────────────────────────────────────────────────────────────────────
TAX_KEYWORDS = [
    "RMF", "ThaiESG", "TESGX",
    "ลดหย่อน", "ภาษี", "กองทุน",
    "เกษียณ", "ความเสี่ยง", "ประหยัด",
    "ถอน", "ล็อค", "โควตา",
    "marginal", "DCA", "สิทธิ์",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def thai_tokenize(text: str) -> str:
    """Tokenize Thai text with spaces (for ROUGE)."""
    if THAI_NLP:
        tokens = word_tokenize(text, engine="newmm", keep_whitespace=False)
        return " ".join(tokens)
    # fallback: character-level
    return " ".join(list(text.replace(" ", "")))


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    """Compute ROUGE-L F1 on Thai-tokenized text."""
    scorer = rouge_scorer_module.RougeScorer(["rougeL"], use_stemmer=False)
    ref_tok = thai_tokenize(reference)
    hyp_tok = thai_tokenize(hypothesis)
    result = scorer.score(ref_tok, hyp_tok)
    return result["rougeL"].fmeasure


def compute_keyword_coverage(text: str) -> float:
    """วัดว่า text ครอบคลุม tax keywords กี่ตัว."""
    found = sum(1 for kw in TAX_KEYWORDS if kw.lower() in text.lower())
    return found / len(TAX_KEYWORDS)


def fetch_recommended_funds(risk_tolerance: str, fund_types: List[str] = None) -> List[Dict]:
    """ดึง recommended funds จาก PostgreSQL เหมือน /api/ai-optimizer/recommend-funds"""
    import psycopg2, psycopg2.extras

    if fund_types is None:
        fund_types = ["RMF", "TESG", "TESGX"]

    max_risk = 3 if risk_tolerance == "conservative" else 8 if risk_tolerance == "aggressive" else 6

    try:
        conn = psycopg2.connect("postgresql://postgres:projectyear4@localhost:5432/SmartTax")
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # 1. หา fundId ที่ตรง specCode
        cur.execute(
            'SELECT "fundId", "specCode" FROM fund_specs WHERE "specCode" = ANY(%s)',
            (fund_types,)
        )
        spec_rows = cur.fetchall()
        fund_id_to_spec = {r["fundId"]: r["specCode"] for r in spec_rows}
        eligible_ids = list(fund_id_to_spec.keys())

        if not eligible_ids:
            return []

        # 2. filter active + risk spectrum
        cur.execute("""
            SELECT f.id, f."projNameTh", f."projAbbrName", f."policyDesc",
                   rs."riskSpectrum",
                   a."nameTh" as "amcNameTh"
            FROM funds f
            JOIN fund_amcs a ON f."amcId" = a.id
            JOIN (
                SELECT DISTINCT ON ("fundId") "fundId", "riskSpectrum"
                FROM fund_risk_spectrums
                ORDER BY "fundId", "endDate" DESC
            ) rs ON rs."fundId" = f.id
            WHERE f.id = ANY(%s)
              AND f."fundStatus" IN ('Registered', 'IPO')
              AND rs."riskSpectrum" <= %s
        """, (eligible_ids, max_risk))
        funds = cur.fetchall()

        if not funds:
            conn.close()
            return []

        fund_ids = [r["id"] for r in funds]

        # 3. performance
        cur.execute("""
            SELECT "fundId", "referencePeriod", "performanceValue"
            FROM fund_performances
            WHERE "fundId" = ANY(%s)
              AND "performanceTypeDesc" = 'ผลตอบแทนกองทุนรวม'
            ORDER BY "endDate" DESC
        """, (fund_ids,))
        perf_map: Dict[str, Dict] = {}
        for p in cur.fetchall():
            fid = p["fundId"]
            if fid not in perf_map:
                perf_map[fid] = {"return1y": None, "return3y": None, "return5y": None}
            period = (p["referencePeriod"] or "").lower().strip()
            if period == "1 year"  and perf_map[fid]["return1y"] is None:
                perf_map[fid]["return1y"] = p["performanceValue"]
            elif period == "3 years" and perf_map[fid]["return3y"] is None:
                perf_map[fid]["return3y"] = p["performanceValue"]
            elif period == "5 years" and perf_map[fid]["return5y"] is None:
                perf_map[fid]["return5y"] = p["performanceValue"]

        # 4. statistics
        cur.execute("""
            SELECT DISTINCT ON ("fundId") "fundId", "sharpeRatio", "alpha", "maxDrawdown"
            FROM fund_statistics
            WHERE "fundId" = ANY(%s)
            ORDER BY "fundId", "endDate" DESC
        """, (fund_ids,))
        stats_map: Dict[str, Dict] = {
            r["fundId"]: {
                "sharpeRatio": r["sharpeRatio"],
                "alpha": r["alpha"],
                "maxDrawdown": r["maxDrawdown"],
            }
            for r in cur.fetchall()
        }

        conn.close()

        # 5. score + rank (เหมือน Next.js route)
        scored = []
        for f in funds:
            fid = f["id"]
            perf  = perf_map.get(fid, {})
            stats = stats_map.get(fid, {})
            score = 0.0
            sh = stats.get("sharpeRatio")
            al = stats.get("alpha")
            md = stats.get("maxDrawdown")
            r1 = perf.get("return1y")
            r3 = perf.get("return3y")
            r5 = perf.get("return5y")
            if sh is not None and abs(sh) < 100: score += sh * 4
            if al is not None and abs(al) < 100: score += al * 3
            if md is not None and abs(md) < 999:  score += (100 + md) * 0.15
            if r1 is not None: score += r1 * 0.10
            if r3 is not None: score += r3 * 0.03
            if r5 is not None: score += r5 * 0.02
            scored.append({
                "fundId"    : fid,
                "abbr"      : f["projAbbrName"],
                "nameTh"    : f["projNameTh"],
                "amcNameTh" : f["amcNameTh"],
                "fundType"  : fund_id_to_spec.get(fid, ""),
                "policyDesc": f["policyDesc"],
                "riskSpectrum": f["riskSpectrum"],
                "performance": perf,
                "statistics" : stats,
                "score"      : score,
            })

        # top 3 per type
        result: List[Dict] = []
        for ft in fund_types:
            top = sorted(
                [s for s in scored if s["fundType"] == ft],
                key=lambda x: x["score"], reverse=True
            )[:3]
            result.extend(top)

        return result

    except Exception as e:
        print(f"   ⚠️  DB fund fetch failed: {e} — ใช้ [] แทน")
        return []


def avg(lst: List[float]) -> float:
    return sum(lst) / len(lst) if lst else 0.0


def make_user_profile(kw: dict) -> UserProfile:
    """แปลง profile_kwargs เป็น UserProfile dataclass."""
    return UserProfile(
        age=kw["age"],
        annual_income=kw["annual_income"],
        monthly_expenses=kw["monthly_expenses"],
        existing_savings=0,
        emergency_fund=0,
        risk_tolerance=kw["risk_tolerance"],
        occupation=kw.get("occupation", "employee"),
        marital_status=kw.get("marital_status", "single"),
        dependents=kw.get("dependents", 0),
        existing_rmf=kw.get("existing_rmf", 0),
        existing_thai_esg=kw.get("existing_thai_esg", 0),
        existing_insurance=kw.get("existing_insurance", 0),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main Evaluation
# ─────────────────────────────────────────────────────────────────────────────

async def run_evaluation():
    print("=" * 65)
    print("  LLM Explanation Quality Evaluation")
    print(f"  Models : {', '.join(MODELS)}")
    print(f"  Cases  : {len(TEST_CASES)}")
    print(f"  Date   : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)

    # ── init services ─────────────────────────────────────────────────────────
    print("\n🔧 Initialising services...")
    tax_svc = TaxFundService(sec_service=None)

    print("🔍 Connecting RAG (Qdrant)...")
    rag_svc = RAGService()
    rag_available = rag_svc.is_available()
    print(f"   RAG available: {rag_available}")

    # สร้าง AITaxAdvisor แยกต่างหากสำหรับแต่ละ model
    advisors: Dict[str, AITaxAdvisor] = {}
    for model in MODELS:
        adv = AITaxAdvisor(provider="ollama", model=model)
        advisors[model] = adv
        print(f"   ✅ Advisor created: {model}")

    results: List[Dict] = []

    # ── loop test cases ────────────────────────────────────────────────────────
    for tc in TEST_CASES:
        print(f"\n{'─'*65}")
        print(f"📋 {tc['id']}: {tc['desc']}")
        print(f"{'─'*65}")

        # 1. สร้าง UserProfile
        profile = make_user_profile(tc["profile_kwargs"])

        # 2. ใช้ object สำหรับ _calculate_family_deductions (ต้องการ attribute จาก ProfileRequest)
        class ProfileProxy:
            """Minimal proxy ที่ _calculate_family_deductions ต้องการ."""
            marital_status          = tc["profile_kwargs"].get("marital_status", "single")
            num_children            = tc["profile_kwargs"].get("num_children", 0)
            num_parents             = tc["profile_kwargs"].get("num_parents", 0)
            life_insurance_amount   = tc["profile_kwargs"].get("life_insurance_amount", 0)
            health_insurance_amount = tc["profile_kwargs"].get("health_insurance_amount", 0)
            annual_income           = tc["profile_kwargs"]["annual_income"]
            occupation              = tc["profile_kwargs"].get("occupation", "employee")
            existing_insurance      = tc["profile_kwargs"].get("existing_insurance", 0)

        proxy = ProfileProxy()
        family_deductions = _calculate_family_deductions(proxy)

        # 3. calculate_allocation (เหมือน /optimize endpoint)
        allocation = calculate_allocation(
            age               = tc["profile_kwargs"]["age"],
            income            = tc["profile_kwargs"]["annual_income"],
            goal              = tc["money_goal"],
            monthly_budget    = tc["monthly_budget"],
            risk_tolerance    = tc["profile_kwargs"]["risk_tolerance"],
            income_growth_rate= tc["income_growth_rate"],
            existing_rmf      = tc["profile_kwargs"].get("existing_rmf", 0),
            existing_thai_esg = tc["profile_kwargs"].get("existing_thai_esg", 0),
        )

        # 4. calculate_tax_savings
        savings = tax_svc.calculate_tax_savings(
            annual_income       = tc["profile_kwargs"]["annual_income"],
            rmf_investment      = tc["profile_kwargs"].get("existing_rmf", 0) + allocation["rmf_amount"],
            thai_esg_investment = (
                tc["profile_kwargs"].get("existing_thai_esg", 0)
                + allocation["tesg_amount"]
                + allocation["tesgx_amount"]
            ),
            family_deductions   = family_deductions,
        )

        # 5. 3-year breakdown — เหมือน production เลย
        year_breakdown = _calculate_3year_breakdown(
            annual_income      = tc["profile_kwargs"]["annual_income"],
            available_budget   = tc["monthly_budget"] * 12,
            existing_rmf       = tc["profile_kwargs"].get("existing_rmf", 0),
            existing_thai_esg  = tc["profile_kwargs"].get("existing_thai_esg", 0),
            family_deductions  = family_deductions,
            income_growth_rate = tc["income_growth_rate"],
            tax_fund_svc       = tax_svc,
            age                = tc["profile_kwargs"]["age"],
            goal               = tc["money_goal"],
            risk_tolerance     = tc["profile_kwargs"]["risk_tolerance"],
        )

        # 6. RAG context
        rag_query = (
            f"RMF ThaiESG ลดหย่อนภาษี เงื่อนไขถอน {tc['money_goal']} "
            f"ความเสี่ยง {tc['profile_kwargs']['risk_tolerance']}"
        )
        if rag_available:
            rag_docs = await rag_svc.retrieve_relevant_documents(rag_query, k=3)
            rag_context = "\n\n".join(d.page_content for d in rag_docs)
        else:
            rag_context = ""
            print("   ⚠️  RAG ไม่พร้อม — ใช้ prompt ไม่มี context")

        # 7. ดึง recommended funds จาก DB (เหมือน production)
        fund_types = ["RMF", "TESG"]
        if tc["profile_kwargs"]["risk_tolerance"] == "aggressive":
            fund_types.append("TESGX")
        recommended_funds = fetch_recommended_funds(
            risk_tolerance=tc["profile_kwargs"]["risk_tolerance"],
            fund_types=fund_types,
        )

        print(f"   Allocation  : RMF={allocation['rmf_amount']:,.0f} "
              f"ThaiESG={allocation['tesg_amount']:,.0f} "
              f"TESGX={allocation['tesgx_amount']:,.0f}")
        print(f"   Tax saved   : {savings.get('tax_saved', 0):,.0f} บาท")
        print(f"   Funds from DB: {len(recommended_funds)} กอง")
        print(f"   RAG context : {len(rag_context)} chars")

        tc_result = {
            "id": tc["id"],
            "desc": tc["desc"],
            "allocation": {
                "rmf_amount"  : allocation["rmf_amount"],
                "tesg_amount" : allocation["tesg_amount"],
                "tesgx_amount": allocation["tesgx_amount"],
                "total_amount": allocation["total_amount"],
            },
            "tax_saved"  : savings.get("tax_saved", 0),
            "rag_chars"  : len(rag_context),
            "models"     : {},
        }

        # 7. เรียก LLM ทั้ง 3 model
        for model in MODELS:
            print(f"\n   🤖 {model} ...", end="", flush=True)
            advisor = advisors[model]
            start = time.time()
            try:
                explanation = await advisor.generate_recommendation_explanation(
                    profile           = profile,
                    allocation        = allocation,
                    tax_savings       = savings,
                    year_breakdown    = year_breakdown,
                    recommended_funds = recommended_funds,  # ดึงจาก DB จริง
                    income_growth_rate= tc["income_growth_rate"],
                    monthly_budget    = float(tc["monthly_budget"]),
                    rag_context       = rag_context,
                )
                latency = time.time() - start

                # รวม 8 fields เป็น text เดียวสำหรับ ROUGE
                full_text = " ".join(
                    str(v) for v in explanation.values() if isinstance(v, str) and v
                )

                rouge_l  = compute_rouge_l(tc["reference"], full_text)
                kw_cov   = compute_keyword_coverage(full_text)
                fields_ok = sum(1 for k in [
                    "age_analysis", "goal_analysis", "risk_analysis",
                    "budget_analysis", "fund_reasons", "warnings",
                    "future_advice", "summary"
                ] if explanation.get(k, "").strip())

                print(f" ROUGE-L={rouge_l:.3f}  KW={kw_cov:.0%}  "
                      f"Fields={fields_ok}/8  {latency:.1f}s")

                tc_result["models"][model] = {
                    "rouge_l"         : round(rouge_l, 4),
                    "keyword_coverage": round(kw_cov, 4),
                    "fields_complete" : fields_ok,
                    "latency_sec"     : round(latency, 1),
                    "response_len"    : len(full_text),
                    "explanation"     : explanation,   # เก็บ raw output ด้วย
                }

            except Exception as e:
                latency = time.time() - start
                print(f" ❌ ERROR: {e}")
                tc_result["models"][model] = {
                    "rouge_l"         : 0.0,
                    "keyword_coverage": 0.0,
                    "fields_complete" : 0,
                    "latency_sec"     : round(latency, 1),
                    "response_len"    : 0,
                    "error"           : str(e),
                }

        results.append(tc_result)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("  SUMMARY — Average across 5 test cases")
    print(f"{'='*65}")
    print(f"{'Model':<22} {'ROUGE-L':>9} {'KW Cov':>8} {'Fields':>8} {'Latency':>10}")
    print(f"{'─'*22} {'─'*9} {'─'*8} {'─'*8} {'─'*10}")

    summary: Dict[str, Dict] = {}
    for model in MODELS:
        rouge_vals   = [r["models"][model]["rouge_l"]          for r in results if model in r["models"]]
        kw_vals      = [r["models"][model]["keyword_coverage"] for r in results if model in r["models"]]
        field_vals   = [r["models"][model]["fields_complete"]  for r in results if model in r["models"]]
        lat_vals     = [r["models"][model]["latency_sec"]      for r in results if model in r["models"]]

        summary[model] = {
            "avg_rouge_l"          : round(avg(rouge_vals), 4),
            "avg_keyword_coverage" : round(avg(kw_vals), 4),
            "avg_fields_complete"  : round(avg(field_vals), 2),
            "avg_latency_sec"      : round(avg(lat_vals), 1),
        }
        s = summary[model]
        print(
            f"{model:<22} {s['avg_rouge_l']:>9.4f} "
            f"{s['avg_keyword_coverage']:>7.1%} "
            f"{s['avg_fields_complete']:>8.2f} "
            f"{s['avg_latency_sec']:>9.1f}s"
        )

    # ── Save results ────────────────────────────────────────────────────────────
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"eval_{timestamp}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "models"   : MODELS,
                "summary"  : summary,
                "details"  : results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n✅ Results saved → {out_file}")
    print(f"\n🏆 Best ROUGE-L  : {max(summary, key=lambda m: summary[m]['avg_rouge_l'])}")
    print(f"🏆 Best KW Cover : {max(summary, key=lambda m: summary[m]['avg_keyword_coverage'])}")
    print(f"⚡ Fastest       : {min(summary, key=lambda m: summary[m]['avg_latency_sec'])}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_evaluation())
