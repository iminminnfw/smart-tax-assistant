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
  Heart
} from 'lucide-react';

// Backend API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_TAX_API_URL || 'http://localhost:8000';

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
  financial_goals: string[];
}

interface TaxScenario {
  id: string;
  name: string;
  description: string;
  badge: string;
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
  financial_goals: []
};

const GOAL_EXAMPLES = [
  'อยากประหยัดภาษีสูงสุด แต่ยังมีเงินเหลือใช้',
  'อยากซื้อบ้าน 3 ล้านบาท ใน 3 ปี',
  'อยากเกษียณอายุ 50 สบายๆ',
  'อยากมีเงินสดเหลือ 200,000 บาท/ปี',
  'อยากปกป้องครอบครัว มีเงินออมพอประมาณ',
  'อยากสมดุลระหว่างการออมและการใช้ชีวิต',
];

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

  // Goal & Results state
  const [userGoal, setUserGoal] = useState<string>('');
  const [scenarios, setScenarios] = useState<TaxScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [, setParsedGoal] = useState<ParsedGoal | null>(null);
  const [profileAnalysis, setProfileAnalysis] = useState<ProfileAnalysis | null>(null);

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
            financial_goals: data.financial_goals || [],
          });

          console.log('Profile loaded from DB:', data.has_profile ? 'existing profile' : 'default values');
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

  // API Functions
  const saveProfile = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/user/financial-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      if (!response.ok) {
        console.warn('Failed to save profile to DB');
        return false;
      }
      console.log('Profile saved to DB');
      return true;
    } catch (err) {
      console.error('Error saving profile:', err);
      return false;
    }
  };

  const analyzeProfile = async (): Promise<ProfileAnalysis | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai-optimizer/analyze-profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      if (!response.ok) throw new Error('Failed to analyze profile');
      return await response.json();
    } catch (err) {
      console.error('Profile analysis error:', err);
      return null;
    }
  };

  const parseGoal = async (goal: string): Promise<ParsedGoal | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai-optimizer/parse-goal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal_text: goal,
          profile: profile,
        }),
      });
      if (!response.ok) throw new Error('Failed to parse goal');
      return await response.json();
    } catch (err) {
      console.error('Goal parsing error:', err);
      return null;
    }
  };

  const generateScenarios = async (goal: ParsedGoal): Promise<TaxScenario[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai-optimizer/generate-scenarios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile: profile,
          goal: goal,
        }),
      });
      if (!response.ok) throw new Error('Failed to generate scenarios');
      const data = await response.json();
      return data.scenarios || [];
    } catch (err) {
      console.error('Scenario generation error:', err);
      return [];
    }
  };

  const handleGenerateScenarios = async () => {
    if (!userGoal.trim()) return;

    setLoading(true);
    setLoadingStep(0);
    setError(null);

    try {
      // Step 0: Save profile to DB (background, don't block)
      saveProfile();

      // Step 1: Analyze profile
      setLoadingStep(1);
      const analysis = await analyzeProfile();
      setProfileAnalysis(analysis);

      // Step 2: Parse goal
      setLoadingStep(2);
      const parsed = await parseGoal(userGoal);
      if (!parsed) throw new Error('ไม่สามารถวิเคราะห์เป้าหมายได้');
      setParsedGoal(parsed);

      // Step 3: Generate scenarios
      setLoadingStep(3);
      const generatedScenarios = await generateScenarios(parsed);

      if (generatedScenarios.length === 0) {
        throw new Error('ไม่สามารถสร้างแผนการลงทุนได้');
      }

      // Step 4: Complete
      setLoadingStep(4);
      setScenarios(generatedScenarios);
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
                        value={profile.annual_income}
                        onChange={(e) => setProfile({ ...profile, annual_income: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-200 outline-none text-slate-800"
                        disabled={loading}
                      />
                    </div>

                    {/* Age */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        อายุ (ปี)
                      </label>
                      <input
                        type="number"
                        value={profile.age}
                        onChange={(e) => setProfile({ ...profile, age: Number(e.target.value) })}
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
                        value={profile.monthly_expenses}
                        onChange={(e) => setProfile({ ...profile, monthly_expenses: Number(e.target.value) })}
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
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                          <Heart className="w-4 h-4 inline mr-1" />
                          สถานะ
                        </label>
                        <select
                          value={profile.has_spouse ? 'married' : 'single'}
                          onChange={(e) => setProfile({ ...profile, has_spouse: e.target.value === 'married' })}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:border-blue-500 outline-none text-slate-800 text-sm"
                          disabled={loading}
                        >
                          <option value="single">โสด</option>
                          <option value="married">แต่งงาน</option>
                        </select>
                      </div>
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
                    </div>
                  </div>
                </div>

                {/* Goal Input */}
                <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-center gap-2 mb-6">
                    <Target className="w-5 h-5 text-blue-600" />
                    <h2 className="text-lg font-semibold text-slate-800">เป้าหมายของคุณ</h2>
                  </div>

                  {/* Goal Textarea */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      บอก AI ว่าคุณต้องการอะไร
                    </label>
                    <textarea
                      value={userGoal}
                      onChange={(e) => setUserGoal(e.target.value)}
                      placeholder="เช่น: อยากประหยัดภาษีสูงสุด แต่ยังมีเงินเหลือใช้ในชีวิตประจำวัน หรือ อยากซื้อบ้าน 3 ล้านใน 3 ปี"
                      className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-colors min-h-[120px] resize-none text-slate-800"
                      disabled={loading}
                    />
                    <p className="text-sm text-slate-500 mt-2">
                      บอกเป้าหมายให้ละเอียดเท่าไหร่ AI จะแม่นยำมากขึ้นเท่านั้น
                    </p>
                  </div>

                  {/* Example Goals */}
                  <div className="mb-6">
                    <p className="text-sm font-medium text-slate-700 mb-3">ตัวอย่างเป้าหมาย (คลิกเพื่อใช้):</p>
                    <div className="flex flex-wrap gap-2">
                      {GOAL_EXAMPLES.map((example, index) => (
                        <button
                          key={index}
                          onClick={() => setUserGoal(example)}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 text-sm rounded-lg transition-colors border border-slate-200 hover:border-blue-300"
                          disabled={loading}
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={handleGenerateScenarios}
                    disabled={loading || !userGoal.trim()}
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
                          'วิเคราะห์โปรไฟล์และสถานะภาษี...',
                          'ตีความเป้าหมายของคุณ...',
                          'สร้างแผนการลงทุนที่เหมาะสม...',
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
                            style={{ width: `${(loadingStep / 4) * 100}%` }}
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
