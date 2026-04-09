# Smart Tax Assistant — AI Tax Optimizer

ระบบผู้ช่วยวางแผนภาษีอัจฉริยะ สำหรับบุคคลธรรมดาในประเทศไทย ที่ใช้ AI วิเคราะห์ข้อมูลการเงินและแนะนำแผนลงทุนเพื่อประหยัดภาษีอย่างเหมาะสม

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI (Python), Uvicorn |
| Database | PostgreSQL + Prisma ORM |
| AI | Claude API (Anthropic) + RAG (Qdrant) |
| Auth | NextAuth.js v4 |
| Storage | AWS S3 |
| Email | AWS SES |
| Fund Data | SEC Thailand Open API |

## Features

- **คำนวณภาษีบุคคลธรรมดา** — รองรับเงินได้ประเภท 40(1)/40(2)/40(3)/40(6)/40(8) และ AMT มาตรา 48(2)
- **AI Optimizer** — แนะนำแผนลงทุน RMF / ThaiESG / TESGX ที่เหมาะกับอายุ ความเสี่ยง และเป้าหมายการเงิน
- **จัดการเอกสาร** — อัปโหลด / จัดโฟลเดอร์ / ถังขยะ ผ่าน AWS S3
- **ปฏิทินภาษี** — แจ้งเตือนกำหนดส่งแบบภาษีผ่านอีเมล
- **RAG Knowledge Base** — ตอบคำถามภาษีจากเอกสารกฎหมายภาษีไทย
- **SEC Fund Data** — ดึงข้อมูลกองทุนจาก SEC Thailand API แบบ real-time

## Project Structure

```
smart_tax_assistant/          # Next.js Frontend
├── src/
│   ├── app/                  # App Router (pages + API routes)
│   │   ├── (app)/            # หน้าหลักหลัง login
│   │   │   ├── ai-optimizer/ # AI วางแผนภาษี
│   │   │   ├── financial-info/
│   │   │   ├── tax-deduction-calculator/
│   │   │   ├── tax-calendar/
│   │   │   └── document/
│   │   ├── api/              # API Routes
│   │   └── auth/             # Login / Register
│   ├── components/
│   ├── lib/                  # Prisma, Auth, AWS, Email
│   └── modules/              # Business logic (auth, docs, rag, users)
├── prisma/                   # Schema + Migrations
└── tax-advisor-backend/      # FastAPI Backend
    ├── app/
    │   ├── routers/          # ai_optimizer endpoint
    │   └── services/         # AI, RAG, SEC API, Tax Calculator
    ├── data/tax_knowledge/   # Knowledge base สำหรับ RAG
    └── evaluation/           # Evaluation scripts
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
```

### 3. Setup Database

```bash
npx prisma migrate dev
npx prisma generate
```

### 4. Run Frontend

```bash
npm run dev
```

Frontend จะรันที่ `http://localhost:3000`

### 5. Install & Run Backend

```bash
cd tax-advisor-backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt   # หรือ pip install -e .

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend จะรันที่ `http://localhost:8000`

## AI Optimizer — วิธีทำงาน

1. ผู้ใช้กรอกข้อมูลการเงิน (รายได้ อายุ ค่าใช้จ่าย)
2. Frontend คำนวณภาษีปัจจุบัน (`calcTaxFromFormData`)
3. ส่งข้อมูลไป Backend พร้อม `pre_calculated_tax`
4. Backend คำนวณ allocation RMF/ThaiESG/TESGX ตาม quota cap ของกฎหมาย
5. Claude API อธิบายแผนที่แนะนำเป็นภาษาไทย
6. แสดงผลบนหน้า AI Optimizer

## API Endpoints (Backend)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check + Qdrant status |
| POST | `/api/calculate-tax` | คำนวณภาษี + แนะนำแผนลงทุน |
| POST | `/api/ai-optimizer/optimize` | AI Optimizer (แผนเดียวละเอียด) |

## Deployment

Production deploy บน AWS EC2 + Nginx + PM2 + Let's Encrypt

**Domain**: [https://smarttax.help](https://smarttax.help)
