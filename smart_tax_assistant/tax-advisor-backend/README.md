# Tax Advisor Backend

ระบบ Backend สำหรับคำนวณภาษีและแนะนำการลงทุนด้วย AI

## Technology Stack

- **FastAPI** - Python REST API framework
- **LangChain** - RAG orchestration
- **OpenAI GPT-4o** - AI recommendation generation
- **Qdrant** - Vector database for tax knowledge
- **Docker Compose** - Qdrant deployment

## Setup Instructions

### 1. Start Qdrant Database

```bash
cd tax-advisor-backend
docker-compose up -d
```

Verify at: http://localhost:6333/dashboard

### 2. Setup Python Environment

**Windows:**
```bash
cd tax-advisor-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
cd tax-advisor-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file (or copy from `.env.example`):
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=tax_knowledge
```

### 4. Ingest Tax Knowledge

```bash
python scripts/ingest_data.py
```

This will load tax knowledge from `data/tax_knowledge/` into Qdrant.

### 5. Run Backend Server

```bash
uvicorn app.main:app --reload
```

API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## API Endpoints

### POST /api/calculate-tax

Calculate tax and get AI investment recommendations.

**Request Body:**
```json
{
  "gross_income": 600000,
  "personal_deduction": 60000,
  "spouse_deduction": 60000,
  "child_deduction": 60000,
  // ... other deductions
  "risk_tolerance": "medium"
}
```

**Response:**
```json
{
  "tax_result": {
    "gross_income": 600000,
    "taxable_income": 450000,
    "tax_amount": 15000,
    "effective_tax_rate": 2.5
  },
  "investment_plans": {
    "plans": [
      {
        "plan_id": "conservative",
        "plan_name": "แผนอนุรักษ์นิยม",
        "total_investment": 40000,
        "total_tax_saving": 6000,
        "allocations": [...]
      }
    ]
  }
}
```

## Directory Structure

```
tax-advisor-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── config.py            # Configuration
│   └── services/
│       ├── tax_calculator.py  # Tax calculation logic
│       ├── ai_service.py      # OpenAI integration
│       └── rag_service.py     # Qdrant RAG service
├── data/
│   └── tax_knowledge/       # Tax knowledge documents
├── scripts/
│   └── ingest_data.py       # Data ingestion script
├── docker-compose.yml       # Qdrant database
└── requirements.txt         # Python dependencies
```

## Troubleshooting

### Qdrant Connection Error
- Make sure Docker is running
- Run `docker-compose up -d`
- Check http://localhost:6333/dashboard

### OpenAI API Error
- Verify `OPENAI_API_KEY` in `.env`
- Check API key validity at https://platform.openai.com/api-keys

### Import Errors
- Activate virtual environment
- Run `pip install -r requirements.txt`
