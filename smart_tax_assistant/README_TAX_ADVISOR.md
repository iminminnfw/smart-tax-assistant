# SmartTax Assistant - คู่มือการใช้งานระบบคำนวณภาษี

## ภาพรวมระบบ

โปรเจกต์นี้รวมระบบคำนวณภาษีและแนะนำการลงทุนด้วย AI เข้ากับระบบหลัก SmartTax Assistant

### เทคโนโลยีที่ใช้

**Frontend:**
- Next.js 15.3.1
- TypeScript
- Tailwind CSS
- Recharts (สำหรับกราฟ)

**Backend:**
- FastAPI (Python)
- OpenAI GPT-4o
- Qdrant Vector Database
- LangChain

## การติดตั้งและรันระบบ

### ขั้นตอนที่ 1: ติดตั้ง Dependencies

```bash
# ติดตั้ง Frontend dependencies
npm install

# ติดตั้ง Backend dependencies
cd tax-advisor-backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

### ขั้นตอนที่ 2: ตั้งค่า Backend

1. **สร้างไฟล์ .env:**
```bash
cd tax-advisor-backend
cp .env.example .env
```

2. **แก้ไขไฟล์ .env:**
```env
OPENAI_API_KEY=your_actual_openai_api_key
OPENAI_MODEL=gpt-4o
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=tax_knowledge
```

3. **เริ่ม Qdrant Database:**
```bash
docker-compose up -d
```

4. **นำเข้าข้อมูลภาษี:**
```bash
# Make sure venv is activated
python scripts/ingest_data.py
```

### ขั้นตอนที่ 3: รันระบบ

**Terminal 1 - Backend:**
```bash
cd tax-advisor-backend

# Activate venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

### ขั้นตอนที่ 4: เข้าใช้งาน

1. เปิดเบราว์เซอร์ที่ http://localhost:3000
2. Login เข้าสู่ระบบ
3. คลิกที่เมนู hamburger (☰) มุมซ้ายบน
4. เลือก **"คำนวณการลดหย่อนภาษี"**

## โครงสร้างโปรเจกต์

```
smart_tax_assistant/
├── src/
│   ├── app/
│   │   └── (app)/
│   │       └── tax-deduction-calculator/
│   │           └── page.tsx              # หน้าคำนวณภาษี
│   ├── components/
│   │   └── TaxAdvisor/
│   │       └── MultiplePlansView.tsx     # แสดงแผนการลงทุน
│   ├── lib/
│   │   └── tax-advisor/
│   │       └── types.ts                  # Type definitions
│   └── config/
│       ├── menuItems.ts                   # เมนูนำทาง
│       └── api.ts                         # API configuration
├── tax-advisor-backend/                   # Backend API
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── services/
│   ├── data/
│   │   └── tax_knowledge/
│   ├── scripts/
│   └── docker-compose.yml
└── package.json
```

## ฟีเจอร์หลัก

### 1. คำนวณภาษี
- รองรับกฎหมายภาษี พ.ศ. 2568
- คำนวณค่าลดหย่อนได้ 29+ ประเภท
- แสดงผลภาษีที่ต้องจ่ายแบบเรียลไทม์

### 2. แนะนำการลงทุน
- AI สร้าง 3 แผนการลงทุน (Conservative, Balanced, Aggressive)
- แสดงการกระจายการลงทุนด้วยกราฟ Pie Chart
- คำนวณประหยัดภาษีที่แม่นยำ 100%

### 3. การเปลี่ยนแปลงสำคัญปี 2568
- ยกเลิก SSF → ใช้ ThaiESG/ThaiESGX
- Easy e-Receipt เพิ่มเป็น 50,000 บาท
- ค่าอุปการะบิดามารดาเพิ่มเป็น 120,000 บาท
- ลงทุนหุ้นจดทะเบียนใหม่ ลดหย่อนได้ 100,000 บาท

## การตั้งค่า API

API endpoint สามารถเปลี่ยนได้ผ่าน environment variable:

**สร้างไฟล์ .env.local:**
```env
NEXT_PUBLIC_TAX_ADVISOR_API_URL=http://localhost:8000
```

หรือแก้ไขใน `src/config/api.ts` โดยตรง

## การแก้ไขปัญหา

### ❌ Error: Failed to fetch
- ตรวจสอบว่า Backend รันอยู่ที่ http://localhost:8000
- ตรวจสอบ CORS settings ใน backend

### ❌ Qdrant Connection Error
- ตรวจสอบว่า Docker รันอยู่
- Run `docker-compose up -d` ใน `tax-advisor-backend/`
- ตรวจสอบที่ http://localhost:6333/dashboard

### ❌ OpenAI API Error
- ตรวจสอบ `OPENAI_API_KEY` ใน `.env`
- ตรวจสอบ API key ที่ https://platform.openai.com/api-keys

### ❌ Recharts Import Error
- ตรวจสอบว่าติดตั้ง recharts แล้ว: `npm list recharts`
- ถ้ายังไม่มี: `npm install recharts`

## Git และ Deployment

### ไฟล์ที่ควร ignore (.gitignore)

```gitignore
# Backend
tax-advisor-backend/venv/
tax-advisor-backend/.env
tax-advisor-backend/__pycache__/
tax-advisor-backend/qdrant_storage/

# Frontend
node_modules/
.next/
.env.local
```

### การ Deploy

1. **Backend**: Deploy ไปยัง service เช่น Railway, Render, หรือ AWS
2. **Frontend**: Deploy ผ่าน Vercel หรือ Netlify
3. **Database**: ใช้ Qdrant Cloud หรือ self-hosted Qdrant

## การพัฒนาต่อ

### เพิ่มค่าลดหย่อนใหม่
1. แก้ไข `tax-advisor-backend/app/models.py`
2. แก้ไข `tax-advisor-backend/app/services/tax_calculator.py`
3. แก้ไข Frontend form ใน `page.tsx`

### เพิ่มความรู้ด้านภาษี
1. เพิ่มไฟล์ `.txt` ใน `tax-advisor-backend/data/tax_knowledge/`
2. รัน `python scripts/ingest_data.py`

## ติดต่อและสนับสนุน

- เจอ Bug หรือต้องการ Feature ใหม่: สร้าง Issue
- ต้องการความช่วยเหลือ: ดูเอกสารใน `tax-advisor-backend/README.md`

---

**สร้างด้วย ❤️ โดยทีม SmartTax Assistant**
