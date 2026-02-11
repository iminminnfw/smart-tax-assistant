from curl_cffi import requests
import json

def test_final_sec_connection():
    print("🚀 Testing SEC API (v1) with curl_cffi...")
    
    # ✅ URL ที่ถูกต้องตาม Docs (ห้ามเปลี่ยน)
    url = "https://api.sec.or.th/v1/fund/general-info/amcs"
    
    # ⚠️ ใส่ Key ของคุณ (ผมเห็นในภาพคุณมี Key แล้ว)
    api_key = "55cd28016a844bc799d2e7a550e8f85a" 
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key,
    }

    try:
        # กำหนด current_page ตาม Docs
        params = {"current_page": 1}
        
        print(f"   Target: {url}")
        
        # 🔥 ท่าไม้ตาย: impersonate="chrome110" 
        # เพื่อหลอก Server ว่าเราคือ Google Chrome ของจริง ไม่ใช่ Python Script
        response = requests.get(
            url, 
            headers=headers, 
            params=params, 
            impersonate="chrome110",
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! เชื่อมต่อสำเร็จ")
            print(f"   เจอข้อมูลทั้งหมด: {len(data.get('items', []))} รายการ")
            if data.get('items'):
                print(f"   ตัวอย่าง: {data['items'][0]['comp_name_th']}")
        else:
            print("❌ Failed.")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_final_sec_connection()