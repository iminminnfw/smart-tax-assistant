"""
Dynamic Few-Shot Example Pool
เลือก few-shot example ที่ใกล้เคียง test case มากที่สุด
ตาม income tier + risk level

ใช้ COMPLETE JSON example เพื่อบังคับให้ LLM ใช้ category ที่ถูกต้อง
(smaller models like qwen2.5:14b need to SEE the format, not just read instructions)

หลักการสำคัญ:
- Conservative ต้องเน้น "ความคุ้มครอง" + "ประกัน" เสมอ ไม่ว่า risk จะเป็นอะไร
- Balanced ต้องเน้น "กระจายความเสี่ยง" + "สมดุล" เสมอ
- Growth ต้องเน้น "ลดหย่อนภาษีสูงสุด" + "วงเงิน" เสมอ
"""

import json
from typing import Dict, Any


class FewShotPool:
    """Dynamic few-shot example selection based on user profile similarity

    Returns COMPLETE JSON examples so the model copies the correct format and categories.
    """

    # Complete JSON examples organized by (income_tier, risk_level)
    EXAMPLES = {
        # =====================================================================
        # Low income (< 600K)
        # =====================================================================
        ("low", "low"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองชีวิตและสุขภาพเป็นหลัก เหมาะสำหรับผู้มีรายได้ไม่สูงที่ต้องการประกันพื้นฐานพร้อมลดหย่อนภาษี พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 50, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษีได้"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 20, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด 25,000"]},
                        {"category": "ประกันบำนาญ", "percentage": 30, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงระหว่างประกันและกองทุน RMF สมดุลระหว่างความคุ้มครองและการออมระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 30, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 40, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง", "ออมเพื่อเกษียณ"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ประกันบำนาญ", "percentage": 20, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีเต็มวงเงิน ใช้ RMF ร่วมกับประกันครบด้านเพื่อประหยัดภาษีสูงสุด พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 20, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 5, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 50, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "low",
                         "pros": ["ลดหย่อนเพิ่มจาก RMF"], "cons": ["ต้องถือ 8 ปี"]},
                    ]
                },
            ]
        },
        ("low", "medium"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองด้วยประกันชีวิตและสุขภาพ เงินลงทุนพอเหมาะสำหรับรายได้ระดับต้น พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 45, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 20, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "ประกันบำนาญ", "percentage": 35, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงระหว่างประกันและกองทุน RMF สมดุลระหว่างความคุ้มครองและการเติบโต พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 25, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 45, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโต"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ประกันบำนาญ", "percentage": 20, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุด ผสม RMF กับ ThaiESG ใช้วงเงินเต็มที่เพื่อผลตอบแทนระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 15, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 50, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง", "ผลตอบแทนดีระยะยาว"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 35, "risk_level": "medium",
                         "pros": ["ลดหย่อนเพิ่มจาก RMF", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                    ]
                },
            ]
        },
        ("low", "high"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองพื้นฐานด้วยประกันชีวิตและสุขภาพ สร้างฐานความมั่นคงแม้รายได้ไม่สูง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 45, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 20, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "ประกันบำนาญ", "percentage": 35, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงระหว่างประกันและกองทุนหุ้น RMF สมดุลระหว่างความคุ้มครองและการเติบโต พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 20, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 50, "risk_level": "high",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโตสูง"], "cons": ["ความผันผวนสูง"]},
                        {"category": "ประกันบำนาญ", "percentage": 20, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุดด้วย RMF และ ThaiESG ใช้วงเงินเต็มที่เพื่อผลตอบแทนสูง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 15, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 45, "risk_level": "high",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโตสูง"], "cons": ["ความผันผวนสูง"]},
                        {"category": "ThaiESG", "percentage": 40, "risk_level": "high",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                    ]
                },
            ]
        },
        # =====================================================================
        # Medium income (600K - 1.5M)
        # =====================================================================
        ("medium", "low"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองครอบคลุมด้วยประกันชีวิตและสุขภาพ เหมาะกับรายได้ระดับกลางที่ต้องการความปลอดภัย พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 35, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 15, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด 25,000"]},
                        {"category": "ประกันบำนาญ", "percentage": 50, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ", "ลดหย่อนภาษี"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงเน้นประกันและกองทุนบำนาญ สมดุลระหว่างความคุ้มครองและการออมระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 20, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 40, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง", "ออมเพื่อเกษียณ"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ประกันบำนาญ", "percentage": 30, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีเต็มวงเงินแบบปลอดภัย ใช้ RMF ร่วมกับประกันบำนาญเพื่อประหยัดภาษีสูงสุด พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 15, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 45, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "low",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ประกันบำนาญ", "percentage": 15, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
            ]
        },
        ("medium", "medium"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองด้วยประกันชีวิตและสุขภาพ เงินลงทุนพอเหมาะสำหรับรายได้ระดับกลาง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 35, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 15, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "ประกันบำนาญ", "percentage": 50, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ", "ลดหย่อนภาษี"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงอย่างสมดุลระหว่างประกันและกองทุน RMF เพื่อความคุ้มครองและการเติบโตควบคู่กัน พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 20, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 45, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโต"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ประกันบำนาญ", "percentage": 25, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุด ใช้วงเงินลงทุนเต็มที่ใน RMF และ ThaiESG เพื่อผลตอบแทนระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 10, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 45, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง", "ผลตอบแทนดีระยะยาว"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 30, "risk_level": "medium",
                         "pros": ["ลดหย่อนเพิ่มจาก RMF", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ประกันบำนาญ", "percentage": 15, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
            ]
        },
        ("medium", "high"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองพื้นฐานด้วยประกันชีวิตและสุขภาพ สร้างฐานความมั่นคงสำหรับรายได้ระดับกลาง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 40, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 15, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "ประกันบำนาญ", "percentage": 45, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงระหว่างประกันและกองทุน RMF สมดุลระหว่างความคุ้มครองและผลตอบแทนระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 20, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 45, "risk_level": "high",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโตสูง"], "cons": ["ความผันผวนสูง"]},
                        {"category": "ประกันบำนาญ", "percentage": 25, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุดด้วย RMF และ ThaiESG ใช้วงเงินเต็มที่เพื่อผลตอบแทนระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 10, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 40, "risk_level": "high",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโตสูง"], "cons": ["ความผันผวนสูง"]},
                        {"category": "ThaiESG", "percentage": 35, "risk_level": "high",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ประกันบำนาญ", "percentage": 15, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
            ]
        },
        # =====================================================================
        # High income (>= 1.5M)
        # =====================================================================
        ("high", "low"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองครบถ้วนด้วยประกันชีวิตและสุขภาพเต็มวงเงิน เหมาะกับรายได้สูงที่เน้นความปลอดภัย พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 30, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด 25,000"]},
                        {"category": "ประกันบำนาญ", "percentage": 30, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ", "ลดหย่อนภาษี"], "cons": ["ผูกพันระยะยาว"]},
                        {"category": "RMF", "percentage": 30, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง", "ออมเพื่อเกษียณ"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงระหว่างประกันครบด้านและกองทุน RMF สมดุลเน้นความมั่นคงระยะยาวสำหรับรายได้สูง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 15, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 5, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 40, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "low",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ประกันบำนาญ", "percentage": 15, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุดแบบปลอดภัย ใช้วงเงินเต็มทั้ง RMF ThaiESG และประกันบำนาญ พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 10, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 35, "risk_level": "low",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "low",
                         "pros": ["ลดหย่อนเพิ่ม"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ThaiESGX", "percentage": 15, "risk_level": "low",
                         "pros": ["ลดหย่อนเพิ่มจาก ThaiESG"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "เงินบริจาคการศึกษา", "percentage": 15, "risk_level": "low",
                         "pros": ["ลดหย่อนได้ทันที"], "cons": ["ไม่ได้ผลตอบแทนกลับ"]},
                    ]
                },
            ]
        },
        ("high", "medium"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองด้วยประกันชีวิตและสุขภาพ เสริมด้วยประกันบำนาญสำหรับรายได้สูง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 30, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "ประกันบำนาญ", "percentage": 35, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                        {"category": "RMF", "percentage": 25, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงอย่างสมดุลระหว่างประกันและ RMF/ThaiESG สำหรับรายได้สูงที่ต้องการผลตอบแทนปานกลาง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 15, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 5, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 40, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโต"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "medium",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ประกันบำนาญ", "percentage": 15, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุด ใช้วงเงิน RMF ThaiESG และเงินบริจาคการศึกษาเต็มที่ พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 10, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 35, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "medium",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ThaiESGX", "percentage": 15, "risk_level": "medium",
                         "pros": ["ลดหย่อนเพิ่มจาก ThaiESG"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "เงินบริจาคการศึกษา", "percentage": 15, "risk_level": "low",
                         "pros": ["ลดหย่อนได้ทันที"], "cons": ["ไม่ได้ผลตอบแทนกลับ"]},
                    ]
                },
            ]
        },
        ("high", "high"): {
            "plans": [
                {
                    "plan_type": "conservative",
                    "description": "เน้นความคุ้มครองพื้นฐานด้วยประกันชีวิตและสุขภาพ สร้างฐานความมั่นคงสำหรับรายได้สูง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 30, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต", "ลดหย่อนภาษี"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 10, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "ประกันบำนาญ", "percentage": 30, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                        {"category": "RMF", "percentage": 30, "risk_level": "medium",
                         "pros": ["ลดหย่อนภาษีได้สูง"], "cons": ["ถอนได้เมื่ออายุ 55"]},
                    ]
                },
                {
                    "plan_type": "balanced",
                    "description": "กระจายความเสี่ยงระหว่างประกันและกองทุน RMF/ThaiESG สมดุลระหว่างความคุ้มครองและผลตอบแทนสูง พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 15, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "ประกันสุขภาพ", "percentage": 5, "risk_level": "low",
                         "pros": ["คุ้มครองค่ารักษาพยาบาล"], "cons": ["วงเงินจำกัด"]},
                        {"category": "RMF", "percentage": 40, "risk_level": "high",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโตสูง"], "cons": ["ความผันผวนสูง"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "high",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ประกันบำนาญ", "percentage": 15, "risk_level": "low",
                         "pros": ["รับเงินบำนาญหลังเกษียณ"], "cons": ["ผูกพันระยะยาว"]},
                    ]
                },
                {
                    "plan_type": "growth",
                    "description": "เน้นลดหย่อนภาษีสูงสุดด้วย RMF และ ThaiESG ใช้วงเงินเต็มที่ลงทุนเพื่อผลตอบแทนระยะยาว พร้อมอ้างอิงสิทธิลดหย่อนตามมาตรา [ระบุเลขมาตรา] และ พ.ร.ฎ. [ระบุเลขพ.ร.ฎ.]",
                    "allocations": [
                        {"category": "ประกันชีวิต", "percentage": 8, "risk_level": "low",
                         "pros": ["ให้ความคุ้มครองชีวิต"], "cons": ["ผลตอบแทนต่ำ"]},
                        {"category": "RMF", "percentage": 35, "risk_level": "high",
                         "pros": ["ลดหย่อนภาษีได้สูง", "โอกาสเติบโตสูง"], "cons": ["ความผันผวนสูง"]},
                        {"category": "ThaiESG", "percentage": 25, "risk_level": "high",
                         "pros": ["ลดหย่อนเพิ่ม", "ลงทุนยั่งยืน"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "ThaiESGX", "percentage": 17, "risk_level": "high",
                         "pros": ["ลดหย่อนเพิ่มจาก ThaiESG"], "cons": ["ต้องถือ 8 ปี"]},
                        {"category": "เงินบริจาคการศึกษา", "percentage": 15, "risk_level": "low",
                         "pros": ["ลดหย่อนได้ทันที"], "cons": ["ไม่ได้ผลตอบแทนกลับ"]},
                    ]
                },
            ]
        },
    }

    @staticmethod
    def _get_income_tier(gross_income: float) -> str:
        """Classify income into tiers"""
        if gross_income < 600000:
            return "low"
        elif gross_income < 1500000:
            return "medium"
        else:
            return "high"

    @staticmethod
    def _normalize_risk(risk_tolerance: str) -> str:
        """Normalize risk tolerance to low/medium/high"""
        risk_map = {
            "low": "low", "conservative": "low",
            "medium": "medium", "moderate": "medium",
            "high": "high", "aggressive": "high",
        }
        return risk_map.get(risk_tolerance, "medium")

    def select_best_example(self, gross_income: float, risk_tolerance: str) -> Dict[str, Any]:
        """Select the closest few-shot example based on income tier and risk profile"""
        tier = self._get_income_tier(gross_income)
        risk = self._normalize_risk(risk_tolerance)

        key = (tier, risk)
        example = self.EXAMPLES.get(key)

        if not example:
            example = self.EXAMPLES[("medium", "medium")]

        return example

    def get_few_shot_prompt_section(self, gross_income: float, risk_tolerance: str) -> str:
        """Generate a complete JSON few-shot example section"""
        example = self.select_best_example(gross_income, risk_tolerance)

        # Format as JSON string
        example_json = json.dumps(example, indent=2, ensure_ascii=False)

        section = """
══════════════════════════════════════════════════════════
EXAMPLE OUTPUT (ตัวอย่าง — ให้เรียบเรียง description ใหม่ตามสถานการณ์จริงของลูกค้า แต่ต้องใช้ category เหมือนตัวอย่างนี้):
══════════════════════════════════════════════════════════
"""
        section += example_json

        return section
