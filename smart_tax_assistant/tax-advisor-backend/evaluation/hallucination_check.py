"""
Hallucination Checker
======================
จับผิด LLM ว่าพูดผิดไหม — ไม่ใช่แค่ "พูดถึงหรือเปล่า" แต่ "พูดถูกหรือเปล่า"

ตรวจ 4 ประเภท:
  CORRECT  = พูดถึงตัวเลข/ข้อมูลถูกต้อง
  MISSING  = ไม่ได้พูดถึงเลย (ไม่ได้ผิด แค่ไม่ครบ)
  WRONG    = พูดถึงแต่ตัวเลขผิด (hallucination!)
  CONFLICT = พูดทั้งถูกและผิดในคำตอบเดียวกัน

วิธีรัน:
  python evaluation/hallucination_check.py
"""

import json, sys, re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ─── load result ─────────────────────────────────────────────────────────────
RESULTS_DIR = Path(__file__).parent / "results"
files = sorted(RESULTS_DIR.glob("eval_*.json"), reverse=True)
if not files:
    print("ไม่พบ result file"); sys.exit(1)

with open(files[0], encoding="utf-8") as f:
    data = json.load(f)

MODELS  = data["models"]
DETAILS = data["details"]

CURRENT_YEAR_BE = 2569
TESG_LOCK       = 5
RMF_MIN_AGE     = 55

TC_PROFILES = {
    "TC1": {"age": 28, "income": 600_000,   "risk": "moderate",     "goal": "retirement"},
    "TC2": {"age": 35, "income": 1_500_000, "risk": "aggressive",   "goal": "retirement"},
    "TC3": {"age": 40, "income": 840_000,   "risk": "moderate",     "goal": "mid_term"},
    "TC4": {"age": 50, "income": 1_200_000, "risk": "conservative", "goal": "retirement"},
    "TC5": {"age": 32, "income": 360_000,   "risk": "conservative", "goal": "short_term"},
}

# ─── helpers ─────────────────────────────────────────────────────────────────
def extract_numbers_near(text: str, keyword: str, window: int = 60) -> List[int]:
    """หาตัวเลขทั้งหมดในรัศมี window ตัวอักษรรอบๆ keyword"""
    results = []
    for m in re.finditer(re.escape(keyword), text):
        start = max(0, m.start() - window)
        end   = min(len(text), m.end() + window)
        snippet = text[start:end]
        for num in re.findall(r"[\d,]+", snippet):
            clean = num.replace(",", "")
            if clean.isdigit():
                results.append(int(clean))
    return results

def extract_all_numbers(text: str) -> set:
    nums = set()
    for n in re.findall(r"[\d,]+", text):
        c = n.replace(",", "")
        if c.isdigit() and len(c) >= 2:
            nums.add(int(c))
    return nums

def is_similar(a: int, b: int, pct: float = 0.15) -> bool:
    """ตัวเลขใกล้เคียงกัน ±15% (เพื่อจับ hallucination)"""
    if b == 0:
        return False
    return abs(a - b) / b <= pct

STATUS_ICON = {
    "CORRECT" : "✅",
    "MISSING" : "⬜",
    "WRONG"   : "❌",
    "CONFLICT": "⚠️",
}

# ─── check แต่ละ fact ────────────────────────────────────────────────────────
def check_fact(
    field_text: str,
    correct_value: int,
    wrong_candidates: Optional[set] = None,
    label: str = "",
) -> str:
    """
    ตรวจว่า field_text พูดถึง correct_value ถูกต้องไหม

    Returns: CORRECT / MISSING / WRONG / CONFLICT
    """
    all_nums = extract_all_numbers(field_text)
    has_correct = correct_value in all_nums

    # หาตัวเลขที่ใกล้เคียง correct แต่ไม่ใช่ correct (potential wrong)
    if wrong_candidates is None:
        wrong_candidates = set()
    similar_wrong = {
        n for n in all_nums
        if n != correct_value
        and is_similar(n, correct_value)
        and n not in wrong_candidates  # ไม่นับตัวเลขที่ถูกต้องอื่นๆ
    }

    if has_correct and similar_wrong:
        return "CONFLICT"
    if has_correct:
        return "CORRECT"
    if similar_wrong:
        return "WRONG"
    return "MISSING"


# ─── define checks per TC ────────────────────────────────────────────────────
def get_checks(tc_id: str, tc_data: dict) -> List[Dict]:
    """
    คืน list ของ checks แต่ละอัน:
      field       - ตรวจใน field ไหน
      label       - ชื่อ fact
      value       - ค่าที่ถูกต้อง
      safe_values - ตัวเลขอื่นที่ "ถูก" ในบริบทนี้ (ไม่ถือว่า wrong)
    """
    profile = TC_PROFILES[tc_id]
    alloc   = tc_data["allocation"]
    age     = profile["age"]

    rmf   = int(alloc["rmf_amount"])
    tesg  = int(alloc["tesg_amount"])
    tesgx = int(alloc["tesgx_amount"])
    total = int(alloc["total_amount"])
    tax   = int(tc_data["tax_saved"])

    years_to_55  = max(0, RMF_MIN_AGE - age)
    rmf_year_be  = CURRENT_YEAR_BE + years_to_55
    tesg_year_be = CURRENT_YEAR_BE + TESG_LOCK

    monthly_rmf  = rmf  // 12
    monthly_tesg = tesg // 12

    # safe_values = ตัวเลขอื่นๆ ที่ถูกต้องในบริบท (เพื่อไม่ให้ false positive)
    all_correct = {rmf, tesg, tesgx, total, tax, years_to_55,
                   rmf_year_be, tesg_year_be, monthly_rmf, monthly_tesg,
                   age, RMF_MIN_AGE, TESG_LOCK}

    checks = []

    # age_analysis — ตรวจปีที่ล็อคและถอนได้
    if years_to_55 > 0:
        checks.append({"field": "age_analysis", "label": f"years_to_55 ({years_to_55}ปี)",
                       "value": years_to_55, "safe": all_correct})
    checks.append({"field": "age_analysis", "label": f"ThaiESG unlock ({tesg_year_be})",
                   "value": tesg_year_be, "safe": all_correct})
    if 0 < years_to_55 <= 35:
        checks.append({"field": "age_analysis", "label": f"RMF unlock ({rmf_year_be})",
                       "value": rmf_year_be, "safe": all_correct})

    # budget_analysis — ตรวจตัวเลขเงิน
    if rmf > 0:
        checks.append({"field": "budget_analysis", "label": f"RMF/ปี ({rmf:,})",
                       "value": rmf, "safe": all_correct})
    if tesg > 0:
        checks.append({"field": "budget_analysis", "label": f"ThaiESG/ปี ({tesg:,})",
                       "value": tesg, "safe": all_correct})
    if monthly_rmf > 0:
        checks.append({"field": "budget_analysis", "label": f"RMF DCA/เดือน ({monthly_rmf:,})",
                       "value": monthly_rmf, "safe": all_correct})
    if tax > 0:
        checks.append({"field": "budget_analysis", "label": f"tax saved ({tax:,})",
                       "value": tax, "safe": all_correct})

    # summary — ตรวจตัวเลขสรุป
    if total > 0:
        checks.append({"field": "summary", "label": f"total invest ({total:,})",
                       "value": total, "safe": all_correct})
    if tax > 0:
        checks.append({"field": "summary", "label": f"tax saved ({tax:,})",
                       "value": tax, "safe": all_correct})

    return checks


# ─── Main ────────────────────────────────────────────────────────────────────
print("=" * 75)
print("  Hallucination Check — จับผิดตัวเลขใน LLM response")
print("=" * 75)
print(f"  ✅ CORRECT  = พูดถูกต้อง")
print(f"  ⬜ MISSING  = ไม่ได้พูดถึง (ไม่ได้ผิด)")
print(f"  ❌ WRONG    = พูดถึงแต่ตัวเลขผิด ← จับผิดได้!")
print(f"  ⚠️  CONFLICT = มีทั้งถูกและผิดในคำตอบเดียว")

# สะสม stats
model_stats: Dict[str, Dict] = {
    m: {"CORRECT": 0, "MISSING": 0, "WRONG": 0, "CONFLICT": 0}
    for m in MODELS
}

for tc in DETAILS:
    tc_id  = tc["id"]
    checks = get_checks(tc_id, tc)

    print(f"\n{'─'*75}")
    print(f"📋 {tc_id}: {tc['desc']}")
    print(f"{'─'*75}")

    for model in MODELS:
        r = tc["models"].get(model, {})
        if r.get("error") or not r.get("explanation"):
            print(f"  {model}: SKIP"); continue

        exp = r["explanation"]
        row_results = []

        for chk in checks:
            field_text = exp.get(chk["field"], "")
            status = check_fact(
                field_text,
                chk["value"],
                wrong_candidates=chk["safe"],
                label=chk["label"],
            )
            model_stats[model][status] += 1
            row_results.append((chk["label"], status))

        # แสดงผล compact
        wrong_items   = [(l, s) for l, s in row_results if s == "WRONG"]
        conflict_items = [(l, s) for l, s in row_results if s == "CONFLICT"]
        correct_count = sum(1 for _, s in row_results if s == "CORRECT")
        total_count   = len(row_results)

        flag = ""
        if wrong_items:
            flag = f"  ← ❌ WRONG: {', '.join(l for l,_ in wrong_items)}"
        elif conflict_items:
            flag = f"  ← ⚠️  CONFLICT: {', '.join(l for l,_ in conflict_items)}"

        print(f"  {model:<22} "
              f"✅{correct_count} "
              f"⬜{sum(1 for _,s in row_results if s=='MISSING')} "
              f"❌{sum(1 for _,s in row_results if s=='WRONG')} "
              f"⚠️{sum(1 for _,s in row_results if s=='CONFLICT')}"
              f"{flag}")

# ─── Summary ─────────────────────────────────────────────────────────────────
print(f"\n\n{'='*75}")
print("  HALLUCINATION SUMMARY")
print(f"{'='*75}")
print(f"{'Model':<22} {'✅CORRECT':>10} {'⬜MISSING':>10} {'❌WRONG':>8} {'⚠️CONFLICT':>10} {'Accuracy':>9}")
print(f"{'─'*22} {'─'*10} {'─'*10} {'─'*8} {'─'*10} {'─'*9}")

for model in MODELS:
    s  = model_stats[model]
    total = sum(s.values())
    acc   = s["CORRECT"] / total if total else 0
    print(f"{model:<22} {s['CORRECT']:>10} {s['MISSING']:>10} "
          f"{s['WRONG']:>8} {s['CONFLICT']:>10} {acc:>8.0%}")

print(f"\n  * Accuracy = CORRECT / (CORRECT + MISSING + WRONG + CONFLICT)")
print(f"  * ❌ WRONG คือสิ่งที่เป็น hallucination จริงๆ — LLM บอกตัวเลขผิด")
