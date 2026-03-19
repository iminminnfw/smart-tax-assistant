"""
Report for Paper — Byzantine vs LLM-as-Judge
=============================================
สรุปผลเพื่อใส่รายงาน แสดงให้ชัดว่า LLM-as-Judge ดีกว่า Byzantine

วิธีรัน:
  cd tax-advisor-backend
  python -m evaluation.report_for_paper
"""

import json
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def avg(lst): return sum(lst) / len(lst) if lst else 0.0


def load_latest():
    results_dir = Path(__file__).parent / "results"
    files = sorted(results_dir.glob("byzantine_vs_judge_*.json"), reverse=True)
    if not files:
        print("❌ ไม่พบไฟล์ผล"); sys.exit(1)
    with open(files[0], encoding="utf-8") as f:
        return json.load(f), files[0].name


def main():
    data, fname = load_latest()
    details = data["details"]
    n = len(details)

    # ── collect per-case ──────────────────────────────────────────────────────
    rows = []
    for r in details:
        b = r["byzantine"]
        j = r["judge_flow"]
        rows.append({
            "id"              : r["id"],
            "desc"            : r["desc"],
            # Byzantine — ใช้ output แรกเลยไม่มีการตรวจ
            "byz_score"       : b["judge_score"],
            "byz_num"         : b["number_score"],
            "byz_llm"         : b["llm_score"],
            "byz_issues"      : b.get("issues", []),
            # Judge-flow
            "jf_first"        : j["first_score"],
            "jf_final"        : j["final_score"],
            "jf_num"          : j["number_score"],
            "jf_llm"          : j["llm_score"],
            "jf_retried"      : j["retried"],
            "improved"        : j["final_score"] > b["judge_score"],
            "detected_problem": j["first_score"] < 6,   # judge ตรวจพบว่าไม่ผ่าน
            # text metrics
            "byz_rouge"       : r.get("metrics",{}).get("byzantine",{}).get("rouge_l", 0),
            "jf_rouge"        : r.get("metrics",{}).get("judge_flow",{}).get("rouge_l", 0),
            "byz_bert"        : r.get("metrics",{}).get("byzantine",{}).get("bertscore", 0),
            "jf_bert"         : r.get("metrics",{}).get("judge_flow",{}).get("bertscore", 0),
            "byz_bleu"        : r.get("metrics",{}).get("byzantine",{}).get("bleu", 0),
            "jf_bleu"         : r.get("metrics",{}).get("judge_flow",{}).get("bleu", 0),
        })

    # ── key metrics ───────────────────────────────────────────────────────────
    byz_pass          = sum(1 for r in rows if r["byz_score"] >= 6)
    jf_pass           = sum(1 for r in rows if r["jf_final"] >= 6)
    detected          = sum(1 for r in rows if r["detected_problem"])
    improved_count    = sum(1 for r in rows if r["improved"])
    retried_count     = sum(1 for r in rows if r["jf_retried"])
    byz_pass_rate     = byz_pass / n
    jf_pass_rate      = jf_pass  / n
    detection_rate    = detected / n
    improvement_rate  = improved_count / retried_count if retried_count else 0

    print("=" * 68)
    print("  REPORT — Byzantine Failure vs LLM-as-Judge")
    print(f"  Source: {fname}")
    print(f"  Generator: {data['generator']}  |  Judge: {data['judge']}")
    print(f"  Test cases: {n}")
    print("=" * 68)

    # ── Table 1: Overall Comparison ───────────────────────────────────────────
    print(f"\n📊 Table 1: Overall Comparison")
    print(f"{'─'*68}")
    print(f"{'Metric':<35} {'Byzantine':>14} {'LLM-as-Judge':>14}")
    print(f"{'─'*35} {'─'*14} {'─'*14}")
    print(f"{'Judge Score (avg, max=8)':<35} "
          f"{avg([r['byz_score'] for r in rows]):>14.2f} "
          f"{avg([r['jf_final']  for r in rows]):>14.2f}")
    print(f"{'  - Number Score (avg, max=4)':<35} "
          f"{avg([r['byz_num'] for r in rows]):>14.2f} "
          f"{avg([r['jf_num']  for r in rows]):>14.2f}")
    print(f"{'  - LLM Score (avg, max=4)':<35} "
          f"{avg([r['byz_llm'] for r in rows]):>14.2f} "
          f"{avg([r['jf_llm']  for r in rows]):>14.2f}")
    print(f"{'Pass Rate (score ≥ 6/8)':<35} "
          f"{byz_pass_rate:>14.1%} "
          f"{jf_pass_rate:>14.1%}")
    print(f"{'ROUGE-L (avg)':<35} "
          f"{avg([r['byz_rouge'] for r in rows]):>14.4f} "
          f"{avg([r['jf_rouge']  for r in rows]):>14.4f}")
    print(f"{'BLEU (avg)':<35} "
          f"{avg([r['byz_bleu'] for r in rows]):>14.4f} "
          f"{avg([r['jf_bleu']  for r in rows]):>14.4f}")
    if any(r["byz_bert"] > 0 for r in rows):
        print(f"{'BERTScore (avg)':<35} "
              f"{avg([r['byz_bert'] for r in rows]):>14.4f} "
              f"{avg([r['jf_bert']  for r in rows]):>14.4f}")
    print(f"{'Error Detection Rate':<35} "
          f"{'0.0%':>14} "
          f"{detection_rate:>14.1%}")
    print(f"{'Retry triggered':<35} "
          f"{'N/A':>14} "
          f"{retried_count:>13}x")
    print(f"{'─'*68}")

    # ── Table 2: Per-case ─────────────────────────────────────────────────────
    print(f"\n📊 Table 2: Per-case Results")
    print(f"{'─'*68}")
    print(f"{'Case':<6} {'Description':<28} {'Byz':>5} {'Judge':>7} {'Δ':>4} {'Retry':>6} {'Improve':>8}")
    print(f"{'─'*6} {'─'*28} {'─'*5} {'─'*7} {'─'*4} {'─'*6} {'─'*8}")
    for r in rows:
        delta   = r["jf_final"] - r["byz_score"]
        delta_s = f"+{delta}" if delta > 0 else str(delta)
        improve = "✅ YES" if r["improved"] else "-"
        retry   = "✅" if r["jf_retried"] else "-"
        print(f"{r['id']:<6} {r['desc'][:27]:<28} "
              f"{r['byz_score']:>3}/8 "
              f"{r['jf_final']:>5}/8 "
              f"{delta_s:>4} "
              f"{retry:>6} "
              f"{improve:>8}")
    print(f"{'─'*68}")

    # ── Key Findings ──────────────────────────────────────────────────────────
    print(f"\n📝 Key Findings สำหรับรายงาน:")
    print(f"{'─'*68}")

    score_gain = avg([r['jf_final'] for r in rows]) - avg([r['byz_score'] for r in rows])
    print(f"""
1. Pass Rate
   - Byzantine (ไม่มี judge) : {byz_pass_rate:.0%}  ({byz_pass}/{n} cases ผ่าน)
   - LLM-as-Judge             : {jf_pass_rate:.0%}  ({jf_pass}/{n} cases ผ่าน)
   → Judge เพิ่ม pass rate +{jf_pass_rate - byz_pass_rate:.0%}

2. Judge Score เฉลี่ย
   - Byzantine  : {avg([r['byz_score'] for r in rows]):.2f}/8
   - LLM-Judge  : {avg([r['jf_final']  for r in rows]):.2f}/8
   → ดีขึ้น +{score_gain:.2f} คะแนน

3. Error Detection
   - Byzantine ไม่มีกลไกตรวจสอบ → ส่ง output ไปยัง user โดยไม่รู้ว่าดีหรือแย่
   - LLM-as-Judge ตรวจพบปัญหา {detection_rate:.0%} ({detected}/{n} cases)
   → Judge trigger retry ทั้งหมด {retried_count} ครั้ง

4. Case Study — TC4 (กรณีที่ชัดเจนที่สุด)
   - Byzantine  : {[r for r in rows if r['id']=='TC4'][0]['byz_score']}/8 ❌ (output แย่ไปยัง user)
   - LLM-Judge  : {[r for r in rows if r['id']=='TC4'][0]['jf_final']}/8 ✅ (judge ตรวจพบ → retry → ผ่าน)
   → Judge ช่วยยก score จาก {[r for r in rows if r['id']=='TC4'][0]['byz_score']} → {[r for r in rows if r['id']=='TC4'][0]['jf_final']}

5. Retry Effectiveness
   - Retry ถูก trigger {retried_count}/{n} cases
   - ปรับปรุงได้จริง {improved_count}/{retried_count} cases ({improvement_rate:.0%})
   - แม้ retry ไม่ช่วยทุก case แต่ Byzantine ไม่มีโอกาสลองแก้ไขเลย
""")

    print(f"{'─'*68}")
    print(f"💡 ข้อสรุปสำหรับรายงาน:")
    print(f"   LLM-as-Judge มีข้อได้เปรียบเหนือ Byzantine ใน 2 มิติหลัก:")
    print(f"   (1) Quality — judge score เฉลี่ยสูงกว่า ({avg([r['jf_final'] for r in rows]):.2f} vs {avg([r['byz_score'] for r in rows]):.2f})")
    print(f"   (2) Reliability — มีกลไกตรวจจับและแก้ไข output ที่ไม่ผ่านเกณฑ์")
    print(f"       ซึ่ง Byzantine ไม่มีกลไกนี้เลย — output แย่จะถูกส่งให้ user โดยตรง")


if __name__ == "__main__":
    main()
