"""
Re-analyze ผล Byzantine vs Judge จาก JSON ที่มีอยู่แล้ว
======================================================
ไม่ต้องรัน LLM ใหม่ — อ่านจาก results/ แล้วคำนวณ metrics ใหม่

วิธีรัน:
  cd tax-advisor-backend

  # ใช้ไฟล์ล่าสุดอัตโนมัติ
  python -m evaluation.reanalyze

  # หรือระบุไฟล์เอง
  python -m evaluation.reanalyze evaluation/results/byzantine_vs_judge_20260316_012153.json
"""

import json
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# Config — ปรับได้เลยโดยไม่ต้องรัน LLM ใหม่
# ─────────────────────────────────────────────────────────────────────────────
STRICT_THRESHOLD   = 6   # score/8  รวม number check (เหมือน production)
LLM_ONLY_THRESHOLD = 3   # llm_score/4  ตัด number check ออก


def avg(lst):
    return sum(lst) / len(lst) if lst else 0.0


def load_latest_result() -> tuple[dict, Path]:
    results_dir = Path(__file__).parent / "results"
    files = sorted(results_dir.glob("byzantine_vs_judge_*.json"), reverse=True)
    if not files:
        print("❌ ไม่พบไฟล์ผลใน evaluation/results/")
        sys.exit(1)
    path = files[0]
    print(f"📂 โหลดไฟล์: {path.name}")
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def reanalyze(data: dict):
    details = data.get("details", [])
    if not details:
        print("❌ ไม่มี details ในไฟล์นี้")
        return

    print(f"\n   Generator : {data.get('generator', '?')}")
    print(f"   Judge     : {data.get('judge', '?')}")
    print(f"   Cases     : {len(details)}")

    rows = []
    for r in details:
        byz  = r.get("byzantine", {})
        jf   = r.get("judge_flow", {})

        byz_judge_score  = byz.get("judge_score", 0)
        byz_llm_score    = byz.get("llm_score", 0)
        byz_num_score    = byz.get("number_score", 0)

        jf_judge_score   = jf.get("final_score", 0)
        jf_llm_score     = jf.get("llm_score", 0)
        jf_num_score     = jf.get("number_score", 0)
        jf_first_score   = jf.get("first_score", jf_judge_score)

        rows.append({
            "id"               : r["id"],
            "desc"             : r["desc"],
            # Byzantine
            "byz_score"        : byz_judge_score,
            "byz_num"          : byz_num_score,
            "byz_llm"          : byz_llm_score,
            "byz_strict_pass"  : byz_judge_score  >= STRICT_THRESHOLD,
            "byz_llm_pass"     : byz_llm_score    >= LLM_ONLY_THRESHOLD,
            "byz_issues"       : byz.get("issues", []),
            # Judge-flow
            "jf_first_score"   : jf_first_score,
            "jf_final_score"   : jf_judge_score,
            "jf_num"           : jf_num_score,
            "jf_llm"           : jf_llm_score,
            "jf_strict_pass"   : jf_judge_score   >= STRICT_THRESHOLD,
            "jf_llm_pass"      : jf_llm_score     >= LLM_ONLY_THRESHOLD,
            "retried"          : jf.get("retried", False),
            "jf_issues"        : jf.get("issues", []),
            # text metrics (ถ้ามี)
            "byz_rouge_l"      : r.get("metrics", {}).get("byzantine",  {}).get("rouge_l",   0),
            "byz_bleu"         : r.get("metrics", {}).get("byzantine",  {}).get("bleu",      0),
            "byz_bert"         : r.get("metrics", {}).get("byzantine",  {}).get("bertscore", 0),
            "jf_rouge_l"       : r.get("metrics", {}).get("judge_flow", {}).get("rouge_l",   0),
            "jf_bleu"          : r.get("metrics", {}).get("judge_flow", {}).get("bleu",      0),
            "jf_bert"          : r.get("metrics", {}).get("judge_flow", {}).get("bertscore", 0),
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    byz_strict_rate = avg([1 if r["byz_strict_pass"] else 0 for r in rows])
    jf_strict_rate  = avg([1 if r["jf_strict_pass"]  else 0 for r in rows])
    byz_llm_rate    = avg([1 if r["byz_llm_pass"]    else 0 for r in rows])
    jf_llm_rate     = avg([1 if r["jf_llm_pass"]     else 0 for r in rows])
    retried_count   = sum(1 for r in rows if r["retried"])

    print(f"\n{'='*70}")
    print(f"  Re-Analysis — Strict vs LLM-only scoring")
    print(f"  Strict threshold   : {STRICT_THRESHOLD}/8  (number check + LLM check)")
    print(f"  LLM-only threshold : {LLM_ONLY_THRESHOLD}/4  (LLM check เท่านั้น, ตัด number check)")
    print(f"{'='*70}")
    print(f"{'Metric':<30} {'Byzantine':>18} {'LLM-as-Judge':>15}")
    print(f"{'─'*30} {'─'*18} {'─'*15}")
    print(f"{'Judge Score avg (0-8)':<30} "
          f"{avg([r['byz_score'] for r in rows]):>18.2f} "
          f"{avg([r['jf_final_score'] for r in rows]):>15.2f}")
    print(f"{'Number Score avg (0-4)':<30} "
          f"{avg([r['byz_num'] for r in rows]):>18.2f} "
          f"{avg([r['jf_num'] for r in rows]):>15.2f}")
    print(f"{'LLM Score avg (0-4)':<30} "
          f"{avg([r['byz_llm'] for r in rows]):>18.2f} "
          f"{avg([r['jf_llm'] for r in rows]):>15.2f}")
    print(f"{'─'*30} {'─'*18} {'─'*15}")
    print(f"{'Pass Rate STRICT (≥6/8)':<30} {byz_strict_rate:>18.1%} {jf_strict_rate:>15.1%}")
    print(f"{'Pass Rate LLM-only (≥3/4)':<30} {byz_llm_rate:>18.1%} {jf_llm_rate:>15.1%}")
    print(f"{'─'*30} {'─'*18} {'─'*15}")
    print(f"{'ROUGE-L avg':<30} "
          f"{avg([r['byz_rouge_l'] for r in rows]):>18.4f} "
          f"{avg([r['jf_rouge_l'] for r in rows]):>15.4f}")
    print(f"{'BLEU avg':<30} "
          f"{avg([r['byz_bleu'] for r in rows]):>18.4f} "
          f"{avg([r['jf_bleu'] for r in rows]):>15.4f}")
    if any(r["byz_bert"] > 0 for r in rows):
        print(f"{'BERTScore avg':<30} "
              f"{avg([r['byz_bert'] for r in rows]):>18.4f} "
              f"{avg([r['jf_bert'] for r in rows]):>15.4f}")
    print(f"{'Retries triggered':<30} {'N/A':>18} {retried_count:>14}x")
    print(f"{'='*70}")

    # ── Per-case ──────────────────────────────────────────────────────────────
    print(f"\n📊 Per-case (score = num+llm / llm-only):")
    print(f"{'ID':<6} {'Byz score':>10} {'Byz LLM':>8} {'Byz LLM✓':>9} │ "
          f"{'Jdg score':>10} {'Jdg LLM':>8} {'Jdg LLM✓':>9} {'Retry':>6}")
    print(f"{'─'*6} {'─'*10} {'─'*8} {'─'*9} {'─':>2} "
          f"{'─'*10} {'─'*8} {'─'*9} {'─'*6}")
    for r in rows:
        print(
            f"{r['id']:<6} "
            f"{r['byz_score']:>8}/8  "
            f"{r['byz_llm']:>6}/4  "
            f"{'✅' if r['byz_llm_pass'] else '❌':>8}   │ "
            f"{r['jf_final_score']:>8}/8  "
            f"{r['jf_llm']:>6}/4  "
            f"{'✅' if r['jf_llm_pass'] else '❌':>8}  "
            f"{'✅' if r['retried'] else '-':>5}"
        )

    # ── Issues breakdown ──────────────────────────────────────────────────────
    print(f"\n🔍 Issues ที่ judge พบ (Byzantine):")
    for r in rows:
        if r["byz_issues"]:
            print(f"   {r['id']}: {', '.join(r['byz_issues'][:3])}")
        else:
            print(f"   {r['id']}: ไม่มี issues")

    print(f"\n🔍 Issues ที่ judge พบ (Judge-flow final):")
    for r in rows:
        if r["jf_issues"]:
            print(f"   {r['id']}: {', '.join(r['jf_issues'][:3])}")
        else:
            print(f"   {r['id']}: ไม่มี issues")

    # ── Interpretation ────────────────────────────────────────────────────────
    print(f"\n💡 Interpretation:")
    if jf_llm_rate > byz_llm_rate:
        print(f"   ✅ LLM-only pass rate: Judge {jf_llm_rate:.0%} > Byzantine {byz_llm_rate:.0%} "
              f"(+{jf_llm_rate - byz_llm_rate:.0%})")
    elif jf_llm_rate == byz_llm_rate:
        print(f"   ➡️  LLM-only pass rate เท่ากัน ({jf_llm_rate:.0%}) "
              f"— Judge ยังมีประโยชน์ตรง retry mechanism")
    score_diff = avg([r['jf_llm'] for r in rows]) - avg([r['byz_llm'] for r in rows])
    if score_diff > 0:
        print(f"   📈 LLM score เฉลี่ยดีขึ้น +{score_diff:.2f}/4 เมื่อใช้ Judge")
    if retried_count > 0:
        print(f"   🔄 Judge retry {retried_count} ครั้ง — Byzantine ไม่มีกลไกนี้")
    print(f"   📌 Number check คือสาเหตุหลักที่ทำให้ strict pass rate ต่ำ "
          f"(num avg Byzantine={avg([r['byz_num'] for r in rows]):.2f}/4, "
          f"Judge={avg([r['jf_num'] for r in rows]):.2f}/4)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        print(f"📂 โหลดไฟล์: {path.name}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data, _ = load_latest_result()

    reanalyze(data)
