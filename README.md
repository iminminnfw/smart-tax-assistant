# Smart Tax Assistant — AI Tax Optimizer

ระบบผู้ช่วยวางแผนภาษีอัจฉริยะสำหรับบุคคลธรรมดาในประเทศไทย รองรับเงินได้ประเภท 40(6) และ 40(8) โดยใช้ AI วิเคราะห์และแนะนำแผนลงทุนเพื่อประหยัดภาษีอย่างเหมาะสม

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI (Python), Uvicorn |
| Database | PostgreSQL + Prisma ORM |
| AI | Claude API (Anthropic) + RAG (Qdrant Vector DB) |
| Auth | NextAuth.js v4 + OTP Email Verification |
| Storage | AWS S3 |
| Email | AWS SES |
| Fund Data | SEC Thailand Open API |

## Features

### คำนวณภาษีบุคคลธรรมดา
- รองรับเงินได้ประเภท **40(6)** (วิชาชีพอิสระ) และ **40(8)** (ธุรกิจ/เงินได้อื่นๆ 43 ประเภท)
- คำนวณค่าลดหย่อนครบทุกหมวด: ส่วนตัว, ครอบครัว, ประกัน, กองทุน, เงินบริจาค
- รองรับ AMT มาตรา 48(2) — 0.5% ของเงินได้พึงประเมิน

### กองทุนลดหย่อนภาษีปี 2568
- **RMF** — สูงสุด 30% ของรายได้ หรือ 500,000 บาท
- **ThaiESG** — สูงสุด 30% ของรายได้ หรือ 300,000 บาท
- **ThaiESGX** — เงินใหม่ หรือโอนจาก LTF (30% หรือ 300,000 บาท)
- **ประกันบำนาญ** — สูงสุด 15% ของรายได้ หรือ 200,000 บาท
- **กอช. (NSF)** — สูงสุด 30,000 บาท

### AI Optimizer
- ดึงข้อมูลกองทุนจาก SEC Thailand API แบบ real-time
- วิเคราะห์ผ่าน SmartFundAnalyzer (4 Intelligence Layers: Exposure, Performance, Tax, Compliance)
- Claude API อธิบายแผนที่แนะนำเป็นภาษาไทย
- คำนวณ projection รายได้ 3 ปีข้างหน้า

### จัดการเอกสาร
- อัปโหลดไฟล์ (PDF, รูปภาพ, Excel, เอกสาร) ผ่าน AWS S3
- จัดโฟลเดอร์พร้อม color tag, ค้นหา/กรอง/เรียงลำดับ
- Soft delete + ถังขยะ + restore + ลบถาวร

### ปฏิทินภาษี
- กำหนดส่งแบบ ภ.ง.ด. 94 (กลางปี) และ ภ.ง.ด. 90 (ประจำปี)
- รองรับทั้งยื่นกระดาษและ e-Filing
- นับถอยหลังถึงกำหนด + มาร์กว่ายื่นแล้ว

### Authentication
- สมัครสมาชิกพร้อม OTP ยืนยันอีเมล
- Login พร้อม Optional MFA (OTP ทางอีเมล)
- JWT session ผ่าน NextAuth.js

## Project Structure

```
smart_tax_assistant/
├── src/
│   ├── app/
│   │   ├── (app)/                        # หน้าหลัก (ต้อง login)
│   │   │   ├── WelcomeHome/              # Dashboard สรุปภาษี
│   │   │   ├── financial-info/           # กรอกข้อมูลการเงิน
│   │   │   ├── tax-deduction-calculator/ # คำนวณภาษี + รับแผน AI
│   │   │   ├── ai-optimizer/             # AI วางแผนกองทุน
│   │   │   ├── document/                 # จัดการเอกสาร
│   │   │   ├── trash/                    # ถังขยะ
│   │   │   ├── tax-calendar/             # ปฏิทินภาษี
│   │   │   └── profile-settings/         # ตั้งค่าโปรไฟล์
│   │   ├── api/                          # API Routes (Next.js)
│   │   └── auth/                         # Login / Register
│   ├── components/
│   ├── lib/                              # Prisma, Auth, AWS, Email
│   └── modules/                          # Business logic
├── prisma/                               # Schema + Migrations
└── tax-advisor-backend/                  # FastAPI Backend
    ├── app/
    │   ├── routers/                      # API endpoints
    │   └── services/                     # AI, RAG, SEC, Tax Calculator
    ├── data/tax_knowledge/               # Knowledge base สำหรับ RAG
    └── evaluation/                       # Evaluation scripts
```

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL
- Qdrant (vector database)

### 1. Clone & Install Frontend

```bash
cd smart_tax_assistant
npm install
```

### 2. Setup Environment Variables

สร้างไฟล์ `.env` ใน `smart_tax_assistant/`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/smarttax
NEXTAUTH_SECRET=your_secret
NEXTAUTH_URL=http://localhost:3000

AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=...

ANTHROPIC_API_KEY=...

SEC_API_KEY=...
SEC_FUND_FACTSHEET_PRIMARY_KEY=...
SEC_FUND_DAILY_INFO_PRIMARY_KEY=...

CRON_SECRET=...
```

### 3. Setup Database

```bash
npx prisma migrate dev
npx prisma generate
```

### 4. Run Frontend

```bash
npm run dev
# http://localhost:3000
```

### 5. Install & Run Backend

```bash
cd tax-advisor-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e .

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# http://localhost:8000
```

## API Endpoints (Backend)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check + Qdrant status |
| POST | `/api/calculate-tax` | คำนวณภาษี + แนะนำแผนลงทุน |
| POST | `/api/ai-optimizer/optimize` | AI Optimizer แผนละเอียดรายบุคคล |

## AI Optimizer Flow

```
1. ผู้ใช้กรอกข้อมูลการเงิน (รายได้ อายุ ค่าใช้จ่าย)
        ↓
2. Frontend คำนวณภาษีปัจจุบัน (calcTaxFromFormData)
        ↓
3. ส่ง pre_calculated_tax + ข้อมูลทั้งหมดไป Backend
        ↓
4. Backend คำนวณ allocation RMF/ThaiESG/ThaiESGX ตาม quota cap
        ↓
5. SmartFundAnalyzer ดึงข้อมูลกองทุนจาก SEC Thailand API
        ↓
6. Claude API อธิบายแผนที่แนะนำเป็นภาษาไทย
        ↓
7. แสดงผล: แผนแนะนำ + ประมาณการประหยัดภาษี + projection 3 ปี
```

## Deployment

Production deploy บน AWS EC2 + Nginx + PM2 + Let's Encrypt HTTPS

**Domain**: [https://smarttax.help](https://smarttax.help)
