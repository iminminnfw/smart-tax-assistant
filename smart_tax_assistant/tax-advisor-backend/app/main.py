"""
FastAPI Main Application
Version: Qdrant Support
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file before anything else

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import logging

from app.models import TaxCalculationRequest, TaxCalculationResponse
from app.services.tax_calculator import tax_calculator_service
from app.services.rag_service import RAGService
from app.services.ai_service import AIService
from app.config import settings

# Import AI Optimizer router and lifespan (for services init)
from app.routers.ai_optimizer import router as ai_optimizer_router, lifespan as ai_lifespan

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# ============================================================
# Tax Reminder Job — เรียก Next.js cron endpoint ทุกวัน 08:00 ICT
# ============================================================
async def run_tax_reminder():
    frontend_url = settings.nextauth_url.rstrip("/")
    url = f"{frontend_url}/api/cron/tax-reminder"
    headers = {"x-cron-secret": settings.cron_secret}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(url, headers=headers)
        logger.info(f"[tax-reminder] status={res.status_code} body={res.text[:200]}")
    except Exception as e:
        logger.error(f"[tax-reminder] failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # รัน lifespan ของ AI Optimizer (init services)
    async with ai_lifespan(app):
        # เริ่ม APScheduler
        scheduler = AsyncIOScheduler(timezone="Asia/Bangkok")
        # ทุกวัน 08:00 น. (ICT) — ตรงกับเวลาที่ EventBridge เคยทำ
        scheduler.add_job(run_tax_reminder, CronTrigger(hour=8, minute=0))
        scheduler.start()
        logger.info("✅ Tax Reminder Scheduler started (daily 08:00 ICT)")

        yield

        scheduler.shutdown(wait=False)
        logger.info("✅ Scheduler stopped")


app = FastAPI(
    title="AI Tax Advisor API",
    description="ระบบแนะนำการวางแผนภาษีด้วย AI + Qdrant RAG + SEC API",
    version="3.3-sec-api",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_optimizer_router, prefix="/api/ai-optimizer", tags=["AI Optimizer"])

# Initialize services
print("=" * 50)
print("🚀 Initializing AI Tax Advisor API")
print("=" * 50)

rag_service = RAGService()
ai_service = AIService()

print("=" * 50)
print("✅ Initialization complete")
print("=" * 50)


@app.get("/")
async def root():
    return {
        "message": "AI Tax Advisor API",
        "version": "3.2-qdrant",
        "status": "running",
        "qdrant": {
            "url": settings.qdrant_url,
            "collection": settings.qdrant_collection_name,
            "available": rag_service.is_available()
        }
    }


@app.get("/health")
async def health_check():
    """Health check with Qdrant status"""
    qdrant_info = rag_service.get_collection_info()
    
    return {
        "status": "healthy",
        "qdrant": qdrant_info,
        "rag_available": rag_service.is_available()
    }


@app.post("/api/calculate-tax", response_model=TaxCalculationResponse)
async def calculate_tax_with_multiple_plans(
    request: TaxCalculationRequest
) -> TaxCalculationResponse:
    """
    คำนวณภาษีและรับแผนการลงทุนหลายแผน
    """
    try:
        # 1. คำนวณภาษี
        tax_result = tax_calculator_service.calculate_tax(request)

        # 2. ดึงข้อมูลจาก Qdrant RAG (ส่วนนี้เหมือนเดิม)
        context = "ไม่มีข้อมูลจาก RAG"
        if rag_service.is_available():
            query = f"""
            รายได้ {request.gross_income} บาท
            ระดับความเสี่ยง {request.risk_tolerance}
            ต้องการวางแผนภาษีและลงทุน
            มีครอบครัว บุตร บิดามารดา
            """
            try:
                retrieved_docs = await rag_service.retrieve_relevant_documents(
                    query,
                    k=settings.rag_top_k
                )
                if retrieved_docs:
                    context_parts = [doc.page_content for doc in retrieved_docs if hasattr(doc, 'page_content')]
                    if context_parts:
                        context = "\n\n".join(context_parts)
                        print(f"✅ RAG Context: {len(context)} characters")
                else:
                    print("⚠️ RAG: No documents retrieved")
            except Exception as e:
                print(f"⚠️ RAG Error: {e}")
        else:
            print("⚠️ RAG not available - using AI without context")

        # 3. เรียก AI เพื่อสร้างหลายแผน (จะได้แผนที่มีแค่ percentage)
        investment_plans = await ai_service.generate_recommendations(
            request, tax_result, context
        )

        # ✨ =================================================================
        # ✨ ขั้นตอนที่ 4: คำนวณตัวเลขด้วย Python เพื่อความแม่นยำ 100%
        # ✨ =================================================================
        print("🤖 Calculating exact investment amounts and tax savings...")

        # กำหนด tiers ตามรายได้ (ต้องตรงกับ AI service)
        gross = tax_result.gross_income
        if gross < 600000:
            tiers = [40000, 60000, 80000]
        elif gross < 1000000:
            tiers = [60000, 100000, 150000]
        elif gross < 1500000:
            tiers = [200000, 350000, 500000]
        elif gross < 2000000:
            tiers = [300000, 500000, 800000]
        elif gross < 3000000:
            tiers = [500000, 800000, 1200000]
        else:
            tiers = [800000, 1200000, 1800000]

        # 🔧 คำนวณ tax saving อย่างถูกต้องตามหลักภาษี Progressive Tax
        # Tax Saving = ภาษีที่ลดได้จากการลงทุน
        # = (ภาษีโดยไม่ลงทุน) - (ภาษีถ้าลงทุน)
        # ✅ ใช้ Multi-Bracket Calculation (ไม่ใช่ Simple Marginal Rate!)

        # วนลูปทุกแผนที่ AI ส่งมา และบังคับใช้ tier values
        for idx, plan in enumerate(investment_plans.get("plans", [])):
            # 🎯 บังคับใช้ total_investment ตาม tier (ไม่ใช้ค่าจาก AI)
            if idx < len(tiers):
                total_investment = tiers[idx]
                plan["total_investment"] = total_investment
            else:
                total_investment = plan.get("total_investment", 0)

            # ✅ Smart Redistribute: cap ตามกฎหมาย + เติมส่วนเกินตาม priority
            corrected_allocs = tax_calculator_service.redistribute_plan_allocations(
                allocations=plan.get("allocations", []),
                total_investment=total_investment,
                gross_income=tax_result.gross_income,
                request=request,
            )
            plan["allocations"] = corrected_allocs

            # คำนวณ total_investment จริงหลัง redistribute (อาจน้อยกว่า tier ถ้าทุก cap เต็มหมด)
            actual_total = sum(a.get("investment_amount", 0) for a in corrected_allocs)
            plan["total_investment"] = actual_total

            # ✅ คำนวณ tax saving แบบ Multi-Bracket จาก actual_total
            calculated_total_tax_saving = tax_calculator_service.calculate_tax_saving_accurate(
                taxable_base=tax_result.taxable_income,
                investment=actual_total,
            )
            plan["total_tax_saving"] = calculated_total_tax_saving

            # แจกจ่าย tax_saving ตามสัดส่วน investment_amount จริง
            for alloc in corrected_allocs:
                amt = alloc.get("investment_amount", 0)
                alloc["tax_saving"] = (
                    int((amt / actual_total) * calculated_total_tax_saving)
                    if actual_total > 0 else 0
                )

        print("✅ Calculation complete.")
        # ✨ =================================================================

        # 5. Return response (ตอนนี้จะมีตัวเลขที่ถูกต้องครบถ้วนแล้ว)
        return TaxCalculationResponse(
            tax_result=tax_result,
            investment_plans=investment_plans
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )