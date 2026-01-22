"""
AI Optimizer API Endpoints
FastAPI routes for AI-powered tax optimization

Add to main.py:
    from app.routers import ai_optimizer
    app.include_router(ai_optimizer.router, prefix="/api/ai", tags=["AI Optimizer"])
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

logger = logging.getLogger(__name__)

# ============================================================
# Request/Response Models
# ============================================================

class UserProfileRequest(BaseModel):
    """User profile for AI analysis"""
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

    # Existing deductions
    existing_rmf: float = Field(default=0, ge=0, description="Existing RMF investment")
    existing_ssf: float = Field(default=0, ge=0, description="Existing SSF investment")
    existing_thai_esg: float = Field(default=0, ge=0, description="Existing ThaiESG investment")
    existing_insurance: float = Field(default=0, ge=0, description="Existing insurance premium")


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
    """Request for tax calculation"""
    annual_income: float = Field(..., gt=0)
    rmf_investment: float = Field(default=0, ge=0)
    ssf_investment: float = Field(default=0, ge=0)
    thai_esg_investment: float = Field(default=0, ge=0)
    existing_deductions: float = Field(default=0, ge=0)


class AllocationRequest(BaseModel):
    """Request for optimal allocation"""
    annual_income: float = Field(..., gt=0)
    available_budget: float = Field(..., gt=0)
    existing_rmf: float = Field(default=0, ge=0)
    existing_ssf: float = Field(default=0, ge=0)
    existing_thai_esg: float = Field(default=0, ge=0)
    priority: str = Field(
        default="balanced",
        description="Priority: tax_max, balanced, conservative"
    )


# ============================================================
# Global Services
# ============================================================

sec_service: Optional[SECService] = None
tax_fund_service: Optional[TaxFundService] = None
ai_advisor: Optional[AITaxAdvisor] = None


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
    global sec_service, tax_fund_service, ai_advisor

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

        # Initialize AI Advisor (if API key available)
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if openai_key:
            ai_advisor = AITaxAdvisor(provider="openai", api_key=openai_key)
            logger.info("✅ AI Advisor initialized with OpenAI")
        elif anthropic_key:
            ai_advisor = AITaxAdvisor(provider="anthropic", api_key=anthropic_key)
            logger.info("✅ AI Advisor initialized with Anthropic")
        else:
            logger.warning("⚠️ No LLM API key found. AI features will be limited.")
            ai_advisor = None

        logger.info("✅ AI Optimizer services initialized")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")

    yield

    # Shutdown
    if sec_service:
        await sec_service.close()
        logger.info("✅ SEC Service closed")


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
            "ai_provider": ai_advisor.provider if ai_advisor else None
        }
    }


# ============================================================
# Tax Fund Endpoints
# ============================================================

@router.get("/tax-funds")
async def get_tax_funds(
    category: Optional[str] = Query(
        None,
        description="Filter by category: RMF, SSF, ThaiESG"
    ),
    include_nav: bool = Query(False, description="Include NAV data"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results")
):
    """
    Get tax-saving funds from SEC API

    Returns filtered list of RMF, SSF, and ThaiESG funds.
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
            ssf_investment=request.ssf_investment,
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
            existing_ssf=request.existing_ssf,
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
                    "ssf": max(0, limits['ssf_max'] - profile.existing_ssf),
                    "thai_esg": max(0, limits['thai_esg_max'] - profile.existing_thai_esg)
                }
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
            existing_ssf=profile.existing_ssf,
            existing_thai_esg=profile.existing_thai_esg,
            existing_insurance=profile.existing_insurance
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
        raise HTTPException(503, "AI advisor not available. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

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
            existing_ssf=request.profile.existing_ssf,
            existing_thai_esg=request.profile.existing_thai_esg,
            existing_insurance=request.profile.existing_insurance
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
            existing_ssf=request.profile.existing_ssf,
            existing_thai_esg=request.profile.existing_thai_esg,
            existing_insurance=request.profile.existing_insurance
        )

        # Get available funds if requested
        available_funds = []
        if request.include_fund_recommendations and tax_fund_service:
            try:
                available_funds = await tax_fund_service.get_tax_funds(limit=20)
            except Exception as e:
                logger.warning(f"Could not fetch funds: {e}")

        # Generate scenarios
        if ai_advisor:
            # Parse goal first
            parsed_goal = await ai_advisor.parse_goal(request.goal, user_profile)

            # Generate AI scenarios
            scenarios = await ai_advisor.generate_scenarios(
                user_profile,
                parsed_goal,
                available_funds
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
                            "ssf": s.ssf_investment,
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
                existing_ssf=request.profile.existing_ssf,
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
    ssf_investment: float = Body(0, ge=0),
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
        # Calculate tax savings
        savings = tax_fund_service.calculate_tax_savings(
            annual_income=annual_income,
            rmf_investment=rmf_investment,
            ssf_investment=ssf_investment,
            thai_esg_investment=thai_esg_investment
        )

        # Calculate remaining budget
        total_investment = rmf_investment + ssf_investment + thai_esg_investment
        estimated_monthly_savings = annual_income / 12 * 0.3  # Assume 30% savings rate
        annual_savings = estimated_monthly_savings * 12
        cash_after_investment = annual_savings - total_investment + cash_reserve

        return {
            "success": True,
            "simulation": {
                "inputs": {
                    "annual_income": annual_income,
                    "rmf": rmf_investment,
                    "ssf": ssf_investment,
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
# Export router setup function
# ============================================================

def get_router():
    """Get the router with services initialized"""
    return router
