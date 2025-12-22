"""
Script to add expected text ground truth to all 20 test cases
This enables BLEU, ROUGE-L, and BERTScore evaluation
"""

# Template expected text for each plan type based on risk tolerance and investment amount

PLAN_TEMPLATES = {
    "low_risk": {
        "plan_1": {
            "description": "เน้นความคุ้มครอง เงินลงทุนพอเหมาะสำหรับผู้ที่ต้องการความปลอดภัย",
            "keywords": ["ความคุ้มครอง", "ประกัน", "ความเสี่ยงต่ำ", "เงินลงทุนน้อย"],
            "key_points": [
                "เน้นประกันชีวิตและประกันสุขภาพเป็นหลัก",
                "เหมาะกับผู้ที่ต้องการความคุ้มครองและความมั่นคง",
                "ลดหย่อนภาษีได้ในระดับพื้นฐาน"
            ]
        },
        "plan_2": {
            "description": "กระจายความเสี่ยง เน้นประกันและการออมแบบปลอดภัย",
            "keywords": ["สมดุล", "ประกันบำนาญ", "ความปลอดภัย", "การออม"],
            "key_points": [
                "ผสมผสานระหว่างประกันและการออมระยะยาว",
                "เน้นความมั่นคงและความปลอดภัยของเงินลงทุน",
                "เหมาะกับผู้ที่ไม่ชอบความเสี่ยง"
            ]
        },
        "plan_3": {
            "description": "เน้นลดหย่อนภาษีแบบปลอดภัย เพิ่มความคุ้มครองครบถ้วน",
            "keywords": ["ลดหย่อนภาษี", "ความคุ้มครอง", "ประกันครบถ้วน", "ความมั่นคง"],
            "key_points": [
                "ใช้วงเงินลดหย่อนภาษีเต็มที่แบบปลอดภัย",
                "เพิ่มความคุ้มครองชีวิตและสุขภาพอย่างครบถ้วน",
                "เหมาะกับผู้ที่ต้องการความมั่นคงสูงสุด"
            ]
        }
    },
    "medium_risk": {
        "plan_1": {
            "description": "เน้นความคุ้มครอง เงินลงทุนพอเหมาะสำหรับรายได้ระดับกลาง",
            "keywords": ["ความคุ้มครอง", "ประกัน", "ความเสี่ยงต่ำ", "เงินลงทุนพอเหมาะ"],
            "key_points": [
                "เน้นประกันชีวิตและประกันสุขภาพเป็นหลัก",
                "เหมาะกับผู้ที่ต้องการความคุ้มครอง",
                "ลดหย่อนภาษีได้ในระดับพื้นฐาน"
            ]
        },
        "plan_2": {
            "description": "กระจายความเสี่ยง เน้นการลงทุนแบบสมดุลระหว่างประกันและกองทุน",
            "keywords": ["สมดุล", "กระจายความเสี่ยง", "RMF", "ThaiESG", "ความเสี่ยงปานกลาง"],
            "key_points": [
                "ผสมผสานระหว่างกองทุนรวมและประกัน",
                "เน้น RMF และ ThaiESG สำหรับการลงทุนระยะยาว",
                "ความเสี่ยงปานกลาง เหมาะกับผู้มีรายได้ปานกลาง"
            ]
        },
        "plan_3": {
            "description": "เน้นลดหย่อนภาษีสูงสุด ใช้วงเงินลงทุนเต็มที่สำหรับผลประโยชน์ทางภาษีสูงสุด",
            "keywords": ["ลดหย่อนสูงสุด", "RMF", "ThaiESG", "วงเงินเต็มที่", "ผลประโยชน์ภาษี"],
            "key_points": [
                "ใช้วงเงินลดหย่อนภาษีเต็มที่",
                "เน้น RMF และ ThaiESG สำหรับผลตอบแทนระยะยาว",
                "เหมาะกับผู้ที่ต้องการลดภาษีสูงสุด"
            ]
        }
    },
    "high_risk": {
        "plan_1": {
            "description": "เน้นการลงทุน เพิ่มผลตอบแทนแบบรับความเสี่ยง",
            "keywords": ["ผลตอบแทนสูง", "หุ้น", "กองทุนรวม", "รับความเสี่ยง"],
            "key_points": [
                "เน้นกองทุนรวมหุ้นและ SSF สำหรับผลตอบแทนที่ดี",
                "เหมาะกับผู้ที่ยอมรับความเสี่ยงได้",
                "มีศักยภาพผลตอบแทนสูงในระยะยาว"
            ]
        },
        "plan_2": {
            "description": "เน้นการลงทุนแบบก้าวร้าว กระจายในกองทุนหุ้นและตราสารทุน",
            "keywords": ["ก้าวร้าว", "กองทุนหุ้น", "SSF", "RMF", "ความเสี่ยงสูง"],
            "key_points": [
                "กระจายการลงทุนในกองทุนหุ้นและ RMF",
                "เน้น SSF และ RMF equity fund สำหรับผลตอบแทนสูง",
                "เหมาะกับผู้มีรายได้สูงและรับความเสี่ยงได้"
            ]
        },
        "plan_3": {
            "description": "เน้นผลตอบแทนและลดหย่อนภาษีสูงสุด ลงทุนในตราสารทุนเต็มที่",
            "keywords": ["ผลตอบแทนสูงสุด", "ลดหย่อนสูงสุด", "หุ้น", "SSF", "RMF"],
            "key_points": [
                "ใช้วงเงินลดหย่อนภาษีเต็มที่ด้วยกองทุนหุ้น",
                "เน้น RMF, SSF และ ThaiESGX สำหรับผลตอบแทนสูงสุด",
                "เหมาะกับนักลงทุนที่มีประสบการณ์และรับความเสี่ยงสูงได้"
            ]
        }
    }
}

# Test case to risk tolerance mapping (from test data analysis)
TEST_CASE_RISK_MAP = {
    1: "medium",   # รายได้ 600K - ความเสี่ยงกลาง
    2: "high",     # รายได้ 1.5M - ความเสี่ยงสูง
    3: "low",      # รายได้ 360K - ความเสี่ยงต่ำ
    4: "medium",   # ข้าราชการ 900K - ความเสี่ยงกลาง
    5: "low",      # ครูอาจารย์ 720K - ความเสี่ยงต่ำ
    6: "high",     # ฟรีแลนซ์วิศวกร 1.2M - ความเสี่ยงสูง
    7: "high",     # แพทย์ 3M - ความเสี่ยงสูง
    8: "medium",   # ทนายความ 960K - ความเสี่ยงกลาง
    9: "high",     # สถาปนิก 1.8M - ความเสี่ยงสูง
    10: "low",     # ร้านตัดผม 540K - ความเสี่ยงต่ำ
    11: "medium",  # ร้านขายของ 1M - ความเสี่ยงกลาง
    12: "medium",  # ร้านอาหาร 1.5M - ความเสี่ยงกลาง
    13: "medium",  # นักแสดง 600K - ความเสี่ยงกลาง
    14: "low",     # ช่างภาพ 720K - ความเสี่ยงต่ำ
    15: "medium",  # ร้านเสริมสวย 840K - ความเสี่ยงกลาง
    16: "high",    # โรงซ่อมรถ 2.4M - ความเสี่ยงสูง
    17: "medium",  # ขนส่ง 1.2M - ความเสี่ยงกลาง
    18: "low",     # โรงซักรีด 600K - ความเสี่ยงต่ำ
    19: "high",    # โรงพิมพ์ 1.8M - ความเสี่ยงสูง
    20: "low",     # เกษตรกร 480K - ความเสี่ยงต่ำ
}

def generate_expected_text_for_test_case(test_case_num: int) -> dict:
    """Generate expected text structure for a test case"""
    risk = TEST_CASE_RISK_MAP.get(test_case_num, "medium")
    template = PLAN_TEMPLATES[f"{risk}_risk"]

    result = {}
    for plan_key in ["plan_1", "plan_2", "plan_3"]:
        result[plan_key] = {
            "expected_text": template[plan_key]
        }

    return result

def print_expected_text_additions():
    """Print the expected_text additions for all test cases"""
    print("# Expected Text Ground Truth for All Test Cases")
    print("# Copy and paste these into the evaluation_test_data.py file\n")

    for i in range(1, 21):
        print(f"\n# Test Case {i}: Risk = {TEST_CASE_RISK_MAP[i]}")
        expected = generate_expected_text_for_test_case(i)

        for plan_key in ["plan_1", "plan_2", "plan_3"]:
            text = expected[plan_key]["expected_text"]
            print(f"""
                "{plan_key}": {{
                    "expected_text": {{
                        "description": "{text['description']}",
                        "keywords": {text['keywords']},
                        "key_points": {text['key_points']}
                    }}
                }},""")

if __name__ == "__main__":
    print_expected_text_additions()
