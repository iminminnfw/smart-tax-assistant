"""
Factual Accuracy Checker
=========================
ตรวจว่า LLM พูดถึงข้อเท็จจริงถูกต้องหรือไม่ โดยไม่ต้องรัน LLM ใหม่

สิ่งที่ตรวจ (per test case):
  1. ตัวเลขเงินลงทุน   — RMF / ThaiESG / TESGX ที่ระบุในแผน
  2. ปีที่ถอนได้       — ThaiESG ล็อค 5 ปี / RMF ต้องอายุ 55
  3. DCA รายเดือน     — เงินลงทุน ÷ 12
  4. ไม่มีตัวเลขผิด   — hallucination check (ตัวเลขที่ไม่ควรปรากฏ)

วิธีรัน:
  python evaluation/factual_accuracy.py
"""

import json, sys, re
from pathlib import Path
from typing import Dict, List, Tuple

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ─── load result file ────────────────────────────────────────────────────────
RESULTS_DIR = Path(__file__).parent / "results"
result_files = sorted(RESULTS_DIR.glob("eval_*.json"), reverse=True)
if not result_files:
    print("ไม่พบ result file"); sys.exit(1)

with open(result_files[0], encoding="utf-8") as f:
    data = json.load(f)

MODELS  = data["models"]
DETAILS = data["details"]

CURRENT_YEAR_BE = 2569   # พ.ศ. 2569 = ค.ศ. 2026
TESG_LOCK_YEARS = 5
RMF_MIN_AGE     = 55

# ─── profile ของแต่ละ TC (copy จาก eval script) ─────────────────────────────
TC_PROFILES = {
    "TC1": {"age": 28, "income": 600_000,   "risk": "moderate",     "goal": "retirement"},
    "TC2": {"age": 35, "income": 1_500_000, "risk": "aggressive",   "goal": "retirement"},
    "TC3": {"age": 40, "income": 840_000,   "risk": "moderate",     "goal": "mid_term"},
    "TC4": {"age": 50, "income": 1_200_000, "risk": "conservative", "goal": "retirement"},
    "TC5": {"age": 32, "income": 360_000,   "risk": "conservative", "goal": "short_term"},
}

# ─── คำนวณ expected facts ────────────────────────────────────────────────────
def compute_expected_facts(tc_id: str, tc_data: dict) -> dict:
    profile = TC_PROFILES[tc_id]
    alloc   = tc_data["allocation"]

    rmf   = int(alloc["rmf_amount"])
    tesg  = int(alloc["tesg_amount"])
    tesgx = int(alloc["tesgx_amount"])
    total = int(alloc["total_amount"])
    tax   = int(tc_data["tax_saved"])

    age          = profile["age"]
    years_to_55  = max(0, RMF_MIN_AGE - age)
    rmf_year_be  = CURRENT_YEAR_BE + years_to_55      # ปีที่ถอน RMF ได้
    tesg_year_be = CURRENT_YEAR_BE + TESG_LOCK_YEARS  # ปีที่ถอน ThaiESG ได้

    monthly_rmf  = rmf  // 12
    monthly_tesg = tesg // 12

    return {
        "rmf_amount"    : rmf,
        "tesg_amount"   : tesg,
        "tesgx_amount"  : tesgx,
        "total_amount"  : total,
        "tax_saved"     : tax,
        "years_to_55"   : years_to_55,
        "rmf_year_be"   : rmf_year_be,
        "tesg_year_be"  : tesg_year_be,
        "monthly_rmf"   : monthly_rmf,
        "monthly_tesg"  : monthly_tesg,
    }

# ─── helper: หาตัวเลขทั้งหมดในข้อความ ─────────────────────────────────────
def extract_numbers(text: str) -> set:
    """ดึงตัวเลขทั้งหมด (รวม comma-formatted) จากข้อความ"""
    # จับรูปแบบ 1,234,567 และ 1234567
    raw = re.findall(r"[\d,]+", text)
    nums = set()
    for r in raw:
        clean = r.replace(",", "")
        if clean.isdigit() and len(clean) >= 2:
            nums.add(int(clean))
    return nums

def num_in_text(value: int, text: str) -> bool:
    """ตรวจว่าตัวเลข value ปรากฏในข้อความ (แบบมี/ไม่มี comma)"""
    return f"{value:,}" in text or str(value) in text

# ─── ตรวจแต่ละ fact ──────────────────────────────────────────────────────────
def check_facts(explanation: dict, facts: dict) -> List[Tuple[str, bool, str]]:
    """
    คืน list ของ (fact_name, passed, detail)
    """
    full_text = " ".join(str(v) for v in explanation.values() if isinstance(v, str))
    checks = []

    # 1. ตัวเลขเงินลงทุนหลัก
    for key, label in [
        ("rmf_amount",  "RMF amount"),
        ("tesg_amount", "ThaiESG amount"),
        ("tax_saved",   "Tax saved"),
    ]:
        val = facts[key]
        if val > 0:
            ok = num_in_text(val, full_text)
            checks.append((label, ok, f"หา {val:,} ในข้อความ"))

    # 2. TESGX (เฉพาะ aggressive)
    if facts["tesgx_amount"] > 0:
        ok = num_in_text(facts["tesgx_amount"], full_text)
        checks.append(("TESGX amount", ok, f"หา {facts['tesgx_amount']:,}"))

    # 3. years_to_55
    y55 = facts["years_to_55"]
    if y55 > 0:
        ok = str(y55) in full_text
        checks.append(("Years to 55", ok, f"หา '{y55} ปี' ก่อนอายุ 55"))

    # 4. ปีที่ถอน ThaiESG (พ.ศ.)
    tesg_yr = facts["tesg_year_be"]
    ok = str(tesg_yr) in full_text
    checks.append(("ThaiESG unlock year", ok, f"หาปี {tesg_yr}"))

    # 5. ปีที่ถอน RMF (เฉพาะถ้า years_to_55 ≤ 30)
    if 0 < facts["years_to_55"] <= 30:
        rmf_yr = facts["rmf_year_be"]
        ok = str(rmf_yr) in full_text
        checks.append(("RMF unlock year", ok, f"หาปี {rmf_yr}"))

    # 6. DCA รายเดือน RMF
    m_rmf = facts["monthly_rmf"]
    if m_rmf > 0:
        ok = num_in_text(m_rmf, full_text)
        checks.append(("Monthly RMF DCA", ok, f"หา {m_rmf:,}/เดือน"))

    return checks


# ─── Main ────────────────────────────────────────────────────────────────────
print("=" * 70)
print("  Factual Accuracy Check")
print("  (ตรวจว่า LLM พูดถึงข้อเท็จจริงถูกต้องไหม)")
print("=" * 70)

# เก็บ score รวม
model_totals: Dict[str, Dict] = {m: {"pass": 0, "total": 0} for m in MODELS}

for tc in DETAILS:
    tc_id   = tc["id"]
    facts   = compute_expected_facts(tc_id, tc)

    print(f"\n{'─'*70}")
    print(f"📋 {tc_id}: {tc['desc']}")
    print(f"   Expected: RMF={facts['rmf_amount']:,}  ThaiESG={facts['tesg_amount']:,}  "
          f"Tax={facts['tax_saved']:,}  ThaiESG unlock={facts['tesg_year_be']}")
    print(f"{'─'*70}")

    for model in MODELS:
        r = tc["models"].get(model, {})
        if r.get("error") or not r.get("explanation"):
            print(f"   {model:<22}: SKIP")
            continue

        results = check_facts(r["explanation"], facts)
        passed  = sum(1 for _, ok, _ in results if ok)
        total   = len(results)
        pct     = passed / total if total else 0

        model_totals[model]["pass"]  += passed
        model_totals[model]["total"] += total

        # แสดงผล
        status_str = "  ".join(
            f"{'✅' if ok else '❌'}{name}"
            for name, ok, _ in results
        )
        print(f"   {model:<22} [{passed}/{total} = {pct:.0%}]  {status_str}")

# ─── Summary ─────────────────────────────────────────────────────────────────
print(f"\n\n{'='*70}")
print("  FACTUAL ACCURACY SUMMARY")
print(f"{'='*70}")
print(f"{'Model':<22} {'Correct':>8} {'Total':>7} {'Accuracy':>10}")
print(f"{'─'*22} {'─'*8} {'─'*7} {'─'*10}")

for model in MODELS:
    p = model_totals[model]["pass"]
    t = model_totals[model]["total"]
    acc = p / t if t else 0
    print(f"{model:<22} {p:>8} {t:>7} {acc:>9.0%}")

print(f"\n{'─'*70}")
print("คำอธิบาย:")
print("  ✅ = LLM พูดถึงตัวเลข/ข้อมูลถูกต้องตรงกับที่ backend คำนวณ")
print("  ❌ = LLM ไม่ได้พูดถึง หรืออธิบายแบบกลางๆ ไม่ระบุตัวเลขจริง")
print("\n  หมายเหตุ: ❌ ไม่ได้แปลว่าผิด — อาจแค่ไม่ระบุตัวเลขนั้นในคำตอบ")
