'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { AppNavigation } from '@/components/AppNavigation';
import {
  Sparkles,
  Target,
  TrendingUp,
  PiggyBank,
  CheckCircle2,
  AlertCircle,
  Zap,
  Brain,
  Calendar,
  Loader2,
  RefreshCw,
  User,
  Heart,
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
  retirement_age: number;
}

interface TaxScenario {
  id: string;
  name: string;
  description: string;
  badge: string;
  strategy: string;
  total_investment: number;
  tax_savings: number;
  cash_remaining: number;
  risk_level: number;
  risk_label: string;
  allocations: {
    category: string;
    amount: number;
    fund_recommendations?: string[];
  }[];
  explanation: string;
  pros: string[];
  cons: string[];
  suitable_for: string;
  action_steps: string[];
  // Goal-based projections (from actual NAV data)
  expected_return_rate: number;
  projected_retirement_fund: number;
  years_to_retire: number;
  savings_target_amount: number;
  years_to_target: number | null;
  monthly_investment: number;
}

interface ParsedGoal {
  goal_type: string;
  target_amount?: number;
  timeline_years?: number;
  priorities: string[];
  constraints: string[];
  raw_input: string;
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
  retirement_age: 60,
};

interface GoalForm {
  planMarriage: boolean;       // only for single users
  savingsTarget: number;       // total savings goal in THB
  incomeGrowthRate: number;    // expected annual income growth in %
}

function buildGoalFromForm(form: GoalForm, profile: UserProfile): string {
  const parts: string[] = [];

  if (!profile.has_spouse && form.planMarriage) {
    parts.push('วางแผนแต่งงานในปีหน้า');
  }

  if (form.incomeGrowthRate > 0) {
    parts.push(`รายได้คาดว่าจะเพิ่มขึ้น ${form.incomeGrowthRate}% ต่อปี`);
  }

  if (form.savingsTarget > 0) {
    parts.push(`ต้องการมีเงินออมเป้าหมาย ${form.savingsTarget.toLocaleString('th-TH')} บาท`);
  }

  parts.push('ต้องการวางแผนภาษีและการลงทุนให้เหมาะสมกับเป้าหมาย');
  return parts.join(' ');
}

const RISK_OPTIONS = [
  { value: 'conservative', label: 'ระมัดระวัง', description: 'เน้นความปลอดภัย ผลตอบแทนต่ำ' },
  { value: 'moderate', label: 'ปานกลาง', description: 'สมดุลระหว่างความเสี่ยงและผลตอบแทน' },
  { value: 'aggressive', label: 'กล้าเสี่ยง', description: 'ยอมรับความเสี่ยงสูงเพื่อผลตอบแทนสูง' },
];

export default function AIOptimizerPage() {
  const router = useRouter();
  const { status } = useSession();

  // Profile state
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [showProfileForm, setShowProfileForm] = useState(true);
  const [hasLifeInsurance, setHasLifeInsurance] = useState(false);
  const [hasHealthInsurance, setHasHealthInsurance] = useState(false);

  // Goal & Results state
  const [userGoal, setUserGoal] = useState<string>('');
  const [goalForm, setGoalForm] = useState<GoalForm>({ planMarriage: false, savingsTarget: 0, incomeGrowthRate: 0 });
  const [scenarios, setScenarios] = useState<TaxScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [, setParsedGoal] = useState<ParsedGoal | null>(null);
  const [profileAnalysis, setProfileAnalysis] = useState<ProfileAnalysis | null>(null);
  const [recommendedFunds, setRecommendedFunds] = useState<RecommendedFund[]>([]);
  const [expandedFund, setExpandedFund] = useState<string | null>(null);

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
            retirement_age: data.retirement_age || DEFAULT_PROFILE.retirement_age,
          });

          setHasLifeInsurance((data.current_deductions?.life_insurance || 0) > 0);
          setHasHealthInsurance((data.current_deductions?.health_insurance || 0) > 0);
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
          savings_target: goalForm.savingsTarget > 0 ? goalForm.savingsTarget : null,
          plan_to_marry: !profile.has_spouse && goalForm.planMarriage,
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
        const taxInfo = data.tax_info;
        setProfileAnalysis({
          tax_bracket: taxInfo.tax_bracket?.marginal_rate_percent || 0,
          marginal_rate: taxInfo.tax_bracket?.marginal_rate_percent || 0,
          current_tax: taxInfo.tax_bracket?.total_tax || 0,
          max_potential_savings: taxInfo.deduction_remaining?.total || 0,
          recommended_focus: [],
          warnings: [],
        });
      }

      // Step 4: Map scenarios from backend
      setLoadingStep(4);

      const backendScenarios = data.scenarios || [];
      const mappedScenarios: TaxScenario[] = backendScenarios.map((s: any) => ({
        id: s.id?.toString() || `scenario-${s.id}`,
        name: s.name || '',
        description: s.description || '',
        badge: s.badge || '📊',
        strategy: s.strategy || '',
        total_investment: s.total_investment || 0,
        tax_savings: s.tax_saved || 0,
        cash_remaining: s.cash_remaining || 0,
        risk_level: (s.risk_level || 5) * 10,
        risk_label: (s.risk_level || 5) <= 3 ? 'ต่ำ' : (s.risk_level || 5) <= 6 ? 'ปานกลาง' : 'สูง',
        allocations: [
          ...(s.rmf_investment ? [{ category: 'RMF', amount: s.rmf_investment }] : []),
          ...(s.thai_esg_investment ? [{ category: 'ThaiESG', amount: s.thai_esg_investment }] : []),
        ].filter((a) => a.amount > 0),
        explanation: s.ai_explanation || s.description || '',
        pros: s.pros || [],
        cons: s.cons || [],
        suitable_for: s.description || '',
        action_steps: (s.recommended_funds || []).map((f: any) =>
          typeof f === 'string' ? f : `${f.abbr || f.fundType || ''} - ${f.nameTh || ''}`
        ),
        // Goal-based projections
        expected_return_rate: s.expected_return_rate || 0,
        projected_retirement_fund: s.projected_retirement_fund || 0,
        years_to_retire: s.years_to_retire || 0,
        savings_target_amount: s.savings_target || 0,
        years_to_target: s.years_to_target ?? null,
        monthly_investment: s.monthly_investment || 0,
      }));

      if (mappedScenarios.length === 0) {
        throw new Error('ไม่สามารถสร้างแผนการลงทุนได้');
      }

      setScenarios(mappedScenarios);

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
    setScenarios([]);
    setSelectedScenario(null);
    setParsedGoal(null);
    setProfileAnalysis(null);
    setRecommendedFunds([]);
    setExpandedFund(null);
    setUserGoal('');
    setShowProfileForm(true);
    setError(null);
  };

  const getRiskColor = (level: number) => {
    if (level <= 20) return 'text-green-600 bg-green-50';
    if (level <= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
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

          {showProfileForm && scenarios.length === 0 ? (
            <>
              {/* Profile & Goal Input */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* Profile Form */}
                <div className="lg:col-span-1 bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <User className="w-5 h-5 text-blue-600" />
                    <h2 className="text-lg font-semibold text-slate-800">โปรไฟล์ของคุณ</h2>
                    {profileLoading && (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600 ml-auto" />
                    )}
                  </div>

                  <div className="space-y-4">
                    {/* Annual Income */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        รายได้ต่อปี (บาท)
                      </label>
                      <input
                        type="number"
                        value={profile.annual_income || ''}
                        onChange={(e) => setProfile({ ...profile, annual_income: e.target.value === '' ? 0 : Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                        disabled={loading}
                      />
                      {(() => {
                        const income = profile.annual_income;
                        const netIncome = income - 60000; // รายได้สุทธิ = รายได้ - ลดหย่อนส่วนตัว
                        if (income > 0 && netIncome <= 150000) {
                          return (
                            <p className="mt-1.5 text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5">
                              ✅ รายได้สุทธิ <strong>{netIncome.toLocaleString('th-TH')} บาท</strong> ≤ 150,000 บาท — <strong>ไม่ต้องเสียภาษี</strong>
                            </p>
                          );
                        }
                        return null;
                      })()}
                    </div>

                    {/* Age */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        อายุ (ปี)
                      </label>
                      <input
                        type="number"
                        value={profile.age || ''}
                        onChange={(e) => setProfile({ ...profile, age: e.target.value === '' ? 0 : Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                        disabled={loading}
                      />
                    </div>

                    {/* Monthly Expenses */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        ค่าใช้จ่ายต่อเดือน (บาท)
                      </label>
                      <input
                        type="number"
                        value={profile.monthly_expenses || ''}
                        onChange={(e) => setProfile({ ...profile, monthly_expenses: e.target.value === '' ? 0 : Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                        disabled={loading}
                      />
                    </div>

                    {/* Risk Tolerance */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        ระดับความเสี่ยงที่รับได้
                      </label>
                      <div className="space-y-2">
                        {RISK_OPTIONS.map((option) => (
                          <label
                            key={option.value}
                            className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
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
                            <div>
                              <p className="font-medium text-slate-800 text-sm">{option.label}</p>
                              <p className="text-xs text-slate-500">{option.description}</p>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Family Status */}
                    <div className={`grid gap-3 ${profile.has_spouse ? 'grid-cols-2' : 'grid-cols-1'}`}>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          <Heart className="w-4 h-4 inline mr-1" />
                          สถานะ
                        </label>
                        <select
                          value={profile.has_spouse ? 'married' : 'single'}
                          onChange={(e) => setProfile({ ...profile, has_spouse: e.target.value === 'married', num_children: e.target.value === 'single' ? 0 : profile.num_children })}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 outline-none text-slate-800 text-sm"
                          disabled={loading}
                        >
                          <option value="single">โสด</option>
                          <option value="married">แต่งงาน</option>
                        </select>
                      </div>
                      {profile.has_spouse && (
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-1">
                            จำนวนบุตร
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={profile.num_children}
                            onChange={(e) => setProfile({ ...profile, num_children: Number(e.target.value) })}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 outline-none text-slate-800 text-sm"
                            disabled={loading}
                          />
                        </div>
                      )}
                    </div>

                    {/* Parents */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        อุปการะพ่อแม่อายุ 60+ ปีไหม?
                        <span className="ml-1 text-xs font-normal text-slate-400">(ลดหย่อนได้ 30,000/คน)</span>
                      </label>
                      <div className="flex gap-2">
                        {[0, 1, 2, 3, 4].map((n) => (
                          <button
                            key={n}
                            type="button"
                            onClick={() => setProfile({ ...profile, num_parents: n })}
                            disabled={loading}
                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                              profile.num_parents === n
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            {n === 0 ? 'ไม่มี' : `${n} คน`}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-slate-100 pt-4">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">ลดหย่อนที่มีอยู่แล้ว</p>

                      {/* Life Insurance */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          <Shield className="w-4 h-4 inline mr-1" />
                          ประกันชีวิต
                          <span className="ml-1 text-xs font-normal text-slate-400">(ลดหย่อนได้สูงสุด 100,000 บาท)</span>
                        </label>
                        <div className="flex gap-2 mb-2">
                          <button
                            type="button"
                            onClick={() => { setHasLifeInsurance(true); }}
                            disabled={loading}
                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                              hasLifeInsurance ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            มี
                          </button>
                          <button
                            type="button"
                            onClick={() => { setHasLifeInsurance(false); setProfile({ ...profile, current_deductions: { ...profile.current_deductions, life_insurance: 0 } }); }}
                            disabled={loading}
                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                              !hasLifeInsurance ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            ไม่มี
                          </button>
                        </div>
                        {hasLifeInsurance && (
                          <div>
                            <input
                              type="number"
                              min="0"
                              max="100000"
                              value={profile.current_deductions?.life_insurance || ''}
                              onChange={(e) => setProfile({ ...profile, current_deductions: { ...profile.current_deductions, life_insurance: e.target.value === '' ? 0 : Number(e.target.value) } })}
                              placeholder="จ่ายปีละเท่าไหร่ (บาท)"
                              disabled={loading}
                              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800 text-sm"
                            />
                            {(profile.current_deductions?.life_insurance || 0) > 100000 && (
                              <p className="text-xs text-amber-600 mt-1">เกินสิทธิ์ — ระบบจะใช้ 100,000 บาท</p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Health Insurance */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                          <Shield className="w-4 h-4 inline mr-1 text-green-600" />
                          ประกันสุขภาพ
                          <span className="ml-1 text-xs font-normal text-slate-400">(ลดหย่อนได้สูงสุด 25,000 บาท)</span>
                        </label>
                        <div className="flex gap-2 mb-2">
                          <button
                            type="button"
                            onClick={() => { setHasHealthInsurance(true); }}
                            disabled={loading}
                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                              hasHealthInsurance ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            มี
                          </button>
                          <button
                            type="button"
                            onClick={() => { setHasHealthInsurance(false); setProfile({ ...profile, current_deductions: { ...profile.current_deductions, health_insurance: 0 } }); }}
                            disabled={loading}
                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                              !hasHealthInsurance ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            ไม่มี
                          </button>
                        </div>
                        {hasHealthInsurance && (
                          <div>
                            <input
                              type="number"
                              min="0"
                              max="25000"
                              value={profile.current_deductions?.health_insurance || ''}
                              onChange={(e) => setProfile({ ...profile, current_deductions: { ...profile.current_deductions, health_insurance: e.target.value === '' ? 0 : Number(e.target.value) } })}
                              placeholder="จ่ายปีละเท่าไหร่ (บาท)"
                              disabled={loading}
                              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800 text-sm"
                            />
                            {(profile.current_deductions?.health_insurance || 0) > 25000 && (
                              <p className="text-xs text-amber-600 mt-1">เกินสิทธิ์ — ระบบจะใช้ 25,000 บาท</p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Retirement Age */}
                    <div className="border-t border-slate-100 pt-4">
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        <Calendar className="w-4 h-4 inline mr-1" />
                        อายุที่ตั้งใจเกษียณ (ปี)
                      </label>
                      <input
                        type="number"
                        min={profile.age + 1}
                        max="80"
                        value={profile.retirement_age || ''}
                        onChange={(e) => setProfile({ ...profile, retirement_age: e.target.value === '' ? 60 : Number(e.target.value) })}
                        disabled={loading}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800 text-sm"
                      />
                      {profile.age > 0 && profile.retirement_age > profile.age && (
                        <p className="text-xs text-slate-400 mt-1">
                          อีก {profile.retirement_age - profile.age} ปีจากนี้
                          {profile.retirement_age < 55 && (
                            <span className="ml-1 text-amber-600">⚠️ RMF ต้องถือถึงอายุ 55 ปี</span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Goal Input */}
                <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <Target className="w-5 h-5 text-blue-600" />
                    <h2 className="text-lg font-semibold text-slate-800">เป้าหมายของคุณ</h2>
                  </div>

                  {/* Goal Form */}
                  <div className="mb-6 space-y-4">
                    <p className="text-sm text-slate-500">ตอบคำถามเพื่อให้ AI วางแผนและคาดการณ์ได้แม่นยำขึ้น</p>

                    {/* Q1: แต่งงาน — แสดงเฉพาะคนโสด */}
                    {!profile.has_spouse && (
                      <div className="p-4 border border-slate-200 rounded-lg">
                        <p className="text-sm font-medium text-slate-700 mb-3">
                          คุณวางแผนที่จะแต่งงานในปีหน้าไหม?
                          <span className="ml-1 text-xs font-normal text-slate-400">(มีผลต่อลดหย่อนคู่สมรส)</span>
                        </p>
                        <div className="flex gap-3">
                          <button
                            type="button"
                            onClick={() => setGoalForm({ ...goalForm, planMarriage: true })}
                            disabled={loading}
                            className={`flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition-colors ${
                              goalForm.planMarriage
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            ใช่
                          </button>
                          <button
                            type="button"
                            onClick={() => setGoalForm({ ...goalForm, planMarriage: false })}
                            disabled={loading}
                            className={`flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition-colors ${
                              !goalForm.planMarriage
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            ยังไม่
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Q2: รายได้เพิ่มขึ้นไหม */}
                    <div className="p-4 border border-slate-200 rounded-lg">
                      <p className="text-sm font-medium text-slate-700 mb-3">
                        รายได้ของคุณคาดว่าจะเพิ่มขึ้นเท่าไหร่ต่อปี?
                        <span className="ml-1 text-xs font-normal text-slate-400">(ใช้คาดการณ์การเติบโต)</span>
                      </p>
                      <div className="flex gap-2 mb-2 flex-wrap">
                        {[0, 3, 5, 10].map((rate) => (
                          <button
                            key={rate}
                            type="button"
                            onClick={() => setGoalForm({ ...goalForm, incomeGrowthRate: rate })}
                            disabled={loading}
                            className={`flex-1 min-w-[60px] py-2 rounded-lg border text-sm font-medium transition-colors ${
                              goalForm.incomeGrowthRate === rate
                                ? 'bg-blue-600 text-white border-blue-600'
                                : 'bg-white text-slate-700 border-slate-300 hover:border-blue-400'
                            }`}
                          >
                            {rate === 0 ? 'ไม่เพิ่ม' : `+${rate}%`}
                          </button>
                        ))}
                      </div>
                      {goalForm.incomeGrowthRate > 0 && (
                        <p className="text-xs text-slate-400">
                          รายได้ปีหน้า ≈ ฿{Math.round(profile.annual_income * (1 + goalForm.incomeGrowthRate / 100)).toLocaleString('th-TH')}
                        </p>
                      )}
                    </div>

                    {/* Q3: เงินออมเป้าหมาย */}
                    <div className="p-4 border border-slate-200 rounded-lg">
                      <p className="text-sm font-medium text-slate-700 mb-3">
                        คุณต้องการมีเงินออมทั้งหมดเท่าไหร่? (บาท)
                        <span className="ml-1 text-xs font-normal text-slate-400">(AI จะคำนวณว่าถึงเป้าใน กี่ปี)</span>
                      </p>
                      <input
                        type="number"
                        min="0"
                        value={goalForm.savingsTarget || ''}
                        onChange={(e) => setGoalForm({ ...goalForm, savingsTarget: e.target.value === '' ? 0 : Number(e.target.value) })}
                        disabled={loading}
                        placeholder="เช่น 5000000 (5 ล้านบาท)"
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800 text-sm"
                      />
                      <p className="text-xs text-slate-400 mt-1">ถ้ายังไม่มีเป้าหมาย ปล่อยว่างได้เลย</p>
                    </div>
                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={handleOptimize}
                    disabled={loading}
                    className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
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

                  {/* Loading Steps */}
                  {loading && (
                    <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                        <p className="font-medium text-blue-800">AI กำลังทำงาน...</p>
                      </div>

                      <div className="space-y-3">
                        {[
                          'ส่งข้อมูลไปวิเคราะห์...',
                          'คำนวณภาษีและกรองกองทุนจากฐานข้อมูล...',
                          'วิเคราะห์โปรไฟล์และสร้างแผน...',
                          'AI สร้าง 3 แผนการลงทุน...',
                          'เสร็จสิ้น!'
                        ].map((step, index) => (
                          <div key={index} className="flex items-center gap-3">
                            {loadingStep > index ? (
                              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                            ) : loadingStep === index ? (
                              <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
                            ) : (
                              <div className="w-5 h-5 border-2 border-slate-300 rounded-full flex-shrink-0" />
                            )}
                            <span className={`text-sm ${
                              loadingStep > index ? 'text-green-700 font-medium' :
                              loadingStep === index ? 'text-blue-700 font-medium' :
                              'text-slate-500'
                            }`}>
                              {step}
                            </span>
                          </div>
                        ))}
                      </div>

                      <div className="mt-4 bg-white rounded-lg p-3">
                        <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-600 transition-all duration-500"
                            style={{ width: `${(loadingStep / 5) * 100}%` }}
                          />
                        </div>
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
                        AI สร้าง {scenarios.length} แผนเรียบร้อย!
                      </h2>
                      <p className="text-slate-600">เลือกแผนที่เหมาะกับคุณที่สุด</p>
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
                    <strong>เป้าหมายของคุณ:</strong>
                  </p>
                  <p className="text-slate-800 italic">"{userGoal}"</p>
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
                        Top {recommendedFunds.length} กองทุนแนะนำ
                      </h3>
                      <p className="text-sm text-slate-500">
                        คัดเลือกจากฐานข้อมูล SEC Thailand ตามระดับความเสี่ยงและผลตอบแทนย้อนหลัง
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {recommendedFunds.map((fund) => {
                      const isExpanded = expandedFund === fund.fundId;
                      const riskColor = fund.riskSpectrum <= 3
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : fund.riskSpectrum <= 6
                          ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
                          : 'bg-red-100 text-red-800 border-red-200';

                      const typeColor = fund.fundType === 'RMF'
                        ? 'bg-blue-100 text-blue-700'
                        : fund.fundType === 'TESG' || fund.fundType === 'TESGX'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-slate-100 text-slate-700';

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
                                {fund.rank}
                              </div>
                              <div className="min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <p className="font-semibold text-slate-800">{fund.abbr}</p>
                                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeColor}`}>
                                    {fund.fundType === 'TESG' ? 'ThaiESG' : fund.fundType === 'TESGX' ? 'ThaiESGX' : fund.fundType}
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
              )}

              {/* Scenarios Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {scenarios.map((scenario) => (
                  <div
                    key={scenario.id}
                    className={`bg-white rounded-xl border p-6 transition-all duration-200 cursor-pointer ${
                      selectedScenario === scenario.id
                        ? 'border-blue-500 ring-2 ring-blue-200'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                    onClick={() => setSelectedScenario(selectedScenario === scenario.id ? null : scenario.id)}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-slate-800 mb-1">{scenario.name}</h3>
                        <span className="text-2xl">{scenario.badge}</span>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(scenario.risk_level)}`}>
                        ความเสี่ยง: {scenario.risk_label}
                      </div>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="bg-green-50 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-1">
                          <TrendingUp className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-700 font-medium">ลดภาษีได้</span>
                        </div>
                        <p className="text-2xl font-bold text-green-900">
                          ฿{formatCurrency(scenario.tax_savings)}
                        </p>
                      </div>

                      <div className="bg-blue-50 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-1">
                          <PiggyBank className="w-4 h-4 text-blue-600" />
                          <span className="text-sm text-blue-700 font-medium">เงินสดคงเหลือ</span>
                        </div>
                        <p className="text-2xl font-bold text-blue-900">
                          ฿{formatCurrency(scenario.cash_remaining)}
                        </p>
                      </div>
                    </div>

                    {/* Projection Card (NAV-based) */}
                    {scenario.expected_return_rate > 0 && (
                      <div className="bg-purple-50 rounded-xl p-4 mb-4 border border-purple-100">
                        <div className="flex items-center gap-2 mb-2">
                          <BarChart3 className="w-4 h-4 text-purple-600" />
                          <span className="text-sm font-medium text-purple-800">การคาดการณ์จาก NAV จริง</span>
                          <span className="text-xs text-purple-400 ml-auto">ผลตอบแทนเฉลี่ย {scenario.expected_return_rate}%/ปี</span>
                        </div>
                        {scenario.strategy === 'tax_max' && scenario.projected_retirement_fund > 0 && (
                          <div>
                            <p className="text-xl font-bold text-purple-900">฿{formatCurrency(scenario.projected_retirement_fund)}</p>
                            <p className="text-xs text-purple-600 mt-0.5">คาดว่าจะมีเมื่อเกษียณ (อีก {scenario.years_to_retire} ปี) | ลงทุน ฿{formatCurrency(scenario.monthly_investment)}/เดือน</p>
                          </div>
                        )}
                        {scenario.strategy === 'balanced' && (
                          <div>
                            {scenario.savings_target_amount > 0 ? (
                              scenario.years_to_target !== null ? (
                                <>
                                  <p className="text-xl font-bold text-purple-900">{scenario.years_to_target} ปี</p>
                                  <p className="text-xs text-purple-600 mt-0.5">ถึงเป้าหมาย ฿{formatCurrency(scenario.savings_target_amount)} | ลงทุน ฿{formatCurrency(scenario.monthly_investment)}/เดือน</p>
                                </>
                              ) : (
                                <>
                                  <p className="text-xl font-bold text-purple-900">&gt; 100 ปี</p>
                                  <p className="text-xs text-purple-600 mt-0.5">เป้าหมาย ฿{formatCurrency(scenario.savings_target_amount)} ต้องเพิ่มงบลงทุน</p>
                                </>
                              )
                            ) : (
                              <>
                                <p className="text-xl font-bold text-purple-900">฿{formatCurrency(scenario.projected_retirement_fund)}</p>
                                <p className="text-xs text-purple-600 mt-0.5">คาดว่าจะมีเมื่อเกษียณ | ลงทุน ฿{formatCurrency(scenario.monthly_investment)}/เดือน</p>
                              </>
                            )}
                          </div>
                        )}
                        {scenario.strategy === 'conservative' && (
                          <div>
                            <p className="text-xl font-bold text-purple-900">฿{formatCurrency(scenario.monthly_investment)}/เดือน</p>
                            <p className="text-xs text-purple-600 mt-0.5">ลงทุน | เหลือเงินสด ฿{formatCurrency(Math.round(scenario.cash_remaining / 12))}/เดือน สำหรับแผนชีวิต</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Allocations */}
                    <div className="space-y-2 mb-4">
                      <p className="font-semibold text-slate-800 text-sm">📝 แผนการลงทุน:</p>
                      {scenario.allocations.map((alloc, idx) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="text-slate-600">• {alloc.category}</span>
                          <span className="font-medium">฿{formatCurrency(alloc.amount)}</span>
                        </div>
                      ))}
                    </div>

                    {/* AI Explanation */}
                    <div className="bg-blue-50 rounded-lg p-4 mb-4 border border-blue-100">
                      <div className="flex items-start gap-2">
                        <Brain className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-medium text-blue-800 mb-2">AI วิเคราะห์ให้คุณ:</p>
                          <p className="text-sm text-slate-700 leading-relaxed">
                            {scenario.explanation}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Expandable Details */}
                    {selectedScenario === scenario.id && (
                      <div className="space-y-4 border-t pt-4">
                        {/* Pros */}
                        <div>
                          <p className="font-semibold text-green-700 mb-2 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            ข้อดี:
                          </p>
                          <ul className="space-y-1">
                            {scenario.pros.map((pro, idx) => (
                              <li key={idx} className="text-sm text-slate-700">• {pro}</li>
                            ))}
                          </ul>
                        </div>

                        {/* Cons */}
                        <div>
                          <p className="font-semibold text-red-700 mb-2 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" />
                            ข้อควรระวัง:
                          </p>
                          <ul className="space-y-1">
                            {scenario.cons.map((con, idx) => (
                              <li key={idx} className="text-sm text-slate-700">• {con}</li>
                            ))}
                          </ul>
                        </div>

                        {/* Suitable For */}
                        <div className="bg-indigo-50 rounded-xl p-4">
                          <p className="font-semibold text-indigo-900 mb-2 flex items-center gap-2">
                            <Target className="w-4 h-4" />
                            เหมาะสำหรับ:
                          </p>
                          <p className="text-sm text-indigo-700">{scenario.suitable_for}</p>
                        </div>

                        {/* Action Steps */}
                        {scenario.action_steps && scenario.action_steps.length > 0 && (
                          <div className="bg-indigo-50 rounded-xl p-4">
                            <p className="font-semibold text-indigo-900 mb-3 flex items-center gap-2">
                              <Calendar className="w-4 h-4" />
                              📅 ขั้นตอนถัดไป:
                            </p>
                            <div className="space-y-3">
                              {scenario.action_steps.map((step, idx) => (
                                <div key={idx} className="flex items-start gap-3">
                                  <div className="w-6 h-6 bg-indigo-200 text-indigo-900 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                                    {idx + 1}
                                  </div>
                                  <p className="text-sm text-slate-700">{step}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Action Button */}
                        <button className="w-full py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 text-sm">
                          <Zap className="w-4 h-4" />
                          เลือกแผนนี้และดำเนินการ
                        </button>
                      </div>
                    )}

                    {selectedScenario !== scenario.id && (
                      <p className="text-center text-sm text-slate-500 mt-4">
                        คลิกเพื่อดูรายละเอียดเพิ่มเติม
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
