"""
Script to programmatically inject expected_text into all test cases
This modifies evaluation_test_data.py to add text ground truth for BLEU/ROUGE/BERTScore evaluation
"""

import re

# Template expected text for each plan type based on risk tolerance
PLAN_TEMPLATES = {
    "low": {
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
    "medium": {
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
    "high": {
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

# Test case to risk tolerance mapping
TEST_CASE_RISK_MAP = {
    1: "medium", 2: "high", 3: "low", 4: "medium", 5: "low",
    6: "high", 7: "high", 8: "medium", 9: "high", 10: "low",
    11: "medium", 12: "medium", 13: "medium", 14: "low", 15: "medium",
    16: "high", 17: "medium", 18: "low", 19: "high", 20: "low"
}

def format_expected_text(text_data: dict, indent: int = 16) -> str:
    """Format expected_text dictionary as Python code"""
    base_indent = " " * indent
    inner_indent = " " * (indent + 4)
    list_indent = " " * (indent + 8)

    lines = []
    lines.append(f'{base_indent}"expected_text": {{')
    lines.append(f'{inner_indent}"description": "{text_data["description"]}",')

    # Keywords
    keywords_str = ", ".join([f'"{kw}"' for kw in text_data["keywords"]])
    lines.append(f'{inner_indent}"keywords": [{keywords_str}],')

    # Key points
    lines.append(f'{inner_indent}"key_points": [')
    for i, point in enumerate(text_data["key_points"]):
        comma = "," if i < len(text_data["key_points"]) - 1 else ""
        lines.append(f'{list_indent}"{point}"{comma}')
    lines.append(f'{inner_indent}]')

    lines.append(f'{base_indent}}}')

    return "\n".join(lines)

def inject_expected_text_into_file():
    """Read the test data file and inject expected_text into all test cases"""

    file_path = "/Users/atikun/Desktop/Rag/rag_new/backend/app/services/evaluation_test_data.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match plan entries that need expected_text
    # Match: "plan_X": { "total_investment": ..., "total_tax_saving": ..., }
    # But skip if it already has "expected_text"

    for test_num in range(1, 21):
        if test_num == 1:
            # Test case 1 already has expected_text, skip it
            continue

        risk = TEST_CASE_RISK_MAP[test_num]

        for plan_key in ["plan_1", "plan_2", "plan_3"]:
            template = PLAN_TEMPLATES[risk][plan_key]
            expected_text_str = format_expected_text(template)

            # Find the pattern for this specific test case and plan
            # Pattern: "plan_X": { ... "total_tax_saving": NUMBER, # comment }
            # We want to add expected_text before the closing }

            pattern = rf'("{plan_key}": {{\s*"total_investment": \d+,\s*"total_tax_saving": \d+,\s*#[^\n]*\n)(\s*}})'

            def replacement(match):
                plan_header = match.group(1)
                closing_brace = match.group(2)
                return f'{plan_header}{expected_text_str}\n{closing_brace}'

            # Apply replacement
            content = re.sub(pattern, replacement, content, count=1)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Successfully injected expected_text into all test cases!")
    print(f"Updated file: {file_path}")

if __name__ == "__main__":
    inject_expected_text_into_file()
