#!/usr/bin/env python3
"""
AI Tax Advisor - Auto Setup Script
สคริปต์สร้างไฟล์โปรเจกต์อัตโนมัติ
"""

import os
import sys

def create_directories():
    """สร้างโฟลเดอร์ทั้งหมด"""
    dirs = [
        'frontend/app/lib',
        'backend/app/services',
        'backend/data/tax_knowledge',
        'backend/scripts',
    ]
    
    print("📁 กำลังสร้างโฟลเดอร์...")
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"   ✓ {d}")

def create_file(path, content):
    """สร้างไฟล์"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"   ✓ {path}")

def setup_project():
    """สร้างไฟล์ทั้งหมด"""
    
    print("\n" + "="*60)
    print("🚀 AI Tax Advisor - Auto Setup")
    print("="*60 + "\n")
    
    # สร้างโฟลเดอร์
    create_directories()
    
    print("\n📝 กำลังสร้างไฟล์...")
    
    # ========================================
    # Docker Compose
    # ========================================
    create_file('docker-compose.yml', '''version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant_tax_advisor
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    restart: unless-stopped
''')
    
    # ========================================
    # Backend Files
    # ========================================
    
    # requirements.txt
    create_file('backend/requirements.txt', '''fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
python-dotenv==1.0.0
langchain==0.1.5
langchain-openai==0.0.5
langchain-community==0.0.16
openai==1.10.0
qdrant-client==1.7.3
tiktoken==0.5.2
httpx==0.26.0
numpy==1.26.3
''')
    
    # .env
    create_file('backend/.env', '''OPENAI_API_KEY=sk-YOUR-API-KEY-HERE
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=tax_knowledge
''')
    
    # Sample data
    create_file('backend/data/tax_knowledge/tax_strategies.txt', '''# กลยุทธ์การลดภาษีเงินได้บุคคลธรรมดา - ประเทศไทย 2025

## กองทุน RMF (Retirement Mutual Fund)

กองทุนรวมเพื่อการเลี้ยงชีพ (RMF) เป็นหนึ่งในเครื่องมือลดหย่อนภาษีที่ได้รับความนิยมสูงสุด

**ข้อกำหนด:**
- ลดหย่อนได้สูงสุด 30% ของรายได้ ไม่เกิน 500,000 บาท
- ต้องถือจนอายุ 55 ปี หรือถือครบ 5 ปี

**ผลตอบแทน:**
- กองทุนหุ้น: 8-12% ต่อปี
- กองทุนผสม: 5-8% ต่อปี
- กองทุนตราสารหนี้: 3-5% ต่อปี

**เหมาะสำหรับ:**
- ผู้มีรายได้สูง
- วัยทำงาน อายุ 30-50 ปี
- มีเป้าหมายออมเพื่อการเกษียณ

## กองทุน SSF (Super Savings Fund)

**ข้อกำหนด:**
- ลดหย่อนได้สูงสุด 30% ของรายได้ ไม่เกิน 200,000 บาท
- ต้องถือครบ 10 ปี

**ผลตอบแทน:** 4-7% ต่อปี

**เหมาะสำหรับ:**
- ผู้ที่ต้องการความยืดหยุ่น
- อายุต่ำกว่า 45 ปี

## ประกันบำนาญ

**ข้อกำหนด:**
- ลดหย่อนได้สูงสุด 15% ของรายได้ ไม่เกิน 200,000 บาท

**ผลตอบแทน:** 3-4% ต่อปี (รับประกัน)

**เหมาะสำหรับ:**
- ผู้ที่ไม่ชอบความเสี่ยง
- ต้องการรายได้หลังเกษียณที่แน่นอน
''')
    
    # ========================================
    # Frontend Files  
    # ========================================
    
    # package.json
    create_file('frontend/package.json', '''{
  "name": "ai-tax-advisor",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "next": "14.2.3",
    "lucide-react": "^0.263.1",
    "recharts": "^2.12.7"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "@types/node": "^20.12.12",
    "@types/react": "^18.3.2",
    "@types/react-dom": "^18.3.0",
    "tailwindcss": "^3.4.3",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19"
  }
}
''')
    
    # next.config.js
    create_file('frontend/next.config.js', '''/** @type {import('next').NextConfig} */
const nextConfig = {}
module.exports = nextConfig
''')
    
    # postcss.config.js
    create_file('frontend/postcss.config.js', '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''')
    
    # tailwind.config.js
    create_file('frontend/tailwind.config.js', '''module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: { extend: {} },
  plugins: [],
}
''')
    
    # tsconfig.json
    create_file('frontend/tsconfig.json', '''{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
''')
    
    # globals.css
    create_file('frontend/app/globals.css', '''@tailwind base;
@tailwind components;
@tailwind utilities;
''')
    
    # ========================================
    # README
    # ========================================
    create_file('README.md', '''# 🚀 AI Tax Advisor

## ขั้นตอนการรัน

### 1. เปิด Qdrant (Database)
```bash
docker-compose up -d
```

เช็คที่: http://localhost:6333/dashboard

### 2. รัน Backend

**Windows:**
```bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt

# ⚠️ แก้ไข .env ใส่ OPENAI_API_KEY ก่อน!

python scripts/ingest_data.py
uvicorn app.main:app --reload
```

**Mac/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ⚠️ แก้ไข .env ใส่ OPENAI_API_KEY ก่อน!

python scripts/ingest_data.py
uvicorn app.main:app --reload
```

เช็คที่: http://localhost:8000/docs

### 3. รัน Frontend (Terminal ใหม่)
```bash
cd frontend
npm install
npm run dev
```

เปิดเบราว์เซอร์: http://localhost:3000

## ⚠️ สิ่งที่ต้องทำเพิ่มเติม

1. **ดาวน์โหลดไฟล์โค้ดจาก Claude Artifacts:**
   - ไฟล์ Backend Python (11 ไฟล์)
   - ไฟล์ Frontend TypeScript (2 ไฟล์หลัก)

2. **แก้ไข backend/.env** ใส่ OpenAI API Key ของคุณ

3. **ดูรายละเอียดไฟล์ที่ต้องเพิ่ม** ใน Artifacts ทางด้านขวา
''')
    
    print("\n" + "="*60)
    print("✅ สร้างไฟล์เสร็จสิ้น!")
    print("="*60)
    print("\n📋 ไฟล์ที่สร้างแล้ว:")
    print("   ✓ docker-compose.yml")
    print("   ✓ backend/requirements.txt")
    print("   ✓ backend/.env")
    print("   ✓ backend/data/tax_knowledge/tax_strategies.txt")
    print("   ✓ frontend/package.json")
    print("   ✓ frontend/tsconfig.json")
    print("   ✓ frontend/tailwind.config.js")
    print("   ✓ frontend/next.config.js")
    print("   ✓ frontend/postcss.config.js")
    print("   ✓ frontend/app/globals.css")
    print("   ✓ README.md")
    
    print("\n⚠️  สิ่งที่ต้องทำต่อ:")
    print("   1. แก้ไข backend/.env ใส่ OPENAI_API_KEY")
    print("   2. ดาวน์โหลดไฟล์โค้ดจาก Artifacts (ข้างขวา)")
    print("   3. ทำตามขั้นตอนใน README.md")
    print()

if __name__ == '__main__':
    try:
        setup_project()
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        sys.exit(1)