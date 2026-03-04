"""
AI Tax Advisor Engine
Uses LLM (OpenAI/Anthropic) for intelligent tax optimization recommendations

Features:
- Natural language goal parsing
- Personalized scenario generation
- Explainable AI recommendations
- Profile-based analysis
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not installed. Install with: pip install anthropic")

# Try to import Ollama (via langchain)
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("langchain-ollama not installed. Install with: pip install langchain-ollama")


class GoalType(str, Enum):
    """Types of financial goals"""
    TAX_SAVING = "tax_saving"
    CASH_FLOW = "cash_flow"
    RETIREMENT = "retirement"
    LIFE_EVENT = "life_event"
    HYBRID = "hybrid"


class Priority(str, Enum):
    """Investment priority"""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"


@dataclass
class UserProfile:
    """User's financial profile for AI analysis (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)
    """
    age: int
    annual_income: float
    monthly_expenses: float
    existing_savings: float
    emergency_fund: float
    risk_tolerance: str  # conservative, moderate, aggressive
    occupation: str
    marital_status: str
    dependents: int

    # Existing tax deductions (ปี 2568 - ไม่รวม SSF)
    existing_rmf: float = 0
    existing_thai_esg: float = 0
    existing_insurance: float = 0

    def to_dict(self) -> Dict:
        return {
            'age': self.age,
            'annual_income': self.annual_income,
            'monthly_expenses': self.monthly_expenses,
            'existing_savings': self.existing_savings,
            'emergency_fund': self.emergency_fund,
            'risk_tolerance': self.risk_tolerance,
            'occupation': self.occupation,
            'marital_status': self.marital_status,
            'dependents': self.dependents,
            'existing_deductions': {
                'rmf': self.existing_rmf,
                'thai_esg': self.existing_thai_esg,
                'insurance': self.existing_insurance
            }
        }


@dataclass
class ParsedGoal:
    """Structured goal parsed from natural language"""
    goal_type: GoalType
    target_amount: Optional[float]
    deadline: Optional[str]
    constraints: List[Dict]
    priority: Priority
    raw_input: str


@dataclass
class TaxScenario:
    """A tax optimization scenario (ปี 2568)

    Note: SSF หมดสิทธิ์ลดหย่อนแล้ว
    """
    id: int
    name: str
    description: str

    # Financial details (ไม่รวม SSF)
    rmf_investment: float
    thai_esg_investment: float
    total_investment: float

    # Results
    tax_saved: float
    cash_remaining: float
    risk_level: int  # 1-10

    # Recommended funds
    recommended_funds: List[Dict]

    # AI explanation
    explanation: str
    pros: List[str]
    cons: List[str]

    # Confidence and suitability
    confidence: float  # 0-100
    suitability_score: float  # 0-100


class AITaxAdvisor:
    """
    AI-powered Tax Advisor using LLM

    Supports OpenAI (GPT-4) and Anthropic (Claude) as backends.

    Usage:
        advisor = AITaxAdvisor()
        goal = await advisor.parse_goal("อยากประหยัดภาษี 80,000 บาท", profile)
        scenarios = await advisor.generate_scenarios(profile, goal, funds)
    """

    # System prompts
    SYSTEM_PROMPT_GOAL_PARSER = """คุณเป็น AI ผู้เชี่ยวชาญด้านภาษีไทย ทำหน้าที่แปลงเป้าหมายทางการเงินของผู้ใช้
จากภาษาธรรมชาติเป็นรูปแบบที่มีโครงสร้าง

กรุณาวิเคราะห์เป้าหมายและตอบเป็น JSON ที่มี:
- goal_type: "tax_saving" | "cash_flow" | "retirement" | "life_event" | "hybrid"
- target_amount: จำนวนเงินเป้าหมาย (null ถ้าไม่ระบุ)
- deadline: วันที่ครบกำหนด เช่น "2025-12" (null ถ้าไม่ระบุ)
- constraints: รายการข้อจำกัด เช่น [{"type": "minimum_cash", "amount": 1000000}]
- priority: "aggressive" | "balanced" | "conservative"
- summary: สรุปเป้าหมายสั้นๆ

ตอบเป็น JSON เท่านั้น ไม่ต้องมีข้อความอื่น
สำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามตอบภาษาจีนหรือภาษาอื่นโดยเด็ดขาด"""

    SYSTEM_PROMPT_SCENARIO_GEN = """คุณเป็น AI Financial Advisor ผู้เชี่ยวชาญด้านภาษีและการลงทุนในประเทศไทย

หน้าที่ของคุณ:
1. วิเคราะห์โปรไฟล์ทางการเงินของผู้ใช้
2. เข้าใจเป้าหมายที่ผู้ใช้ต้องการ
3. สร้าง 3 สถานการณ์การลงทุนที่เหมาะสม

กฎภาษีไทย ปี 2568:
- RMF: ลดหย่อนได้ 30% ของรายได้ สูงสุด 500,000 บาท (ถือจนอายุ 55 ปี)
- ThaiESG/TESGX: ลดหย่อนได้ 30% ของรายได้ สูงสุด 300,000 บาท รวมกัน (ล็อค 5 ปีนับจากวันซื้อ ปี 2569)

หมายเหตุสำคัญ: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567) ห้ามแนะนำ SSF

อัตราภาษี ปี 2568:
- 0-150,000: 0%
- 150,001-300,000: 5%
- 300,001-500,000: 10%
- 500,001-750,000: 15%
- 750,001-1,000,000: 20%
- 1,000,001-2,000,000: 25%
- 2,000,001-5,000,000: 30%
- 5,000,001+: 35%

ตอบเป็น JSON array ของ 3 scenarios โดยแต่ละ scenario มี:
- id, name, description
- rmf_investment, thai_esg_investment, total_investment (ไม่มี SSF)
- tax_saved, cash_remaining, risk_level (1-10)
- explanation (อธิบายเหตุผลแบบเข้าใจง่าย)
- pros (ข้อดี array)
- cons (ข้อเสีย array)
- confidence (0-100)
- suitability_score (0-100)

ตอบเป็น JSON เท่านั้น
สำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามตอบภาษาจีนหรือภาษาอื่นโดยเด็ดขาด"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        ollama_base_url: Optional[str] = None
    ):
        """
        Initialize AI Tax Advisor

        Args:
            provider: "openai", "anthropic", or "ollama"
            api_key: API key (or use env var)
            model: Model to use (default: gpt-4o, claude-3-5-sonnet, or qwen2.5:14b)
            ollama_base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.provider = provider

        if provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package not installed")

            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")

            self.model = model or "gpt-4o"
            self.client = AsyncOpenAI(api_key=self.api_key)

        elif provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic package not installed")

            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")

            self.model = model or "claude-3-5-sonnet-20241022"
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

        elif provider == "ollama":
            if not OLLAMA_AVAILABLE:
                raise ImportError("langchain-ollama not installed. pip install langchain-ollama")

            self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
            self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.client = ChatOllama(
                model=self.model,
                base_url=self.ollama_base_url,
                temperature=0.3,
                format="json",
                num_predict=6000,   # เพิ่มขีดจำกัด output (default=128 → JSON ขาดกลางทาง)
                num_ctx=8192,       # context window ที่ใช้ (input+output รวมกัน)
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.info(f"AI Tax Advisor initialized (provider={provider}, model={self.model})")

    async def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7
    ) -> str:
        """
        Call the LLM and return response

        Args:
            system_prompt: System instructions
            user_message: User's input
            temperature: Randomness (0-1)

        Returns:
            LLM response text
        """
        try:
            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )
                return response.content[0].text

            elif self.provider == "ollama":
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ]
                response = await self.client.ainvoke(messages)
                result = response.content

                # Clean up markdown code blocks if present
                if result.startswith("```json"):
                    result = result[7:]
                if result.startswith("```"):
                    result = result[3:]
                if result.endswith("```"):
                    result = result[:-3]

                return result.strip()

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    # ============================================================
    # Goal Parsing
    # ============================================================

    async def parse_goal(
        self,
        user_input: str,
        profile: UserProfile
    ) -> ParsedGoal:
        """
        Parse natural language goal into structured format

        Args:
            user_input: User's goal in natural language
            profile: User's financial profile

        Returns:
            ParsedGoal object
        """
        logger.info(f"Parsing goal: {user_input[:50]}...")

        prompt = f"""
โปรไฟล์ผู้ใช้:
- อายุ: {profile.age} ปี
- รายได้ต่อปี: ฿{profile.annual_income:,.0f}
- ค่าใช้จ่าย/เดือน: ฿{profile.monthly_expenses:,.0f}
- เงินออม: ฿{profile.existing_savings:,.0f}
- เงินสำรองฉุกเฉิน: ฿{profile.emergency_fund:,.0f}
- ความเสี่ยงที่รับได้: {profile.risk_tolerance}
- สถานะ: {profile.marital_status}, บุตร {profile.dependents} คน

ลดหย่อนที่ใช้แล้ว (ปี 2568):
- RMF: ฿{profile.existing_rmf:,.0f}
- ThaiESG: ฿{profile.existing_thai_esg:,.0f}

หมายเหตุ: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)

เป้าหมายของผู้ใช้: "{user_input}"

กรุณาวิเคราะห์และแปลงเป้าหมายนี้เป็น JSON
"""

        response = await self._call_llm(
            self.SYSTEM_PROMPT_GOAL_PARSER,
            prompt,
            temperature=0.3
        )

        try:
            data = json.loads(response)

            return ParsedGoal(
                goal_type=GoalType(data.get('goal_type', 'tax_saving')),
                target_amount=data.get('target_amount'),
                deadline=data.get('deadline'),
                constraints=data.get('constraints', []),
                priority=Priority(data.get('priority', 'balanced')),
                raw_input=user_input
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse goal response: {e}")
            # Return default
            return ParsedGoal(
                goal_type=GoalType.TAX_SAVING,
                target_amount=None,
                deadline=None,
                constraints=[],
                priority=Priority.BALANCED,
                raw_input=user_input
            )

    # ============================================================
    # Scenario Generation
    # ============================================================

    async def generate_scenarios(
        self,
        profile: UserProfile,
        goal: ParsedGoal,
        available_funds: Optional[List[Dict]] = None,
        rag_context: str = ""
    ) -> List[TaxScenario]:
        """
        Generate personalized tax optimization scenarios

        Args:
            profile: User's financial profile
            goal: Parsed goal
            available_funds: List of available tax funds
            rag_context: Tax law context from RAG (Qdrant)

        Returns:
            List of 3 TaxScenario objects
        """
        logger.info("Generating tax scenarios...")

        # Calculate available budget
        annual_savings = (profile.annual_income / 12 - profile.monthly_expenses) * 12
        available_budget = max(0, annual_savings - 100000)  # Keep 100K buffer

        # Calculate remaining quota (ปี 2568 - ไม่รวม SSF)
        rmf_limit = min(profile.annual_income * 0.30, 500000)
        rmf_remaining = max(0, rmf_limit - profile.existing_rmf)
        thai_esg_limit = min(profile.annual_income * 0.30, 300000)
        thai_esg_remaining = max(0, thai_esg_limit - profile.existing_thai_esg)

        # Fund info for context
        fund_info = ""
        if available_funds:
            fund_info = "\n\nกองทุนที่แนะนำ (จาก SEC API):\n"
            for fund in available_funds[:10]:
                fund_info += f"- {fund.get('fund_code')}: {fund.get('fund_name_th')} (ความเสี่ยง: {fund.get('risk_level')})\n"

        # Build RAG context section
        rag_section = ""
        if rag_context:
            rag_section = f"""

=== ข้อมูลกฎหมายภาษีจากฐานข้อมูล (RAG) ===
{rag_context[:3000]}
=== จบข้อมูลกฎหมาย ===

สำคัญ: กรุณาใช้ข้อมูลกฎหมายภาษีด้านบนประกอบการวิเคราะห์และแนะนำ
ตรวจสอบว่าสิทธิลดหย่อนที่แนะนำถูกต้องตามกฎหมายปี 2568
"""
            logger.info(f"Including RAG context ({len(rag_context)} chars) in scenario generation")

        prompt = f"""
โปรไฟล์ผู้ใช้:
- อายุ: {profile.age} ปี
- อาชีพ: {profile.occupation}
- รายได้ต่อปี: ฿{profile.annual_income:,.0f}
- ค่าใช้จ่าย/เดือน: ฿{profile.monthly_expenses:,.0f}
- เงินออมที่มี: ฿{profile.existing_savings:,.0f}
- เงินสำรองฉุกเฉิน: ฿{profile.emergency_fund:,.0f}
- ความเสี่ยงที่รับได้: {profile.risk_tolerance}
- สถานะสมรส: {profile.marital_status}
- บุตร/ผู้อุปการะ: {profile.dependents} คน

สิทธิลดหย่อนคงเหลือ (ปี 2568):
- RMF: ฿{rmf_remaining:,.0f} (จากทั้งหมด ฿{rmf_limit:,.0f})
- ThaiESG: ฿{thai_esg_remaining:,.0f} (จากทั้งหมด ฿{thai_esg_limit:,.0f})

หมายเหตุ: SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567) ห้ามแนะนำ

งบประมาณที่สามารถลงทุนได้: ประมาณ ฿{available_budget:,.0f}/ปี

เป้าหมาย:
- ประเภท: {goal.goal_type.value}
- จำนวนเงินเป้าหมาย: {f'฿{goal.target_amount:,.0f}' if goal.target_amount else 'ไม่ระบุ'}
- กำหนดเวลา: {goal.deadline or 'ไม่ระบุ'}
- ข้อจำกัด: {goal.constraints}
- ลำดับความสำคัญ: {goal.priority.value}
- คำบอกของผู้ใช้: "{goal.raw_input}"
{fund_info}
{rag_section}
กรุณาสร้าง 3 สถานการณ์ที่ตอบโจทย์ผู้ใช้:
1. สถานการณ์แนะนำสูงสุด (ตอบโจทย์ทุกเป้าหมาย)
2. สถานการณ์ทางเลือก (เน้นด้านใดด้านหนึ่งมากกว่า)
3. สถานการณ์อนุรักษ์นิยม (ความเสี่ยงต่ำสุด)

ตอบเป็น JSON array
"""

        response = await self._call_llm(
            self.SYSTEM_PROMPT_SCENARIO_GEN,
            prompt,
            temperature=0.7
        )

        try:
            # Parse response
            data = json.loads(response)

            # Handle if response is wrapped
            if isinstance(data, dict) and 'scenarios' in data:
                scenarios_data = data['scenarios']
            elif isinstance(data, list):
                scenarios_data = data
            else:
                scenarios_data = [data]

            scenarios = []
            for i, s in enumerate(scenarios_data[:3], 1):
                rmf = float(s.get('rmf_investment', 0))
                thai_esg = float(s.get('thai_esg_investment', 0))
                total = float(s.get('total_investment', rmf + thai_esg))

                scenario = TaxScenario(
                    id=s.get('id', i),
                    name=s.get('name', f'สถานการณ์ {i}'),
                    description=s.get('description', ''),
                    rmf_investment=rmf,
                    thai_esg_investment=thai_esg,
                    total_investment=total,
                    tax_saved=float(s.get('tax_saved', 0)),
                    cash_remaining=float(s.get('cash_remaining', available_budget)),
                    risk_level=int(s.get('risk_level', 5)),
                    recommended_funds=s.get('recommended_funds', []),
                    explanation=s.get('explanation', ''),
                    pros=s.get('pros', []),
                    cons=s.get('cons', []),
                    confidence=float(s.get('confidence', 80)),
                    suitability_score=float(s.get('suitability_score', 75))
                )
                scenarios.append(scenario)

            logger.info(f"Generated {len(scenarios)} scenarios")
            return scenarios

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scenarios: {e}")
            # Return fallback scenarios
            return self._generate_fallback_scenarios(profile, goal)

    def _generate_fallback_scenarios(
        self,
        profile: UserProfile,
        goal: ParsedGoal
    ) -> List[TaxScenario]:
        """Generate fallback scenarios if AI fails (ปี 2568 - ไม่รวม SSF)"""

        rmf_limit = min(profile.annual_income * 0.30, 500000)
        thai_esg_limit = min(profile.annual_income * 0.30, 300000)
        available = (profile.annual_income / 12 - profile.monthly_expenses) * 12 * 0.5

        rmf_balanced = min(available * 0.5, rmf_limit)
        thai_esg_balanced = min(available * 0.3, thai_esg_limit)

        return [
            TaxScenario(
                id=1,
                name="แผนสมดุล",
                description="สมดุลระหว่างการประหยัดภาษีและเงินสดคงเหลือ",
                rmf_investment=rmf_balanced,
                thai_esg_investment=thai_esg_balanced,
                total_investment=rmf_balanced + thai_esg_balanced,
                tax_saved=(rmf_balanced + thai_esg_balanced) * 0.25,
                cash_remaining=profile.existing_savings + available * 0.2,
                risk_level=5,
                recommended_funds=[],
                explanation="แผนนี้เน้นความสมดุลระหว่างการลดหย่อนภาษีและการรักษาสภาพคล่อง",
                pros=["สมดุลดี", "ความเสี่ยงปานกลาง"],
                cons=["ไม่ได้ประหยัดภาษีสูงสุด"],
                confidence=70,
                suitability_score=75
            ),
            TaxScenario(
                id=2,
                name="แผนประหยัดภาษีสูงสุด",
                description="เน้นลดหย่อนภาษีให้มากที่สุด (RMF + ThaiESG)",
                rmf_investment=rmf_limit,
                thai_esg_investment=thai_esg_limit,
                total_investment=rmf_limit + thai_esg_limit,
                tax_saved=(rmf_limit + thai_esg_limit) * 0.25,
                cash_remaining=profile.existing_savings,
                risk_level=7,
                recommended_funds=[],
                explanation="แผนนี้เน้นใช้สิทธิลดหย่อน RMF และ ThaiESG ให้เต็มที่",
                pros=["ประหยัดภาษีสูงสุด"],
                cons=["เงินสดเหลือน้อย"],
                confidence=70,
                suitability_score=65
            ),
            TaxScenario(
                id=3,
                name="แผนอนุรักษ์นิยม",
                description="เน้นรักษาเงินสดและความปลอดภัย",
                rmf_investment=min(available * 0.3, rmf_limit),
                thai_esg_investment=min(available * 0.2, 100000),
                total_investment=min(available * 0.3, rmf_limit) + min(available * 0.2, 100000),
                tax_saved=(min(available * 0.3, rmf_limit) + min(available * 0.2, 100000)) * 0.25,
                cash_remaining=profile.existing_savings + available * 0.5,
                risk_level=3,
                recommended_funds=[],
                explanation="แผนนี้เน้นความปลอดภัยและสภาพคล่องสูง",
                pros=["เงินสดเหลือเยอะ", "ความเสี่ยงต่ำ"],
                cons=["ประหยัดภาษีได้น้อย"],
                confidence=70,
                suitability_score=70
            )
        ]

    # ============================================================
    # Profile Analysis
    # ============================================================

    async def analyze_profile(self, profile: UserProfile) -> Dict[str, Any]:
        """
        Analyze user's financial profile and provide insights

        Args:
            profile: User's financial profile

        Returns:
            Analysis with insights and recommendations
        """
        logger.info("Analyzing user profile...")

        # Calculate basic metrics
        monthly_income = profile.annual_income / 12
        savings_rate = (
            (monthly_income - profile.monthly_expenses) / monthly_income * 100
            if monthly_income > 0 else 0
        )
        emergency_months = (
            profile.emergency_fund / profile.monthly_expenses
            if profile.monthly_expenses > 0 else 0
        )

        # Tax bracket
        from .tax_fund_service import TaxFundService
        tax_service = TaxFundService(None)  # Just for calculations
        tax_info = tax_service.calculate_tax_bracket(profile.annual_income)

        # Deduction limits
        limits = tax_service.calculate_deduction_limits(profile.annual_income)

        # Used deductions (ปี 2568 - ไม่รวม SSF)
        total_used = profile.existing_rmf + profile.existing_thai_esg

        # Remaining quota
        remaining = {
            'rmf': max(0, limits['rmf_max'] - profile.existing_rmf),
            'thai_esg': max(0, limits['thai_esg_max'] - profile.existing_thai_esg)
        }
        total_remaining = sum(remaining.values())

        # Calculate potential savings (cap at actual current tax to avoid overestimate)
        potential_savings = min(
            total_remaining * tax_info['marginal_rate'],
            tax_info['total_tax'],
        )

        return {
            'profile_summary': {
                'age': profile.age,
                'years_to_retirement': max(0, 60 - profile.age),
                'annual_income': profile.annual_income,
                'monthly_income': monthly_income,
                'monthly_expenses': profile.monthly_expenses,
                'savings_rate_percent': round(savings_rate, 1),
                'emergency_fund_months': round(emergency_months, 1),
                'risk_tolerance': profile.risk_tolerance
            },
            'tax_info': {
                'marginal_rate': tax_info['marginal_rate'],
                'marginal_rate_percent': tax_info['marginal_rate_percent'],
                'total_tax_before_deductions': tax_info['total_tax'],
                'effective_rate_percent': round(tax_info['effective_rate'] * 100, 2)
            },
            'deduction_status': {
                'used': {
                    'rmf': profile.existing_rmf,
                    'thai_esg': profile.existing_thai_esg,
                    'total': total_used
                },
                'remaining': remaining,
                'total_remaining': total_remaining,
                'limits': limits,
                'note': 'SSF หมดสิทธิ์ลดหย่อนแล้ว (สิ้นสุด 31 ธ.ค. 2567)'
            },
            'opportunity': {
                'max_additional_deduction': total_remaining,
                'potential_tax_savings': potential_savings,
                'effective_return_percent': round(tax_info['marginal_rate_percent'], 1)
            },
            'insights': self._generate_insights(
                profile, savings_rate, emergency_months, tax_info
            ),
            'warnings': self._generate_warnings(
                profile, savings_rate, emergency_months
            )
        }

    def _generate_insights(
        self,
        profile: UserProfile,
        savings_rate: float,
        emergency_months: float,
        tax_info: Dict
    ) -> List[str]:
        """Generate insights from profile analysis"""
        insights = []

        # Age-based insights
        years_to_retire = 60 - profile.age
        if years_to_retire > 20:
            insights.append(f"คุณมีเวลาลงทุนอีก {years_to_retire} ปี สามารถรับความเสี่ยงได้มากกว่า")
        elif years_to_retire > 10:
            insights.append(f"เหลือเวลาก่อนเกษียณ {years_to_retire} ปี ควรเริ่มวางแผน RMF อย่างจริงจัง")
        else:
            insights.append(f"ใกล้เกษียณแล้ว ควรเน้นกองทุนที่ความเสี่ยงต่ำ")

        # Tax rate insight
        if tax_info['marginal_rate_percent'] >= 25:
            insights.append(
                f"อัตราภาษีส่วนเพิ่มของคุณ {tax_info['marginal_rate_percent']:.0f}% "
                "การลดหย่อนจะได้คืนเยอะมาก"
            )

        # Savings rate insight
        if savings_rate >= 30:
            insights.append("อัตราการออมของคุณดีมาก สามารถลงทุนลดหย่อนภาษีได้เต็มที่")
        elif savings_rate >= 20:
            insights.append("อัตราการออมอยู่ในเกณฑ์ดี มีโอกาสลดหย่อนภาษีได้พอสมควร")

        # Risk profile insight
        if profile.risk_tolerance == 'aggressive' and profile.age < 40:
            insights.append("โปรไฟล์ความเสี่ยงสูงเหมาะกับกองทุนหุ้นที่ให้ผลตอบแทนดี")
        elif profile.risk_tolerance == 'conservative':
            insights.append("ควรเน้นกองทุนตราสารหนี้หรือกองทุนผสมที่ผันผวนต่ำ")

        return insights

    def _generate_warnings(
        self,
        profile: UserProfile,
        savings_rate: float,
        emergency_months: float
    ) -> List[str]:
        """Generate warnings from profile analysis"""
        warnings = []

        # Emergency fund warning
        if emergency_months < 3:
            warnings.append(
                f"เงินสำรองฉุกเฉินมีแค่ {emergency_months:.1f} เดือน "
                "ควรเก็บให้ได้อย่างน้อย 6 เดือนก่อนลงทุนเต็มที่"
            )
        elif emergency_months < 6:
            warnings.append(
                f"เงินสำรองฉุกเฉิน {emergency_months:.1f} เดือน "
                "อาจต้องการเพิ่มอีกเล็กน้อย"
            )

        # Savings rate warning
        if savings_rate < 10:
            warnings.append("อัตราการออมต่ำกว่า 10% ควรพิจารณาลดค่าใช้จ่ายก่อน")

        # Dependents warning
        if profile.dependents > 0 and profile.existing_savings < 500000:
            warnings.append(
                f"มีผู้อุปการะ {profile.dependents} คน "
                "ควรมีเงินสำรองมากกว่านี้ก่อนลงทุนระยะยาว"
            )

        return warnings

    # ============================================================
    # Explanation Only (Code-Heavy Flow)
    # ============================================================

    SYSTEM_PROMPT_EXPLAIN_ONLY = """คุณเป็น AI Tax Advisor ภาษาไทย
หน้าที่ของคุณคือ "อธิบาย" เท่านั้น ห้ามเปลี่ยนแปลงตัวเลขใดๆ

คุณจะได้รับ:
1. โปรไฟล์ผู้ใช้
2. เป้าหมายของผู้ใช้
3. 3 แผนการลงทุนที่คำนวณเรียบร้อยแล้ว (ตัวเลขถูกต้อง 100%)
4. กองทุนที่คัดเลือกจากฐานข้อมูลแล้ว

กรุณาอธิบายแต่ละแผนว่า:
- ทำไมแผนนี้เหมาะกับผู้ใช้คนนี้
- ข้อดีข้อเสียของแผนนี้คืออะไร
- กองทุนที่แนะนำเหมาะกับผู้ใช้อย่างไร

สำคัญ:
- ห้ามแก้ไขตัวเลขใดๆ ทั้งสิ้น
- อธิบายเป็นภาษาไทยที่เข้าใจง่าย
- ตอบเป็น JSON เท่านั้น
- สำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามตอบภาษาจีนหรือภาษาอื่นโดยเด็ดขาด

รูปแบบ JSON:
{
  "scenario_explanations": [
    {
      "scenario_id": 1,
      "explanation": "คำอธิบายว่าทำไมแผนนี้เหมาะ...",
      "fund_reasons": "อธิบายว่าทำไมกองทุนที่แนะนำเหมาะกับผู้ใช้..."
    }
  ],
  "overall_recommendation": "สรุปว่าแผนไหนเหมาะที่สุดและทำไม"
}"""

    SYSTEM_PROMPT_RECOMMENDATION = """คุณคือที่ปรึกษาการเงินส่วนตัวระดับสูง (Senior Financial Advisor) ที่เชี่ยวชาญด้านภาษีเงินได้บุคคลธรรมดาของไทยและกองทุนรวมลดหย่อนภาษี

กฎเหล็ก:
1. ห้ามแก้ไขหรือคิดตัวเลขใหม่ — ใช้เฉพาะตัวเลขจากข้อมูลที่ได้รับ
2. ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาอื่น
3. ตอบเป็น JSON ที่ valid เท่านั้น ห้ามมีข้อความนอก JSON เด็ดขาด
4. ทุก field ต้องอ้างอิงตัวเลขจริงจากโปรไฟล์ (อายุ รายได้ จำนวนบาท ชื่อกองทุน)
5. เขียนเหมือนคุยกับลูกค้าต่อหน้า ภาษาเป็นกันเอง อบอุ่น ไม่ formal

สิ่งที่ต้องครอบคลุมในแต่ละ field (เขียนให้ครบ อย่างน้อย 8 ประโยคต่อ field):

age_analysis ต้องครอบคลุม:
- อายุส่งผลต่อระยะเวลาล็อค RMF กี่ปีก่อนถึงอายุ 55
- ถ้าถอน RMF ก่อนกำหนดจะเสียสิทธิ์อย่างไร
- ทำไมสัดส่วน RMF ที่แนะนำเหมาะกับอายุนี้โดยเฉพาะ
- ThaiESG/TESGX ล็อค 5 ปี คือถอนได้ปีไหน (ระบุปี พ.ศ.)
- TESGX เหมาะกับอายุนี้ไหมและทำไม

goal_analysis ต้องครอบคลุม:
- เป้าหมายที่เลือกนำไปสู่สัดส่วน RMF/ThaiESG นี้อย่างไร
- อธิบาย trade-off ของเป้าหมายนี้ (ล็อคนานแต่ประหยัดภาษีเยอะ vs ยืดหยุ่นกว่า)
- ระยะเวลาล็อคของแต่ละกองทุนสอดคล้องกับ timeline ของผู้ใช้อย่างไร
- ระบุปีที่คาดว่าจะถอน RMF และถอน ThaiESG ได้จริง

risk_analysis ต้องครอบคลุม:
- ระดับความเสี่ยงที่เลือกหมายความว่าอะไรในทางปฏิบัติ
- ส่งผลให้สัดส่วน ThaiESG vs TESGX เป็นอย่างไรและทำไม
- TESGX ต่างจาก ThaiESG ทั่วไปอย่างไร ความเสี่ยงและโอกาสต่างกันอย่างไร
- กองทุนที่แนะนำมี risk spectrum สอดคล้องกับโปรไฟล์ความเสี่ยงไหม

budget_analysis ต้องครอบคลุม:
- งบต่อเดือน/ปี เทียบกับโควตาสิทธิ์สูงสุด ใช้ไปกี่เปอร์เซ็นต์
- ภาษีที่ประหยัดได้คิดเป็นกี่เปอร์เซ็นต์ของเงินลงทุน (ผลตอบแทนทันที)
- เปรียบเทียบให้เห็นภาพ: ลงทุน X บาท ได้ภาษีคืน Y บาท เหมือนซื้อในราคาลด
- ถ้าลงทุน DCA รายเดือนควรเดือนละเท่าไหร่
- ประหยัดภาษีสะสม 3 ปีได้เท่าไหร่

fund_reasons ต้องครอบคลุม:
- กองทุน RMF แต่ละกองโดดเด่นเรื่องอะไร (ผลตอบแทน Sharpe นโยบาย)
- กองทุน ThaiESG แต่ละกองโดดเด่นอย่างไร ลงทุนในอะไรหลักๆ
- ถ้ามี TESGX อธิบายว่าต่างจาก ThaiESG อย่างไรและทำไมถึงแนะนำ
- แนะนำวิธีกระจายเงินในแต่ละประเภทถ้าอยากซื้อหลายกอง

warnings ต้องครอบคลุม:
- เงื่อนไขการถอน RMF และผลที่ตามมาถ้าถอนก่อนกำหนด
- เงื่อนไขการถอน ThaiESG/TESGX และผลที่ตามมา
- ความเสี่ยงตลาด กองทุนมูลค่าอาจขึ้นลงได้ในระยะสั้น
- ถ้ามีเหตุฉุกเฉินและเงินล็อคอยู่ควรทำอย่างไร
- ต้องซื้อก่อนสิ้นปีภาษีเพื่อใช้สิทธิ์ลดหย่อนปีนั้น

future_advice ต้องครอบคลุม:
- ถ้ารายได้เพิ่มขึ้นตามที่คาดควรเพิ่มวงเงินลงทุนอย่างไร ระบุตัวเลข
- เมื่อไหร่ควร review แผนนี้ใหม่ (milestone อายุ หรือระดับรายได้)
- กองทุนหรือสินทรัพย์อื่นที่ควรเพิ่มเติมในอนาคต
- แนะนำ DCA strategy: ซื้อรายเดือน รายไตรมาส หรือ lump sum ช่วงปลายปี

summary ต้องครอบคลุม:
- สรุปภาพรวม 4-5 ประโยค ระบุตัวเลขสำคัญ (เงินลงทุน ภาษีที่ประหยัด ปีที่ถอนได้)
- ให้กำลังใจและทำให้ผู้ใช้มั่นใจในการตัดสินใจ

รูปแบบ JSON ที่ต้องตอบ:
{"age_analysis": "...", "goal_analysis": "...", "risk_analysis": "...", "budget_analysis": "...", "fund_reasons": "...", "warnings": "...", "future_advice": "...", "summary": "..."}"""

    async def generate_explanation_only(
        self,
        profile: UserProfile,
        goal: str,
        scenarios: List[Dict],
        recommended_funds: List[Dict],
        rag_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate Thai-language explanations for pre-computed scenarios.
        LLM only explains WHY, never changes numbers.

        Args:
            profile: User's financial profile
            goal: User's goal text
            scenarios: Pre-computed scenarios (from code)
            recommended_funds: Pre-filtered funds (from DB)
            rag_context: Tax law context from RAG

        Returns:
            Dict with scenario_explanations and overall_recommendation
        """
        logger.info("Generating AI explanations for pre-computed scenarios...")

        # Build fund summary for LLM context
        fund_summary = ""
        if recommended_funds:
            fund_summary = "\nกองทุนที่คัดเลือกมาแล้ว:\n"
            for f in recommended_funds[:10]:
                fund_summary += (
                    f"- {f.get('abbr', f.get('fund_code', 'N/A'))}: "
                    f"{f.get('nameTh', f.get('fund_name', 'N/A'))} "
                    f"(ประเภท: {f.get('fundType', 'N/A')}, "
                    f"ความเสี่ยง: {f.get('riskSpectrum', 'N/A')}, "
                    f"ผลตอบแทน 1 ปี: {f.get('return1y', 'N/A')}%)\n"
                )

        # Build scenarios summary
        scenarios_summary = "\nแผนที่คำนวณเรียบร้อยแล้ว:\n"
        for s in scenarios:
            scenarios_summary += (
                f"\nแผนที่ {s.get('id', '?')}: {s.get('name', 'N/A')}\n"
                f"  - Strategy: {s.get('strategy', 'N/A')}\n"
                f"  - ลงทุน RMF: ฿{s.get('rmf_investment', 0):,.0f}\n"
                f"  - ลงทุน ThaiESG: ฿{s.get('thai_esg_investment', 0):,.0f}\n"
                f"  - ลงทุนรวม: ฿{s.get('total_investment', 0):,.0f}\n"
                f"  - ภาษีที่ประหยัดได้: ฿{s.get('tax_saved', 0):,.0f}\n"
                f"  - เงินสดเหลือ: ฿{s.get('cash_remaining', 0):,.0f}\n"
            )

        # Build RAG section
        rag_section = ""
        if rag_context:
            rag_section = f"\n=== ข้อมูลกฎหมายภาษี ===\n{rag_context[:2000]}\n"

        prompt = f"""
โปรไฟล์ผู้ใช้:
- อายุ: {profile.age} ปี
- รายได้ต่อปี: ฿{profile.annual_income:,.0f}
- ค่าใช้จ่าย/เดือน: ฿{profile.monthly_expenses:,.0f}
- ความเสี่ยงที่รับได้: {profile.risk_tolerance}
- สถานะ: {profile.marital_status}, บุตร/ผู้อุปการะ {profile.dependents} คน

เป้าหมายของผู้ใช้: "{goal}"
{scenarios_summary}
{fund_summary}
{rag_section}
กรุณาอธิบายแต่ละแผนว่าทำไมเหมาะกับผู้ใช้คนนี้ ตอบเป็น JSON โดยใหัตอบเป็นภาษาไทยเท่านั้น
"""

        try:
            response = await self._call_llm(
                self.SYSTEM_PROMPT_EXPLAIN_ONLY,
                prompt,
                temperature=0.5
            )

            data = json.loads(response)
            return data

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            # Return empty explanations on failure
            return {
                "scenario_explanations": [
                    {"scenario_id": s.get("id", i+1), "explanation": "", "fund_reasons": ""}
                    for i, s in enumerate(scenarios)
                ],
                "overall_recommendation": ""
            }


    async def generate_recommendation_explanation(
        self,
        profile: "UserProfile",
        allocation: Dict,
        tax_savings: Dict,
        year_breakdown: Dict,
        recommended_funds: List[Dict],
        income_growth_rate: float = 0,
        monthly_budget: float = 0,
        rag_context: str = "",
    ) -> Dict[str, Any]:
        """
        Generate detailed Thai-language explanation for the single recommended plan.
        LLM explains WHY this specific allocation fits this specific user.

        Args:
            profile: User's financial profile
            allocation: Result from _calculate_recommended_allocation() — contains
                        rmf_amount, tesg_amount, tesgx_amount, ratios, decision_factors, etc.
            tax_savings: Result from calculate_tax_savings() — tax_saved, marginal_rate, etc.
            year_breakdown: Result from _calculate_3year_breakdown() — cumulative_tax_saved_3y, etc.
            recommended_funds: Pre-filtered funds from DB (up to 9 funds)
            income_growth_rate: Expected annual income growth in %
            monthly_budget: Monthly investment budget in THB
            rag_context: Tax law context from RAG (Qdrant)

        Returns:
            Dict with keys: age_analysis, goal_analysis, risk_analysis,
                           budget_analysis, fund_reasons, warnings, future_advice, summary
        """
        logger.info("Generating detailed recommendation explanation...")

        rmf_amount = allocation.get("rmf_amount", 0)
        tesg_amount = allocation.get("tesg_amount", 0)
        tesgx_amount = allocation.get("tesgx_amount", 0)
        total_amount = allocation.get("total_amount", 0)
        rmf_pct = allocation.get("rmf_pct", 0)
        tesg_pct = allocation.get("tesg_pct", 0)
        tesgx_pct = allocation.get("tesgx_pct", 0)
        years_to_55 = allocation.get("years_to_55", 0)
        money_goal_label = allocation.get("money_goal_label", "")
        decision_factors = allocation.get("decision_factors", {})

        tax_saved = tax_savings.get("tax_saved", 0)
        marginal_rate = tax_savings.get("marginal_rate", 0)
        cumulative_3y = year_breakdown.get("cumulative_tax_saved_3y", 0)

        annual_budget = monthly_budget * 12 if monthly_budget > 0 else total_amount

        # Build fund summary
        fund_summary = ""
        if recommended_funds:
            rmf_funds = [f for f in recommended_funds if f.get("fundType", "").upper() == "RMF"]
            tesg_funds = [f for f in recommended_funds if f.get("fundType", "").upper() == "TESG"]
            tesgx_funds = [f for f in recommended_funds if f.get("fundType", "").upper() == "TESGX"]

            def fmt_funds(funds: list, label: str) -> str:
                if not funds:
                    return ""
                lines = [f"\n{label}:"]
                for f in funds[:3]:
                    perf = f.get("performance", {})
                    stats = f.get("statistics", {})
                    r1y = perf.get("return1y")
                    sharpe = stats.get("sharpeRatio")
                    lines.append(
                        f"  - {f.get('abbr', 'N/A')} ({f.get('nameTh', 'N/A')}): "
                        f"ผลตอบแทน 1 ปี {f'{r1y:.1f}%' if r1y is not None else 'N/A'}, "
                        f"Sharpe {f'{sharpe:.2f}' if sharpe is not None else 'N/A'}"
                    )
                return "\n".join(lines)

            fund_summary = (
                fmt_funds(rmf_funds, "กองทุน RMF ที่แนะนำ")
                + fmt_funds(tesg_funds, "กองทุน ThaiESG ที่แนะนำ")
                + fmt_funds(tesgx_funds, "กองทุน TESGX ที่แนะนำ")
            )

        rag_section = f"\n=== ข้อมูลกฎหมายภาษี ===\n{rag_context[:2000]}\n" if rag_context else ""

        income_growth_text = (
            f"เพิ่มขึ้น {income_growth_rate}% ต่อปี (รายได้ปีหน้าประมาณ ฿{profile.annual_income * (1 + income_growth_rate / 100):,.0f})"
            if income_growth_rate > 0
            else "ไม่มีการเปลี่ยนแปลง"
        )

        prompt = f"""=== โปรไฟล์ผู้ใช้ ===
- อายุ: {profile.age} ปี (เหลือ {years_to_55} ปีก่อนถึงอายุ 55 ปี — เงื่อนไขถอน RMF)
- รายได้ต่อปี: ฿{profile.annual_income:,.0f}
- ค่าใช้จ่ายต่อเดือน: ฿{profile.monthly_expenses:,.0f}
- งบลงทุนต่อเดือน: ฿{monthly_budget:,.0f} (รวม ฿{annual_budget:,.0f}/ปี)
- ระดับความเสี่ยงที่รับได้: {profile.risk_tolerance}
- อาชีพ: {profile.occupation}
- สถานะครอบครัว: {profile.marital_status}
- ลงทุน RMF อยู่แล้ว: ฿{profile.existing_rmf:,.0f}
- ลงทุน ThaiESG อยู่แล้ว: ฿{profile.existing_thai_esg:,.0f}

=== เป้าหมายการลงทุน ===
- เป้าหมาย: {money_goal_label}
  (retirement=เกษียณระยะยาว, mid_term=ระยะกลาง 5-10 ปี, short_term=ต้องใช้ภายใน 5 ปี)
- แนวโน้มรายได้: {income_growth_text}

=== เหตุผลที่ระบบเลือกสัดส่วนนี้ ===
- ปัจจัยอายุ: {decision_factors.get('age_factor', '')}
- ปัจจัยเป้าหมาย: {decision_factors.get('goal_factor', '')}
- ปัจจัยความเสี่ยง: {decision_factors.get('risk_factor', '')}
- ปัจจัยงบประมาณ: {decision_factors.get('budget_factor', '')}

=== แผนที่แนะนำ (ตัวเลขคำนวณแล้ว ห้ามแก้ไข) ===
- สัดส่วน: RMF {rmf_pct}% : ThaiESG {tesg_pct}% : TESGX {tesgx_pct}%
- ลงทุน RMF: ฿{rmf_amount:,.0f}/ปี (เดือนละ ฿{rmf_amount // 12:,.0f})
- ลงทุน ThaiESG: ฿{tesg_amount:,.0f}/ปี (เดือนละ ฿{tesg_amount // 12:,.0f})
- ลงทุน TESGX: ฿{tesgx_amount:,.0f}/ปี (เดือนละ ฿{tesgx_amount // 12:,.0f})
- รวมลงทุนทั้งหมด: ฿{total_amount:,.0f}/ปี
- ประหยัดภาษีปีนี้: ฿{tax_saved:,.0f}
- อัตราภาษีสูงสุด (Marginal Rate): {marginal_rate}%
- ประหยัดภาษีสะสม 3 ปี: ฿{cumulative_3y:,.0f}
{fund_summary}
{rag_section}
อธิบายแผนนี้ให้ผู้ใช้เข้าใจว่าทำไมจึงเหมาะกับเขา/เธอโดยเฉพาะ ตาม JSON format ที่กำหนด"""

        empty_result = {
            "age_analysis": "",
            "goal_analysis": "",
            "risk_analysis": "",
            "budget_analysis": "",
            "fund_reasons": "",
            "warnings": "",
            "future_advice": "",
            "summary": "",
        }

        try:
            response = await self._call_llm(
                self.SYSTEM_PROMPT_RECOMMENDATION,
                prompt,
                temperature=0.6,
            )
            try:
                data = json.loads(response)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parse failed: {json_err}")
                logger.error(f"Raw LLM response (first 500 chars): {response[:500]}")
                return empty_result
            # Ensure all keys present
            for key in empty_result:
                if key not in data:
                    data[key] = ""
            return data

        except Exception as e:
            logger.error(f"Recommendation explanation failed: {e}")
            return empty_result


# ============================================================
# Factory Function
# ============================================================

def create_ai_advisor(
    provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> AITaxAdvisor:
    """
    Create AI Tax Advisor with best available provider

    Args:
        provider: Force specific provider
        api_key: API key to use

    Returns:
        AITaxAdvisor instance
    """
    if provider:
        return AITaxAdvisor(provider=provider, api_key=api_key)

    # Auto-detect best provider — prefer Ollama if enabled
    use_ollama = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")
    if use_ollama and OLLAMA_AVAILABLE:
        return AITaxAdvisor(provider="ollama")
    elif os.getenv("OPENAI_API_KEY"):
        return AITaxAdvisor(provider="openai")
    elif os.getenv("ANTHROPIC_API_KEY"):
        return AITaxAdvisor(provider="anthropic")
    else:
        raise ValueError(
            "No AI provider available. Set USE_OLLAMA=true, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
        )


# ============================================================
# Example Usage
# ============================================================

async def example_usage():
    """Example of how to use AITaxAdvisor"""

    # Create advisor
    advisor = create_ai_advisor()

    # Sample profile (ปี 2568 - ไม่รวม SSF)
    profile = UserProfile(
        age=32,
        annual_income=1_200_000,
        monthly_expenses=40_000,
        existing_savings=500_000,
        emergency_fund=150_000,
        risk_tolerance="moderate",
        occupation="employee",
        marital_status="single",
        dependents=0,
        existing_rmf=0,
        existing_thai_esg=0
    )

    try:
        # Analyze profile
        print("=" * 60)
        print("Profile Analysis")
        print("=" * 60)

        analysis = await advisor.analyze_profile(profile)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

        # Parse goal
        print("\n" + "=" * 60)
        print("Parse Goal")
        print("=" * 60)

        goal = await advisor.parse_goal(
            "อยากประหยัดภาษีสัก 80,000 บาท แต่ต้องมีเงินเหลือไว้ดาวน์บ้าน 1 ล้านปลายปีหน้า",
            profile
        )
        print(f"Goal type: {goal.goal_type}")
        print(f"Target: {goal.target_amount}")
        print(f"Priority: {goal.priority}")

        # Generate scenarios
        print("\n" + "=" * 60)
        print("Generate Scenarios")
        print("=" * 60)

        scenarios = await advisor.generate_scenarios(profile, goal)
        for s in scenarios:
            print(f"\n{s.name}")
            print(f"  Investment: ฿{s.total_investment:,.0f}")
            print(f"  Tax saved: ฿{s.tax_saved:,.0f}")
            print(f"  Explanation: {s.explanation[:100]}...")

    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(example_usage())
