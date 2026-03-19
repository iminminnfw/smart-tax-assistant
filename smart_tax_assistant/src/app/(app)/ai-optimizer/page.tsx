'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { AppNavigation } from '@/components/AppNavigation';
import {
  Sparkles,
  Target,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Zap,
  Brain,
  Loader2,
  RefreshCw,
  Shield,
  BarChart3,
  Award,
  Building2
} from 'lucide-react';

// Backend API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_TAX_ADVISOR_API_URL || 'http://localhost:8000';

// Types matching the backend
interface UserProfile {
  annual_income: number;
  age: number;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  existing_rmf: number;       // ลงทุน RMF ไปแล้วปีนี้ (หักจากวงเงิน)
  existing_thai_esg: number;  // ลงทุน ThaiESG/TESGX ไปแล้วปีนี้
  current_deductions: {
    rmf?: number;
    ssf?: number;
    thai_esg?: number;
    life_insurance?: number;
    health_insurance?: number;
    pension_fund?: number;
    social_security?: number;
    provident_fund?: number;
  };
  has_spouse: boolean;
  num_children: number;
  num_parents: number;
  has_disability: boolean;
  monthly_expenses: number;
  emergency_fund: number;
  financial_goals: string[];
  available_budget: number;
  budget_period: 'monthly' | 'yearly';
  occupation: 'employee' | 'freelance' | 'business';
}

interface AIExplanation {
  age_analysis: string;
  goal_analysis: string;
  risk_analysis: string;
  budget_analysis: string;
  fund_reasons: string;
  warnings: string;
  future_advice: string;
  summary: string;
}

interface RecommendedPlan {
  rmf_amount: number;
  tesg_amount: number;
  tesgx_amount: number;
  total_amount: number;
  rmf_pct: number;
  tesg_pct: number;
  tesgx_pct: number;
  tax_before: number;
  tax_after: number;
  tax_saved: number;
  effective_return_percent: number;
  cash_remaining: number;
  monthly_investment: number;
  years_to_55: number;
  rmf_eligible: boolean;
  money_goal: string;
  money_goal_label: string;
  year_breakdown: {
    year: number;
    tax_year: number;
    income: number;
    rmf_investment: number;
    thai_esg_investment: number;
    total_investment: number;
    tax_saved: number;
  }[];
  cumulative_tax_saved_3y: number;
  cumulative_investment_3y: number;
  recommended_funds: RecommendedFund[];
  ai_explanation: AIExplanation | null;
}

interface ProfileAnalysis {
  tax_bracket: number;
  marginal_rate: number;
  current_tax: number;
  max_potential_savings: number;
  recommended_focus: string[];
  warnings: string[];
}

interface RecommendedFund {
  rank: number;
  fundId: string;
  abbr: string;
  nameTh: string;
  nameEn: string;
  amcNameTh: string;
  amcNameEn: string;
  fundType: string;
  policyDesc: string | null;
  riskSpectrum: number;
  riskLabel: string;
  riskLabelEn: string;
  performance: {
    return3m: number | null;
    return1y: number | null;
    return3y: number | null;
    return5y: number | null;
  };
  statistics: {
    sharpeRatio: number | null;
    maxDrawdown: number | null;
    alpha: number | null;
    beta: number | null;
  };
  topHoldings: { assetName: string; assetRatio: number | null }[];
  factsheet: { amcUrl: string | null; pdfUrl: string | null };
  score: number;
}

// Default profile for demo
const DEFAULT_PROFILE: UserProfile = {
  annual_income: 1200000,
  age: 35,
  risk_tolerance: 'moderate',
  existing_rmf: 0,
  existing_thai_esg: 0,
  current_deductions: {},
  has_spouse: false,
  num_children: 0,
  num_parents: 0,
  has_disability: false,
  monthly_expenses: 40000,
  emergency_fund: 0,
  financial_goals: [],
  available_budget: 0,
  budget_period: 'monthly',
  occupation: 'employee',
};

interface GoalForm {
  moneyGoal: 'retirement' | 'mid_term' | 'short_term';
  monthlyInvestmentBudget: number;   // งบลงทุนต่อเดือน (บาท)
  incomeGrowthRate: number;          // expected annual income growth in %
}

const MONEY_GOAL_OPTIONS = [
  {
    value: 'retirement',
    label: 'เก็บยาวเพื่อเกษียณ',
    description: 'ไม่รีบถอน ยอมล็อคเงินระยะยาวเพื่อผลตอบแทนสูงสุด',
    icon: '🏖️',
  },
  {
    value: 'mid_term',
    label: 'ลดหย่อน + ถอนได้ในระยะกลาง (5-10 ปี)',
    description: 'ต้องการลดหย่อนภาษีแต่ยังต้องการสภาพคล่องในอนาคต',
    icon: '⚖️',
  },
  {
    value: 'short_term',
    label: 'ต้องใช้เงินก้อนในอนาคตอันใกล้',
    description: 'มีแผนใช้เงินภายใน 5 ปี เช่น ดาวน์บ้าน แต่งงาน',
    icon: '📅',
  },
] as const;

function buildGoalFromForm(form: GoalForm, profile: UserProfile): string {
  const goalLabel = MONEY_GOAL_OPTIONS.find(o => o.value === form.moneyGoal)?.label || '';
  const parts: string[] = [`เป้าหมาย: ${goalLabel}`];

  if (form.incomeGrowthRate > 0) {
    parts.push(`รายได้คาดว่าจะเพิ่มขึ้น ${form.incomeGrowthRate}% ต่อปี`);
  }

  if (form.monthlyInvestmentBudget > 0) {
    parts.push(`งบลงทุนต่อเดือน ${form.monthlyInvestmentBudget.toLocaleString('th-TH')} บาท`);
  }

  parts.push(`ระดับความเสี่ยง: ${profile.risk_tolerance}`);
  parts.push('ต้องการวางแผนภาษีและการลงทุนให้เหมาะสมกับโปรไฟล์');
  return parts.join(' | ');
}

const RISK_OPTIONS = [
  { value: 'conservative', label: 'ต่ำ', description: 'เน้นความปลอดภัย ผลตอบแทนต่ำ' },
  { value: 'moderate', label: 'ปานกลาง', description: 'สมดุลระหว่างความเสี่ยงและผลตอบแทน' },
  { value: 'aggressive', label: 'สูง', description: 'ยอมรับความเสี่ยงสูงเพื่อผลตอบแทนสูง' },
];

export default function AIOptimizerPage() {
  const router = useRouter();
  const { status } = useSession();

  // Profile state
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [showProfileForm, setShowProfileForm] = useState(true);

  // Goal & Results state
  const [userGoal, setUserGoal] = useState<string>('');
  const [goalForm, setGoalForm] = useState<GoalForm>({ moneyGoal: 'mid_term', monthlyInvestmentBudget: 0, incomeGrowthRate: 0 });
  const [recommendedPlan, setRecommendedPlan] = useState<RecommendedPlan | null>(null);
  const [profileAnalysis, setProfileAnalysis] = useState<ProfileAnalysis | null>(null);
  const [recommendedFunds, setRecommendedFunds] = useState<RecommendedFund[]>([]);
  const [expandedFund, setExpandedFund] = useState<string | null>(null);
  const [expandedExplanation, setExpandedExplanation] = useState<string | null>(null);
  const [taxInfo, setTaxInfo] = useState<{ deduction_remaining?: { rmf: number; thai_esg: number; total: number } } | null>(null);

  // Loading state
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);

  // Check authentication
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth');
    }
  }, [status, router]);

  // Load profile from database
  useEffect(() => {
    const loadProfile = async () => {
      if (status !== 'authenticated') return;

      try {
        setProfileLoading(true);
        const response = await fetch('/api/user/financial-profile');

        if (response.ok) {
          const data = await response.json();

          // Update profile with data from DB
          setProfile({
            annual_income: data.annual_income || DEFAULT_PROFILE.annual_income,
            age: data.age || DEFAULT_PROFILE.age,
            risk_tolerance: data.risk_tolerance || DEFAULT_PROFILE.risk_tolerance,
            existing_rmf: data.existing_rmf || 0,
            existing_thai_esg: data.existing_thai_esg || 0,
            current_deductions: data.current_deductions || {},
            has_spouse: data.has_spouse || false,
            num_children: data.num_children || 0,
            num_parents: data.num_parents || 0,
            has_disability: data.has_disability || false,
            monthly_expenses: data.monthly_expenses || DEFAULT_PROFILE.monthly_expenses,
            emergency_fund: data.emergency_fund || 0,
            financial_goals: data.financial_goals || [],
            available_budget: data.available_budget || 0,
            budget_period: data.budget_period || 'monthly',
            occupation: data.occupation || DEFAULT_PROFILE.occupation,
          });

        }
      } catch (err) {
        console.error('Failed to load profile:', err);
        // Keep default profile on error
      } finally {
        setProfileLoading(false);
      }
    };

    loadProfile();
  }, [status]);

  // Save profile to DB (background)
  const saveProfile = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/user/financial-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      if (!response.ok) {
        return false;
      }
      return true;
    } catch (err) {
      console.error('Error saving profile:', err);
      return false;
    }
  };

  // Unified optimize handler - 1 API call instead of 4
  const handleOptimize = async () => {
    setLoading(true);
    setLoadingStep(0);
    setError(null);

    const goal = buildGoalFromForm(goalForm, profile);
    setUserGoal(goal);

    try {
      // Save profile in background (don't block)
      saveProfile();

      // Step 1: Sending request
      setLoadingStep(1);

      const response = await fetch('/api/ai-optimizer/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile,
          goal,
          risk_tolerance: profile.risk_tolerance,
          fund_types: ['RMF', 'TESG', 'TESGX'],
          top_n_funds: 5,
          include_ai_explanation: true,
          money_goal: goalForm.moneyGoal,
          monthly_investment_budget: goalForm.monthlyInvestmentBudget > 0 ? goalForm.monthlyInvestmentBudget : null,
          income_growth_rate: goalForm.incomeGrowthRate,
        }),
      });

      // Step 2: Processing response
      setLoadingStep(2);


      if (!response.ok) {
        const errorData = await response.text();
        console.error('Optimize error:', response.status, errorData);
        throw new Error('ไม่สามารถวิเคราะห์ได้ กรุณาลองใหม่อีกครั้ง');
      }

      const data = await response.json();

      // Step 3: Map profile analysis
      setLoadingStep(3);
      if (data.tax_info) setTaxInfo(data.tax_info);

      // Map profile_analysis from backend
      if (data.profile_analysis) {
        // ai_advisor.analyze_profile() returns nested structure
        const pa = data.profile_analysis;
        setProfileAnalysis({
          tax_bracket: pa.tax_info?.marginal_rate_percent || 0,
          marginal_rate: pa.tax_info?.marginal_rate_percent || 0,
          current_tax: pa.tax_info?.total_tax_before_deductions || 0,
          max_potential_savings: pa.opportunity?.potential_tax_savings || 0,
          recommended_focus: [],
          warnings: pa.warnings || [],
        });
      } else if (data.tax_info) {
        // Fallback: construct from tax_info when AI advisor not available
        const ti = data.tax_info;
        setProfileAnalysis({
          tax_bracket: ti.tax_bracket?.marginal_rate_percent || 0,
          marginal_rate: ti.tax_bracket?.marginal_rate_percent || 0,
          current_tax: ti.tax_bracket?.total_tax || 0,
          max_potential_savings: ti.deduction_remaining?.total || 0,
          recommended_focus: [],
          warnings: [],
        });
      }

      // Step 4: Map recommended_plan from backend
      setLoadingStep(4);

      const rawPlan = data.recommended_plan;
      if (!rawPlan) {
        throw new Error('ไม่สามารถสร้างแผนการลงทุนได้');
      }

      const plan: RecommendedPlan = {
        rmf_amount: rawPlan.rmf_amount || 0,
        tesg_amount: rawPlan.tesg_amount || 0,
        tesgx_amount: rawPlan.tesgx_amount || 0,
        total_amount: rawPlan.total_amount || 0,
        rmf_pct: rawPlan.rmf_pct || 0,
        tesg_pct: rawPlan.tesg_pct || 0,
        tesgx_pct: rawPlan.tesgx_pct || 0,
        tax_before: rawPlan.tax_before || 0,
        tax_after: rawPlan.tax_after || 0,
        tax_saved: rawPlan.tax_saved || 0,
        effective_return_percent: rawPlan.effective_return_percent || 0,
        cash_remaining: rawPlan.cash_remaining || 0,
        monthly_investment: rawPlan.monthly_investment || 0,
        years_to_55: rawPlan.years_to_55 || 0,
        rmf_eligible: rawPlan.rmf_eligible ?? true,
        money_goal: rawPlan.money_goal || 'mid_term',
        money_goal_label: rawPlan.money_goal_label || '',
        year_breakdown: rawPlan.year_breakdown || [],
        cumulative_tax_saved_3y: rawPlan.cumulative_tax_saved_3y || 0,
        cumulative_investment_3y: rawPlan.cumulative_investment_3y || 0,
        recommended_funds: (rawPlan.recommended_funds || []).map((f: any) => ({
          rank: f.rank || 0,
          fundId: f.fundId || '',
          abbr: f.abbr || '',
          nameTh: f.nameTh || '',
          nameEn: f.nameEn || '',
          amcNameTh: f.amcNameTh || '',
          amcNameEn: f.amcNameEn || '',
          fundType: f.fundType || '',
          policyDesc: f.policyDesc || null,
          riskSpectrum: f.riskSpectrum || 0,
          riskLabel: f.riskLabel || '',
          riskLabelEn: f.riskLabelEn || '',
          performance: f.performance || { return3m: null, return1y: null, return3y: null, return5y: null },
          statistics: f.statistics || { sharpeRatio: null, maxDrawdown: null, alpha: null, beta: null },
          topHoldings: f.topHoldings || [],
          factsheet: f.factsheet || { amcUrl: null, pdfUrl: null },
          score: f.score || 0,
        })),
        ai_explanation: rawPlan.ai_explanation || null,
      };

      setRecommendedPlan(plan);

      // Map recommended funds from enriched DB data
      const funds: RecommendedFund[] = (data.recommended_funds || []).map((f: any) => ({
        rank: f.rank || 0,
        fundId: f.fundId || '',
        abbr: f.abbr || '',
        nameTh: f.nameTh || '',
        nameEn: f.nameEn || '',
        amcNameTh: f.amcNameTh || '',
        amcNameEn: f.amcNameEn || '',
        fundType: f.fundType || '',
        policyDesc: f.policyDesc || null,
        riskSpectrum: f.riskSpectrum || 0,
        riskLabel: f.riskLabel || '',
        riskLabelEn: f.riskLabelEn || '',
        performance: f.performance || { return3m: null, return1y: null, return3y: null, return5y: null },
        statistics: f.statistics || { sharpeRatio: null, maxDrawdown: null, alpha: null, beta: null },
        topHoldings: f.topHoldings || [],
        factsheet: f.factsheet || { amcUrl: null, pdfUrl: null },
        score: f.score || 0,
      }));
      setRecommendedFunds(funds);

      // Step 5: Complete
      setLoadingStep(5);
      setShowProfileForm(false);

    } catch (err: any) {
      console.error('Error:', err);
      setError(err.message || 'เกิดข้อผิดพลาดในการวิเคราะห์');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setRecommendedPlan(null);
    setProfileAnalysis(null);
    setRecommendedFunds([]);
    setExpandedFund(null);
    setExpandedExplanation(null);
    setUserGoal('');
    setShowProfileForm(true);
    setError(null);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('th-TH').format(amount);
  };

  // Loading state for auth
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <AppNavigation />

      <div className="bg-slate-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-slate-800">
                  AI Tax Optimizer
                </h1>
                <p className="text-slate-600">ให้ AI วิเคราะห์และแนะนำแผนภาษีที่เหมาะกับคุณ</p>
              </div>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-800">
                <strong>เกิดข้อผิดพลาด:</strong> {error}
              </div>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                ✕
              </button>
            </div>
          )}

          {showProfileForm && !recommendedPlan ? (
            <>
              {/* Input Form — Simple 6-field card */}
              <div className="max-w-2xl mx-auto">
                <div className="bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-5 h-5 text-blue-600" />
                    <h2 className="text-lg font-semibold text-slate-800">ข้อมูลสำหรับวิเคราะห์</h2>
                    {profileLoading && <Loader2 className="w-4 h-4 animate-spin text-blue-600 ml-auto" />}
                  </div>
                  <p className="text-sm text-slate-500 mb-6">
                    AI จะคำนวณสัดส่วน RMF / ThaiESG / TESGX ที่เหมาะกับคุณที่สุด
                  </p>

                  <div className="space-y-5">

                    {/* Field 0: รายได้ต่อปี */}
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-1">
                        รายได้ต่อปี (บาท)
                        <span className="ml-1 text-xs font-normal text-slate-400">— ใช้คำนวณวงเงิน RMF / ThaiESG และภาษีที่ประหยัดได้</span>
                      </label>
                      <input
                        type="number"
                        value={profile.annual_income || ''}
                        onChange={(e) => setProfile({ ...profile, annual_income: e.target.value === '' ? 0 : Number(e.target.value) })}
                        placeholder="เช่น 1200000"
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                        disabled={loading}
                      />
                      {profile.annual_income > 0 && (
                        <p className="mt-1 text-xs text-slate-500">
                          วงเงิน RMF สูงสุด: ฿{Math.min(profile.annual_income * 0.30, 500000).toLocaleString('th-TH')} &nbsp;|&nbsp;
                          ThaiESG สูงสุด: ฿{Math.min(profile.annual_income * 0.30, 300000).toLocaleString('th-TH')}
                        </p>
                      )}
                    </div>

                    <div className="border-t border-slate-100" />

                    {/* Field 1: อายุ */}
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-1">
                        1. อายุ (ปี)
                        <span className="ml-1 text-xs font-normal text-slate-400">— กำหนดระยะเวลาที่ต้องล็อค RMF ถึงอายุ 55</span>
                      </label>
                      <input
                        type="number"
                        min="18"
                        max="70"
                        value={profile.age || ''}
                        onChange={(e) => setProfile({ ...profile, age: e.target.value === '' ? 0 : Number(e.target.value) })}
                        placeholder="เช่น 35"
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                        disabled={loading}
                      />
                      {profile.age > 0 && profile.age < 55 && (
                        <p className="mt-1 text-xs text-slate-500">
                          เหลืออีก <strong>{55 - profile.age} ปี</strong> ก่อนครบอายุ 55 (เงื่อนไขถอน RMF)
                        </p>
                      )}
                    </div>

                    {/* Field 2: เป้าหมายการใช้เงิน */}
                    <div>
                      <p className="text-sm font-semibold text-slate-700 mb-3">
                        2. เป้าหมายการใช้เงินก้อนนี้คืออะไร?
                        <span className="ml-1 text-xs font-normal text-slate-400">— กำหนดสัดส่วน RMF vs ThaiESG</span>
                      </p>
                      <div className="space-y-2">
                        {MONEY_GOAL_OPTIONS.map((opt) => (
                          <label
                            key={opt.value}
                            className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                              goalForm.moneyGoal === opt.value
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-slate-200 hover:border-slate-300'
                            }`}
                          >
                            <input
                              type="radio"
                              name="moneyGoal"
                              value={opt.value}
                              checked={goalForm.moneyGoal === opt.value}
                              onChange={() => setGoalForm({ ...goalForm, moneyGoal: opt.value })}
                              className="sr-only"
                              disabled={loading}
                            />
                            <span className="text-xl mt-0.5 flex-shrink-0">{opt.icon}</span>
                            <div>
                              <p className="font-medium text-slate-800 text-sm">{opt.label}</p>
                              <p className="text-xs text-slate-500">{opt.description}</p>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Field 3: งบลงทุนต่อเดือน */}
                    <div>
                      <p className="text-sm font-semibold text-slate-700 mb-1">
                        3. งบลงทุนต่อเดือนสำหรับกองทุนลดหย่อนภาษี (บาท)
                      </p>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-2">
                        <p className="text-xs text-blue-700">
                          💡 <strong>วิธีคำนวณ:</strong> รายได้/เดือน − ค่าใช้จ่ายรายเดือน − เงินออมฉุกเฉิน = งบที่พร้อมลงทุน
                        </p>
                      </div>
                      <input
                        type="number"
                        min="0"
                        value={goalForm.monthlyInvestmentBudget || ''}
                        onChange={(e) => setGoalForm({ ...goalForm, monthlyInvestmentBudget: e.target.value === '' ? 0 : Number(e.target.value) })}
                        disabled={loading}
                        placeholder="เช่น 10000 บาท/เดือน"
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                      />
                      {goalForm.monthlyInvestmentBudget > 0 ? (
                        <p className="text-xs text-blue-600 mt-1">
                          = ฿{(goalForm.monthlyInvestmentBudget * 12).toLocaleString('th-TH')} ต่อปี
                        </p>
                      ) : (
                        <p className="text-xs text-slate-400 mt-1">ถ้าปล่อยว่าง ระบบจะคำนวณงบให้อัตโนมัติ</p>
                      )}
                    </div>

                    {/* Field 4: ระดับความเสี่ยง */}
                    <div>
                      <p className="text-sm font-semibold text-slate-700 mb-2">
                        4. ระดับความเสี่ยงที่รับได้
                        <span className="ml-1 text-xs font-normal text-slate-400">— กล้าเสี่ยง = เพิ่ม TESGX</span>
                      </p>
                      <div className="grid grid-cols-3 gap-2">
                        {RISK_OPTIONS.map((option) => (
                          <label
                            key={option.value}
                            className={`flex flex-col items-center p-3 border rounded-lg cursor-pointer transition-colors text-center ${
                              profile.risk_tolerance === option.value
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-slate-200 hover:border-slate-300'
                            }`}
                          >
                            <input
                              type="radio"
                              name="risk"
                              value={option.value}
                              checked={profile.risk_tolerance === option.value}
                              onChange={(e) => setProfile({ ...profile, risk_tolerance: e.target.value as any })}
                              className="sr-only"
                              disabled={loading}
                            />
                            <p className="font-medium text-slate-800 text-sm">{option.label}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{option.description}</p>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Field 5: แนวโน้มรายได้ */}
                    <div>
                      <p className="text-sm font-semibold text-slate-700 mb-2">
                        5. รายได้คาดว่าจะเพิ่มขึ้นเท่าไหร่ต่อปี?
                        <span className="ml-1 text-xs font-normal text-slate-400">— ใช้คาดการณ์ภาษี 3 ปีข้างหน้า</span>
                      </p>
                      <div className="flex gap-2">
                        {[0, 3, 5, 10].map((rate) => (
                          <button
                            key={rate}
                            type="button"
                            onClick={() => setGoalForm({ ...goalForm, incomeGrowthRate: rate })}
                            disabled={loading}
                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                              goalForm.incomeGrowthRate === rate
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            {rate === 0 ? 'ไม่เพิ่ม' : `+${rate}%`}
                          </button>
                        ))}
                      </div>
                      {goalForm.incomeGrowthRate > 0 && profile.annual_income > 0 && (
                        <p className="text-xs text-slate-400 mt-2">
                          รายได้ปีหน้า ≈ ฿{Math.round(profile.annual_income * (1 + goalForm.incomeGrowthRate / 100)).toLocaleString('th-TH')}
                        </p>
                      )}
                    </div>

                    {/* Optional: ลงทุนไปแล้วปีนี้ */}
                    <div className="border border-dashed border-slate-300 rounded-lg p-4">
                      <p className="text-sm font-semibold text-slate-600 mb-1">
                        ลงทุน RMF / ThaiESG ไปแล้วปีนี้? <span className="font-normal text-slate-400">(ไม่บังคับ)</span>
                      </p>
                      <p className="text-xs text-slate-400 mb-3">ระบบจะหักออกจากวงเงินคงเหลือก่อนคำนวณ</p>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">RMF ที่ลงทุนแล้ว (บาท/ปี)</label>
                          <input
                            type="number"
                            min="0"
                            value={profile.existing_rmf || ''}
                            onChange={(e) => setProfile({ ...profile, existing_rmf: e.target.value === '' ? 0 : Number(e.target.value) })}
                            disabled={loading}
                            placeholder="0"
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800 text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">ThaiESG/TESGX แล้ว (บาท/ปี)</label>
                          <input
                            type="number"
                            min="0"
                            value={profile.existing_thai_esg || ''}
                            onChange={(e) => setProfile({ ...profile, existing_thai_esg: e.target.value === '' ? 0 : Number(e.target.value) })}
                            disabled={loading}
                            placeholder="0"
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800 text-sm"
                          />
                        </div>
                      </div>
                    </div>

                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={handleOptimize}
                    disabled={loading || profile.annual_income === 0}
                    className="mt-6 w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>AI กำลังวิเคราะห์...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5" />
                        <span>ให้ AI วิเคราะห์และสร้างแผน</span>
                      </>
                    )}
                  </button>
                  {profile.annual_income === 0 && (
                    <p className="text-xs text-center text-red-500 mt-2">กรุณากรอกรายได้ต่อปีก่อน</p>
                  )}

                  {/* Loading Steps */}
                  {loading && (
                    <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                        <p className="text-sm font-medium text-blue-800">AI กำลังทำงาน...</p>
                      </div>
                      <div className="space-y-2">
                        {[
                          'ส่งข้อมูลไปวิเคราะห์...',
                          'คำนวณภาษีและกรองกองทุนจากฐานข้อมูล...',
                          'คำนวณสัดส่วน RMF / ThaiESG / TESGX...',
                          'AI กำลังอธิบายเหตุผลแบบละเอียด...',
                          'เสร็จสิ้น!',
                        ].map((step, index) => (
                          <div key={index} className="flex items-center gap-2">
                            {loadingStep > index ? (
                              <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                            ) : loadingStep === index ? (
                              <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
                            ) : (
                              <div className="w-4 h-4 border-2 border-slate-300 rounded-full flex-shrink-0" />
                            )}
                            <span className={`text-xs ${
                              loadingStep > index ? 'text-green-700 font-medium' :
                              loadingStep === index ? 'text-blue-700 font-medium' :
                              'text-slate-400'
                            }`}>
                              {step}
                            </span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-600 transition-all duration-500"
                          style={{ width: `${(loadingStep / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Results Header */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-slate-800">
                        AI วิเคราะห์เสร็จแล้ว!
                      </h2>
                      <p className="text-slate-600">แผนที่แนะนำที่สุดสำหรับคุณ</p>
                    </div>
                  </div>
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2 text-sm font-medium"
                  >
                    <RefreshCw className="w-4 h-4" />
                    เริ่มใหม่
                  </button>
                </div>

                {/* User Goal Display */}
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-700 mb-1">
                    <strong>โปรไฟล์ที่วิเคราะห์:</strong>
                  </p>
                  <p className="text-slate-800 text-sm">{userGoal}</p>
                </div>
              </div>

              {/* Profile Analysis Summary */}
              {profileAnalysis && (
                <div className="bg-blue-600 rounded-xl p-6 mb-6 text-white">
                  <div className="flex items-start gap-4 mb-6">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Brain className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-2">สรุปการวิเคราะห์</h3>
                      <p className="text-white/90 leading-relaxed text-sm">
                        รายได้ ฿{formatCurrency(profile.annual_income)}/ปี อยู่ในอัตราภาษี {profileAnalysis.marginal_rate}%
                        สามารถประหยัดภาษีได้สูงสุด ฿{formatCurrency(profileAnalysis.max_potential_savings)}
                      </p>
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-white/10 rounded-lg p-5">
                    <div>
                      <p className="text-white/80 text-sm mb-1">ภาษีปัจจุบัน</p>
                      <p className="text-xl font-semibold">฿{formatCurrency(profileAnalysis.current_tax)}</p>
                    </div>
                    <div>
                      <p className="text-white/80 text-sm mb-1">อัตราภาษีสูงสุด</p>
                      <p className="text-xl font-semibold">{profileAnalysis.marginal_rate}%</p>
                    </div>
                    <div>
                      <p className="text-white/80 text-sm mb-1">ประหยัดได้สูงสุด</p>
                      <p className="text-xl font-semibold">฿{formatCurrency(profileAnalysis.max_potential_savings)}</p>
                    </div>
                  </div>

                  {/* Warnings */}
                  {profileAnalysis.warnings && profileAnalysis.warnings.length > 0 && (
                    <div className="mt-4 p-4 bg-white/10 rounded-lg">
                      <p className="text-sm text-white/90">
                        <strong>⚠️ ข้อควรระวัง:</strong>{' '}
                        {profileAnalysis.warnings.join(' • ')}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Recommended Funds Section */}
              {recommendedFunds.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center">
                      <Award className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-800">
                        กองทุนแนะนำ แยกตามประเภท
                      </h3>
                      <p className="text-sm text-slate-500">
                        Top 3 ต่อประเภท — คัดจาก SEC Thailand ตาม Sharpe Ratio และผลตอบแทนย้อนหลัง
                      </p>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {(['RMF', 'TESG', 'TESGX'] as const).map((fundTypeGroup) => {
                      const groupFunds = recommendedFunds.filter(f => f.fundType === fundTypeGroup);
                      if (groupFunds.length === 0) return null;
                      const groupCfg = {
                        RMF:   { label: 'RMF',      bg: 'bg-blue-50',    border: 'border-blue-200',   tag: 'bg-blue-100 text-blue-700',       headerBorder: 'border-blue-200' },
                        TESG:  { label: 'ThaiESG',  bg: 'bg-emerald-50', border: 'border-emerald-200', tag: 'bg-emerald-100 text-emerald-700', headerBorder: 'border-emerald-200' },
                        TESGX: { label: 'ThaiESGX', bg: 'bg-purple-50',  border: 'border-purple-200',  tag: 'bg-purple-100 text-purple-700',   headerBorder: 'border-purple-200' },
                      }[fundTypeGroup];
                      return (
                        <div key={fundTypeGroup}>
                          {/* Section Header */}
                          <div className={`flex items-center gap-2 mb-3 pb-2 border-b ${groupCfg.headerBorder}`}>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${groupCfg.tag}`}>
                              {groupCfg.label}
                            </span>
                            <span className="text-xs text-slate-400">Top {groupFunds.length}</span>
                          </div>
                          <div className="space-y-3">
                            {groupFunds.map((fund, idx) => {
                      const isExpanded = expandedFund === fund.fundId;
                      const riskColor = fund.riskSpectrum <= 3
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : fund.riskSpectrum <= 6
                          ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
                          : 'bg-red-100 text-red-800 border-red-200';

                      const typeColor = fundTypeGroup === 'RMF'
                        ? 'bg-blue-100 text-blue-700'
                        : fundTypeGroup === 'TESG'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-purple-100 text-purple-700';

                      return (
                        <div
                          key={fund.fundId}
                          className={`border rounded-xl p-4 cursor-pointer transition-all ${
                            isExpanded ? 'border-blue-400 ring-1 ring-blue-200 bg-blue-50/30' : 'border-slate-200 hover:border-slate-300'
                          }`}
                          onClick={() => setExpandedFund(isExpanded ? null : fund.fundId)}
                        >
                          {/* Fund Header */}
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-start gap-3 min-w-0">
                              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-bold text-sm">
                                {idx + 1}
                              </div>
                              <div className="min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <p className="font-semibold text-slate-800">{fund.abbr}</p>
                                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeColor}`}>
                                    {fundTypeGroup === 'TESG' ? 'ThaiESG' : fundTypeGroup === 'TESGX' ? 'ThaiESGX' : fundTypeGroup}
                                  </span>
                                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${riskColor}`}>
                                    <Shield className="w-3 h-3 inline mr-0.5" />
                                    ความเสี่ยง {fund.riskSpectrum} ({fund.riskLabel})
                                  </span>
                                </div>
                                <p className="text-sm text-slate-600 truncate mt-0.5">{fund.nameTh}</p>
                              </div>
                            </div>

                            {/* Performance Badge */}
                            <div className="text-right flex-shrink-0">
                              {fund.performance.return1y !== null && (
                                <div>
                                  <p className={`text-lg font-bold ${fund.performance.return1y >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {fund.performance.return1y >= 0 ? '+' : ''}{fund.performance.return1y.toFixed(2)}%
                                  </p>
                                  <p className="text-xs text-slate-500">ผลตอบแทน 1 ปี</p>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Expanded Details */}
                          {isExpanded && (
                            <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
                              {/* AMC Info */}
                              <div className="flex items-center gap-2 text-sm text-slate-600">
                                <Building2 className="w-4 h-4" />
                                <span>บลจ. {fund.amcNameTh}</span>
                              </div>

                              {/* Performance Grid */}
                              <div className="grid grid-cols-2 gap-3">
                                {[
                                  { label: 'ผลตอบแทน 3 เดือน', value: fund.performance.return3m },
                                  { label: 'ผลตอบแทน 1 ปี', value: fund.performance.return1y },
                                ].map((item) => (
                                  <div key={item.label} className="bg-slate-50 rounded-lg p-3 text-center">
                                    <p className="text-xs text-slate-500 mb-1">{item.label}</p>
                                    <p className={`text-base font-bold ${
                                      item.value === null ? 'text-slate-400' :
                                      item.value >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}>
                                      {item.value !== null
                                        ? `${item.value >= 0 ? '+' : ''}${item.value.toFixed(2)}%`
                                        : 'N/A'}
                                    </p>
                                  </div>
                                ))}
                              </div>

                              {/* Statistics */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {[
                                  { label: 'Sharpe Ratio', value: fund.statistics.sharpeRatio, format: (v: number) => v.toFixed(2) },
                                  { label: 'Max Drawdown', value: fund.statistics.maxDrawdown, format: (v: number) => `${v.toFixed(2)}%` },
                                  { label: 'Alpha', value: fund.statistics.alpha, format: (v: number) => v.toFixed(2) },
                                  { label: 'Beta', value: fund.statistics.beta, format: (v: number) => v.toFixed(2) },
                                ].map((item) => (
                                  <div key={item.label} className="bg-slate-50 rounded-lg p-3 text-center">
                                    <p className="text-xs text-slate-500 mb-1">{item.label}</p>
                                    <p className="text-sm font-semibold text-slate-800">
                                      {item.value !== null ? item.format(item.value) : 'N/A'}
                                    </p>
                                  </div>
                                ))}
                              </div>

                              {/* Top Holdings */}
                              {fund.topHoldings.length > 0 && (
                                <div>
                                  <p className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
                                    <BarChart3 className="w-4 h-4" />
                                    สินทรัพย์ที่ถือครอง Top 5
                                  </p>
                                  <div className="space-y-1.5">
                                    {fund.topHoldings.map((h, idx) => (
                                      <div key={idx} className="flex justify-between text-sm">
                                        <span className="text-slate-600 truncate mr-2">{h.assetName}</span>
                                        <span className="font-medium text-slate-800 flex-shrink-0">
                                          {h.assetRatio !== null ? `${h.assetRatio.toFixed(2)}%` : '-'}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Policy Description */}
                              {fund.policyDesc && (
                                <div className="bg-blue-50 rounded-lg p-3">
                                  <p className="text-xs text-blue-600 mb-1 font-medium">ประเภทกองทุน</p>
                                  <p className="text-sm text-slate-700">{fund.policyDesc}</p>
                                </div>
                              )}

                              {/* Factsheet Links */}
                              {(fund.factsheet.amcUrl || fund.factsheet.pdfUrl) && (
                                <div className="flex gap-2 pt-1">
                                  {fund.factsheet.amcUrl && (
                                    <a
                                      href={fund.factsheet.amcUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                      🌐 ดูข้อมูลกองทุน
                                    </a>
                                  )}
                                  {fund.factsheet.pdfUrl && (
                                    <a
                                      href={fund.factsheet.pdfUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700 transition-colors"
                                    >
                                      📄 PDF Factsheet
                                    </a>
                                  )}
                                </div>
                              )}
                            </div>
                          )}

                          {!isExpanded && (
                            <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                              {fund.performance.return3m !== null && (
                                <span>3 เดือน: <strong className={fund.performance.return3m >= 0 ? 'text-green-600' : 'text-red-600'}>
                                  {fund.performance.return3m >= 0 ? '+' : ''}{fund.performance.return3m.toFixed(2)}%
                                </strong></span>
                              )}
                              {fund.statistics.sharpeRatio !== null && (
                                <span>Sharpe: <strong>{fund.statistics.sharpeRatio.toFixed(2)}</strong></span>
                              )}
                              <span className="ml-auto text-slate-400">คลิกเพื่อดูเพิ่มเติม</span>
                            </div>
                          )}
                        </div>
                      );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Deduction Quota Remaining */}
              {taxInfo?.deduction_remaining && (
                <div className="bg-white border border-slate-200 rounded-xl p-4 mb-2 flex flex-wrap gap-4 items-center">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-slate-500" />
                    <span className="text-sm font-medium text-slate-700">สิทธิ์ลดหย่อนที่เหลือปีนี้</span>
                  </div>
                  <div className="flex gap-6 ml-auto">
                    <div className="text-center">
                      <p className="text-xs text-slate-400 mb-0.5">RMF</p>
                      <p className="font-bold text-slate-800">฿{formatCurrency(taxInfo.deduction_remaining.rmf)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-slate-400 mb-0.5">ThaiESG</p>
                      <p className="font-bold text-slate-800">฿{formatCurrency(taxInfo.deduction_remaining.thai_esg)}</p>
                    </div>
                    <div className="text-center border-l border-slate-200 pl-6">
                      <p className="text-xs text-slate-400 mb-0.5">รวมทั้งหมด</p>
                      <p className="font-bold text-blue-700">฿{formatCurrency(taxInfo.deduction_remaining.total)}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Recommended Plan Card */}
              {recommendedPlan && (
                <div className="space-y-6">

                  {/* Allocation Overview */}
                  <div className="bg-white rounded-xl border border-slate-200 p-6">
                    <div className="flex items-center gap-3 mb-5">
                      <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                        <Target className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-slate-800">แผนที่แนะนำ</h3>
                        <p className="text-sm text-slate-500">{recommendedPlan.money_goal_label}</p>
                      </div>
                    </div>

                    {/* Allocation Ratio Bar */}
                    <div className="mb-5">
                      <p className="text-sm font-medium text-slate-700 mb-2">สัดส่วนการลงทุน</p>
                      <div className="flex h-6 rounded-full overflow-hidden mb-2">
                        {recommendedPlan.rmf_pct > 0 && (
                          <div
                            className="bg-blue-500 flex items-center justify-center text-xs text-white font-bold"
                            style={{ width: `${recommendedPlan.rmf_pct}%` }}
                          >
                            {recommendedPlan.rmf_pct}%
                          </div>
                        )}
                        {recommendedPlan.tesg_pct > 0 && (
                          <div
                            className="bg-emerald-500 flex items-center justify-center text-xs text-white font-bold"
                            style={{ width: `${recommendedPlan.tesg_pct}%` }}
                          >
                            {recommendedPlan.tesg_pct}%
                          </div>
                        )}
                        {recommendedPlan.tesgx_pct > 0 && (
                          <div
                            className="bg-violet-500 flex items-center justify-center text-xs text-white font-bold"
                            style={{ width: `${recommendedPlan.tesgx_pct}%` }}
                          >
                            {recommendedPlan.tesgx_pct}%
                          </div>
                        )}
                      </div>
                      <div className="flex gap-4 text-xs">
                        {recommendedPlan.rmf_pct > 0 && (
                          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-500 inline-block" /> RMF</span>
                        )}
                        {recommendedPlan.tesg_pct > 0 && (
                          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> ThaiESG</span>
                        )}
                        {recommendedPlan.tesgx_pct > 0 && (
                          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-violet-500 inline-block" /> TESGX</span>
                        )}
                      </div>
                    </div>

                    {/* Amount Breakdown */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
                      {recommendedPlan.rmf_amount > 0 && (
                        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                          <p className="text-xs font-semibold text-blue-600 mb-1">RMF</p>
                          <p className="text-xl font-bold text-blue-900">฿{formatCurrency(recommendedPlan.rmf_amount)}</p>
                          <p className="text-xs text-blue-500 mt-0.5">฿{formatCurrency(Math.round(recommendedPlan.rmf_amount / 12))}/เดือน</p>
                          <p className="text-xs text-blue-400 mt-1">ล็อคถึงอายุ 55 ({recommendedPlan.years_to_55} ปี)</p>
                        </div>
                      )}
                      {recommendedPlan.tesg_amount > 0 && (
                        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
                          <p className="text-xs font-semibold text-emerald-600 mb-1">ThaiESG</p>
                          <p className="text-xl font-bold text-emerald-900">฿{formatCurrency(recommendedPlan.tesg_amount)}</p>
                          <p className="text-xs text-emerald-500 mt-0.5">฿{formatCurrency(Math.round(recommendedPlan.tesg_amount / 12))}/เดือน</p>
                          <p className="text-xs text-emerald-400 mt-1">ล็อค 5 ปีนับจากวันซื้อ</p>
                        </div>
                      )}
                      {recommendedPlan.tesgx_amount > 0 && (
                        <div className="bg-violet-50 border border-violet-100 rounded-xl p-4">
                          <p className="text-xs font-semibold text-violet-600 mb-1">TESGX</p>
                          <p className="text-xl font-bold text-violet-900">฿{formatCurrency(recommendedPlan.tesgx_amount)}</p>
                          <p className="text-xs text-violet-500 mt-0.5">฿{formatCurrency(Math.round(recommendedPlan.tesgx_amount / 12))}/เดือน</p>
                          <p className="text-xs text-violet-400 mt-1">ล็อค 5 ปีนับจากวันซื้อ | ความเสี่ยงสูง</p>
                        </div>
                      )}
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-green-50 rounded-xl p-3">
                        <div className="flex items-center gap-1.5 mb-1">
                          <TrendingUp className="w-3.5 h-3.5 text-green-600" />
                          <span className="text-xs text-green-700 font-medium">ลดภาษีปีนี้</span>
                        </div>
                        <p className="text-xl font-bold text-green-900">฿{formatCurrency(recommendedPlan.tax_saved)}</p>
                      </div>
                      <div className="bg-slate-50 rounded-xl p-3">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Zap className="w-3.5 h-3.5 text-slate-500" />
                          <span className="text-xs text-slate-600 font-medium">ลงทุน/เดือน</span>
                        </div>
                        <p className="text-xl font-bold text-slate-800">฿{formatCurrency(recommendedPlan.monthly_investment)}</p>
                      </div>
                      <div className="bg-amber-50 rounded-xl p-3">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Award className="w-3.5 h-3.5 text-amber-600" />
                          <span className="text-xs text-amber-700 font-medium">ผลตอบแทนทันที</span>
                        </div>
                        <p className="text-xl font-bold text-amber-900">{recommendedPlan.effective_return_percent.toFixed(1)}%</p>
                      </div>
                    </div>

                    {/* 3-Year Breakdown */}
                    {recommendedPlan.year_breakdown && recommendedPlan.year_breakdown.length > 0 && (
                      <div className="mt-5 border border-slate-200 rounded-xl p-4 bg-slate-50">
                        <div className="flex items-center gap-2 mb-4">
                          <BarChart3 className="w-4 h-4 text-slate-500" />
                          <span className="text-sm font-semibold text-slate-700">แผนภาษี 3 ปีข้างหน้า</span>
                        </div>
                        <div className="flex gap-2 items-stretch mb-4">
                          {recommendedPlan.year_breakdown.map((yr, idx) => (
                            <div key={yr.year} className="flex items-center gap-2 flex-1">
                              <div className="flex-1 bg-white border border-slate-200 rounded-lg p-3 shadow-sm">
                                <div className="inline-block bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded-full mb-2">
                                  ปี {yr.tax_year}
                                </div>
                                <div className="mb-2">
                                  <p className="text-xs text-slate-400 mb-0.5">ลงทุน</p>
                                  <p className="text-base font-bold text-slate-800">฿{formatCurrency(yr.total_investment)}</p>
                                </div>
                                <div className="border-t border-dashed border-slate-200 my-2" />
                                <div>
                                  <p className="text-xs text-slate-400 mb-0.5">ประหยัดภาษี</p>
                                  <p className="text-base font-bold text-emerald-600">฿{formatCurrency(yr.tax_saved)}</p>
                                </div>
                              </div>
                              {idx < recommendedPlan.year_breakdown.length - 1 && (
                                <span className="text-slate-300 text-lg font-light flex-shrink-0">›</span>
                              )}
                            </div>
                          ))}
                        </div>
                        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3 flex justify-between items-center">
                          <div>
                            <p className="text-xs text-slate-400">รวม 3 ปี ลงทุนทั้งหมด</p>
                            <p className="text-sm font-semibold text-slate-700">฿{formatCurrency(recommendedPlan.cumulative_investment_3y)}</p>
                          </div>
                          <div className="w-px h-8 bg-slate-200" />
                          <div className="text-right">
                            <p className="text-xs text-slate-400">รวม 3 ปี ประหยัดภาษีได้</p>
                            <p className="text-lg font-bold text-emerald-600">฿{formatCurrency(recommendedPlan.cumulative_tax_saved_3y)}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* AI Explanation Sections */}
                  {recommendedPlan.ai_explanation && (
                    <div className="bg-white rounded-xl border border-slate-200 p-6">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
                          <Brain className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-slate-800">AI อธิบายทำไมแผนนี้เหมาะกับคุณ</h3>
                          <p className="text-sm text-slate-500">วิเคราะห์จากโปรไฟล์และเป้าหมายของคุณโดยเฉพาะ</p>
                        </div>
                      </div>

                      {/* Summary — always visible */}
                      {recommendedPlan.ai_explanation.summary && (
                        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5 mb-5">
                          <p className="text-sm font-semibold text-indigo-700 mb-2">สรุป</p>
                          <p className="text-slate-800 leading-relaxed">{recommendedPlan.ai_explanation.summary}</p>
                        </div>
                      )}

                      {/* Explanation Sections — accordion */}
                      <div className="space-y-3">
                        {(
                          [
                            { key: 'age_analysis',    icon: '🎂', label: 'วิเคราะห์อายุ — ทำไมสัดส่วนนี้ถึงเหมาะ' },
                            { key: 'goal_analysis',   icon: '🎯', label: 'วิเคราะห์เป้าหมาย' },
                            { key: 'risk_analysis',   icon: '📊', label: 'วิเคราะห์ระดับความเสี่ยง' },
                            { key: 'budget_analysis', icon: '💰', label: 'วิเคราะห์งบประมาณและผลคืนภาษี' },
                            { key: 'fund_reasons',    icon: '🏦', label: 'ทำไมกองทุนที่แนะนำถึงเหมาะ' },
                            { key: 'warnings',        icon: '⚠️', label: 'ข้อควรระวังก่อนตัดสินใจ' },
                            { key: 'future_advice',   icon: '🚀', label: 'แนะนำการปรับแผนในอนาคต' },
                          ] as { key: keyof AIExplanation; icon: string; label: string }[]
                        ).map(({ key, icon, label }) => {
                          const text = recommendedPlan.ai_explanation![key];
                          if (!text) return null;
                          const isOpen = expandedExplanation === key;
                          return (
                            <div key={key} className="border border-slate-200 rounded-xl overflow-hidden">
                              <button
                                type="button"
                                onClick={() => setExpandedExplanation(isOpen ? null : key)}
                                className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
                              >
                                <span className="flex items-center gap-2 text-sm font-medium text-slate-700">
                                  <span>{icon}</span>
                                  {label}
                                </span>
                                <span className="text-slate-400 text-lg">{isOpen ? '▲' : '▼'}</span>
                              </button>
                              {isOpen && (
                                <div className="px-4 py-4 bg-white">
                                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{text}</p>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ===== Disclaimer ===== */}
              <div className="mt-6 border border-amber-300 bg-amber-50 rounded-xl p-5">
                <div className="flex items-start gap-3">
                  <span className="text-2xl flex-shrink-0">⚠️</span>
                  <div>
                    <p className="font-semibold text-amber-800 mb-1">
                      คำเตือนสำคัญ — โปรดอ่านก่อนตัดสินใจลงทุน
                    </p>
                    <p className="text-sm text-amber-700 leading-relaxed">
                      การแนะนำกองทุนข้างต้นเป็น <strong>การแนะนำเบื้องต้นเท่านั้น</strong>{' '}
                      จัดทำขึ้นเพื่อประกอบการพิจารณา ไม่ใช่คำแนะนำการลงทุนอย่างเป็นทางการ
                      กรุณา<strong>อ่านหนังสือชี้ชวน (Fund Factsheet)</strong> ของแต่ละกองทุนและศึกษาข้อมูลให้ครบถ้วนก่อนตัดสินใจลงทุนจริง
                    </p>
                    <ul className="mt-2 space-y-1 text-xs text-amber-700 list-disc list-inside">
                      <li>ผลการดำเนินงานในอดีตไม่ได้รับประกันผลตอบแทนในอนาคต</li>
                      <li>การลงทุนในกองทุนรวมมีความเสี่ยง มูลค่าหน่วยลงทุนอาจเพิ่มขึ้นหรือลดลงได้</li>
                      <li>กองทุน RMF / ThaiESG / TESGX มีเงื่อนไขการถอนและระยะเวลาล็อคที่แตกต่างกัน</li>
                      <li>ข้อมูลภาษีเป็นการประมาณการเบื้องต้น ควรปรึกษาผู้เชี่ยวชาญด้านภาษีเพิ่มเติม</li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
