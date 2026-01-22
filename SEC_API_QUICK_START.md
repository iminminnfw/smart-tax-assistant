# SEC API Integration - Quick Start Guide

สำหรับโปรเจค Smart Tax Assistant

---

## 📋 สิ่งที่ได้สร้างไว้แล้ว

### 1. Core Services (Backend)
```
tax-advisor-backend/app/services/
├── sec_rate_limiter.py      # Rate limiting (3,000 req/300s)
├── sec_api_client.py         # HTTP client with retry logic
├── sec_cache.py              # Redis caching layer
└── sec_service.py            # Complete integration
```

### 2. API Endpoints (Example)
```
tax-advisor-backend/app/routers/
└── sec_api_example.py        # FastAPI routes
```

### 3. Documentation
```
/
├── SEC_API_RATE_LIMITING_GUIDE.md    # Full guide
├── SEC_API_QUICK_START.md            # This file
└── requirements-sec-api.txt          # Dependencies
```

---

## 🚀 การติดตั้ง

### Step 1: Install Dependencies

```bash
cd smart_tax_assistant/tax-advisor-backend
pip install -r requirements-sec-api.txt
```

หรือติดตั้งแยก:
```bash
pip install httpx>=0.27.0
pip install redis>=5.0.0
```

### Step 2: Install Redis (Optional แต่แนะนำ)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux/Ubuntu:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**หมายเหตุ:** ถ้าไม่มี Redis โค้ดจะยังทำงานได้ แต่จะไม่มี caching (ทำให้เรียก API บ่อยขึ้น)

---

## 💻 การใช้งาน

### Option 1: ใช้ SECService (แนะนำ)

**ใช้งานง่ายที่สุด พร้อม caching และ rate limiting:**

```python
from app.services.sec_service import SECService

# Initialize service
service = SECService()

# Get NAV (with automatic caching)
nav = await service.get_nav("KFRMF")
print(f"NAV: {nav}")

# Get fund info
info = await service.get_fund_info("KFRMF")
print(f"Fund: {info}")

# Bulk fetch (efficient with cache)
results = await service.bulk_get_nav([
    "KFRMF",
    "SCBRMF",
    "K-GLOBAL"
])
print(f"Summary: {results['summary']}")

# Close when done
await service.close()
```

### Option 2: ใช้ API Client เท่านั้น (ไม่มี cache)

**ถ้าไม่ต้องการ caching:**

```python
from app.services.sec_api_client import SECAPIClient

client = SECAPIClient()

nav = await client.get_nav("KFRMF")
print(f"NAV: {nav}")

await client.close()
```

### Option 3: ใช้ Rate Limiter เท่านั้น

**ถ้าต้องการควบคุมเอง:**

```python
from app.services.sec_rate_limiter import SECRateLimiter
import httpx

limiter = SECRateLimiter()

# Wait for rate limiter before each request
await limiter.acquire()
response = await httpx.get("https://api.sec.or.th/...")
```

---

## 🔌 FastAPI Integration

### Step 1: เพิ่ม Lifespan Management

แก้ไขไฟล์ `main.py`:

```python
from contextlib import asynccontextmanager
from app.services.sec_service import SECService

# Global service
sec_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sec_service

    # Startup
    sec_service = SECService(
        redis_url="redis://localhost:6379",
        enable_cache=True
    )

    yield

    # Shutdown
    await sec_service.close()

# Create app with lifespan
app = FastAPI(lifespan=lifespan)
```

### Step 2: สร้าง API Endpoints

```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/api/sec/nav/{fund_code}")
async def get_nav(fund_code: str):
    """Get NAV with caching"""
    try:
        data = await sec_service.get_nav(fund_code)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/sec/nav/bulk")
async def bulk_get_nav(fund_codes: List[str]):
    """Bulk fetch NAV"""
    try:
        results = await sec_service.bulk_get_nav(fund_codes)
        return {"success": True, **results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add router to app
app.include_router(router)
```

**หรือใช้ example ที่สร้างไว้แล้ว:**

```python
from app.routers import sec_api_example

app.include_router(
    sec_api_example.router,
    prefix="/api/sec",
    tags=["SEC API"]
)
```

---

## 📊 API Endpoints (ถ้าใช้ example router)

### Health Check
```bash
GET /api/sec/health
```

### Get Fund List
```bash
GET /api/sec/funds?force_refresh=false
```

### Get NAV
```bash
GET /api/sec/nav/KFRMF?as_of_date=2025-01-10&force_refresh=false
```

### Bulk Get NAV
```bash
POST /api/sec/nav/bulk
Content-Type: application/json

["KFRMF", "SCBRMF", "K-GLOBAL"]
```

### Get Fund Info
```bash
GET /api/sec/fund/KFRMF
```

### Get Performance
```bash
GET /api/sec/performance/KFRMF?start_date=2024-01-01&end_date=2024-12-31
```

### Cache Management
```bash
# Invalidate specific fund
POST /api/sec/cache/invalidate/KFRMF

# Clear all cache
POST /api/sec/cache/clear

# Get statistics
GET /api/sec/stats
```

---

## 🧪 การทดสอบ

### Test Rate Limiter

```bash
cd smart_tax_assistant/tax-advisor-backend
python -m app.services.sec_rate_limiter
```

**คาดว่าจะได้:**
- 20 requests ใช้เวลา ~2.2 วินาที
- Average: 110ms per request

### Test API Client

```bash
python -m app.services.sec_api_client
```

### Test Cache

```bash
python -m app.services.sec_cache
```

### Test Complete Service

```bash
python -m app.services.sec_service
```

---

## ⚙️ Configuration

### Environment Variables

สร้างไฟล์ `.env`:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# SEC API Configuration
SEC_ENABLE_CACHE=true
SEC_RATE_LIMIT_MAX_REQUESTS=3000
SEC_RATE_LIMIT_TIME_WINDOW=300
SEC_RATE_LIMIT_SAFE_BUFFER=0.11
```

### ใช้งานกับ Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

service = SECService(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    enable_cache=os.getenv("SEC_ENABLE_CACHE", "true") == "true"
)
```

---

## 📈 Performance Expectations

### Without Caching:
- **100 fund NAV requests**: ~11 seconds
- **API calls**: 100
- **Cost**: 100x API calls

### With Caching (80% hit rate):
- **100 fund NAV requests**: ~2.2 seconds
- **API calls**: 20 (80 from cache)
- **Cost**: 20x API calls
- **Speed**: **5x faster**

### Cache Hit Rates:
- **NAV**: 70-90% (depends on usage pattern)
- **Fund Info**: 90-95% (rarely changes)
- **Fund List**: 95%+ (very stable)

---

## ⚠️ Important Notes

### ต้องปฏิบัติตาม:

1. ✅ **Rate Limiting**: 3,000 requests per 300 seconds (มีในโค้ดแล้ว)
2. ✅ **Minimum Interval**: 110ms between requests (มีในโค้ดแล้ว)
3. ✅ **HTTP 421 Handling**: Auto-retry with backoff (มีในโค้ดแล้ว)
4. ✅ **Caching**: ลดการเรียก API (แนะนำให้เปิด)

### ข้อควรระวัง:

❌ **อย่าเรียก API โดยตรงด้วย requests/httpx** - ใช้ service ที่สร้างไว้
❌ **อย่าปิด cache ถ้าไม่จำเป็น** - จะทำให้โดน rate limit
❌ **อย่า parallel request เยอะเกินไป** - rate limiter จะบล็อค
❌ **อย่าลืม close service** - ใช้ `await service.close()`

---

## 🔍 Monitoring

### Check Statistics

```python
# Get stats
stats = service.get_stats()

print(f"Cache efficiency: {stats['service_stats']['cache_efficiency_percent']}%")
print(f"API calls saved: {stats['service_stats']['cache_saves']}")
print(f"Cache hit rate: {stats['cache_stats']['hit_rate_percent']}%")

# Or print formatted
service.print_stats()
```

### Example Output:

```
============================================================
SEC SERVICE STATISTICS
============================================================

🎯 Service Stats:
  cache_saves: 80
  api_calls: 20
  total_operations: 100
  cache_efficiency_percent: 80.0

💾 Cache Stats:
  hits: 80
  misses: 20
  hit_rate_percent: 80.0
  enabled: True

📡 API Client Stats:
  total_requests: 20
  successful_requests: 20
  failed_requests: 0
  rate_limit_hits: 0
  success_rate: 100.0
============================================================
```

---

## 🐛 Troubleshooting

### Problem: Redis Connection Error

**Error:**
```
Failed to connect to Redis: [Errno 61] Connection refused
```

**Solution:**
1. ตรวจสอบ Redis running: `redis-cli ping` (ควรได้ "PONG")
2. หรือปิด cache: `SECService(enable_cache=False)`

### Problem: Rate Limit Hit (HTTP 421)

**Error:**
```
Rate limit hit (HTTP 421). Retry after 60s
```

**Solution:**
- โค้ดจะ retry อัตโนมัติ
- ถ้าเกิดบ่อย: เพิ่ม caching
- ถ้ายังไม่พอ: ติดต่อ repcenter@sec.or.th

### Problem: Slow Performance

**Solution:**
1. เปิด caching: `enable_cache=True`
2. เช็ค cache hit rate: `stats['cache_stats']['hit_rate_percent']`
3. ตรวจสอบ Redis latency: `redis-cli --latency`

---

## 📞 Support

- **SEC API Documentation**: https://api.sec.or.th/
- **Contact SEC**: repcenter@sec.or.th (สำหรับขอ rate limit สูงขึ้น)
- **Project Issues**: GitHub Issues

---

## 🎯 Next Steps

### For Development:
1. ✅ ติดตั้ง dependencies
2. ✅ ติดตั้ง Redis (optional)
3. ✅ Test ด้วย example scripts
4. ✅ Integrate กับ FastAPI
5. ✅ Monitor statistics

### For Production:
1. 📌 ใช้ Redis persistent storage
2. 📌 Monitor cache hit rates
3. 📌 Set up logging
4. 📌 Configure environment variables
5. 📌 Test with load testing

### Future Enhancements:
- 🔮 Fund selection algorithm (based on risk/performance)
- 🔮 Real-time NAV updates
- 🔮 Performance comparison charts
- 🔮 Automatic fund recommendations

---

## ✨ Summary

คุณตอนนี้มี:

✅ **Rate Limiter** - ป้องกันโดน rate limit
✅ **API Client** - HTTP 421 handling + retry logic
✅ **Caching** - ลดการเรียก API 80%+
✅ **Complete Service** - พร้อมใช้งานทันที
✅ **FastAPI Integration** - Example endpoints
✅ **Monitoring** - Statistics tracking

**เพียงแค่:**
```python
service = SECService()
nav = await service.get_nav("KFRMF")
```

**Done! 🎉**
