import re
from typing import Dict, Any, Optional

class RuleBasedGoalParser:
    """
    สมองสำรอง: ทำงานด้วย Regex ไม่ต้องใช้ GPU/Internet
    ใช้เมื่อ LLM (Qwen/OpenAI) ไม่ตอบสนอง
    """
    
    def parse(self, text: str) -> Dict[str, Any]:
        text = text.lower()
        result = {
            "intent": "balanced",  # Default
            "constraints": {
                "min_liquidity": 0,
                "max_budget": -1
            }
        }

        if any(w in text for w in ['ลดหย่อนภาษี', 'ประหยัดภาษี', 'tax', 'save tax']):
            result["intent"] = "tax_saving"
        elif any(w in text for w in ['เงินสด', 'สภาพคล่อง', 'เงินสำรอง', 'cash', 'liquidity']):
            result["intent"] = "liquidity"
        
        # หาตัวเลขที่มีคำว่า "บาท", "k", "m" หรือตัวเลขเฉยๆ ที่ดูเหมือนจำนวนเงิน
        amounts = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)', text)
        
        if amounts:
            # แปลง string "1,000,000" -> float 1000000.0
            val = float(amounts[0].replace(',', ''))
            
            if "เหลือ" in text or "เก็บ" in text or "สำรอง" in text:
                result["constraints"]["min_liquidity"] = val
            elif "ลงทุน" in text or "มีเงิน" in text:
                 # ถ้าบอกว่า "มีเงิน 5 แสน" อาจหมายถึง budget
                result["constraints"]["max_budget"] = val

        return result

