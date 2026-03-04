"""
AI Optimizer API Endpoints
FastAPI routes for AI-powered tax optimization

Add to main.py:
    from app.routers import ai_optimizer
    app.include_router(ai_optimizer.router, prefix="/api/ai", tags=["AI Optimizer"])

Endpoints:
    - /health: Health check
    - /tax-funds: Get tax-saving funds
    - /calculate/*: Tax calculations
    - /analyze-profile: Profile analysis
    - /parse-goal: Goal parsing
    - /generate-scenarios: Scenario generation
    - /simulate: What-if simulator
    - /smart-fund/{fund_code}: Deep fund analysis with 4 Intelligence Layers (NEW)
    - /smart-funds/batch: Batch fund analysis with filtering (NEW)
    - /smart-funds/top-picks: AI-recommended funds for user (NEW)
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
import os

from ..services.sec_service import SECService
from ..services.tax_fund_service import TaxFundService, TaxFundCategory
from ..services.ai_tax_advisor import (
    AITaxAdvisor,
    UserProfile,
    ParsedGoal,
    TaxScenario,
    create_ai_advisor
)

# SmartFundAnalyzer - 4 Intelligence Layers
from ..services.smart_fund_analyzer import (
    SmartFundAnalyzer,
    SmartFundAnalysisResult,
    SmartAnalysisBatchResult,
    FundType,
    create_smart_analyzer
)
from ..services.sec_api_client import SECAPIClient
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

# ============================================================
# Request/Response Models
# ============================================================

class UserProfileRequest(BaseModel):
    """User profile for AI analysis (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)
    """
    age: int = Field(..., ge=18, le=100, description="User's age")
    annual_income: float = Field(..., gt=0, description="Annual income in THB")
    monthly_expenses: float = Field(..., ge=0, description="Monthly expenses")
    existing_savings: float = Field(default=0, ge=0, description="Current savings")
    emergency_fund: float = Field(default=0, ge=0, description="Emergency fund")
    risk_tolerance: str = Field(
        default="moderate",
        description="Risk tolerance: conservative, moderate, aggressive"
    )
    occupation: str = Field(default="employee", description="Occupation type")
    marital_status: str = Field(default="single", description="Marital status")
    dependents: int = Field(default=0, ge=0, description="Number of dependents")

    # Existing deductions (ปี 2568 - ไม่รวม SSF)
    existing_rmf: float = Field(default=0, ge=0, description="Existing RMF investment")
    existing_thai_esg: float = Field(default=0, ge=0, description="Existing ThaiESG investment")
    existing_insurance: float = Field(default=0, ge=0, description="Existing insurance premium (life + health, legacy)")

    # Family deductions
    num_children: int = Field(default=0, ge=0, description="Number of children for tax deduction")
    num_parents: int = Field(default=0, ge=0, le=4, description="Number of parents (own + spouse) aged 60+, max 4")
    life_insurance_amount: float = Field(default=0, ge=0, description="Annual life insurance premium (raw, capped at 100,000)")
    health_insurance_amount: float = Field(default=0, ge=0, description="Annual health insurance premium (raw, capped at 25,000)")

    # Investment budget — monthly (backend multiplies ×12 internally)
    monthly_budget: Optional[float] = Field(default=None, ge=0, description="Monthly investment budget in THB (0 = auto 15% of income)")

    # Goal-based planning
    income_growth_rate: float = Field(default=0, ge=0, le=50, description="Expected annual income growth rate %")

        # Investment budget (user-specified, overrides auto-calc if provided)
    available_budget: Optional[float] = Field(default=None, ge=0, description="Annual investment budget in THB")

    # Retirement planning
    retirement_age: Optional[int] = Field(default=None, ge=18, le=100, description="Target retirement age")

    # Goal-based planning
    savings_target: Optional[float] = Field(default=None, ge=0, description="Total savings goal in THB")
    plan_to_marry: bool = Field(default=False, description="Single user planning to marry next year")

    # ประเภทเงินได้
    income_type: str = "40(8)"  # "40(6)" หรือ "40(8)"

    # วิธีหักค่าใช้จ่าย
    expense_deduction_type: str = "standard"  # "standard" (เหมา) หรือ "actual" (ตามจริง)

    # จด VAT หรือไม่ (สำหรับ 40(8))
    is_vat_registered: bool = False
    money_goal: Optional[str] = Field(default="mid_term", description="short_term, mid_term, retirement")


class GoalRequest(BaseModel):
    """User's goal in natural language"""
    goal: str = Field(..., min_length=5, description="Goal description in Thai or English")
    profile: UserProfileRequest


class ScenarioRequest(BaseModel):
    """Request for scenario generation"""
    profile: UserProfileRequest
    goal: str = Field(..., description="User's goal")
    include_fund_recommendations: bool = Field(
        default=True,
        description="Include fund recommendations from SEC API"
    )


class TaxCalculationRequest(BaseModel):
    """Request for tax calculation (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว
    """
    annual_income: float = Field(..., gt=0)
    rmf_investment: float = Field(default=0, ge=0)
    thai_esg_investment: float = Field(default=0, ge=0)
    existing_deductions: float = Field(default=0, ge=0)


class AllocationRequest(BaseModel):
    """Request for optimal allocation (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว
    """
    annual_income: float = Field(..., gt=0)
    available_budget: float = Field(..., gt=0)
    existing_rmf: float = Field(default=0, ge=0)
    existing_thai_esg: float = Field(default=0, ge=0)
    priority: str = Field(
        default="balanced",
        description="Priority: tax_max, balanced, conservative"
    )


class SmartFundBatchRequest(BaseModel):
    """Request for batch fund analysis with 4 Intelligence Layers"""
    fund_codes: Optional[List[str]] = Field(
        None,
        description="List of fund codes to analyze. If empty, analyzes all tax funds."
    )
    annual_income: float = Field(
        ...,
        gt=0,
        description="User's annual income for tax bracket calculation"
    )
    filter_accumulating_only: bool = Field(
        default=False,
        description="Only include funds with no dividend (tax-efficient)"
    )
    max_risk_level: Optional[int] = Field(
        None,
        ge=1,
        le=8,
        description="Maximum risk level (1-8)"
    )
    min_return_1y: Optional[float] = Field(
        None,
        description="Minimum 1-year return percentage"
    )
    fund_type: Optional[str] = Field(
        None,
        description="Filter by fund type: RMF, ThaiESG"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum funds to return"
    )


class TopPicksRequest(BaseModel):
    """Request for AI-recommended top fund picks"""
    annual_income: float = Field(..., gt=0, description="User's annual income")
    risk_tolerance: str = Field(
        default="moderate",
        description="conservative, moderate, aggressive"
    )
    fund_type: Optional[str] = Field(
        None,
        description="RMF or ThaiESG"
    )
    top_n: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top picks to return"
    )


# ============================================================
# Global Services
# ============================================================

sec_service: Optional[SECService] = None
tax_fund_service: Optional[TaxFundService] = None
ai_advisor: Optional[AITaxAdvisor] = None
smart_fund_analyzer: Optional[SmartFundAnalyzer] = None
sec_api_client: Optional[SECAPIClient] = None
rag_service: Optional[RAGService] = None


# ============================================================
# Lifespan Management
# ============================================================

@asynccontextmanager
async def lifespan(app):
    """
    Initialize and cleanup services

    Add to FastAPI app:
        app = FastAPI(lifespan=lifespan)
    """
    global sec_service, tax_fund_service, ai_advisor, smart_fund_analyzer, sec_api_client, rag_service

    # Startup
    logger.info("Initializing AI Optimizer services...")

    try:
        # Initialize SEC Service
        sec_service = SECService(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            enable_cache=True
        )

        # Initialize Tax Fund Service
        tax_fund_service = TaxFundService(sec_service)

        # Initialize AI Advisor
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")
        openai_key = os.getenv("OPENAI_API_KEY")

        if use_ollama:
            try:
                ai_advisor = AITaxAdvisor(provider="ollama")
                logger.info(f"✅ AI Advisor initialized with Ollama ({os.getenv('OLLAMA_MODEL', 'qwen2.5:14b')})")
            except Exception as e:
                logger.warning(f"⚠️ Ollama init failed: {e}, falling back to OpenAI")
                ai_advisor = None

        if ai_advisor is None and openai_key:
            ai_advisor = AITaxAdvisor(provider="openai", api_key=openai_key)
            logger.info("✅ AI Advisor initialized with OpenAI")
        elif ai_advisor is None:
            logger.warning("⚠️ No LLM provider available. AI features will be limited.")

        # Initialize SEC API Client and SmartFundAnalyzer
        sec_api_key = os.getenv("SEC_API_KEY")
        if sec_api_key:
            sec_api_client = SECAPIClient(api_key=sec_api_key)
            smart_fund_analyzer = SmartFundAnalyzer(sec_client=sec_api_client)
            logger.info("✅ SmartFundAnalyzer initialized with 4 Intelligence Layers")
        else:
            logger.warning("⚠️ SEC_API_KEY not set. SmartFundAnalyzer will not be available.")
            sec_api_client = None
            smart_fund_analyzer = None

        # Initialize RAG Service (Qdrant) for tax law context
        try:
            rag_service = RAGService()
            if rag_service.is_available():
                logger.info("✅ RAG Service (Qdrant) initialized for AI Optimizer")
            else:
                logger.warning("⚠️ RAG Service not available - AI will work without tax law context")
        except Exception as e:
            logger.warning(f"⚠️ RAG Service initialization failed: {e}")
            rag_service = None

        logger.info("✅ AI Optimizer services initialized")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")

    yield

    # Shutdown
    if sec_service:
        await sec_service.close()
        logger.info("✅ SEC Service closed")

    if sec_api_client:
        await sec_api_client.close()
        logger.info("✅ SEC API Client closed")


# ============================================================
# Router
# ============================================================

router = APIRouter()


# ============================================================
# Health Check
# ============================================================

@router.get("/health")
async def health_check():
    """Health check for AI Optimizer services"""
    return {
        "status": "healthy",
        "services": {
            "sec_service": sec_service is not None,
            "tax_fund_service": tax_fund_service is not None,
            "ai_advisor": ai_advisor is not None,
            "ai_provider": ai_advisor.provider if ai_advisor else None,
            "smart_fund_analyzer": smart_fund_analyzer is not None,
            "sec_api_client": sec_api_client is not None,
            "rag_service": rag_service is not None and rag_service.is_available()
        },
        "features": {
            "4_intelligence_layers": smart_fund_analyzer is not None,
            "goal_parsing": ai_advisor is not None,
            "scenario_generation": True,
            "tax_calculation": tax_fund_service is not None
        }
    }


# ============================================================
# Tax Fund Endpoints
# ============================================================

@router.get("/tax-funds")
async def get_tax_funds(
    category: Optional[str] = Query(
        None,
        description="Filter by category: RMF, ThaiESG (SSF หมดสิทธิ์แล้ว)"
    ),
    include_nav: bool = Query(False, description="Include NAV data"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results")
):
    """
    Get tax-saving funds from SEC API

    Returns filtered list of RMF and ThaiESG funds (SSF หมดสิทธิ์แล้ว).
    """
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        # Parse category
        fund_category = None
        if category:
            try:
                fund_category = TaxFundCategory(category.upper())
            except ValueError:
                raise HTTPException(400, f"Invalid category: {category}")

        funds = await tax_fund_service.get_tax_funds(
            category=fund_category,
            include_nav=include_nav,
            limit=limit
        )

        return {
            "success": True,
            "count": len(funds),
            "category": category,
            "data": funds
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tax funds: {e}")
        raise HTTPException(500, str(e))


@router.get("/tax-funds/statistics")
async def get_fund_statistics():
    """Get statistics about available tax funds"""
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        stats = await tax_fund_service.get_fund_statistics()
        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(500, str(e))


@router.get("/tax-funds/top/{category}")
async def get_top_funds(
    category: str,
    limit: int = Query(10, ge=1, le=50)
):
    """Get top performing funds in a category"""
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        fund_category = TaxFundCategory(category.upper())
        funds = await tax_fund_service.get_top_performing_funds(fund_category, limit)

        return {
            "success": True,
            "category": category,
            "count": len(funds),
            "data": funds
        }

    except ValueError:
        raise HTTPException(400, f"Invalid category: {category}")
    except Exception as e:
        logger.error(f"Failed to get top funds: {e}")
        raise HTTPException(500, str(e))


# ============================================================
# Tax Calculation Endpoints
# ============================================================

@router.post("/calculate/tax-savings")
async def calculate_tax_savings(request: TaxCalculationRequest):
    """
    Calculate tax savings from investments

    Returns detailed breakdown of tax savings, effective return,
    and comparison with/without deductions.
    """
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        result = tax_fund_service.calculate_tax_savings(
            annual_income=request.annual_income,
            rmf_investment=request.rmf_investment,
            thai_esg_investment=request.thai_esg_investment,
            existing_deductions=request.existing_deductions
        )

        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Tax calculation failed: {e}")
        raise HTTPException(500, str(e))


@router.post("/calculate/allocation")
async def calculate_optimal_allocation(request: AllocationRequest):
    """
    Calculate optimal allocation across tax fund categories

    Returns recommended distribution of investment budget
    to maximize tax savings based on priority.
    """
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        result = tax_fund_service.calculate_optimal_allocation(
            annual_income=request.annual_income,
            available_budget=request.available_budget,
            existing_rmf=request.existing_rmf,
            existing_thai_esg=request.existing_thai_esg,
            priority=request.priority
        )

        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Allocation calculation failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/calculate/deduction-limits")
async def get_deduction_limits(
    annual_income: float = Query(..., gt=0, description="Annual income")
):
    """Get deduction limits for given income"""
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        limits = tax_fund_service.calculate_deduction_limits(annual_income)
        tax_bracket = tax_fund_service.calculate_tax_bracket(annual_income)

        return {
            "success": True,
            "data": {
                "limits": limits,
                "tax_bracket": tax_bracket
            }
        }

    except Exception as e:
        logger.error(f"Failed to get limits: {e}")
        raise HTTPException(500, str(e))


# ============================================================
# AI Endpoints
# ============================================================

@router.post("/analyze-profile")
async def analyze_profile(profile: UserProfileRequest):
    """
    AI analysis of user's financial profile

    Returns insights, warnings, and tax optimization opportunities.
    """
    if ai_advisor is None:
        # Fallback without AI
        if tax_fund_service is None:
            raise HTTPException(503, "Services not initialized")

        # Basic analysis without LLM
        limits = tax_fund_service.calculate_deduction_limits(profile.annual_income)
        tax_bracket = tax_fund_service.calculate_tax_bracket(profile.annual_income)

        return {
            "success": True,
            "ai_powered": False,
            "data": {
                "tax_bracket": tax_bracket,
                "deduction_limits": limits,
                "remaining_quota": {
                    "rmf": max(0, limits['rmf_max'] - profile.existing_rmf),
                    "thai_esg": max(0, limits['thai_esg_max'] - profile.existing_thai_esg)
                },
                "note": "SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)"
            }
        }

    try:
        user_profile = UserProfile(
            age=profile.age,
            annual_income=profile.annual_income,
            monthly_expenses=profile.monthly_expenses,
            existing_savings=profile.existing_savings,
            emergency_fund=profile.emergency_fund,
            risk_tolerance=profile.risk_tolerance,
            occupation=profile.occupation,
            marital_status=profile.marital_status,
            dependents=profile.dependents,
            existing_rmf=profile.existing_rmf,
            existing_thai_esg=profile.existing_thai_esg,
            existing_insurance=profile.existing_insurance,
            income_type=profile.income_type,
            expense_deduction_type=profile.expense_deduction_type,
            is_vat_registered=profile.is_vat_registered
        )

        analysis = await ai_advisor.analyze_profile(user_profile)

        return {
            "success": True,
            "ai_powered": True,
            "data": analysis
        }

    except Exception as e:
        logger.error(f"Profile analysis failed: {e}")
        raise HTTPException(500, str(e))


@router.post("/parse-goal")
async def parse_goal(request: GoalRequest):
    """
    Parse natural language goal into structured format

    AI understands goals like:
    - "อยากประหยัดภาษี 80,000 บาท"
    - "ต้องมีเงินเหลือดาวน์บ้าน 1 ล้าน ปลายปีหน้า"
    - "อยากเกษียณเร็ว อายุ 55"
    """
    if ai_advisor is None:
        raise HTTPException(503, "AI advisor not available. Set OPENAI_API_KEY")

    try:
        user_profile = UserProfile(
            age=request.profile.age,
            annual_income=request.profile.annual_income,
            monthly_expenses=request.profile.monthly_expenses,
            existing_savings=request.profile.existing_savings,
            emergency_fund=request.profile.emergency_fund,
            risk_tolerance=request.profile.risk_tolerance,
            occupation=request.profile.occupation,
            marital_status=request.profile.marital_status,
            dependents=request.profile.dependents,
            existing_rmf=request.profile.existing_rmf,
            existing_thai_esg=request.profile.existing_thai_esg,
            existing_insurance=request.profile.existing_insurance,
            income_type=request.profile.income_type,
            expense_deduction_type=request.profile.expense_deduction_type,
            is_vat_registered=request.profile.is_vat_registered
        )

        parsed = await ai_advisor.parse_goal(request.goal, user_profile)

        return {
            "success": True,
            "data": {
                "goal_type": parsed.goal_type.value,
                "target_amount": parsed.target_amount,
                "deadline": parsed.deadline,
                "constraints": parsed.constraints,
                "priority": parsed.priority.value,
                "raw_input": parsed.raw_input
            }
        }

    except Exception as e:
        logger.error(f"Goal parsing failed: {e}")
        raise HTTPException(500, str(e))


@router.post("/generate-scenarios")
async def generate_scenarios(request: ScenarioRequest):
    """
    Generate personalized tax optimization scenarios

    AI creates 3 custom scenarios based on:
    - User's financial profile
    - Stated goals and constraints
    - Available tax fund data from SEC
    """
    try:
        user_profile = UserProfile(
            age=request.profile.age,
            annual_income=request.profile.annual_income,
            monthly_expenses=request.profile.monthly_expenses,
            existing_savings=request.profile.existing_savings,
            emergency_fund=request.profile.emergency_fund,
            risk_tolerance=request.profile.risk_tolerance,
            occupation=request.profile.occupation,
            marital_status=request.profile.marital_status,
            dependents=request.profile.dependents,
            existing_rmf=request.profile.existing_rmf,
            existing_thai_esg=request.profile.existing_thai_esg,
            existing_insurance=request.profile.existing_insurance,
            income_type=request.profile.income_type,
            expense_deduction_type=request.profile.expense_deduction_type,
            is_vat_registered=request.profile.is_vat_registered
        )

        # Get available funds if requested
        available_funds = []
        if request.include_fund_recommendations and tax_fund_service:
            try:
                available_funds = await tax_fund_service.get_tax_funds(limit=20)
            except Exception as e:
                logger.warning(f"Could not fetch funds: {e}")

        # Retrieve tax law context from RAG (Qdrant)
        rag_context = ""
        if rag_service and rag_service.is_available():
            try:
                rag_query = f"""
                กฎหมายภาษีไทย ลดหย่อนภาษี RMF ThaiESG
                รายได้ {request.profile.annual_income} บาท
                อายุ {request.profile.age} ปี
                ระดับความเสี่ยง {request.profile.risk_tolerance}
                {request.goal}
                """
                retrieved_docs = await rag_service.retrieve_relevant_documents(
                    rag_query, k=5
                )
                if retrieved_docs:
                    rag_context = "\n\n".join([
                        doc.page_content for doc in retrieved_docs
                        if hasattr(doc, 'page_content')
                    ])
                    logger.info(f"RAG context retrieved: {len(rag_context)} chars from {len(retrieved_docs)} docs")
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        # Generate scenarios
        if ai_advisor:
            # Parse goal first
            parsed_goal = await ai_advisor.parse_goal(request.goal, user_profile)

            # Generate AI scenarios with RAG context
            scenarios = await ai_advisor.generate_scenarios(
                user_profile,
                parsed_goal,
                available_funds,
                rag_context=rag_context
            )

            return {
                "success": True,
                "ai_powered": True,
                "goal": {
                    "type": parsed_goal.goal_type.value,
                    "target": parsed_goal.target_amount,
                    "priority": parsed_goal.priority.value
                },
                "scenarios": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "description": s.description,
                        "investments": {
                            "rmf": s.rmf_investment,
                            "thai_esg": s.thai_esg_investment,
                            "total": s.total_investment
                        },
                        "results": {
                            "tax_saved": s.tax_saved,
                            "cash_remaining": s.cash_remaining,
                            "risk_level": s.risk_level
                        },
                        "recommended_funds": s.recommended_funds,
                        "explanation": s.explanation,
                        "pros": s.pros,
                        "cons": s.cons,
                        "confidence": s.confidence,
                        "suitability_score": s.suitability_score
                    }
                    for s in scenarios
                ],
                "available_funds": available_funds[:5] if available_funds else []
            }

        else:
            # Fallback: rule-based scenarios
            if tax_fund_service is None:
                raise HTTPException(503, "Services not initialized")

            allocation = tax_fund_service.calculate_optimal_allocation(
                annual_income=request.profile.annual_income,
                available_budget=(request.profile.annual_income / 12 - request.profile.monthly_expenses) * 12 * 0.5,
                existing_rmf=request.profile.existing_rmf,
                    existing_thai_esg=request.profile.existing_thai_esg,
                priority='balanced'
            )

            return {
                "success": True,
                "ai_powered": False,
                "message": "AI not available. Showing rule-based recommendation.",
                "scenarios": [
                    {
                        "id": 1,
                        "name": "แผนแนะนำ (Rule-based)",
                        "description": "คำนวณจากกฎภาษีไทย",
                        "investments": allocation['recommended_allocation'],
                        "results": {
                            "tax_saved": allocation['tax_savings'],
                            "cash_remaining": allocation['remaining_budget'],
                            "risk_level": 5
                        },
                        "explanation": "แผนนี้คำนวณจากอัตราภาษีและสิทธิลดหย่อนคงเหลือของคุณ",
                        "pros": ["คำนวณตามกฎภาษีจริง"],
                        "cons": ["ไม่ได้ปรับตามเป้าหมายเฉพาะ"],
                        "confidence": 60,
                        "suitability_score": 60
                    }
                ],
                "available_funds": available_funds[:5] if available_funds else []
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scenario generation failed: {e}")
        raise HTTPException(500, str(e))


# ============================================================
# What-If Simulator
# ============================================================

@router.post("/simulate")
async def simulate_scenario(
    annual_income: float = Body(..., gt=0),
    rmf_investment: float = Body(0, ge=0),
    thai_esg_investment: float = Body(0, ge=0),
    cash_reserve: float = Body(0, ge=0)
):
    """
    What-If simulator for tax scenarios

    Adjust variables and see real-time results.
    """
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        # Calculate tax savings (ปี 2568 - ไม่รวม SSF)
        savings = tax_fund_service.calculate_tax_savings(
            annual_income=annual_income,
            rmf_investment=rmf_investment,
            thai_esg_investment=thai_esg_investment
        )

        # Calculate remaining budget
        total_investment = rmf_investment + thai_esg_investment
        estimated_monthly_savings = annual_income / 12 * 0.3  # Assume 30% savings rate
        annual_savings = estimated_monthly_savings * 12
        cash_after_investment = annual_savings - total_investment + cash_reserve

        return {
            "success": True,
            "simulation": {
                "inputs": {
                    "annual_income": annual_income,
                    "rmf": rmf_investment,
                    "thai_esg": thai_esg_investment,
                    "total_investment": total_investment,
                    "cash_reserve": cash_reserve
                },
                "outputs": {
                    "tax_saved": savings['tax_saved'],
                    "effective_return_percent": savings['effective_return'],
                    "marginal_tax_rate": savings['marginal_rate'],
                    "cash_remaining": cash_after_investment,
                    "tax_before": savings['tax_before'],
                    "tax_after": savings['tax_after']
                },
                "limits": savings['limits'],
                "actual_deductions": savings['actual_deductions']
            }
        }

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(500, str(e))


# ============================================================
# Smart Fund Analyzer Endpoints (4 Intelligence Layers)
# ============================================================

@router.get("/smart-fund/{fund_code}")
async def analyze_fund_smart(
    fund_code: str,
    annual_income: float = Query(
        1000000,
        gt=0,
        description="User's annual income for tax bracket calculation"
    )
):
    """
    Deep analysis of a single fund with 4 Intelligence Layers

    Returns comprehensive analysis including:
    - **Layer 1: True Exposure** - Feeder Fund detection (CIV/FIF/FOF), Master Fund identification, FX risk
    - **Layer 2: Performance Intelligence** - Alpha/Beta with benchmark context, Sharpe ratio analysis
    - **Layer 3: Tax Efficiency** - Dividend policy (Y/N), tax leakage calculation for your bracket
    - **Layer 4: Compliance Evidence** - Official SEC factsheet URLs, data freshness, disclaimers

    Example:
        GET /api/ai/smart-fund/KFGTECH-A?annual_income=1200000
    """
    if smart_fund_analyzer is None:
        raise HTTPException(
            503,
            "SmartFundAnalyzer not available. Set SEC_API_KEY environment variable."
        )

    try:
        # Calculate user's tax bracket
        tax_bracket = smart_fund_analyzer.get_user_tax_bracket(annual_income)

        # Perform deep analysis
        result = await smart_fund_analyzer.analyze_fund(
            fund_code=fund_code,
            user_tax_bracket=tax_bracket
        )

        return {
            "success": True,
            "fund_code": fund_code,
            "user_context": {
                "annual_income": annual_income,
                "tax_bracket": f"{tax_bracket:.0%}",
                "tax_bracket_decimal": tax_bracket
            },
            "analysis": result.model_dump(),
            "summary": {
                "overall_score": result.overall_score,
                "is_feeder_fund": result.true_exposure.is_feeder_fund,
                "tax_efficiency": result.tax_efficiency.tax_efficiency_rating,
                "dividend_policy": result.tax_efficiency.dividend_policy,
                "is_recommended": result.tax_efficiency.is_recommended_for_user,
                "has_factsheet": result.evidence.pdf_factsheet_url is not None
            }
        }

    except ValueError as e:
        raise HTTPException(404, f"Fund not found: {fund_code}")
    except Exception as e:
        logger.error(f"Smart fund analysis failed for {fund_code}: {e}")
        raise HTTPException(500, str(e))


@router.post("/smart-funds/batch")
async def analyze_funds_batch(request: SmartFundBatchRequest):
    """
    Batch analysis of multiple funds with filtering and ranking

    Analyzes funds using 4 Intelligence Layers and returns ranked results
    based on overall suitability score for the user's tax bracket.

    Filters available:
    - `filter_accumulating_only`: Only funds with dividend_policy="N" (tax-efficient)
    - `max_risk_level`: Maximum risk spectrum (1-8)
    - `min_return_1y`: Minimum 1-year return percentage
    - `fund_type`: RMF or ThaiESG

    Example:
        POST /api/ai/smart-funds/batch
        {
            "annual_income": 1200000,
            "filter_accumulating_only": true,
            "max_risk_level": 6,
            "fund_type": "RMF",
            "limit": 10
        }
    """
    if smart_fund_analyzer is None:
        raise HTTPException(
            503,
            "SmartFundAnalyzer not available. Set SEC_API_KEY environment variable."
        )

    try:
        # Calculate user's tax bracket
        tax_bracket = smart_fund_analyzer.get_user_tax_bracket(request.annual_income)

        # Parse fund type filter
        fund_type_filter = None
        if request.fund_type:
            try:
                fund_type_filter = FundType(request.fund_type.upper())
            except ValueError:
                raise HTTPException(400, f"Invalid fund_type: {request.fund_type}. Use RMF or ThaiESG.")

        # Perform batch analysis
        result = await smart_fund_analyzer.analyze_funds_batch(
            fund_codes=request.fund_codes,
            user_tax_bracket=tax_bracket,
            fund_type_filter=fund_type_filter,
            filter_accumulating_only=request.filter_accumulating_only,
            max_risk_level=request.max_risk_level,
            min_return_1y=request.min_return_1y,
            limit=request.limit
        )

        # Convert to response format
        funds_summary = []
        for fund in result.funds:
            funds_summary.append({
                "rank": fund.recommendation_rank,
                "fund_code": fund.fund_info.fund_code,
                "fund_name": fund.fund_info.fund_name_th or fund.fund_info.fund_name_en,
                "fund_type": fund.fund_info.fund_type,
                "overall_score": fund.overall_score,
                "nav": fund.fund_info.nav_per_unit,
                "nav_date": str(fund.fund_info.nav_date) if fund.fund_info.nav_date else None,
                "return_1y": fund.performance.return_1y,
                "risk_level": fund.fund_info.risk_spectrum,
                "intelligence": {
                    "is_feeder_fund": fund.true_exposure.is_feeder_fund,
                    "exposure_type": fund.true_exposure.exposure_type,
                    "master_fund": fund.true_exposure.master_fund_name,
                    "alpha": fund.performance_intelligence.alpha,
                    "sharpe_ratio": fund.performance_intelligence.sharpe_ratio,
                    "dividend_policy": fund.tax_efficiency.dividend_policy,
                    "tax_efficiency": fund.tax_efficiency.tax_efficiency_rating,
                    "is_recommended": fund.tax_efficiency.is_recommended_for_user
                },
                "factsheet_url": fund.evidence.pdf_factsheet_url
            })

        return {
            "success": True,
            "user_context": {
                "annual_income": request.annual_income,
                "tax_bracket": f"{tax_bracket:.0%}",
                "tax_bracket_decimal": tax_bracket
            },
            "filters_applied": result.filters_applied,
            "statistics": {
                "total_analyzed": result.total_funds_analyzed,
                "after_filters": result.recommended_funds_count,
                "returned": len(funds_summary),
                "analysis_time_ms": result.analysis_duration_ms
            },
            "funds": funds_summary,
            "full_analysis": [f.model_dump() for f in result.funds]  # Full data for detailed view
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch fund analysis failed: {e}")
        raise HTTPException(500, str(e))


@router.post("/smart-funds/top-picks")
async def get_smart_top_picks(request: TopPicksRequest):
    """
    Get AI-recommended top fund picks for a user

    Returns the best funds based on:
    - User's tax bracket (high income → prefer accumulating funds)
    - Risk tolerance
    - Fund type preference
    - 4 Intelligence Layers scoring

    Example:
        POST /api/ai/smart-funds/top-picks
        {
            "annual_income": 1500000,
            "risk_tolerance": "moderate",
            "fund_type": "RMF",
            "top_n": 5
        }
    """
    if smart_fund_analyzer is None:
        raise HTTPException(
            503,
            "SmartFundAnalyzer not available. Set SEC_API_KEY environment variable."
        )

    try:
        # Calculate user's tax bracket
        tax_bracket = smart_fund_analyzer.get_user_tax_bracket(request.annual_income)

        # Determine filters based on user profile
        filter_accumulating = tax_bracket >= 0.25  # High income → prefer no dividend

        # Map risk tolerance to max risk level
        risk_level_map = {
            "conservative": 4,
            "moderate": 6,
            "aggressive": 8
        }
        max_risk = risk_level_map.get(request.risk_tolerance, 6)

        # Parse fund type
        fund_type_filter = None
        if request.fund_type:
            try:
                fund_type_filter = FundType(request.fund_type.upper())
            except ValueError:
                pass

        # Get top picks
        result = await smart_fund_analyzer.analyze_funds_batch(
            user_tax_bracket=tax_bracket,
            fund_type_filter=fund_type_filter,
            filter_accumulating_only=filter_accumulating,
            max_risk_level=max_risk,
            limit=request.top_n
        )

        # Format response
        top_picks = []
        for fund in result.funds:
            # Generate recommendation reason
            reasons = []
            if fund.tax_efficiency.is_recommended_for_user:
                reasons.append(f"เหมาะกับฐานภาษี {tax_bracket:.0%}")
            if fund.tax_efficiency.dividend_policy == "N":
                reasons.append("ไม่จ่ายปันผล (ประหยัดภาษี)")
            if fund.performance_intelligence.alpha and fund.performance_intelligence.alpha > 0:
                reasons.append(f"Alpha +{fund.performance_intelligence.alpha:.2f}%")
            if fund.performance.return_1y and fund.performance.return_1y > 5:
                reasons.append(f"ผลตอบแทน 1 ปี {fund.performance.return_1y:.1f}%")
            if not fund.true_exposure.is_feeder_fund:
                reasons.append("ลงทุนโดยตรง")

            top_picks.append({
                "rank": fund.recommendation_rank,
                "fund_code": fund.fund_info.fund_code,
                "fund_name": fund.fund_info.fund_name_th or fund.fund_info.fund_name_en,
                "fund_type": fund.fund_info.fund_type,
                "amc": fund.fund_info.amc_name_th,
                "overall_score": fund.overall_score,
                "recommendation_reasons": reasons,
                "key_metrics": {
                    "nav": fund.fund_info.nav_per_unit,
                    "return_1y": fund.performance.return_1y,
                    "return_3y": fund.performance.return_3y,
                    "risk_level": fund.fund_info.risk_spectrum,
                    "alpha": fund.performance_intelligence.alpha,
                    "sharpe": fund.performance_intelligence.sharpe_ratio
                },
                "tax_analysis": {
                    "dividend_policy": fund.tax_efficiency.dividend_policy,
                    "tax_efficiency": fund.tax_efficiency.tax_efficiency_rating,
                    "recommendation": fund.tax_efficiency.recommendation
                },
                "exposure": {
                    "is_feeder_fund": fund.true_exposure.is_feeder_fund,
                    "type": fund.true_exposure.exposure_type,
                    "master_fund": fund.true_exposure.master_fund_name,
                    "warnings_count": len(fund.true_exposure.warnings)
                },
                "evidence": {
                    "factsheet_url": fund.evidence.pdf_factsheet_url,
                    "data_fresh": fund.evidence.is_data_fresh
                }
            })

        return {
            "success": True,
            "user_profile": {
                "annual_income": request.annual_income,
                "tax_bracket": f"{tax_bracket:.0%}",
                "risk_tolerance": request.risk_tolerance,
                "fund_type_preference": request.fund_type
            },
            "selection_criteria": {
                "prefer_accumulating": filter_accumulating,
                "max_risk_level": max_risk,
                "reason": f"ฐานภาษี {tax_bracket:.0%} {'ควรเลือกกองทุนไม่จ่ายปันผล' if filter_accumulating else 'สามารถเลือกกองทุนจ่ายปันผลได้'}"
            },
            "top_picks": top_picks,
            "disclaimer": "การลงทุนมีความเสี่ยง ผู้ลงทุนควรศึกษาข้อมูลก่อนตัดสินใจลงทุน"
        }

    except Exception as e:
        logger.error(f"Top picks generation failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/smart-fund/{fund_code}/compare")
async def compare_with_benchmark(
    fund_code: str,
    annual_income: float = Query(1000000, gt=0)
):
    """
    Get fund analysis with detailed benchmark comparison

    Returns Layer 2 (Performance Intelligence) in detail with
    contextualized narratives in Thai.
    """
    if smart_fund_analyzer is None:
        raise HTTPException(503, "SmartFundAnalyzer not available.")

    try:
        tax_bracket = smart_fund_analyzer.get_user_tax_bracket(annual_income)
        result = await smart_fund_analyzer.analyze_fund(fund_code, tax_bracket)

        perf = result.performance_intelligence

        return {
            "success": True,
            "fund_code": fund_code,
            "benchmark_analysis": {
                "benchmark_name": perf.benchmark.benchmark_name,
                "fund_return_1y": perf.benchmark.fund_return,
                "alpha": perf.alpha,
                "beta": perf.beta,
                "sharpe_ratio": perf.sharpe_ratio,
                "max_drawdown": perf.max_drawdown,
                "tracking_error": perf.tracking_error
            },
            "narratives": {
                "alpha": perf.alpha_narrative,
                "beta": perf.beta_narrative,
                "sharpe": perf.sharpe_narrative,
                "overall": perf.overall_verdict
            },
            "assessment": {
                "shows_manager_skill": perf.shows_manager_skill,
                "recommend_index_alternative": perf.recommend_index_alternative,
                "verdict": "ผู้จัดการกองทุนสร้างผลตอบแทนเหนือตลาด" if perf.shows_manager_skill else "ควรพิจารณากองทุน Index ที่ค่าธรรมเนียมถูกกว่า" if perf.recommend_index_alternative else "ผลงานอยู่ในเกณฑ์ปกติ"
            }
        }

    except Exception as e:
        logger.error(f"Benchmark comparison failed: {e}")
        raise HTTPException(500, str(e))


# ============================================================
# Unified Optimize Endpoint (Code-Heavy, LLM-Light)
# ============================================================

def _extract_expected_return(funds: list) -> float:
    """Extract average 1-year NAV return from pre_filtered_funds (returns decimal, e.g. 0.07 = 7%)"""
    returns = []
    for f in funds:
        perf = f.get('performance', {})
        r1y = perf.get('return1y')
        if r1y is not None:
            returns.append(r1y)
    if returns:
        avg = sum(returns) / len(returns) / 100  # % → decimal
        return max(0.01, min(avg, 0.25))  # Clamp 1%–25%
    return 0.07  # Default 7% if no NAV data


def _calculate_fv(annual_investment: float, rate: float, years: int) -> float:
    """Future Value of annuity (end-of-period): FV = PMT × ((1+r)^n − 1) / r"""
    if years <= 0 or annual_investment <= 0:
        return 0.0
    if rate < 0.001:
        return annual_investment * years
    return annual_investment * ((1 + rate) ** years - 1) / rate


def _years_to_target(annual_investment: float, rate: float, target: float) -> Optional[int]:
    """Return the number of years to accumulate target via annual_investment at rate; None if > 100 yrs"""
    if annual_investment <= 0 or target <= 0:
        return None
    for n in range(1, 101):
        if _calculate_fv(annual_investment, rate, n) >= target:
            return n
    return None


def _calculate_family_deductions(profile: "UserProfileRequest") -> float:
    """
    คำนวณลดหย่อนครอบครัว + ประกัน + ประกันสังคม สำหรับพนักงานเงินเดือน (ปี 2568)

    ลดหย่อนที่คิด:
    - คู่สมรส (ไม่มีรายได้): 60,000
    - บุตร: คนที่ 1 = 30,000, คนที่ 2+ = 60,000
    - พ่อแม่อายุ 60+ (รวมพ่อแม่คู่สมรส): 30,000/คน สูงสุด 4 คน
    - ประกันชีวิต: min(จำนวน, 100,000)
    - ประกันสุขภาพ: min(จำนวน, 25,000)
    - ประกันสังคม ม.33 (พนักงาน): 9,000/ปี
    """
    total = 0.0

    # คู่สมรส
    if profile.marital_status == 'married':
        total += 60_000

    # บุตร: คนที่ 1 = 30,000, คนที่ 2+ = 60,000
    children = profile.num_children or 0
    if children >= 1:
        total += 30_000
    if children >= 2:
        total += (children - 1) * 60_000

    # พ่อแม่: 30,000/คน สูงสุด 4 คน
    total += min(profile.num_parents or 0, 4) * 30_000

    # ประกันชีวิต: max 100,000
    total += min(profile.life_insurance_amount or 0, 100_000)

    # ประกันสุขภาพ: max 25,000
    total += min(profile.health_insurance_amount or 0, 25_000)

    # ประกันสังคม ม.33 (พนักงานเงินเดือน): 750/เดือน = 9,000/ปี
    if profile.occupation == 'employee':
        total += 9_000

    return total


def calculate_allocation(
    age: int,
    income: float,
    goal: str,
    monthly_budget: float,
    risk_tolerance: str,
    income_growth_rate: float = 0.0,
    existing_rmf: float = 0.0,
    existing_thai_esg: float = 0.0,
) -> Dict:
    """
    คำนวณสัดส่วนการลงทุน RMF : ThaiESG : TESGX ที่เหมาะสมที่สุด (ปี 2569)

    Phase 1: Base allocation (RMF% vs ESG%) — อิงเป้าหมายและอายุ
    Phase 2: ESG split (ThaiESG vs TESGX) — อิงระดับความเสี่ยง
    Phase 3: คำนวณเม็ดเงินจริง + cap ตามโควตากฎหมาย
    """
    # ── Auto budget ─────────────────────────────────────────────────
    if not monthly_budget or monthly_budget <= 0:
        monthly_budget = income / 12 * 0.15  # 15% ของรายได้/เดือน
        budget_factor = (
            f"ไม่ได้ระบุงบลงทุน ระบบประมาณจาก 15% ของรายได้/เดือน "
            f"= ฿{monthly_budget:,.0f}/เดือน (฿{monthly_budget*12:,.0f}/ปี)"
        )
    else:
        budget_factor = (
            f"งบลงทุน ฿{monthly_budget:,.0f}/เดือน = ฿{monthly_budget*12:,.0f}/ปี "
            f"ตามที่ผู้ใช้กำหนด"
        )

    annual_budget = monthly_budget * 12

    # ── Phase 1: Base RMF vs ESG ratio ──────────────────────────────
    goal = (goal or "mid_term").lower().strip()

    if goal == "short_term":
        if age < 47:
            rmf_pct, esg_pct = 0.0, 1.0
            age_factor = (
                f"อายุ {age} ปี เลือกเป้าหมายระยะสั้น (ต้องใช้เงินภายใน 5 ปี) "
                f"RMF ล็อคถึงอายุ 55 ถอนไม่ทันแน่นอน ระบบจึงไม่จัด RMF เลย "
                f"เอาเงินทั้งหมดไปลงกลุ่ม ESG ที่ล็อคแค่ 5 ปีแทน"
            )
            goal_factor = "ต้องการใช้เงินก้อนในอนาคตอันใกล้ ThaiESG ล็อคแค่ 5 ปีเหมาะที่สุด"
        else:
            rmf_pct, esg_pct = 0.30, 0.70
            age_factor = (
                f"อายุ {age} ปี แม้เป้าหมายระยะสั้น แต่อายุใกล้ 55 ปีแล้ว "
                f"RMF จะล็อคไม่นานและลดหย่อนภาษีได้ดี จึงแบ่งบางส่วน"
            )
            goal_factor = "ต้องการใช้เงินเร็ว แต่อายุใกล้ 55 RMF บางส่วนยังคุ้มค่าลดหย่อน"

    elif goal == "retirement":
        if age < 35:
            rmf_pct, esg_pct = 0.70, 0.30
            age_factor = (
                f"อายุ {age} ปี เป้าหมายเกษียณระยะยาว มีเวลาล็อคเงินนาน "
                f"RMF เหมาะมากเพราะลดหย่อนภาษีได้สูงและบังคับออมระยะยาว"
            )
        else:
            rmf_pct, esg_pct = 0.80, 0.20
            age_factor = (
                f"อายุ {age} ปี เป้าหมายเกษียณ อายุ 55 ไม่ไกลมาก "
                f"เน้น RMF หนักเพื่อประหยัดภาษีสูงสุดและออมเพื่อเกษียณโดยตรง"
            )
        goal_factor = "เป้าหมายเกษียณ RMF คือเครื่องมือที่ออกแบบมาเพื่อจุดนี้โดยตรง"

    else:  # mid_term (default)
        if age < 45:
            rmf_pct, esg_pct = 0.20, 0.80
            age_factor = (
                f"อายุ {age} ปี เป้าหมายระยะกลาง 5-10 ปี ยังมีเวลาพอสมควร "
                f"เน้น ThaiESG เพื่อสภาพคล่อง RMF แค่ส่วนน้อยเพื่อลดหย่อนเพิ่ม"
            )
        else:
            rmf_pct, esg_pct = 0.50, 0.50
            age_factor = (
                f"อายุ {age} ปี เป้าหมายระยะกลาง อายุเริ่มเข้าใกล้ 55 ปี "
                f"แบ่ง RMF และ ThaiESG เท่ากันเพื่อสมดุลระหว่างการลดหย่อนและสภาพคล่อง"
            )
        goal_factor = "ระยะกลาง 5-10 ปี ThaiESG ล็อค 5 ปีพอดี สภาพคล่องดีกว่า RMF"

    # ── Phase 2: ESG split by risk ───────────────────────────────────
    risk = (risk_tolerance or "moderate").lower().strip()

    if risk == "conservative":
        tesg_split, tesgx_split = 1.0, 0.0
        risk_factor = (
            "ระดับความเสี่ยงต่ำ เลือก ThaiESG ล้วนๆ ไม่มี TESGX "
            "ThaiESG กระจายหุ้นหลายตลาด ผันผวนน้อยกว่าและเหมาะกับคนรับความเสี่ยงได้จำกัด"
        )
    elif risk == "aggressive":
        tesg_split, tesgx_split = 0.40, 0.60
        risk_factor = (
            "กล้าเสี่ยงสูง เทน้ำหนัก TESGX 60% ซึ่งลงทุนในหุ้นไทยขนาดเล็ก-กลาง "
            "โอกาสเติบโตสูงกว่าแต่ผันผวนมากกว่า เหมาะกับนักลงทุนที่รับ drawdown ได้"
        )
    else:  # moderate
        tesg_split, tesgx_split = 0.80, 0.20
        risk_factor = (
            "ความเสี่ยงปานกลาง ผสม ThaiESG 80% กับ TESGX 20% "
            "ได้โอกาสเติบโตจาก TESGX บางส่วน แต่ยังมีความมั่นคงจาก ThaiESG เป็นหลัก"
        )

    # ── Phase 3: Quota caps (net of existing investments) ────────────
    gross_max_rmf  = min(income * 0.30, 500_000)
    gross_max_esg  = min(income * 0.30, 300_000)

    # หักสิ่งที่ลงทุนไปแล้วในปีนี้
    max_rmf = max(0.0, gross_max_rmf - existing_rmf)
    max_esg = max(0.0, gross_max_esg - existing_thai_esg)

    # Raw amounts from Phase 1 ratios
    rmf_raw = annual_budget * rmf_pct
    esg_raw = annual_budget * esg_pct

    # Cap RMF, overflow → ESG (ถ้า quota ยังเหลือ)
    if rmf_raw > max_rmf:
        overflow  = rmf_raw - max_rmf
        rmf_amount = max_rmf
        esg_raw   = min(esg_raw + overflow, max_esg)
    else:
        rmf_amount = min(rmf_raw, max_rmf)

    # Cap ESG
    esg_amount   = min(esg_raw, max_esg)
    tesg_amount  = esg_amount * tesg_split
    tesgx_amount = esg_amount * tesgx_split

    rmf_amount   = round(rmf_amount)
    tesg_amount  = round(tesg_amount)
    tesgx_amount = round(tesgx_amount)

    total_invested = rmf_amount + tesg_amount + tesgx_amount

    # Final hard cap (งบเกินเพดานรวมกฎหมาย)
    max_total = max_rmf + max_esg
    if total_invested > max_total:
        # กรณีนี้ไม่ควรเกิด แต่ป้องกันไว้
        ratio = max_total / total_invested
        rmf_amount   = round(rmf_amount * ratio)
        tesg_amount  = round(tesg_amount * ratio)
        tesgx_amount = round(tesgx_amount * ratio)
        total_invested = rmf_amount + tesg_amount + tesgx_amount

    cash_remaining = max(0.0, annual_budget - total_invested)

    # Actual % after caps
    if total_invested > 0:
        actual_rmf_pct   = round(rmf_amount   / total_invested * 100, 1)
        actual_tesg_pct  = round(tesg_amount  / total_invested * 100, 1)
        actual_tesgx_pct = round(tesgx_amount / total_invested * 100, 1)
    else:
        actual_rmf_pct = actual_tesg_pct = actual_tesgx_pct = 0.0

    # Remaining quota after this recommendation
    remaining_rmf = max(0.0, max_rmf - rmf_amount)
    remaining_esg = max(0.0, max_esg - tesg_amount - tesgx_amount)

    years_to_55 = max(0, 55 - age)

    goal_labels = {
        "retirement": "เก็บยาวเพื่อเกษียณ",
        "mid_term":   "ลดหย่อน + ถอนได้ระยะกลาง (5-10 ปี)",
        "short_term": "ต้องการใช้เงินก้อนในอนาคตอันใกล้",
    }

    budget_note = (
        f"งบ ฿{annual_budget:,.0f}/ปี, "
        f"ลงทุนจริง ฿{total_invested:,.0f}/ปี"
        + (f", เงินสดเหลือ ฿{cash_remaining:,.0f} (เกินโควตาลดหย่อน)" if cash_remaining > 0 else "")
    )
    budget_factor = f"{budget_factor} — {budget_note}"

    return {
        "rmf_amount":   rmf_amount,
        "tesg_amount":  tesg_amount,
        "tesgx_amount": tesgx_amount,
        "total_amount": total_invested,
        "rmf_pct":      actual_rmf_pct,
        "tesg_pct":     actual_tesg_pct,
        "tesgx_pct":    actual_tesgx_pct,
        "cash_remaining":  round(cash_remaining),
        "monthly_dca":     round(total_invested / 12),
        "years_to_55":     years_to_55,
        "rmf_eligible":    rmf_pct > 0,
        "money_goal":      goal,
        "money_goal_label": goal_labels.get(goal, goal),
        "remaining_quota": {
            "rmf": round(remaining_rmf),
            "esg": round(remaining_esg),
        },
        "decision_factors": {
            "age_factor":    age_factor,
            "goal_factor":   goal_factor,
            "risk_factor":   risk_factor,
            "budget_factor": budget_factor,
        },
    }


def _calculate_3year_breakdown(
    annual_income: float,
    available_budget: float,
    existing_rmf: float,
    existing_thai_esg: float,
    family_deductions: float,
    income_growth_rate: float,
    tax_fund_svc,
    age: int,
    goal: str,
    risk_tolerance: str,
) -> dict:
    """คำนวณ tax savings รายปี สำหรับ 3 ปีข้างหน้า (high-credibility, no long-term speculation)
    ใช้ calculate_allocation() เพื่อให้สอดคล้องกับ recommended_plan หลัก (เดิมใช้ tax_max ทำให้ตัวเลขขัดกัน)
    """
    breakdown = []
    cumulative_tax_saved = 0.0
    cumulative_investment = 0.0

    current_tax_year = 2568  # ปี พ.ศ. ปัจจุบัน
    growth = 1 + (income_growth_rate / 100)

    for yr in range(1, 4):
        yr_income = annual_income * (growth ** (yr - 1))
        yr_budget = available_budget * (growth ** (yr - 1))

        # ปีที่ 2+ user ยังไม่ได้ลงทุน → existing reset เป็น 0
        yr_existing_rmf = existing_rmf if yr == 1 else 0
        yr_existing_thai_esg = existing_thai_esg if yr == 1 else 0

        # ใช้ calculate_allocation() ตัวเดียวกับ recommended_plan — สม่ำเสมอ
        alloc = calculate_allocation(
            age=age,
            income=yr_income,
            goal=goal,
            monthly_budget=yr_budget / 12,  # calculate_allocation รับค่า monthly แล้วคูณ 12 เอง
            risk_tolerance=risk_tolerance,
            income_growth_rate=0.0,  # growth ถูก apply ที่ yr_income/yr_budget แล้ว ไม่ต้องซ้ำ
            existing_rmf=yr_existing_rmf,
            existing_thai_esg=yr_existing_thai_esg,
        )
        rmf_amt = alloc['rmf_amount']
        esg_amt = alloc['tesg_amount'] + alloc['tesgx_amount']  # ThaiESG + TESGX รวมกัน
        total_inv = alloc['total_amount']

        savings = tax_fund_svc.calculate_tax_savings(
            annual_income=yr_income,
            rmf_investment=yr_existing_rmf + rmf_amt,
            thai_esg_investment=yr_existing_thai_esg + esg_amt,
            family_deductions=family_deductions,
        )

        cumulative_tax_saved += savings['tax_saved']
        cumulative_investment += total_inv

        breakdown.append({
            "year": yr,
            "tax_year": current_tax_year + (yr - 1),
            "income": round(yr_income),
            "rmf_investment": round(rmf_amt),
            "thai_esg_investment": round(esg_amt),
            "total_investment": round(total_inv),
            "tax_saved": round(savings['tax_saved']),
        })

    return {
        "year_breakdown": breakdown,
        "cumulative_tax_saved_3y": round(cumulative_tax_saved),
        "cumulative_investment_3y": round(cumulative_investment),
    }


class OptimizeRequest(BaseModel):
    """Single unified request - code does filtering/calculation, LLM only explains"""
    profile: UserProfileRequest
    goal: str = Field(..., min_length=1, description="User's goal in Thai/English")
    risk_tolerance: str = Field(default="moderate", description="conservative, moderate, aggressive")
    fund_types: List[str] = Field(default=["RMF", "ThaiESG"], description="Fund types to consider")
    top_n_funds: int = Field(default=5, ge=1, le=20)
    include_ai_explanation: bool = Field(default=True, description="Call LLM for Thai explanations")
    # Pre-filtered funds from Next.js (Prisma DB)
    pre_filtered_funds: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Pre-filtered funds from frontend DB query"
    )


@router.post("/optimize")
async def optimize(request: OptimizeRequest):
    """
    Unified AI Optimizer endpoint (Code-Heavy, LLM-Light)

    Flow:
    1. Code calculates tax (brackets, deductions, savings)
    2. Code creates 3 scenarios (tax_max / balanced / conservative)
    3. Code assigns pre-filtered funds to scenarios
    4. (Optional) LLM explains WHY these plans fit the user

    No SEC API calls - uses pre-filtered funds from Prisma DB.
    """
    if tax_fund_service is None:
        raise HTTPException(503, "Tax fund service not initialized")

    try:
        # ============================================================
        # Step 1: Calculate tax info (CODE)
        # ============================================================

        # คำนวณลดหย่อนครอบครัว + ประกัน + ประกันสังคม
        family_deductions = _calculate_family_deductions(request.profile)
        logger.info(f"Family deductions: {family_deductions:,.0f} "
                    f"(spouse={request.profile.marital_status=='married'}, "
                    f"children={request.profile.num_children}, "
                    f"parents={request.profile.num_parents}, "
                    f"life_ins={request.profile.life_insurance_amount}, "
                    f"health_ins={request.profile.health_insurance_amount})")

        tax_bracket = tax_fund_service.calculate_tax_bracket(
            request.profile.annual_income, extra_deductions=family_deductions
        )

        # ============================================================
        # Step 2: calculate_allocation() — Phase 1/2/3 ใหม่ทั้งหมด
        # ============================================================

        pre_funds          = request.pre_filtered_funds or []
        income_growth_rate = request.profile.income_growth_rate or 0.0
        monthly_budget_raw = request.profile.monthly_budget or 0.0  # monthly, backend คูณ 12 เอง

        logger.info(
            f"money_goal={request.profile.money_goal}, "
            f"monthly_budget={monthly_budget_raw:,.0f}, "
            f"income_growth_rate={income_growth_rate}%, "
            f"existing_rmf={request.profile.existing_rmf:,.0f}, "
            f"existing_thai_esg={request.profile.existing_thai_esg:,.0f}"
        )

        allocation = calculate_allocation(
            age              = request.profile.age,
            income           = request.profile.annual_income,
            goal             = request.profile.money_goal or "mid_term",
            monthly_budget   = monthly_budget_raw,
            risk_tolerance   = request.profile.risk_tolerance,
            income_growth_rate = income_growth_rate,
            existing_rmf     = request.profile.existing_rmf or 0.0,
            existing_thai_esg= request.profile.existing_thai_esg or 0.0,
        )

        rmf_amount     = allocation["rmf_amount"]
        tesg_amount    = allocation["tesg_amount"]
        tesgx_amount   = allocation["tesgx_amount"]
        total_investment = allocation["total_amount"]
        annual_budget  = (monthly_budget_raw or (request.profile.annual_income / 12 * 0.15)) * 12

        # สรุปสิทธิ์คงเหลือสำหรับ tax_info
        limits           = tax_fund_service.calculate_deduction_limits(request.profile.annual_income)
        remaining_rmf    = allocation["remaining_quota"]["rmf"]
        remaining_thai_esg = allocation["remaining_quota"]["esg"]

        logger.info(
            f"Tax bracket: {tax_bracket['marginal_rate_percent']}%, "
            f"Invested: {total_investment:,.0f}, "
            f"Cash remaining: {allocation['cash_remaining']:,.0f}"
        )

        # Calculate accurate tax savings
        savings = tax_fund_service.calculate_tax_savings(
            annual_income      = request.profile.annual_income,
            rmf_investment     = request.profile.existing_rmf + rmf_amount,
            thai_esg_investment= request.profile.existing_thai_esg + tesg_amount + tesgx_amount,
            family_deductions  = family_deductions,
        )

        # 3-year breakdown — ใช้ logic เดียวกับ recommended_plan (goal + risk aware)
        three_year = _calculate_3year_breakdown(
            annual_income      = request.profile.annual_income,
            available_budget   = annual_budget,
            existing_rmf       = request.profile.existing_rmf,
            existing_thai_esg  = request.profile.existing_thai_esg,
            family_deductions  = family_deductions,
            income_growth_rate = income_growth_rate,
            tax_fund_svc       = tax_fund_service,
            age                = request.profile.age,
            goal               = request.profile.money_goal or "mid_term",
            risk_tolerance     = request.profile.risk_tolerance,
        )

        # ============================================================
        # Step 3: Assign pre-filtered funds (CODE)
        # ============================================================

        rmf_funds   = [f for f in pre_funds if f.get("fundType", "").upper() == "RMF"]
        tesg_funds  = [f for f in pre_funds if f.get("fundType", "").upper() == "TESG"]
        tesgx_funds = [f for f in pre_funds if f.get("fundType", "").upper() == "TESGX"]

        recommended_funds_for_plan = rmf_funds[:3] + tesg_funds[:3] + tesgx_funds[:3]

        recommended_plan = {
            **allocation,
            "tax_before":              savings.get("tax_before", 0),
            "tax_after":               savings.get("tax_after", 0),
            "tax_saved":               savings.get("tax_saved", 0),
            "effective_return_percent": round(savings.get("effective_return", 0), 1),
            "monthly_investment":      allocation["monthly_dca"],
            "year_breakdown":          three_year["year_breakdown"],
            "cumulative_tax_saved_3y": three_year["cumulative_tax_saved_3y"],
            "cumulative_investment_3y": three_year["cumulative_investment_3y"],
            "recommended_funds":       recommended_funds_for_plan,
            "ai_explanation":          None,
        }

        # ============================================================
        # Step 4: Profile analysis (LLM optional)
        # ============================================================
        profile_analysis = None
        user_profile = None
        if ai_advisor:
            try:
                user_profile = UserProfile(
                    age=request.profile.age,
                    annual_income=request.profile.annual_income,
                    monthly_expenses=request.profile.monthly_expenses,
                    existing_savings=request.profile.existing_savings,
                    emergency_fund=request.profile.emergency_fund,
                    risk_tolerance=request.profile.risk_tolerance,
                    occupation=request.profile.occupation,
                    marital_status=request.profile.marital_status,
                    dependents=request.profile.dependents,
                    existing_rmf=request.profile.existing_rmf,
                    existing_thai_esg=request.profile.existing_thai_esg,
                    existing_insurance=request.profile.existing_insurance
                )
                profile_analysis = await ai_advisor.analyze_profile(user_profile)
            except Exception as e:
                logger.warning(f"Profile analysis failed: {e}")

        # ============================================================
        # Step 5: LLM explains WHY — detailed explanation (Optional)
        # ============================================================
        ai_powered = False

        if request.include_ai_explanation and ai_advisor and user_profile:
            try:
                rag_context = ""
                if rag_service and rag_service.is_available():
                    try:
                        # Keep query short — embedding tokenizers have token limits
                        # RAG needs keyword concepts, not the full goal sentence
                        money_goal_val = request.profile.money_goal or "mid_term"
                        rag_query = f"ลดหย่อนภาษี RMF ThaiESG TESGX กฎหมาย 2568 เงื่อนไขถอน {money_goal_val}"
                        retrieved_docs = await rag_service.retrieve_relevant_documents(rag_query, k=3)
                        if retrieved_docs:
                            rag_context = "\n".join([
                                doc.page_content for doc in retrieved_docs
                                if hasattr(doc, "page_content")
                            ])
                    except Exception as e:
                        logger.warning(f"RAG retrieval failed: {e}")

                ai_explanation = await ai_advisor.generate_recommendation_explanation(
                    profile=user_profile,
                    allocation=allocation,
                    tax_savings=savings,
                    year_breakdown=three_year,
                    recommended_funds=recommended_funds_for_plan,
                    income_growth_rate=income_growth_rate,
                    monthly_budget=monthly_budget_raw,
                    rag_context=rag_context,
                )

                recommended_plan["ai_explanation"] = ai_explanation
                ai_powered = True
                logger.info("AI recommendation explanation generated successfully")

            except Exception as e:
                logger.warning(f"AI explanation failed (returning without): {e}")

        # ============================================================
        # Build response
        # ============================================================
        return {
            "success": True,
            "ai_powered": ai_powered,
            "profile_analysis": profile_analysis,
            "tax_info": {
                "tax_bracket": tax_bracket,
                "deduction_limits": limits,
                "deduction_remaining": {
                    "rmf": remaining_rmf,
                    "thai_esg": remaining_thai_esg,
                    "total": remaining_rmf + remaining_thai_esg,
                },
            },
            "recommended_plan": recommended_plan,
            "recommended_funds": pre_funds,
            "disclaimer": "การลงทุนมีความเสี่ยง ผู้ลงทุนควรศึกษาข้อมูลก่อนตัดสินใจลงทุน",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimize failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))


def _generate_action_steps(
    strategy: str,
    rmf_amount: float,
    thai_esg_amount: float,
    monthly_investment: float,
) -> list:
    """สร้างขั้นตอนแนะนำจริงๆ ตาม strategy"""
    steps = []
    if strategy == "tax_max":
        if rmf_amount > 0:
            steps.append(f"ลงทุน RMF ฿{rmf_amount:,.0f}/ปี — DCA เดือนละ ฿{rmf_amount/12:,.0f}")
        if thai_esg_amount > 0:
            steps.append(f"ลงทุน ThaiESG ฿{thai_esg_amount:,.0f}/ปี ควบคู่กัน")
        steps.append("บันทึกหลักฐานการลงทุนและยื่นลดหย่อนก่อน 31 ธ.ค.")
    elif strategy == "balanced":
        if rmf_amount > 0:
            steps.append(f"ลงทุน RMF ฿{rmf_amount:,.0f}/ปี สม่ำเสมอ (เดือนละ ฿{rmf_amount/12:,.0f})")
        if thai_esg_amount > 0:
            steps.append(f"จับคู่ ThaiESG ฿{thai_esg_amount:,.0f}/ปี พร้อมกัน")
        steps.append("ทบทวนและปรับแผนทุกต้นปีเมื่อรายได้เปลี่ยน")
    elif strategy == "conservative":
        if thai_esg_amount > 0:
            steps.append(f"เริ่มด้วย ThaiESG ฿{thai_esg_amount:,.0f}/ปี ก่อน (ระยะถือสั้นกว่า RMF)")
        if rmf_amount > 0:
            steps.append(f"เพิ่ม RMF ฿{rmf_amount:,.0f}/ปี เมื่อพร้อมล็อคเงินระยะยาว")
        steps.append("รักษาสภาพคล่องไว้ก่อน เพิ่มลงทุนเมื่อรายได้มั่นคงขึ้น")
    return steps


def _generate_pros_cons(
    strategy: str,
    total_investment: float,
    tax_saved: float,
    cash_remaining: float,
    available_budget: float,
    limits: Dict,
    cumulative_tax_saved_3y: float = 0,
) -> tuple:
    """Generate 3-year-aware pros and cons for each scenario"""
    pros = []
    cons = []

    total_limit = limits.get('total_potential', limits.get('rmf_max', 0) + limits.get('thai_esg_max', 0))
    utilization = total_investment / total_limit if total_limit > 0 else 0

    if strategy == "tax_max":  # ลดหย่อนสูงสุด
        if cumulative_tax_saved_3y > 0:
            pros.append(f"รวม 3 ปี ประหยัดภาษีได้ ฿{cumulative_tax_saved_3y:,.0f}")
        if tax_saved > 0:
            pros.append(f"ปีนี้ประหยัดภาษีได้ ฿{tax_saved:,.0f}")
        if utilization > 0.7:
            pros.append("ใช้สิทธิลดหย่อนเกือบเต็มที่")
        if cash_remaining < available_budget * 0.3:
            cons.append("เงินสดเหลือน้อย ต้องวางแผนค่าใช้จ่ายดี")
        cons.append("ต้องถือ RMF ถึงอายุ 55 ปี และ ThaiESG 5 ปี (เงินลงทุนตั้งแต่ปี 2567)")

    elif strategy == "balanced":  # สมดุล
        if cumulative_tax_saved_3y > 0:
            pros.append(f"รวม 3 ปี ประหยัดภาษีได้ ฿{cumulative_tax_saved_3y:,.0f}")
        if tax_saved > 0:
            pros.append(f"ปีนี้ประหยัดภาษีได้ ฿{tax_saved:,.0f}")
        pros.append("ยังมีเงินสดเหลือใช้จ่ายในชีวิตประจำวัน")
        cons.append("ประหยัดภาษีได้น้อยกว่าแผนลดหย่อนสูงสุด")
        cons.append("สะสมสิทธิลดหย่อนได้ช้ากว่าแผน 1")

    elif strategy == "conservative":  # ยืดหยุ่น
        if cash_remaining > 0:
            pros.append(f"เหลือเงินสด ฿{cash_remaining:,.0f}/ปี พร้อมรับเหตุการณ์ชีวิต")
        pros.append("ยืดหยุ่นสูง เหมาะกับช่วงเปลี่ยนแปลงในชีวิต")
        if tax_saved > 0:
            pros.append(f"ยังประหยัดภาษีได้ ฿{tax_saved:,.0f}/ปี")
        cons.append("ใช้สิทธิลดหย่อนได้น้อยกว่าแผนอื่น")
        cons.append("ไม่ได้ใช้สิทธิลดหย่อนเต็มที่")

    return pros, cons


# ============================================================
# Export router setup function
# ============================================================

def get_router():
    """Get the router with services initialized"""
    return router
