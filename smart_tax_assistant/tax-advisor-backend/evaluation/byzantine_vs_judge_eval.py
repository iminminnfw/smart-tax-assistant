"""
Byzantine Failure vs LLM-as-Judge Evaluation
=============================================
พิสูจน์ว่า LLM-as-Judge ให้คุณภาพดีกว่าหรือเท่ากับ Byzantine (ไม่มี judge)

นิยาม:
  Byzantine  = รัน generator 1 ครั้ง ใช้ output เลยโดยไม่ตรวจ (ไม่รู้ว่าดีหรือแย่)
  LLM-Judge  = รัน generator → judge ตรวจ → retry ถ้าไม่ผ่าน (production flow)

การเพิ่มความเร็ว:
  - BYZANTINE_RUNS=1 (1 ครั้งพอ — ประเด็นคือ "ไม่มี judge" ไม่ใช่จำนวนครั้ง)
  - ENABLE_BERTSCORE=False (ปิดได้ — โหลด model นาน ~2-3 นาที)
  - LLM calls ต่อ case: 2-3 calls (เทียบกับ 6-10 ของเวอร์ชัน 3 runs)

Metrics:
  - Judge Score  (0-8): Python number check + LLM completeness/Thai check
  - Pass Rate    (%):   score >= 6
  - ROUGE-L      (0-1): text overlap กับ reference
  - BLEU         (0-1): n-gram precision
  - BERTScore    (0-1): semantic similarity  ← ปิดได้ด้วย ENABLE_BERTSCORE

Generator : qwen2.5:14b  |  Judge: llama3.1:8b  (เหมือน production)

วิธีรัน:
  cd tax-advisor-backend
  python -m evaluation.byzantine_vs_judge_eval
"""

import asyncio
import json
import os
import sys
import time

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tax_fund_service import TaxFundService
from app.services.rag_service import RAGService
from app.services.ai_tax_advisor import AITaxAdvisor, UserProfile
from app.routers.ai_optimizer import (
    calculate_allocation,
    _calculate_family_deductions,
    _calculate_3year_breakdown,
)

from rouge_score import rouge_scorer as rouge_scorer_module
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

try:
    from bert_score import score as bert_score_fn
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False

try:
    from pythainlp.tokenize import word_tokenize as thai_word_tokenize
    THAI_NLP = True
except ImportError:
    THAI_NLP = False
    print("⚠️  pythainlp ไม่ได้ติดตั้ง — ใช้ character-level แทน")

# ─────────────────────────────────────────────────────────────────────────────
# Config  ← แก้ที่นี่เพื่อปรับความเร็ว
# ─────────────────────────────────────────────────────────────────────────────
GENERATOR_MODEL      = "qwen2.5:14b"
JUDGE_MODEL          = "llama3.1:8b"
JUDGE_PASS_THRESHOLD = 6       # score >= 6 = ผ่าน (เหมือน production, รวม number check)
LLM_ONLY_THRESHOLD   = 3       # llm_score >= 3 = ผ่าน (ตัด number check ออก, max=4)
ENABLE_BERTSCORE     = True    # True = แม่นขึ้น แต่โหลด model นาน ~2-3 นาที

# ─────────────────────────────────────────────────────────────────────────────
# Test Cases
# ─────────────────────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "TC1", "desc": "พนักงานหนุ่ม เป้าหมายเกษียณ ความเสี่ยงปานกลาง",
        "profile_kwargs": {
            "age": 28, "annual_income": 600_000, "monthly_expenses": 20_000,
            "risk_tolerance": "moderate", "occupation": "employee",
            "marital_status": "single", "dependents": 0, "num_children": 0,
            "num_parents": 0, "life_insurance_amount": 0,
            "health_insurance_amount": 0, "existing_rmf": 0,
            "existing_thai_esg": 0, "existing_insurance": 0,
        },
        "money_goal": "retirement", "monthly_budget": 8_000,
        "income_growth_rate": 5.0,
        "reference": (
            "อายุ 28 ปี เหลือเวลาถึง 27 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF ควรลงทุน RMF "
            "เพื่อประหยัดภาษีและเกษียณ ThaiESG ล็อค 5 ปี ถอนได้ปี 2574 "
            "ระดับความเสี่ยงปานกลาง กองทุน RMF กองทุน ThaiESG ลดหย่อนภาษี "
            "งบลงทุน 8000 บาทต่อเดือน 96000 บาทต่อปี ประหยัดภาษีได้ "
            "DCA ลงทุนรายเดือน ถอน RMF ได้เมื่ออายุ 55 ปี "
            "รายได้เพิ่มขึ้น 5 เปอร์เซ็นต์ต่อปีควรเพิ่มวงเงินลงทุน"
        ),
    },
    {
        "id": "TC2", "desc": "ฟรีแลนซ์รายได้สูง ความเสี่ยงก้าวร้าว TESGX",
        "profile_kwargs": {
            "age": 35, "annual_income": 1_500_000, "monthly_expenses": 50_000,
            "risk_tolerance": "aggressive", "occupation": "freelance",
            "marital_status": "single", "dependents": 0, "num_children": 0,
            "num_parents": 2, "life_insurance_amount": 50_000,
            "health_insurance_amount": 20_000, "existing_rmf": 0,
            "existing_thai_esg": 0, "existing_insurance": 0,
        },
        "money_goal": "retirement", "monthly_budget": 20_000,
        "income_growth_rate": 10.0,
        "reference": (
            "อายุ 35 ปี เหลือ 20 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF "
            "ความเสี่ยงก้าวร้าว aggressive TESGX ThaiESG "
            "สัดส่วน ThaiESG 60 เปอร์เซ็นต์ TESGX 40 เปอร์เซ็นต์ "
            "กองทุน RMF กองทุน ThaiESG กองทุน TESGX ลดหย่อนภาษี "
            "รายได้ 1500000 บาท อัตราภาษีสูงสุด 35 เปอร์เซ็นต์"
        ),
    },
    {
        "id": "TC3", "desc": "มีครอบครัว ลูก 2 คน ระยะกลาง ความเสี่ยงปานกลาง",
        "profile_kwargs": {
            "age": 40, "annual_income": 840_000, "monthly_expenses": 40_000,
            "risk_tolerance": "moderate", "occupation": "employee",
            "marital_status": "married", "dependents": 2, "num_children": 2,
            "num_parents": 2, "life_insurance_amount": 80_000,
            "health_insurance_amount": 25_000, "existing_rmf": 50_000,
            "existing_thai_esg": 30_000, "existing_insurance": 0,
        },
        "money_goal": "mid_term", "monthly_budget": 10_000,
        "income_growth_rate": 3.0,
        "reference": (
            "อายุ 40 ปี เหลือ 15 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF "
            "มีลูก 2 คน ลดหย่อนบุตร สามีภรรยา ลดหย่อนคู่สมรส "
            "ลงทุน RMF อยู่แล้ว 50000 ThaiESG 30000 สิทธิ์คงเหลือ "
            "งบลงทุน 10000 บาทต่อเดือน ThaiESG ล็อค 5 ปี DCA รายเดือน"
        ),
    },
    {
        "id": "TC4", "desc": "ใกล้เกษียณ อายุมาก ความเสี่ยงต่ำ",
        "profile_kwargs": {
            "age": 50, "annual_income": 1_200_000, "monthly_expenses": 45_000,
            "risk_tolerance": "conservative", "occupation": "employee",
            "marital_status": "married", "dependents": 1, "num_children": 1,
            "num_parents": 0, "life_insurance_amount": 100_000,
            "health_insurance_amount": 25_000, "existing_rmf": 200_000,
            "existing_thai_esg": 100_000, "existing_insurance": 0,
        },
        "money_goal": "retirement", "monthly_budget": 25_000,
        "income_growth_rate": 2.0,
        "reference": (
            "อายุ 50 ปี เหลือเพียง 5 ปีก่อนถึงอายุ 55 ปีเงื่อนไขถอน RMF "
            "ใกล้เกษียณต้องรีบเพิ่มสัดส่วน RMF ให้สูงขึ้น "
            "ความเสี่ยงต่ำ conservative ไม่ลงทุน TESGX "
            "ลงทุน RMF อยู่แล้ว 200000 ThaiESG 100000 "
            "งบลงทุน 25000 บาทต่อเดือน อัตราภาษีสูงสุด 35 เปอร์เซ็นต์"
        ),
    },
    {
        "id": "TC5", "desc": "รายได้น้อย เป้าหมายระยะสั้น ความเสี่ยงต่ำ",
        "profile_kwargs": {
            "age": 32, "annual_income": 360_000, "monthly_expenses": 22_000,
            "risk_tolerance": "conservative", "occupation": "employee",
            "marital_status": "single", "dependents": 0, "num_children": 0,
            "num_parents": 1, "life_insurance_amount": 30_000,
            "health_insurance_amount": 10_000, "existing_rmf": 0,
            "existing_thai_esg": 0, "existing_insurance": 0,
        },
        "money_goal": "short_term", "monthly_budget": 3_000,
        "income_growth_rate": 4.0,
        "reference": (
            "อายุ 32 ปี เป้าหมายระยะสั้น short_term ต้องใช้เงินภายใน 5 ปี "
            "ความเสี่ยงต่ำ conservative ไม่เหมาะลงทุน RMF ล็อคนาน "
            "ThaiESG ล็อค 5 ปี งบลงทุน 3000 บาทต่อเดือน 36000 บาทต่อปี "
            "ดูแลพ่อแม่ ลดหย่อนบิดามารดา ควรมีเงินสำรองก่อนลงทุน"
        ),
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Metric Helpers
# ─────────────────────────────────────────────────────────────────────────────

def thai_tokenize(text: str) -> str:
    if THAI_NLP:
        return " ".join(thai_word_tokenize(text, engine="newmm", keep_whitespace=False))
    return " ".join(list(text.replace(" ", "")))


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    scorer = rouge_scorer_module.RougeScorer(["rougeL"], use_stemmer=False)
    return scorer.score(thai_tokenize(reference), thai_tokenize(hypothesis))["rougeL"].fmeasure


def compute_bleu(reference: str, hypothesis: str) -> float:
    smooth = SmoothingFunction().method1
    if THAI_NLP:
        ref_tok = thai_word_tokenize(reference,  engine="newmm", keep_whitespace=False)
        hyp_tok = thai_word_tokenize(hypothesis, engine="newmm", keep_whitespace=False)
    else:
        ref_tok = list(reference.replace(" ", ""))
        hyp_tok = list(hypothesis.replace(" ", ""))
    return sentence_bleu([ref_tok], hyp_tok, smoothing_function=smooth)


def compute_bertscore_batch(references: List[str], hypotheses: List[str]) -> List[float]:
    if not ENABLE_BERTSCORE or not BERTSCORE_AVAILABLE:
        return [0.0] * len(hypotheses)
    try:
        _, _, F1 = bert_score_fn(
            hypotheses, references,
            lang="th", model_type="bert-base-multilingual-cased", verbose=False,
        )
        return F1.tolist()
    except Exception as e:
        print(f"   ⚠️  BERTScore error: {e}")
        return [0.0] * len(hypotheses)


def explanation_to_text(expl: Dict[str, Any]) -> str:
    return " ".join(str(v) for v in expl.values() if isinstance(v, str) and v.strip())


def avg(lst: List[float]) -> float:
    return sum(lst) / len(lst) if lst else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# DB fund fetch (read-only)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_recommended_funds(risk_tolerance: str, fund_types: List[str]) -> List[Dict]:
    import psycopg2, psycopg2.extras
    max_risk = 3 if risk_tolerance == "conservative" else 8 if risk_tolerance == "aggressive" else 6
    try:
        conn = psycopg2.connect("postgresql://postgres:projectyear4@localhost:5432/SmartTax")
        cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT "fundId","specCode" FROM fund_specs WHERE "specCode"=ANY(%s)', (fund_types,))
        spec_rows       = cur.fetchall()
        fund_id_to_spec = {r["fundId"]: r["specCode"] for r in spec_rows}
        eligible_ids    = list(fund_id_to_spec.keys())
        if not eligible_ids:
            conn.close(); return []
        cur.execute("""
            SELECT f.id, f."projAbbrName", f."projNameTh", rs."riskSpectrum"
            FROM funds f
            JOIN (
                SELECT DISTINCT ON ("fundId") "fundId","riskSpectrum"
                FROM fund_risk_spectrums ORDER BY "fundId","endDate" DESC
            ) rs ON rs."fundId"=f.id
            WHERE f.id=ANY(%s) AND f."fundStatus" IN ('Registered','IPO')
              AND rs."riskSpectrum"<=%s
        """, (eligible_ids, max_risk))
        funds = cur.fetchall()
        conn.close()
        result = []
        for ft in fund_types:
            top = [{"abbr": r["projAbbrName"], "nameTh": r["projNameTh"],
                    "fundType": fund_id_to_spec.get(r["id"], ft)}
                   for r in funds if fund_id_to_spec.get(r["id"]) == ft][:3]
            result.extend(top)
        return result
    except Exception as e:
        print(f"   ⚠️  DB fund fetch failed: {e}")
        return []


def make_profile_proxy(kw: dict):
    class P:
        marital_status          = kw.get("marital_status", "single")
        num_children            = kw.get("num_children", 0)
        num_parents             = kw.get("num_parents", 0)
        life_insurance_amount   = kw.get("life_insurance_amount", 0)
        health_insurance_amount = kw.get("health_insurance_amount", 0)
        annual_income           = kw["annual_income"]
        occupation              = kw.get("occupation", "employee")
        existing_insurance      = kw.get("existing_insurance", 0)
    return P()


# ─────────────────────────────────────────────────────────────────────────────
# Core experiment — 1 test case
# ─────────────────────────────────────────────────────────────────────────────

async def run_one_case(
    tc: dict,
    gen_advisor: AITaxAdvisor,
    judge_advisor: AITaxAdvisor,
    tax_svc: TaxFundService,
    rag_svc: RAGService,
) -> dict:
    kw = tc["profile_kwargs"]

    # ── build shared inputs (code-side, no LLM) ──────────────────────────────
    profile        = UserProfile(
        age=kw["age"], annual_income=kw["annual_income"],
        monthly_expenses=kw["monthly_expenses"], existing_savings=0,
        emergency_fund=0, risk_tolerance=kw["risk_tolerance"],
        occupation=kw.get("occupation","employee"),
        marital_status=kw.get("marital_status","single"),
        dependents=kw.get("dependents",0),
        existing_rmf=kw.get("existing_rmf",0),
        existing_thai_esg=kw.get("existing_thai_esg",0),
        existing_insurance=kw.get("existing_insurance",0),
    )
    family_ded     = _calculate_family_deductions(make_profile_proxy(kw))
    allocation     = calculate_allocation(
        age=kw["age"], income=kw["annual_income"],
        goal=tc["money_goal"], monthly_budget=tc["monthly_budget"],
        risk_tolerance=kw["risk_tolerance"],
        income_growth_rate=tc["income_growth_rate"],
        existing_rmf=kw.get("existing_rmf",0),
        existing_thai_esg=kw.get("existing_thai_esg",0),
    )
    savings        = tax_svc.calculate_tax_savings(
        annual_income=kw["annual_income"],
        rmf_investment=kw.get("existing_rmf",0) + allocation["rmf_amount"],
        thai_esg_investment=(
            kw.get("existing_thai_esg",0) + allocation["tesg_amount"] + allocation["tesgx_amount"]
        ),
        family_deductions=family_ded,
    )
    year_breakdown = _calculate_3year_breakdown(
        annual_income=kw["annual_income"],
        available_budget=tc["monthly_budget"] * 12,
        existing_rmf=kw.get("existing_rmf",0),
        existing_thai_esg=kw.get("existing_thai_esg",0),
        family_deductions=family_ded,
        income_growth_rate=tc["income_growth_rate"],
        tax_fund_svc=tax_svc,
        age=kw["age"], goal=tc["money_goal"],
        risk_tolerance=kw["risk_tolerance"],
    )

    rag_context = ""
    if rag_svc.is_available():
        try:
            docs = await rag_svc.retrieve_relevant_documents(
                f"RMF ThaiESG ลดหย่อนภาษี {tc['money_goal']} {kw['risk_tolerance']}", k=3
            )
            rag_context = "\n\n".join(d.page_content for d in docs)
        except Exception:
            pass

    fund_types = ["RMF", "TESG"] + (["TESGX"] if kw["risk_tolerance"] == "aggressive" else [])
    funds      = fetch_recommended_funds(kw["risk_tolerance"], fund_types)

    gen_kwargs = dict(
        profile=profile, allocation=allocation, tax_savings=savings,
        year_breakdown=year_breakdown, recommended_funds=funds,
        income_growth_rate=tc["income_growth_rate"],
        monthly_budget=float(tc["monthly_budget"]),
        rag_context=rag_context,
    )

    # =========================================================
    # CONDITION A — Byzantine: generate แล้วใช้เลย ไม่มี judge
    # (วัด judge score ทีหลังเพื่อ "เปิดเผย" คุณภาพที่ซ่อนอยู่)
    # =========================================================
    print(f"\n   [Byzantine] generate โดยไม่มี judge...", flush=True)
    byz_result: dict = {"judge_score": 0, "judge_passed": False, "text": "", "latency_sec": 0}
    try:
        t0        = time.time()
        expl_byz  = await gen_advisor.generate_recommendation_explanation(**gen_kwargs)
        j_byz     = await judge_advisor.judge_explanation(expl_byz, allocation, savings)
        byz_result = {
            "explanation"  : expl_byz,
            "text"         : explanation_to_text(expl_byz),
            "judge_score"  : j_byz["score"],
            "judge_passed" : j_byz["passed"],
            "number_score" : j_byz["number_score"],
            "llm_score"    : j_byz["llm_score"],
            "issues"       : j_byz.get("issues", []),
            "latency_sec"  : round(time.time() - t0, 1),
        }
        status = "✅ pass" if j_byz["passed"] else "❌ fail"
        print(f"   [Byzantine] score={j_byz['score']}/8 {status}  ({byz_result['latency_sec']}s)", flush=True)
    except Exception as e:
        print(f"   [Byzantine] ❌ ERROR: {e}", flush=True)
        byz_result["error"] = str(e)

    # =========================================================
    # CONDITION B — LLM-as-Judge: generate → judge → retry ถ้าไม่ผ่าน
    # (production flow เป๊ะ)
    # =========================================================
    print(f"\n   [Judge-flow] generate → judge → retry ถ้าไม่ผ่าน...", flush=True)
    judge_result: dict = {"final_score": 0, "final_passed": False, "text": "", "retried": False}
    try:
        t0         = time.time()
        expl_j1    = await gen_advisor.generate_recommendation_explanation(**gen_kwargs)
        j1         = await judge_advisor.judge_explanation(expl_j1, allocation, savings)
        retried    = False

        print(f"   [Judge-flow] 1st score={j1['score']}/8 {'✅' if j1['passed'] else '❌'}", flush=True)

        if not j1["passed"] and j1["score"] != -1:
            print(f"   [Judge-flow] judge ไม่ผ่าน → retry...", flush=True)
            expl_final = await gen_advisor.generate_recommendation_explanation(**gen_kwargs)
            j_final    = await judge_advisor.judge_explanation(expl_final, allocation, savings)
            retried    = True
            print(f"   [Judge-flow] retry score={j_final['score']}/8 {'✅' if j_final['passed'] else '❌'}", flush=True)
        else:
            expl_final = expl_j1
            j_final    = j1
            print(f"   [Judge-flow] ✅ ไม่ต้อง retry", flush=True)

        judge_result = {
            "first_score"  : j1["score"],
            "first_passed" : j1["passed"],
            "final_score"  : j_final["score"],
            "final_passed" : j_final["passed"],
            "retried"      : retried,
            "number_score" : j_final["number_score"],
            "llm_score"    : j_final["llm_score"],
            "issues"       : j_final.get("issues", []),
            "text"         : explanation_to_text(expl_final),
            "explanation"  : expl_final,
            "latency_sec"  : round(time.time() - t0, 1),
        }
    except Exception as e:
        print(f"   [Judge-flow] ❌ ERROR: {e}", flush=True)
        judge_result["error"] = str(e)

    return {
        "id"          : tc["id"],
        "desc"        : tc["desc"],
        "reference"   : tc["reference"],
        "allocation"  : {k: allocation.get(k, 0) for k in
                         ["rmf_amount","tesg_amount","tesgx_amount","total_amount"]},
        "tax_saved"   : savings.get("tax_saved", 0),
        "byzantine"   : byz_result,
        "judge_flow"  : judge_result,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

async def run_evaluation():
    print("=" * 70)
    print("  Byzantine Failure vs LLM-as-Judge Evaluation")
    print(f"  Generator    : {GENERATOR_MODEL}")
    print(f"  Judge        : {JUDGE_MODEL}")
    print(f"  Cases        : {len(TEST_CASES)}")
    print(f"  BERTScore    : {'ON' if ENABLE_BERTSCORE else 'OFF (เร็วขึ้น)'}")
    print(f"  LLM calls    : ~{len(TEST_CASES) * 2}-{len(TEST_CASES) * 4} calls total")
    print(f"  Date         : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    print("\n🔧 Initialising services...")
    tax_svc = TaxFundService(sec_service=None)
    rag_svc = RAGService()
    print(f"   RAG available: {rag_svc.is_available()}")

    gen_advisor   = AITaxAdvisor(
        provider="ollama", model=GENERATOR_MODEL,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    judge_advisor = AITaxAdvisor(
        provider="ollama", model=JUDGE_MODEL,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    print(f"   ✅ Generator  : {GENERATOR_MODEL}")
    print(f"   ✅ Judge      : {JUDGE_MODEL}")

    # ── รัน cases ทีละอัน (Ollama sequential) ────────────────────────────────
    all_results: List[dict] = []
    for tc in TEST_CASES:
        print(f"\n{'─'*70}")
        print(f"📋 {tc['id']}: {tc['desc']}")
        print(f"{'─'*70}")
        result = await run_one_case(tc, gen_advisor, judge_advisor, tax_svc, rag_svc)
        all_results.append(result)

    # ── Text metrics (ROUGE-L, BLEU, BERTScore) ───────────────────────────────
    print(f"\n\n{'─'*70}")
    print("📐 คำนวณ text metrics...")
    references  = [r["reference"]                  for r in all_results]
    byz_texts   = [r["byzantine"].get("text", "")  for r in all_results]
    judge_texts = [r["judge_flow"].get("text", "")  for r in all_results]

    byz_bert   = compute_bertscore_batch(references, byz_texts)
    judge_bert = compute_bertscore_batch(references, judge_texts)

    for i, result in enumerate(all_results):
        byz_llm_score   = result["byzantine"].get("llm_score", 0)
        judge_llm_score = result["judge_flow"].get("llm_score", 0)
        result["metrics"] = {
            "byzantine": {
                "rouge_l"        : round(compute_rouge_l(references[i], byz_texts[i]), 4),
                "bleu"           : round(compute_bleu(references[i], byz_texts[i]), 4),
                "bertscore"      : round(byz_bert[i], 4),
                "judge_score"    : result["byzantine"].get("judge_score", 0),
                "judge_passed"   : result["byzantine"].get("judge_passed", False),
                "llm_score"      : byz_llm_score,
                "llm_only_passed": byz_llm_score >= LLM_ONLY_THRESHOLD,
            },
            "judge_flow": {
                "rouge_l"        : round(compute_rouge_l(references[i], judge_texts[i]), 4),
                "bleu"           : round(compute_bleu(references[i], judge_texts[i]), 4),
                "bertscore"      : round(judge_bert[i], 4),
                "judge_score"    : result["judge_flow"].get("final_score", 0),
                "judge_passed"   : result["judge_flow"].get("final_passed", False),
                "llm_score"      : judge_llm_score,
                "llm_only_passed": judge_llm_score >= LLM_ONLY_THRESHOLD,
            },
        }

    # ── Summary ───────────────────────────────────────────────────────────────
    byz_m   = [r["metrics"]["byzantine"]  for r in all_results]
    judge_m = [r["metrics"]["judge_flow"] for r in all_results]

    byz_pass_rate      = sum(1 for m in byz_m   if m["judge_passed"])    / len(byz_m)
    jdg_pass_rate      = sum(1 for m in judge_m if m["judge_passed"])    / len(judge_m)
    byz_llm_pass_rate  = sum(1 for m in byz_m   if m["llm_only_passed"]) / len(byz_m)
    jdg_llm_pass_rate  = sum(1 for m in judge_m if m["llm_only_passed"]) / len(judge_m)
    retried_count      = sum(1 for r in all_results if r["judge_flow"].get("retried", False))

    print(f"\n\n{'='*70}")
    print("  SUMMARY — Byzantine Failure vs LLM-as-Judge")
    print(f"{'='*70}")
    print(f"{'Metric':<28} {'Byzantine (no judge)':>22} {'LLM-as-Judge':>15}")
    print(f"{'─'*28} {'─'*22} {'─'*15}")
    print(f"{'Judge Score avg (0-8)':<28} "
          f"{avg([m['judge_score'] for m in byz_m]):>22.2f} "
          f"{avg([m['judge_score'] for m in judge_m]):>15.2f}")
    print(f"{'Pass Rate strict (≥6/8)':<28} {byz_pass_rate:>22.1%} {jdg_pass_rate:>15.1%}")
    print(f"{'Pass Rate LLM-only (≥3/4)':<28} {byz_llm_pass_rate:>22.1%} {jdg_llm_pass_rate:>15.1%}")
    print(f"{'ROUGE-L avg':<28} "
          f"{avg([m['rouge_l'] for m in byz_m]):>22.4f} "
          f"{avg([m['rouge_l'] for m in judge_m]):>15.4f}")
    print(f"{'BLEU avg':<28} "
          f"{avg([m['bleu'] for m in byz_m]):>22.4f} "
          f"{avg([m['bleu'] for m in judge_m]):>15.4f}")
    if ENABLE_BERTSCORE:
        print(f"{'BERTScore avg':<28} "
              f"{avg([m['bertscore'] for m in byz_m]):>22.4f} "
              f"{avg([m['bertscore'] for m in judge_m]):>15.4f}")
    print(f"{'Retries triggered':<28} {'N/A':>22} {retried_count:>14}x")
    print(f"{'='*70}")

    print(f"\n📊 Per-case:")
    print(f"{'ID':<6} {'Byz score':>10} {'Byz pass':>10} │ {'Judge score':>12} {'Judge pass':>11} {'Retry':>6}")
    print(f"{'─'*6} {'─'*10} {'─'*10} {'─':>2} {'─'*12} {'─'*11} {'─'*6}")
    for r in all_results:
        bm = r["metrics"]["byzantine"]
        jm = r["metrics"]["judge_flow"]
        retry = "✅" if r["judge_flow"].get("retried") else "-"
        print(f"{r['id']:<6} {bm['judge_score']:>8}/8  {'✅' if bm['judge_passed'] else '❌':>9}   │"
              f" {jm['judge_score']:>10}/8  {'✅' if jm['judge_passed'] else '❌':>10}  {retry:>6}")

    print(f"\n💡 Interpretation:")
    score_diff = avg([m['judge_score'] for m in judge_m]) - avg([m['judge_score'] for m in byz_m])
    if jdg_pass_rate > byz_pass_rate:
        print(f"   ✅ LLM-as-Judge pass rate สูงกว่า Byzantine "
              f"({jdg_pass_rate:.0%} vs {byz_pass_rate:.0%}, +{jdg_pass_rate-byz_pass_rate:.0%})")
    elif jdg_pass_rate == byz_pass_rate:
        print(f"   ➡️  Pass rate เท่ากัน ({jdg_pass_rate:.0%}) แต่ Judge รับประกันคุณภาพ — Byzantine ไม่รู้ว่าดีหรือแย่")
    if retried_count > 0:
        print(f"   🔄 Judge ตรวจพบ output ไม่ผ่านและ retry {retried_count} ครั้ง (Byzantine ไม่มีกลไกนี้)")
    if score_diff > 0:
        print(f"   📈 Judge score เฉลี่ยดีขึ้น +{score_diff:.2f} คะแนน")

    # ── Save ──────────────────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file  = out_dir / f"byzantine_vs_judge_{timestamp}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp"     : timestamp,
            "generator"     : GENERATOR_MODEL,
            "judge"         : JUDGE_MODEL,
            "bertscore_on"  : ENABLE_BERTSCORE,
            "summary": {
                "byzantine" : {
                    "avg_judge_score": round(avg([m["judge_score"] for m in byz_m]), 4),
                    "pass_rate"      : round(byz_pass_rate, 4),
                    "avg_rouge_l"    : round(avg([m["rouge_l"]    for m in byz_m]), 4),
                    "avg_bleu"       : round(avg([m["bleu"]       for m in byz_m]), 4),
                    "avg_bertscore"  : round(avg([m["bertscore"]  for m in byz_m]), 4),
                },
                "judge_flow": {
                    "avg_judge_score": round(avg([m["judge_score"] for m in judge_m]), 4),
                    "pass_rate"      : round(jdg_pass_rate, 4),
                    "avg_rouge_l"    : round(avg([m["rouge_l"]    for m in judge_m]), 4),
                    "avg_bleu"       : round(avg([m["bleu"]       for m in judge_m]), 4),
                    "avg_bertscore"  : round(avg([m["bertscore"]  for m in judge_m]), 4),
                    "retried_count"  : retried_count,
                },
            },
            "details": all_results,
        }, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Results saved → {out_file}\n")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
