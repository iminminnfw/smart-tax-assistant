"""
NitiBench-inspired Evaluation for Thai Tax Law Domain
=====================================================
ประเมินคุณภาพคำตอบของ LLM ด้วยมาตรวัด 3 มิติ ได้แรงบันดาลใจจาก NitiBench
**ใช้ควบคู่กับ ROUGE / BLEU / BERTScore เดิม — ไม่ได้แทนที่**

Implementation: Rule-based heuristic evaluation (deterministic, reproducible)

มิติที่เพิ่มเข้ามา (ที่ ROUGE/BLEU/BERTScore วัดไม่ได้):
1. Coverage Score (0-100 continuous) — ครอบคลุมสาระสำคัญ (keyword/substring matching)
2. Consistency Score (0/1)           — ตรวจจับ Hallucination (regex pattern matching)
3. Citation F1 (0-1)                 — ตรวจการอ้างอิงมาตรากฎหมาย (precision/recall)

ref: NitiBench (arxiv.org/abs/2502.10868) — inspired, not a direct implementation

วิธีรัน:
  cd tax-advisor-backend
  python -m evaluation.nitibench_eval
"""

import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# Thai Tax Law Citation Patterns
# ─────────────────────────────────────────────────────────────────────────────

# Regex สำหรับจับมาตราอ้างอิงในข้อความภาษาไทย
CITATION_PATTERNS = [
    r"มาตรา\s*\d+(?:\s*\(\s*\d+\s*\))?(?:\s*(?:ทวิ|ตรี|จัตวา))?",  # มาตรา 40(6), มาตรา 40 (6)
    r"ม\.\s*\d+(?:\s*\(\s*\d+\s*\))?",                              # ม.40(6), ม. 40(6)
    r"พ\.?ร\.?ฎ\.?\s*(?:\(?ฉบับที่\s*)?\d+\)?",                     # พ.ร.ฎ. 629
    r"พระราชกฤษฎีกา\s*(?:\(?ฉบับที่\s*)?\d+\)?",                    # พระราชกฤษฎีกา (ฉบับที่ 629)
    r"พระราชกฤษฎีกา\s*ฉบับที่\s*\d+",                               # พระราชกฤษฎีกา ฉบับที่ 629
]

# Hallucination patterns — ข้อมูลเก่าที่ AI มักนำมาตอบผิด
KNOWN_HALLUCINATIONS = [
    # อัตราหักเหมา 40(8) เก่า (ก่อน พ.ร.ฎ. 629)
    {"pattern": r"(?:หักเหมา|หักค่าใช้จ่าย).*?(?:65|70|75|80|85)\s*(?:%|เปอร์เซ็นต์|ร้อยละ)",
     "reason": "อ้างอัตราหักเหมาเก่าก่อน พ.ร.ฎ. 629 (ปัจจุบันสูงสุด 60%)"},
    # SSF ยังลดหย่อนได้
    {"pattern": r"(?:SSF|กองทุนรวมเพื่อการออม).*?(?:ลดหย่อน|สิทธิ)",
     "reason": "SSF ไม่สามารถใช้สิทธิลดหย่อนภาษีใหม่ได้ตั้งแต่ 31 ธ.ค. 2567"},
    # RMF เกิน 500,000
    {"pattern": r"RMF.*?(?:สูงสุด|ไม่เกิน|เพดาน).*?(?:600|700|800|900|1,?000,?000)\s*บาท",
     "reason": "RMF เพดานสูงสุด 500,000 บาท (30% ของรายได้)"},
    # ThaiESG เกิน 300,000
    {"pattern": r"(?:ThaiESG|TESG).*?(?:สูงสุด|ไม่เกิน|เพดาน).*?(?:400|500)\s*(?:,?000)\s*บาท",
     "reason": "ThaiESG เพดานสูงสุด 300,000 บาท (30% ของรายได้)"},
    # บริจาคการศึกษา 2 เท่า (สิ้นสุดแล้ว 31 ธ.ค. 2567)
    {"pattern": r"(?:บริจาค|การศึกษา|กีฬา).*?(?:2\s*เท่า|สองเท่า|หักได้\s*2)",
     "reason": "สิทธิลดหย่อนบริจาคการศึกษา/กีฬา 2 เท่า สิ้นสุดแล้ว 31 ธ.ค. 2567 ปี 2568 นับ 1 เท่า"},
]


def extract_citations(text: str) -> Set[str]:
    """ดึงมาตราอ้างอิงทั้งหมดจากข้อความ"""
    citations = set()
    for pattern in CITATION_PATTERNS:
        for match in re.finditer(pattern, text):
            citations.add(match.group(0).strip())
    return citations


def normalize_citation(cite: str) -> str:
    """ทำให้รูปแบบมาตราเป็นมาตรฐานเดียวกัน

    เช่น:
      "พระราชกฤษฎีกา ฉบับที่ 629" -> "พ.ร.ฎ. 629"
      "พ.ร.ฎ.(ฉบับที่ 629)"       -> "พ.ร.ฎ. 629"
      "มาตรา  40(6)"              -> "มาตรา 40(6)"
      "ม.40(6)"                   -> "มาตรา 40(6)"
      "มาตรา 40 (6)"              -> "มาตรา 40(6)"
    """
    cite = re.sub(r"\s+", " ", cite.strip())
    # Normalize พระราชกฤษฎีกา variants -> พ.ร.ฎ. {num}
    m = re.search(r"(?:พระราชกฤษฎีกา|พ\.?ร\.?ฎ\.?)\s*(?:\(?ฉบับที่\s*)?(\d+)\)?", cite)
    if m:
        return f"พ.ร.ฎ. {m.group(1)}"
    # Normalize ม.40(6) -> มาตรา 40(6)
    m = re.search(r"ม\.\s*(\d+)\s*\(\s*(\d+)\s*\)", cite)
    if m:
        return f"มาตรา {m.group(1)}({m.group(2)})"
    # Normalize มาตรา 40 (6) -> มาตรา 40(6) (ลบ space ก่อนวงเล็บ)
    m = re.search(r"มาตรา\s*(\d+)\s*\(\s*(\d+)\s*\)", cite)
    if m:
        return f"มาตรา {m.group(1)}({m.group(2)})"
    return cite


# ─────────────────────────────────────────────────────────────────────────────
# Coverage Score (0-100 continuous)
# ─────────────────────────────────────────────────────────────────────────────

def compute_coverage(
    candidate: str,
    key_points: List[str],
) -> Dict[str, Any]:
    """ประเมิน Coverage ว่าคำตอบครอบคลุมสาระสำคัญมากน้อยเพียงใด

    คะแนนเป็น continuous scale 0-100 ตามสัดส่วน key points ที่ครอบคลุม
    เช่น 7/9 key points = 77.8 คะแนน (ปัดเป็นจำนวนเต็ม)

    เกณฑ์ตัดสิน (สำหรับแสดงในรายงาน):
    - >= 80: GOOD
    - >= 60: FAIR
    - <  60: NEEDS IMPROVEMENT
    """
    if not key_points:
        return {"coverage_score": 100, "covered": 0, "total": 0, "details": []}

    candidate_lower = candidate.lower()
    covered_points = []

    for point in key_points:
        point_lower = point.lower()
        is_covered = False

        # ลอง exact substring
        if point_lower in candidate_lower:
            is_covered = True
        else:
            # ลอง keyword overlap (ถ้า >= 60% ของคำใน key_point อยู่ใน candidate)
            try:
                from pythainlp.tokenize import word_tokenize
                point_tokens = set(word_tokenize(point_lower, engine="newmm"))
                point_tokens = {t for t in point_tokens if len(t) > 1}
                if point_tokens:
                    found = sum(1 for t in point_tokens if t in candidate_lower)
                    ratio = found / len(point_tokens)
                    is_covered = ratio >= 0.6
            except ImportError:
                words = [w for w in point.split() if len(w) > 1]
                if words:
                    found = sum(1 for w in words if w.lower() in candidate_lower)
                    is_covered = (found / len(words)) >= 0.6

        covered_points.append({"point": point, "covered": is_covered})

    covered_count = sum(1 for p in covered_points if p["covered"])
    total = len(key_points)
    ratio = covered_count / total

    # Continuous score: สัดส่วน key_points ที่ครอบคลุม × 100
    score = round(ratio * 100)

    return {
        "coverage_score": score,
        "coverage_ratio": round(ratio, 4),
        "covered": covered_count,
        "total": total,
        "details": covered_points,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Consistency Score (0 / 1) — Hallucination Detection
# ─────────────────────────────────────────────────────────────────────────────

def _has_past_context(text: str, match_start: int, window: int = 60) -> bool:
    """ตรวจว่ามีคำบริบทอดีต (เคย, อดีต, เดิม, ก่อนหน้า) อยู่ก่อน match position หรือไม่
    ถ้ามี แสดงว่าเป็นการอ้างอิงเปรียบเทียบ ไม่ใช่ hallucination
    """
    start = max(0, match_start - window)
    context_before = text[start:match_start]
    past_keywords = ["เคย", "อดีต", "เดิม", "ก่อนหน้า", "แต่ก่อน", "เปลี่ยนจาก", "ปรับลดจาก"]
    return any(kw in context_before for kw in past_keywords)


def compute_consistency(
    candidate: str,
) -> Dict[str, Any]:
    """ตรวจจับ Hallucination / ข้อมูลขัดแย้ง

    Returns:
        consistency_score: 1 (สอดคล้องทั้งหมด) หรือ 0 (มีข้อมูลขัดแย้ง)
        contradictions: รายการข้อมูลที่ขัดแย้ง
    """
    contradictions = []

    # 1. ตรวจ Known Hallucination Patterns (พร้อม context check ลด false positive)
    for halluc in KNOWN_HALLUCINATIONS:
        match = re.search(halluc["pattern"], candidate, re.IGNORECASE)
        if match:
            # ตรวจบริบท: ถ้ามีคำแสดงอดีต (เคย, เดิม, ก่อนหน้า) → ไม่ flag
            if _has_past_context(candidate, match.start()):
                continue
            contradictions.append({
                "type": "hallucination",
                "reason": halluc["reason"],
                "matched": match.group(0),
            })

    # 2. ตรวจ SSF reference (ต้องไม่แนะนำ SSF ให้ลดหย่อนภาษี)
    if re.search(r"(?:SSF|กองทุนรวมเพื่อการออม)", candidate):
        if not re.search(r"(?:หมดสิทธิ์|ยกเลิก|สิ้นสุด|ไม่สามารถ).*?SSF", candidate) and \
           not re.search(r"SSF.*?(?:หมดสิทธิ์|ยกเลิก|สิ้นสุด|ไม่สามารถ)", candidate):
            contradictions.append({
                "type": "outdated_info",
                "reason": "แนะนำ SSF ซึ่งไม่สามารถใช้สิทธิลดหย่อนภาษีใหม่ได้ตั้งแต่ 31 ธ.ค. 2567",
            })

    consistency_score = 0 if contradictions else 1

    return {
        "consistency_score": consistency_score,
        "contradictions": contradictions,
        "num_contradictions": len(contradictions),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Citation F1
# ─────────────────────────────────────────────────────────────────────────────

def compute_citation_f1(
    candidate: str,
    reference: str,
    expected_citations: List[str] = None,
) -> Dict[str, Any]:
    """คำนวณ Citation F1 — ตรวจการอ้างอิงมาตรากฎหมาย

    ถ้ามี expected_citations ใช้ตรงนั้น ไม่งั้นดึงจาก reference text
    """
    cand_citations = extract_citations(candidate)
    cand_normalized = {normalize_citation(c) for c in cand_citations}

    if expected_citations:
        ref_normalized = {normalize_citation(c) for c in expected_citations}
    else:
        ref_citations = extract_citations(reference)
        ref_normalized = {normalize_citation(c) for c in ref_citations}

    if not ref_normalized:
        # ไม่มี expected citations → ไม่สามารถวัดได้ → return None (ไม่นับเข้าค่าเฉลี่ย)
        return {
            "citation_f1": None,
            "citation_precision": None,
            "citation_recall": None,
            "candidate_citations": list(cand_normalized),
            "expected_citations": [],
            "matched": [],
            "missing": [],
            "extra": [],
        }

    matched = cand_normalized & ref_normalized
    missing = ref_normalized - cand_normalized
    extra = cand_normalized - ref_normalized

    precision = len(matched) / len(cand_normalized) if cand_normalized else 0.0
    recall = len(matched) / len(ref_normalized) if ref_normalized else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "citation_f1": round(f1, 4),
        "citation_precision": round(precision, 4),
        "citation_recall": round(recall, 4),
        "candidate_citations": sorted(cand_normalized),
        "expected_citations": sorted(ref_normalized),
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra": sorted(extra),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Combined NitiBench Evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_nitibench(
    candidate: str,
    reference: str,
    key_points: List[str] = None,
    expected_citations: List[str] = None,
) -> Dict[str, Any]:
    """รันการประเมินแบบ NitiBench-inspired ครบ 3 มิติ (ใช้ควบคู่กับ ROUGE/BLEU/BERTScore)

    Args:
        candidate: ข้อความที่ AI สร้าง
        reference: ข้อความเฉลยมาตรฐาน
        key_points: ประเด็นสำคัญที่ต้องครอบคลุม
        expected_citations: มาตราที่ต้องอ้างอิง (optional, ดึงจาก reference ถ้าไม่ระบุ)

    Returns:
        dict ที่มี coverage_score, consistency_score, citation_f1 และ joint_score
    """
    if not key_points:
        key_points = []

    coverage = compute_coverage(candidate, key_points)
    consistency = compute_consistency(candidate)
    citation = compute_citation_f1(candidate, reference, expected_citations)

    # Joint Score: ค่าเฉลี่ยถ่วงน้ำหนัก
    # น้ำหนัก: domain-expert heuristic weighting (ไม่ได้มาจาก research)
    # Coverage 40%, Consistency 35%, Citation 25%
    cov_norm = coverage["coverage_score"] / 100.0
    con_norm = consistency["consistency_score"]
    cit_f1 = citation["citation_f1"]

    if cit_f1 is not None:
        # มี citation ให้วัด → ใช้ weight ปกติ
        joint_score = (cov_norm * 0.40) + (con_norm * 0.35) + (cit_f1 * 0.25)
    else:
        # ไม่มี citation ให้วัด → กระจาย weight ใหม่เฉพาะ Coverage + Consistency
        joint_score = (cov_norm * 0.5333) + (con_norm * 0.4667)

    return {
        "coverage": coverage,
        "consistency": consistency,
        "citation": citation,
        "joint_score": round(joint_score, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test Cases พร้อม key_points สำหรับ NitiBench evaluation
# ─────────────────────────────────────────────────────────────────────────────

NITIBENCH_TEST_CASES = [
    {
        "id": "NB1",
        "desc": "แพทย์เปิดคลินิก 40(6) — หักเหมา 60%",
        "key_points": [
            "เงินได้ประเภท 40(6)",
            "วิชาชีพอิสระ",
            "หักค่าใช้จ่ายเหมา 60%",
            "การประกอบโรคศิลปะ",
            "RMF ลดหย่อนภาษี",
        ],
        "expected_citations": ["มาตรา 40(6)"],
        "reference": (
            "แพทย์เปิดคลินิกส่วนตัว จัดเป็นเงินได้ตามมาตรา 40(6) วิชาชีพอิสระ "
            "การประกอบโรคศิลปะ สามารถหักค่าใช้จ่ายเหมาได้ 60% ของรายได้ "
            "ควรลงทุน RMF และ ThaiESG เพื่อลดหย่อนภาษี"
        ),
    },
    {
        "id": "NB2",
        "desc": "ทนายความอิสระ 40(6) — หักเหมา 30%",
        "key_points": [
            "เงินได้ประเภท 40(6)",
            "วิชาชีพอิสระ",
            "หักค่าใช้จ่ายเหมา 30%",
            "วิชากฎหมาย",
        ],
        "expected_citations": ["มาตรา 40(6)"],
        "reference": (
            "ทนายความอิสระ จัดเป็นเงินได้ตามมาตรา 40(6) วิชาชีพอิสระ "
            "วิชากฎหมาย หักค่าใช้จ่ายเหมาได้ 30% ของรายได้ "
            "ต่างจากแพทย์ที่หักได้ 60%"
        ),
    },
    {
        "id": "NB3",
        "desc": "พ่อค้าออนไลน์ 40(8) — หักเหมาสูงสุด 60% (พ.ร.ฎ. 629)",
        "key_points": [
            "เงินได้ประเภท 40(8)",
            "การพาณิชย์",
            "หักค่าใช้จ่ายเหมาสูงสุด 60%",
            "พระราชกฤษฎีกา 629",
            "หักค่าใช้จ่ายตามจริง",
        ],
        "expected_citations": ["มาตรา 40(8)", "พ.ร.ฎ. 629"],
        "reference": (
            "พ่อค้าออนไลน์ จัดเป็นเงินได้ตามมาตรา 40(8) การพาณิชย์ "
            "ตาม พระราชกฤษฎีกา ฉบับที่ 629 พ.ศ. 2560 "
            "สามารถหักค่าใช้จ่ายเหมาได้สูงสุด 60% หรือเลือกหักตามจริง"
        ),
    },
    {
        "id": "NB4",
        "desc": "ธุรกิจรายรับเกิน 1.8 ล้าน — ภาระ VAT",
        "key_points": [
            "รายรับเกิน 1,800,000 บาท",
            "ภาษีมูลค่าเพิ่ม VAT",
            "จดทะเบียน VAT ภายใน 30 วัน",
            "เบี้ยปรับ",
        ],
        "expected_citations": ["มาตรา 40(8)"],
        "reference": (
            "เมื่อรายรับเกิน 1,800,000 บาทต่อปี ผู้ประกอบการมาตรา 40(8) "
            "ต้องจดทะเบียนภาษีมูลค่าเพิ่ม VAT ภายใน 30 วัน "
            "มิฉะนั้นจะเผชิญเบี้ยปรับ 2 เท่าและเงินเพิ่ม 1.5% ต่อเดือน"
        ),
    },
    {
        "id": "NB5",
        "desc": "กำไรเกิน 1 ล้าน — จุดเปลี่ยนเป็นนิติบุคคล",
        "key_points": [
            "กำไรสุทธิเกิน 1,000,000 บาท",
            "อัตราภาษีก้าวหน้า 35%",
            "จดทะเบียนนิติบุคคล",
            "อัตราภาษี SME",
        ],
        "expected_citations": [],
        "reference": (
            "เมื่อกำไรสุทธิทางภาษีเกิน 1,000,000 บาทต่อปี ภาระภาษีบุคคลธรรมดา "
            "อัตราก้าวหน้าสูงสุด 35% จะสูงมาก ควรพิจารณาจดทะเบียนเป็นนิติบุคคล "
            "เพื่อรับอัตราภาษี SME ที่ต่ำกว่า (ยกเว้น 3 แสนแรก, เสีย 15-20%)"
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Runner & Report
# ─────────────────────────────────────────────────────────────────────────────

def run_nitibench_on_texts(
    candidates: List[str],
    test_cases: List[dict] = None,
) -> Dict[str, Any]:
    """รัน NitiBench evaluation บน candidate texts ที่ได้จาก LLM

    Args:
        candidates: list ของข้อความที่ AI สร้าง (เท่ากับจำนวน test cases)
        test_cases: test cases (default: NITIBENCH_TEST_CASES)

    Returns:
        dict ที่มี per-case results และ aggregate scores
    """
    if test_cases is None:
        test_cases = NITIBENCH_TEST_CASES

    assert len(candidates) == len(test_cases), \
        f"จำนวน candidates ({len(candidates)}) != test_cases ({len(test_cases)})"

    results = []
    for cand, tc in zip(candidates, test_cases):
        result = evaluate_nitibench(
            candidate=cand,
            reference=tc["reference"],
            key_points=tc.get("key_points", []),
            expected_citations=tc.get("expected_citations"),
        )
        result["id"] = tc["id"]
        result["desc"] = tc["desc"]
        results.append(result)

    n = len(results)
    avg_coverage = sum(r["coverage"]["coverage_score"] for r in results) / n
    avg_consistency = sum(r["consistency"]["consistency_score"] for r in results) / n
    # Citation F1: ข้าม cases ที่ไม่มี expected citations (citation_f1 = None)
    valid_citation_f1 = [r["citation"]["citation_f1"] for r in results if r["citation"]["citation_f1"] is not None]
    avg_citation_f1 = sum(valid_citation_f1) / len(valid_citation_f1) if valid_citation_f1 else 0.0
    avg_joint = sum(r["joint_score"] for r in results) / n

    return {
        "timestamp": datetime.now().isoformat(),
        "num_cases": n,
        "aggregate": {
            "avg_coverage_score": round(avg_coverage, 2),
            "avg_consistency_score": round(avg_consistency, 4),
            "avg_citation_f1": round(avg_citation_f1, 4),
            "avg_joint_score": round(avg_joint, 4),
        },
        "per_case": results,
    }


def print_nitibench_report(eval_result: Dict[str, Any]):
    """แสดงผลรายงาน NitiBench"""
    agg = eval_result["aggregate"]
    cases = eval_result["per_case"]

    print(f"\n{'='*70}")
    print(f"  NitiBench-style Evaluation Report")
    print(f"  (ใช้ควบคู่กับ ROUGE / BLEU / BERTScore)")
    print(f"  Date: {eval_result['timestamp'][:19]}")
    print(f"  Cases: {eval_result['num_cases']}")
    print(f"{'='*70}")

    print(f"\n{'Metric':<35} {'Score':>15}")
    print(f"{'---'*17}")
    print(f"{'Coverage Score (0-100)':<35} {agg['avg_coverage_score']:>15.1f}")
    print(f"{'Consistency Score (0-1)':<35} {agg['avg_consistency_score']:>15.4f}")
    print(f"{'Citation F1 (0-1)':<35} {agg['avg_citation_f1']:>15.4f}")
    print(f"{'---'*17}")
    print(f"{'Joint Score (weighted avg)':<35} {agg['avg_joint_score']:>15.4f}")
    print(f"{'='*70}")

    print(f"\nPer-case details:")
    print(f"{'ID':<6} {'Coverage':>10} {'Consist':>10} {'Cite F1':>10} {'Joint':>10} {'Contradictions'}")
    print(f"{'---'*20}")
    for c in cases:
        contradictions_str = ""
        if c["consistency"]["contradictions"]:
            reasons = [ct["reason"][:30] for ct in c["consistency"]["contradictions"][:2]]
            contradictions_str = "; ".join(reasons)
        cite_f1 = c['citation']['citation_f1']
        cite_str = f"{cite_f1:>10.4f}" if cite_f1 is not None else f"{'N/A':>10}"
        print(
            f"{c['id']:<6} "
            f"{c['coverage']['coverage_score']:>10} "
            f"{c['consistency']['consistency_score']:>10} "
            f"{cite_str} "
            f"{c['joint_score']:>10.4f} "
            f"{contradictions_str}"
        )

    print(f"\nCitation details:")
    for c in cases:
        cite = c["citation"]
        if cite["expected_citations"]:
            status = "[OK]" if cite["citation_f1"] >= 0.8 else "[WARN]" if cite["citation_f1"] >= 0.5 else "[FAIL]"
            print(f"  {c['id']}: {status} F1={cite['citation_f1']:.2f} "
                  f"matched={cite['matched']} missing={cite['missing']}")


# ─────────────────────────────────────────────────────────────────────────────
# Main — demo mode
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("NitiBench-style Evaluation — Demo Mode")
    print("   (ใช้ reference text เป็น candidate เพื่อทดสอบ framework)")
    print()

    # Demo: ใช้ reference เป็น candidate (ควรได้ 100% ทุกตัว)
    demo_candidates = [tc["reference"] for tc in NITIBENCH_TEST_CASES]
    result = run_nitibench_on_texts(demo_candidates)
    print_nitibench_report(result)

    # Demo 2: ทดสอบ hallucination detection
    print(f"\n\n{'='*70}")
    print("Hallucination Detection Demo")
    print(f"{'='*70}")

    bad_text = (
        "แพทย์สามารถหักค่าใช้จ่ายเหมาได้ 80% ของรายได้ "
        "ควรลงทุน SSF เพื่อลดหย่อนภาษี RMF สูงสุดไม่เกิน 700,000 บาท"
    )
    consistency = compute_consistency(bad_text)
    print(f"\n   Consistency score: {consistency['consistency_score']}")
    print(f"   Contradictions found: {consistency['num_contradictions']}")
    for ct in consistency["contradictions"]:
        print(f"   [FAIL] {ct['type']}: {ct['reason']}")
        if 'matched' in ct:
            print(f"      matched: \"{ct['matched']}\"")
