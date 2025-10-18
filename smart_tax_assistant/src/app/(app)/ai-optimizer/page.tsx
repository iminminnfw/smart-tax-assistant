'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppNavigation } from '@/components/AppNavigation';
import {
  Sparkles,
  Target,
  TrendingUp,
  Home as HomeIcon,
  PiggyBank,
  Shield,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  TrendingDown,
  Zap,
  Brain,
  DollarSign,
  Calendar,
  BarChart3
} from 'lucide-react';

interface Scenario {
  id: number;
  name: string;
  badge: string;
  taxSavings: number;
  cashRemaining: number;
  riskLevel: number;
  riskLabel: string;
  actions: {
    rmf: number;
    ssf: number;
    insurance: number;
    pension: number;
  };
  explanation: string;
  pros: string[];
  cons: string[];
  suitableFor: string;
}

const DEMO_SCENARIOS: Scenario[] = [
  {
    id: 1,
    name: 'Aggressive Tax Optimizer',
    badge: '🥇 สูงสุด',
    taxSavings: 87500,
    cashRemaining: 152500,
    riskLevel: 40,
    riskLabel: 'ปานกลาง',
    actions: {
      rmf: 300000,
      ssf: 200000,
      insurance: 100000,
      pension: 0
    },
    explanation: 'คุณอยู่ในอัตราภาษี 25% การลงทุนสูงสุดจะให้ผลประโยชน์มากที่สุด ตามกฎ RMF สามารถหักได้ถึง 30% ของรายได้ และ SSF อนุญาต ฿200,000 รวมกับประกันชีวิตจะช่วยลดภาษีสูงสุดพร้อมเหลือเงินสดพอเพียง',
    pros: [
      'ลดภาษีได้มากที่สุด ฿87,500',
      'สร้างเงินออมระยะยาวสูง',
      'สร้างวินัยการออมที่ดี'
    ],
    cons: [
      'เงินสดคงเหลือค่อนข้างน้อย',
      'เงินถูกล็อกระยะยาว',
      'ต้องมีความมั่นคงทางการเงิน'
    ],
    suitableFor: 'คนที่มีรายได้สูง มีเงินสำรองเพียงพอ และต้องการลดภาษีสูงสุด'
  },
  {
    id: 2,
    name: 'Balanced Approach',
    badge: '⚖️ สมดุล',
    taxSavings: 62500,
    cashRemaining: 307500,
    riskLevel: 25,
    riskLabel: 'ต่ำ',
    actions: {
      rmf: 200000,
      ssf: 100000,
      insurance: 50000,
      pension: 0
    },
    explanation: 'แนวทางที่สมดุลระหว่างการลดภาษีและความยืดหยุ่นทางการเงิน เหมาะสำหรับคนที่ต้องการเก็บเงินสดไว้ใช้ในชีวิตประจำวัน แต่ยังได้ประโยชน์จากการลดหย่อนภาษี',
    pros: [
      'ยังคงลดภาษีได้ดี ฿62,500',
      'เหลือเงินสดเพียงพอ',
      'ความเสี่ยงต่ำ'
    ],
    cons: [
      'ลดภาษีน้อยกว่าแบบ Aggressive',
      'ผลตอบแทนระยะยาวอาจน้อยกว่า'
    ],
    suitableFor: 'คนทำงานประจำที่ต้องการความสมดุลระหว่างการออมและใช้จ่าย'
  },
  {
    id: 3,
    name: 'Cash Flow Priority',
    badge: '💰 เงินสด',
    taxSavings: 37500,
    cashRemaining: 432500,
    riskLevel: 15,
    riskLabel: 'ต่ำมาก',
    actions: {
      rmf: 100000,
      ssf: 50000,
      insurance: 30000,
      pension: 0
    },
    explanation: 'เน้นรักษาความยืดหยุ่นทางการเงิน เหมาะสำหรับผู้ที่มีรายจ่ายประจำสูงหรือต้องการเงินสดไว้ใช้ฉุกเฉิน ยังคงได้ประโยชน์จากการลดหย่อนภาษีในระดับหนึ่ง',
    pros: [
      'เงินสดคงเหลือสูงสุด',
      'ความยืดหยุ่นสูง',
      'เหมาะกับคนที่มีค่าใช้จ่ายสูง'
    ],
    cons: [
      'ลดภาษีได้น้อย',
      'เงินออมระยะยาวต่ำ',
      'อาจพลาดโอกาสลงทุน'
    ],
    suitableFor: 'ฟรีแลนซ์หรือผู้ประกอบการที่รายได้ไม่แน่นอน'
  },
  {
    id: 4,
    name: 'Insurance Focus',
    badge: '🛡️ ปกป้อง',
    taxSavings: 45000,
    cashRemaining: 305000,
    riskLevel: 20,
    riskLabel: 'ต่ำ',
    actions: {
      rmf: 100000,
      ssf: 50000,
      insurance: 150000,
      pension: 0
    },
    explanation: 'เน้นการสร้างความคุ้มครองทางการเงินผ่านประกัน เหมาะสำหรับคนที่มีภาระอุปการะครอบครัวหรือต้องการความมั่นคงทางการเงิน',
    pros: [
      'ความคุ้มครองสูง',
      'เหมาะกับคนมีครอบครัว',
      'ยังได้ลดหย่อนภาษี'
    ],
    cons: [
      'ลดภาษีน้อยกว่าแบบลงทุน',
      'ผลตอบแทนต่ำกว่ากองทุน'
    ],
    suitableFor: 'คนมีครอบครัวที่ต้องการความคุ้มครองทางการเงิน'
  },
  {
    id: 5,
    name: 'Retirement Booster',
    badge: '🏖️ เกษียณ',
    taxSavings: 75000,
    cashRemaining: 195000,
    riskLevel: 35,
    riskLabel: 'ปานกลาง',
    actions: {
      rmf: 300000,
      ssf: 150000,
      insurance: 50000,
      pension: 100000
    },
    explanation: 'เน้นการสร้างความมั่นคงหลังเกษียณ เหมาะสำหรับคนอายุ 35+ ที่ต้องการเร่งสร้างกองทุนเกษียณ',
    pros: [
      'กองทุนเกษียณสูง',
      'ลดภาษีได้ดี',
      'ความมั่นคงระยะยาว'
    ],
    cons: [
      'เงินถูกล็อกถึงเกษียณ',
      'เงินสดคงเหลือค่อนข้างน้อย'
    ],
    suitableFor: 'คนวัยกลางคนที่ต้องการเตรียมเกษียณอย่างจริงจัง'
  },
  {
    id: 6,
    name: 'Young Professional',
    badge: '🚀 มือใหม่',
    taxSavings: 30000,
    cashRemaining: 450000,
    riskLevel: 10,
    riskLabel: 'ต่ำมาก',
    actions: {
      rmf: 50000,
      ssf: 50000,
      insurance: 30000,
      pension: 0
    },
    explanation: 'เหมาะสำหรับคนทำงานใหม่ที่เริ่มต้นวางแผนภาษี ลงทุนในระดับที่พอเหมาะเพื่อเริ่มสร้างนิสัยการออม',
    pros: [
      'เริ่มต้นง่าย',
      'เงินสดเหลือเยอะ',
      'ความเสี่ยงต่ำมาก'
    ],
    cons: [
      'ลดภาษีได้น้อย',
      'ยังไม่ใช้ประโยชน์สูงสุด'
    ],
    suitableFor: 'Fresh graduate หรือคนทำงานปีแรก'
  },
  {
    id: 7,
    name: 'House Saver',
    badge: '🏠 บ้าน',
    taxSavings: 40000,
    cashRemaining: 400000,
    riskLevel: 20,
    riskLabel: 'ต่ำ',
    actions: {
      rmf: 100000,
      ssf: 50000,
      insurance: 40000,
      pension: 0
    },
    explanation: 'วางแผนสำหรับคนที่เตรียมซื้อบ้านใน 2-3 ปี โดยเก็บเงินสดไว้เยอะเพื่อใช้เป็นดาวน์',
    pros: [
      'เงินสดสำรองสูง',
      'พร้อมซื้อบ้าน',
      'ยังได้ลดภาษี'
    ],
    cons: [
      'ลดภาษีน้อย',
      'ผลตอบแทนจากการลงทุนต่ำ'
    ],
    suitableFor: 'คนที่กำลังเก็บเงินซื้อบ้าน'
  },
  {
    id: 8,
    name: 'Business Owner',
    badge: '💼 ธุรกิจ',
    taxSavings: 95000,
    cashRemaining: 135000,
    riskLevel: 50,
    riskLabel: 'สูง',
    actions: {
      rmf: 300000,
      ssf: 200000,
      insurance: 200000,
      pension: 100000
    },
    explanation: 'สำหรับเจ้าของธุรกิจที่มีรายได้สูงและต้องการลดภาษีสูงสุด พร้อมสร้างความคุ้มครองครอบครัว',
    pros: [
      'ลดภาษีได้สูงสุด',
      'ความคุ้มครองสูง',
      'เหมาะกับรายได้สูง'
    ],
    cons: [
      'เงินสดคงเหลือน้อย',
      'ความเสี่ยงสูง',
      'ต้องมีรายได้มั่นคง'
    ],
    suitableFor: 'เจ้าของธุรกิจหรือผู้มีรายได้สูงกว่า 2 ล้านบาท/ปี'
  }
];

const GOALS = [
  { id: 'max-savings', label: 'ลดภาษีสูงสุด', icon: DollarSign },
  { id: 'balanced', label: 'สมดุลระหว่างออมและใช้', icon: BarChart3 },
  { id: 'cash-flow', label: 'เก็บเงินสดไว้เยอะ', icon: PiggyBank },
  { id: 'retirement', label: 'เตรียมเกษียณ', icon: Calendar },
  { id: 'house', label: 'ซื้อบ้าน', icon: HomeIcon },
  { id: 'protection', label: 'ปกป้องครอบครัว', icon: Shield },
];

export default function AIOptimizerPage() {
  const router = useRouter();
  const [selectedGoal, setSelectedGoal] = useState<string>('');
  const [showResults, setShowResults] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateScenarios = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setShowResults(true);
    }, 2000);
  };

  const getRiskColor = (level: number) => {
    if (level <= 20) return 'text-green-600 bg-green-50';
    if (level <= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AppNavigation />

      <div className="bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  AI Multi-Scenario Optimizer
                </h1>
                <p className="text-gray-600">ให้ AI วิเคราะห์และแนะนำแผนภาษีที่เหมาะกับคุณ</p>
              </div>
            </div>

          {/* Demo Warning */}
          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-yellow-800">
              <strong>🎭 DEMO MODE</strong> - นี่คือตัวอย่างสถิติ (Static Demo) ยังไม่มี AI จริง
              <br />
              ข้อมูลทั้งหมดเป็นตัวอย่างเพื่อแสดงให้เห็นถึงความสามารถของระบบ
            </div>
          </div>
        </div>

        {!showResults ? (
          <>
            {/* Goal Selection */}
            <div className="bg-white rounded-3xl shadow-xl p-8 mb-6">
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Target className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">เลือกเป้าหมายของคุณ</h2>
                <p className="text-gray-600">AI จะวิเคราะห์และสร้าง 8 สถานการณ์ที่เหมาะกับคุณ</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
                {GOALS.map((goal) => {
                  const Icon = goal.icon;
                  const isSelected = selectedGoal === goal.id;

                  return (
                    <button
                      key={goal.id}
                      onClick={() => setSelectedGoal(goal.id)}
                      className={`p-6 rounded-2xl border-2 transition-all duration-300 ${
                        isSelected
                          ? 'border-purple-500 bg-purple-50 shadow-lg scale-105'
                          : 'border-gray-200 hover:border-purple-300 hover:shadow-md'
                      }`}
                    >
                      <Icon className={`w-8 h-8 mx-auto mb-3 ${
                        isSelected ? 'text-purple-600' : 'text-gray-400'
                      }`} />
                      <p className={`font-medium ${
                        isSelected ? 'text-purple-900' : 'text-gray-700'
                      }`}>
                        {goal.label}
                      </p>
                    </button>
                  );
                })}
              </div>

              {selectedGoal && (
                <div className="mt-8 text-center">
                  <button
                    onClick={handleGenerateScenarios}
                    disabled={loading}
                    className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-2xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center gap-3 mx-auto"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                        <span>AI กำลังวิเคราะห์...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5" />
                        <span>ให้ AI วิเคราะห์ 8 สถานการณ์</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            {/* Results Header */}
            <div className="bg-white rounded-3xl shadow-xl p-6 mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">AI สร้าง 8 สถานการณ์เรียบร้อย!</h2>
                    <p className="text-gray-600">เลือกสถานการณ์ที่เหมาะกับคุณที่สุด</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowResults(false);
                    setSelectedScenario(null);
                  }}
                  className="px-4 py-2 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  เลือกเป้าหมายใหม่
                </button>
              </div>
            </div>

            {/* Scenarios Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {DEMO_SCENARIOS.map((scenario) => (
                <div
                  key={scenario.id}
                  className={`bg-white rounded-3xl shadow-xl p-6 transition-all duration-300 cursor-pointer ${
                    selectedScenario === scenario.id
                      ? 'ring-4 ring-purple-500 scale-105'
                      : 'hover:shadow-2xl hover:scale-102'
                  }`}
                  onClick={() => setSelectedScenario(scenario.id)}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-1">{scenario.name}</h3>
                      <span className="text-2xl">{scenario.badge}</span>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(scenario.riskLevel)}`}>
                      ความเสี่ยง: {scenario.riskLabel}
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
                        ฿{scenario.taxSavings.toLocaleString()}
                      </p>
                    </div>

                    <div className="bg-blue-50 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-1">
                        <PiggyBank className="w-4 h-4 text-blue-600" />
                        <span className="text-sm text-blue-700 font-medium">เงินสดคงเหลือ</span>
                      </div>
                      <p className="text-2xl font-bold text-blue-900">
                        ฿{scenario.cashRemaining.toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="space-y-2 mb-4">
                    <p className="font-semibold text-gray-900 text-sm">📝 แผนการลงทุน:</p>
                    {scenario.actions.rmf > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">• RMF</span>
                        <span className="font-medium">฿{scenario.actions.rmf.toLocaleString()}</span>
                      </div>
                    )}
                    {scenario.actions.ssf > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">• SSF</span>
                        <span className="font-medium">฿{scenario.actions.ssf.toLocaleString()}</span>
                      </div>
                    )}
                    {scenario.actions.insurance > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">• ประกันชีวิต</span>
                        <span className="font-medium">฿{scenario.actions.insurance.toLocaleString()}</span>
                      </div>
                    )}
                    {scenario.actions.pension > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">• กองทุนบำเหน็จบำนาญ</span>
                        <span className="font-medium">฿{scenario.actions.pension.toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Explanation */}
                  <div className="bg-purple-50 rounded-xl p-4 mb-4">
                    <p className="text-sm text-gray-700 leading-relaxed">
                      💡 <strong>AI แนะนำ:</strong> {scenario.explanation}
                    </p>
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
                            <li key={idx} className="text-sm text-gray-700">• {pro}</li>
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
                            <li key={idx} className="text-sm text-gray-700">• {con}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Suitable For */}
                      <div className="bg-indigo-50 rounded-xl p-4">
                        <p className="font-semibold text-indigo-900 mb-2 flex items-center gap-2">
                          <Target className="w-4 h-4" />
                          เหมาะสำหรับ:
                        </p>
                        <p className="text-sm text-indigo-700">{scenario.suitableFor}</p>
                      </div>

                      {/* Action Button */}
                      <button className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-300 flex items-center justify-center gap-2">
                        <Zap className="w-5 h-5" />
                        เลือกแผนนี้และดำเนินการ
                      </button>
                    </div>
                  )}

                  {!selectedScenario && (
                    <p className="text-center text-sm text-gray-500 mt-4">
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
