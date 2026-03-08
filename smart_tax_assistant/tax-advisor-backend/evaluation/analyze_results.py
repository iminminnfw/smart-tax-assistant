"""
Analyze Existing Evaluation Results
=====================================
วัด metrics เพิ่มจาก eval JSON ที่มีอยู่แล้ว (ไม่ต้องรัน LLM ใหม่)

Metrics:
  1. Number Accuracy     — ตัวเลขจากโปรไฟล์ปรากฏในคำตอบกี่ %
  2. Thai Language Purity — % ตัวอักษรภาษาไทยในคำตอบ
  3. Field Length Balance — std dev ของความยาวแต่ละ field (ยิ่งน้อยยิ่งสมดุล)

วิธีรัน:
  python evaluation/analyze_results.py
"""

import json
import sys
import re
import statistics
from pathlib import Path
from typing import Dict, List, Any

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# หา result file ล่าสุด
# ─────────────────────────────────────────────────────────────────────────────
RESULTS_DIR = Path(__file__).parent / "results"
result_files = sorted(RESULTS_DIR.glob("eval_*.json"), reverse=True)
if not result_files:
    print("❌ ไม่พบ result file ใน evaluation/results/")
    sys.exit(1)

RESULT_FILE = result_files[0]
print(f"📂 Loading: {RESULT_FILE.name}\n")

with open(RESULT_FILE, encoding="utf-8") as f:
    data = json.load(f)

MODELS  = data["models"]
DETAILS = data["details"]
FIELDS  = ["age_analysis", "goal_analysis", "risk_analysis", "budget_analysis",
           "fund_reasons", "warnings", "future_advice", "summary"]

# ─────────────────────────────────────────────────────────────────────────────
# ตัวเลขสำคัญของแต่ละ test case (ดึงจาก allocation + tax_saved ใน result)
# ─────────────────────────────────────────────────────────────────────────────
def get_key_numbers(tc: Dict) -> List[str]:
    """ตัวเลขที่ LLM ควรอ้างถึงใน response"""
    nums = []
    alloc = tc.get("allocation", {})
    for key in ["rmf_amount", "tesg_amount", "tesgx_amount", "total_amount"]:
        v = alloc.get(key, 0)
        if v and v > 0:
            # รูปแบบที่อาจปรากฏ: "67,200" หรือ "67200"
            nums.append(f"{v:,.0f}")
            nums.append(f"{int(v)}")
    tax = tc.get("tax_saved", 0)
    if tax and tax > 0:
        nums.append(f"{tax:,.0f}")
        nums.append(f"{int(tax)}")
    return nums


# ─────────────────────────────────────────────────────────────────────────────
# Metric 1: Number Accuracy
# ─────────────────────────────────────────────────────────────────────────────
def number_accuracy(response_text: str, key_numbers: List[str]) -> float:
    """กี่ % ของตัวเลขสำคัญที่ปรากฏในคำตอบ"""
    if not key_numbers:
        return 0.0
    found = sum(1 for n in key_numbers if n in response_text)
    return found / len(key_numbers)


# ─────────────────────────────────────────────────────────────────────────────
# Metric 2: Thai Language Purity
# ─────────────────────────────────────────────────────────────────────────────
def thai_purity(text: str) -> float:
    """% ของตัวอักษรที่เป็นภาษาไทย (Unicode U+0E00–U+0E7F)"""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    thai = sum(1 for c in letters if "\u0e00" <= c <= "\u0e7f")
    return thai / len(letters)


# ─────────────────────────────────────────────────────────────────────────────
# Metric 3: Field Length Balance (std dev)
# ─────────────────────────────────────────────────────────────────────────────
def field_balance(explanation: Dict) -> float:
    """std dev ของความยาวแต่ละ field — ยิ่งน้อยยิ่งสมดุล"""
    lengths = [len(explanation.get(f, "")) for f in FIELDS]
    lengths = [l for l in lengths if l > 0]
    if len(lengths) < 2:
        return 0.0
    return statistics.stdev(lengths)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
model_scores: Dict[str, Dict[str, List[float]]] = {
    m: {"num_acc": [], "thai_purity": [], "field_balance": []}
    for m in MODELS
}

print("=" * 70)
print("  Additional Metrics Analysis")
print("=" * 70)

for tc in DETAILS:
    key_numbers = get_key_numbers(tc)
    print(f"\n{'─'*70}")
    print(f"📋 {tc['id']}: {tc['desc']}")
    print(f"   Key numbers to check: {key_numbers[:6]}")
    print(f"{'─'*70}")

    for model in MODELS:
        r = tc["models"].get(model, {})
        if r.get("error") or not r.get("explanation"):
            print(f"   {model:<22}: SKIP (error/no explanation)")
            continue

        explanation = r["explanation"]
        full_text   = " ".join(str(v) for v in explanation.values() if isinstance(v, str))

        num_acc  = number_accuracy(full_text, key_numbers)
        purity   = thai_purity(full_text)
        balance  = field_balance(explanation)

        model_scores[model]["num_acc"].append(num_acc)
        model_scores[model]["thai_purity"].append(purity)
        model_scores[model]["field_balance"].append(balance)

        print(
            f"   {model:<22}  "
            f"NumAcc={num_acc:.0%}  "
            f"ThaiPurity={purity:.0%}  "
            f"FieldStd={balance:.0f}chars"
        )

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
def avg(lst):
    return sum(lst) / len(lst) if lst else 0.0

print(f"\n\n{'='*70}")
print("  SUMMARY — Average across all test cases")
print(f"{'='*70}")
print(f"{'Model':<22} {'NumAcc':>9} {'ThaiPurity':>11} {'FieldStd':>10}")
print(f"{'─'*22} {'─'*9} {'─'*11} {'─'*10}")

for model in MODELS:
    s = model_scores[model]
    na = avg(s["num_acc"])
    tp = avg(s["thai_purity"])
    fb = avg(s["field_balance"])
    print(f"{model:<22} {na:>8.0%}  {tp:>9.0%}  {fb:>9.0f}chars")

print(f"\n{'─'*70}")
print("คำอธิบาย:")
print("  NumAcc     — % ตัวเลขสำคัญ (RMF/tax) ที่ปรากฏในคำตอบ (ยิ่งสูงยิ่งดี)")
print("  ThaiPurity — % ตัวอักษรภาษาไทย (ยิ่งสูงยิ่งดี)")
print("  FieldStd   — std dev ความยาวแต่ละ field (ยิ่งน้อยยิ่งสมดุล)")

# ─────────────────────────────────────────────────────────────────────────────
# Combined Score (normalize + weight)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("  COMBINED SCORE (ROUGE-L 40% + KW 30% + NumAcc 20% + ThaiPurity 10%)")
print(f"{'='*70}")

orig_summary = data.get("summary", {})

for model in MODELS:
    s   = model_scores[model]
    orig = orig_summary.get(model, {})

    rouge  = orig.get("avg_rouge_l", 0)
    kw     = orig.get("avg_keyword_coverage", 0)
    num_ac = avg(s["num_acc"])
    thai_p = avg(s["thai_purity"])

    combined = rouge * 0.40 + kw * 0.30 + num_ac * 0.20 + thai_p * 0.10
    print(f"  {model:<22}: {combined:.4f}  "
          f"(ROUGE={rouge:.3f} KW={kw:.3f} NumAcc={num_ac:.3f} Thai={thai_p:.3f})")

best = max(MODELS, key=lambda m: (
    orig_summary.get(m, {}).get("avg_rouge_l", 0) * 0.40 +
    orig_summary.get(m, {}).get("avg_keyword_coverage", 0) * 0.30 +
    avg(model_scores[m]["num_acc"]) * 0.20 +
    avg(model_scores[m]["thai_purity"]) * 0.10
))
print(f"\n🏆 Best Overall: {best}")
