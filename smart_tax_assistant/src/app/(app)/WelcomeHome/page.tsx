// src/app/(app)/WelcomeHome/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { AppNavigation } from '@/components/AppNavigation';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  RadialBarChart, RadialBar,
  AreaChart, Area,
} from 'recharts';
import { Loader2, ArrowRight, TrendingUp, TrendingDown, Zap, Target, Calculator, FileText, Settings, ChevronRight } from 'lucide-react';
import Link from 'next/link';

interface TaxFormData {
  gross_income: number; income_type: string; expense_method: string; actual_expenses: number;
  has_spouse: boolean; number_of_children: number; number_of_parents: number; number_of_disabled: number;
  life_insurance: number; life_insurance_pension: number; life_insurance_parents: number;
  health_insurance: number; health_insurance_parents: number; pension_insurance: number;
  social_security: number; provident_fund: number; gpf: number; pvd_teacher: number;
  rmf: number; thai_esg: number; thai_esgx_new: number; thai_esgx_ltf: number;
  stock_investment: number; easy_e_receipt: number; home_loan_interest: number; nsf: number;
  donation_general: number; donation_education: number; donation_social_enterprise: number;
  donation_political: number; risk_tolerance: string;
}

function calcExpense(f: TaxFormData) {
  if (f.expense_method === 'actual') return f.actual_expenses;
  const g = f.gross_income;
  if (f.income_type === '40(1)' || f.income_type === '40(2)') return Math.min(g * 0.5, 100000);
  if (f.income_type === '40(6)') return Math.min(g * 0.3, g);
  return g * 0.6;
}

function calcTax(t: number) {
  if (t <= 0) return 0;
  const bs = [150000, 300000, 500000, 750000, 1000000, 2000000, 5000000];
  const rs = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35];
  let tax = 0, prev = 0;
  for (let i = 0; i <= bs.length; i++) {
    const lim = bs[i] ?? Infinity;
    if (t <= prev) break;
    tax += (Math.min(t, lim) - prev) * rs[i];
    prev = lim;
  }
  return Math.round(tax);
}

function getMarginalRate(t: number) {
  if (t <= 150000) return 0; if (t <= 300000) return 5; if (t <= 500000) return 10;
  if (t <= 750000) return 15; if (t <= 1000000) return 20; if (t <= 2000000) return 25;
  if (t <= 5000000) return 30; return 35;
}

function computeDash(f: TaxFormData) {
  const g = f.gross_income;
  const exp = calcExpense(f);
  const maxRmf = Math.min(g * 0.30, 500000);
  const maxPen = Math.min(g * 0.15, 200000);
  const maxPvd = Math.min(g * 0.15, 500000);

  const items = [
    { label: 'RMF',            used: Math.min(f.rmf, maxRmf),                               max: maxRmf,  color: '#6366f1' },
    { label: 'ThaiESG',        used: Math.min(f.thai_esg, 300000),                           max: 300000,  color: '#10b981' },
    { label: 'ThaiESGX',       used: Math.min(f.thai_esgx_new + f.thai_esgx_ltf, 300000),   max: 300000,  color: '#14b8a6' },
    { label: 'ประกันชีวิต',    used: Math.min(f.life_insurance, 100000),                     max: 100000,  color: '#3b82f6' },
    { label: 'ประกันสุขภาพ',   used: Math.min(f.health_insurance, 25000),                   max: 25000,   color: '#06b6d4' },
    { label: 'ประกันบำนาญ',    used: Math.min(f.pension_insurance, maxPen),                  max: maxPen,  color: '#8b5cf6' },
    { label: 'กองทุนสำรองฯ',   used: Math.min(f.provident_fund, maxPvd),                    max: maxPvd,  color: '#f59e0b' },
    { label: 'Easy e-Receipt', used: Math.min(f.easy_e_receipt, 50000),                      max: 50000,   color: '#f97316' },
    { label: 'ดอกเบี้ยบ้าน',   used: Math.min(f.home_loan_interest, 100000),                max: 100000,  color: '#ec4899' },
    { label: 'ประกันสังคม',     used: Math.min(f.social_security, 9000),                     max: 9000,    color: '#64748b' },
  ];

  const spouse = f.has_spouse ? 60000 : 0;
  const children = f.number_of_children * 30000;
  const parents = Math.min(f.number_of_parents, 4) * 30000;
  const disabled = f.number_of_disabled * 60000;
  const family = spouse + children + parents + disabled;

  const deductSum = items.reduce((s, i) => s + i.used, 0);
  const totalDeduct = exp + 60000 + family + deductSum;
  const taxable = Math.max(0, g - totalDeduct);
  const taxNow = calcTax(taxable);
  const taxBase = calcTax(Math.max(0, g - exp - 60000));
  const saved = Math.max(0, taxBase - taxNow);
  const marginal = getMarginalRate(taxable);

  const potExtra = items.reduce((s, i) => s + Math.max(0, i.max - i.used), 0);
  const potential = Math.max(0, taxNow - calcTax(Math.max(0, taxable - potExtra)));

  const totalMax = items.reduce((s, i) => s + i.max, 0);
  const overallPct = totalMax > 0 ? Math.round((deductSum / totalMax) * 100) : 0;

  const groups: Record<string, number> = {};
  items.forEach(i => { if (i.used > 0) groups[i.label] = i.used; });
  const pieData = Object.entries(groups).map(([name, value]) => ({ name, value }));
  const PIE_COLORS = items.filter(i => i.used > 0).map(i => i.color);

  const areaData = [
    { name: 'รายได้รวม',      tax: taxBase },
    { name: 'หักครอบครัว',   tax: calcTax(Math.max(0, g - exp - 60000 - family)) },
    { name: 'หักประกัน',     tax: calcTax(Math.max(0, taxable + items.filter(i => ['ประกันชีวิต','ประกันสุขภาพ','ประกันบำนาญ','ประกันสังคม'].includes(i.label)).reduce((s,i)=>s+i.used,0))) },
    { name: 'หักกองทุน',     tax: taxNow },
    { name: 'ถ้าใช้สิทธิ์ครบ', tax: Math.max(0, taxNow - potential) },
  ];

  return { g, taxable, taxNow, saved, totalDeduct, deductSum, potential, marginal, overallPct, pieData, PIE_COLORS, items, areaData };
}

const fmt = (n: number) => Math.round(n).toLocaleString('th-TH');

const TipBar = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-xs">
      <p className="font-bold text-gray-700 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.fill || p.color }}>{p.name}: ฿{Number(p.value).toLocaleString()}</p>
      ))}
    </div>
  );
};

const TipPie = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-xs">
      <p className="font-bold text-gray-700">{payload[0].name}</p>
      <p className="text-gray-500">฿{Number(payload[0].value).toLocaleString()}</p>
    </div>
  );
};

export default function WelcomeHomePage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [dash, setDash] = useState<ReturnType<typeof computeDash> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'authenticated') {
      fetch('/api/user/financial-profile').then(r => r.json()).then(d => {
        if (d.tax_form_data?.gross_income > 0) setDash(computeDash(d.tax_form_data as TaxFormData));
      }).catch(() => {}).finally(() => setLoading(false));
    }
  }, [status]);

  if (status === 'loading') return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
    </div>
  );
  if (status === 'unauthenticated') { router.push('/auth'); return null; }

  const name = session?.user?.name || 'ผู้ใช้';

  return (
    <div className="min-h-screen bg-gray-50">
      <AppNavigation />

      {/* HERO BANNER */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 px-4 py-10">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <p className="text-indigo-200 text-sm font-medium mb-1">Smart Tax Assistant 2568</p>
            <h1 className="text-3xl lg:text-4xl font-black text-white mb-2">
              สวัสดี, คุณ{name} 👋
            </h1>
            <p className="text-indigo-100 text-base">
              {dash
                ? `ภาษีที่ต้องจ่าย ฿${fmt(dash.taxNow)} • ประหยัดได้อีก ฿${fmt(dash.potential)}`
                : 'กรอกข้อมูลเพื่อเริ่มวิเคราะห์ภาษีของคุณ'}
            </p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <Link href="/financial-info">
              <button className="bg-white/20 hover:bg-white/30 border border-white/30 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2">
                <Settings className="w-4 h-4" /> ข้อมูลการเงิน
              </button>
            </Link>
            <Link href="/tax-deduction-calculator">
              <button className="bg-white text-indigo-600 hover:bg-indigo-50 px-5 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center gap-2 shadow-lg">
                <Zap className="w-4 h-4" /> รับแผน AI
              </button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">

        {loading && (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500 mr-2" />
            <span className="text-gray-400">กำลังวิเคราะห์ข้อมูล...</span>
          </div>
        )}

        {!loading && !dash && (
          <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center shadow-sm">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-2xl font-bold text-gray-800 mb-2">ยังไม่มีข้อมูลการเงิน</h3>
            <p className="text-gray-500 mb-6">กรอกข้อมูลรายได้และค่าลดหย่อนเพื่อดู Dashboard แบบเรียลไทม์</p>
            <Link href="/financial-info">
              <button className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold px-8 py-3 rounded-xl shadow-md hover:shadow-lg transition-all">
                กรอกข้อมูลเลย →
              </button>
            </Link>
          </div>
        )}

        {dash && (
          <>
            {/* STATS ROW */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'รายได้รวมทั้งปี', value: `฿${fmt(dash.g)}`, icon: TrendingUp, color: 'indigo' },
                { label: 'ค่าลดหย่อนรวม', value: `฿${fmt(dash.totalDeduct)}`, icon: Target, color: 'purple' },
                { label: 'ภาษีที่ต้องจ่าย', value: dash.taxNow === 0 ? 'ไม่ต้องจ่าย!' : `฿${fmt(dash.taxNow)}`, icon: Calculator, color: dash.taxNow === 0 ? 'green' : 'red' },
                { label: 'ประหยัดภาษีได้', value: `฿${fmt(dash.saved)}`, icon: TrendingDown, color: 'emerald' },
              ].map(({ label, value, icon: Icon, color }) => {
                const colorMap: Record<string, { bg: string; icon: string; text: string; border: string }> = {
                  indigo:  { bg: 'bg-indigo-50',  icon: 'bg-indigo-100 text-indigo-600',  text: 'text-indigo-700',  border: 'border-indigo-100' },
                  purple:  { bg: 'bg-purple-50',  icon: 'bg-purple-100 text-purple-600',  text: 'text-purple-700',  border: 'border-purple-100' },
                  green:   { bg: 'bg-green-50',   icon: 'bg-green-100 text-green-600',    text: 'text-green-700',   border: 'border-green-100' },
                  red:     { bg: 'bg-red-50',     icon: 'bg-red-100 text-red-600',        text: 'text-red-700',     border: 'border-red-100' },
                  emerald: { bg: 'bg-emerald-50', icon: 'bg-emerald-100 text-emerald-600',text: 'text-emerald-700', border: 'border-emerald-100' },
                };
                const c = colorMap[color];
                return (
                  <div key={label} className={`${c.bg} border ${c.border} rounded-2xl p-5 shadow-sm`}>
                    <div className={`w-10 h-10 ${c.icon} rounded-xl flex items-center justify-center mb-3`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <p className="text-xs text-gray-500 font-medium mb-1">{label}</p>
                    <p className={`text-xl font-black ${c.text}`}>{value}</p>
                  </div>
                );
              })}
            </div>

            {/* PIE + RADIAL + POTENTIAL */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* Donut */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 text-sm mb-0.5">สัดส่วนค่าลดหย่อน</h3>
                <p className="text-xs text-gray-400 mb-3">แบ่งตามหมวดหมู่</p>
                <ResponsiveContainer width="100%" height={210}>
                  <PieChart>
                    <Pie data={dash.pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={88} paddingAngle={3} dataKey="value">
                      {dash.pieData.map((_, i) => <Cell key={i} fill={dash.PIE_COLORS[i]} stroke="white" strokeWidth={2} />)}
                    </Pie>
                    <Tooltip content={<TipPie />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-2 gap-1 mt-1">
                  {dash.pieData.map((d, i) => (
                    <div key={d.name} className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: dash.PIE_COLORS[i] }} />
                      <span className="text-xs text-gray-500 truncate">{d.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Radial */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 text-sm mb-0.5">ใช้สิทธิ์ไปแล้ว</h3>
                <p className="text-xs text-gray-400 mb-2">เทียบกับวงเงินสูงสุดทั้งหมด</p>
                <ResponsiveContainer width="100%" height={200}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius="55%" outerRadius="85%"
                    data={[{ value: dash.overallPct, fill: dash.overallPct > 70 ? '#10b981' : dash.overallPct > 40 ? '#6366f1' : '#f97316' }]}
                    startAngle={180} endAngle={-180}>
                    <RadialBar dataKey="value" cornerRadius={10} background={{ fill: '#f1f5f9' }} />
                    <text x="50%" y="44%" textAnchor="middle" dominantBaseline="middle"
                      style={{ fontSize: '30px', fontWeight: 900, fill: '#1e293b' }}>{dash.overallPct}%</text>
                    <text x="50%" y="57%" textAnchor="middle" dominantBaseline="middle"
                      style={{ fontSize: '11px', fill: '#94a3b8' }}>ของสิทธิ์ทั้งหมด</text>
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <div className="bg-gray-50 rounded-xl p-2.5 text-center">
                    <p className="text-xs text-gray-400">ใช้สิทธิ์แล้ว</p>
                    <p className="text-sm font-bold text-indigo-600">฿{fmt(dash.deductSum)}</p>
                  </div>
                  <div className="bg-emerald-50 rounded-xl p-2.5 text-center">
                    <p className="text-xs text-gray-400">ประหยัดได้</p>
                    <p className="text-sm font-bold text-emerald-600">฿{fmt(dash.saved)}</p>
                  </div>
                </div>
              </div>

              {/* Potential */}
              <div className="bg-gradient-to-br from-amber-400 via-orange-500 to-pink-500 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
                <div className="absolute -top-6 -right-6 w-28 h-28 bg-white/10 rounded-full" />
                <div className="absolute bottom-0 left-0 w-20 h-20 bg-black/5 rounded-full" />
                <div className="relative">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center mb-3">
                    <Zap className="w-5 h-5 text-white" />
                  </div>
                  <p className="text-sm text-orange-100 mb-1">ถ้าใช้สิทธิ์ครบทั้งหมด</p>
                  <p className="text-4xl font-black mb-0.5">฿{fmt(dash.potential)}</p>
                  <p className="text-orange-100 text-sm mb-4">ประหยัดภาษีได้เพิ่มอีก</p>
                  <div className="space-y-1.5 mb-4">
                    {dash.items.filter(i => i.max - i.used > 0).slice(0, 3).map(i => (
                      <div key={i.label} className="flex justify-between text-xs">
                        <span className="text-orange-100">{i.label} เหลือ</span>
                        <span className="font-bold">฿{fmt(i.max - i.used)}</span>
                      </div>
                    ))}
                  </div>
                  <Link href="/tax-deduction-calculator">
                    <button className="w-full bg-white/25 hover:bg-white/35 border border-white/30 text-white text-sm font-bold py-2.5 rounded-xl transition-all">
                      รับแผน AI →
                    </button>
                  </Link>
                </div>
              </div>
            </div>

            {/* STACKED BAR */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-bold text-gray-800 text-sm">วงเงินลดหย่อนแต่ละประเภท</h3>
                  <p className="text-xs text-gray-400 mt-0.5">ใช้ไปแล้ว (สี) vs ยังเหลือ (เทา)</p>
                </div>
                <Link href="/financial-info" className="text-xs text-indigo-500 hover:text-indigo-700 font-medium flex items-center gap-1">
                  แก้ไข <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
              <ResponsiveContainer width="100%" height={290}>
                <BarChart data={dash.items.map(i => ({ name: i.label, 'ใช้ไปแล้ว': i.used, 'คงเหลือ': Math.max(0, i.max - i.used), color: i.color }))}
                  margin={{ top: 5, right: 10, left: 10, bottom: 70 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} angle={-38} textAnchor="end" height={75} interval={0} />
                  <YAxis tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}K` : String(v)} tick={{ fontSize: 11, fill: '#94a3b8' }} width={42} />
                  <Tooltip content={<TipBar />} />
                  <Bar dataKey="ใช้ไปแล้ว" stackId="a">
                    {dash.items.map((item, i) => <Cell key={i} fill={item.color} />)}
                  </Bar>
                  <Bar dataKey="คงเหลือ" stackId="a" fill="#e2e8f0" radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* AREA + BRACKET */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Area Chart */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 text-sm mb-0.5">จำลองการลดภาษีแต่ละขั้น</h3>
                <p className="text-xs text-gray-400 mb-4">ภาษีลดลงเมื่อใช้สิทธิ์ลดหย่อนเพิ่ม</p>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={dash.areaData} margin={{ top: 5, right: 10, left: 5, bottom: 40 }}>
                    <defs>
                      <linearGradient id="aGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} angle={-25} textAnchor="end" height={50} interval={0} />
                    <YAxis tickFormatter={v => `${(v/1000).toFixed(0)}K`} tick={{ fontSize: 11, fill: '#94a3b8' }} width={38} />
                    <Tooltip content={<TipBar />} />
                    <Area type="monotone" dataKey="tax" stroke="#6366f1" strokeWidth={3} fill="url(#aGrad)"
                      dot={{ fill: '#6366f1', r: 5, strokeWidth: 0 }} name="ภาษี (บาท)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Tax Bracket */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-gray-800 text-sm">Tax Bracket ปัจจุบัน</h3>
                    <p className="text-xs text-gray-400 mt-0.5">เงินได้สุทธิ ฿{fmt(dash.taxable)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-black" style={{
                      color: dash.marginal === 0 ? '#10b981' : dash.marginal <= 10 ? '#6366f1' : dash.marginal <= 20 ? '#f59e0b' : '#ef4444'
                    }}>{dash.marginal}%</p>
                    <p className="text-xs text-gray-400">อัตราสูงสุด</p>
                  </div>
                </div>
                <div className="space-y-2 mb-4">
                  {[
                    { min: 0,       max: 150000,  rate: '0%',   color: '#10b981' },
                    { min: 150001,  max: 300000,  rate: '5%',   color: '#6366f1' },
                    { min: 300001,  max: 500000,  rate: '10%',  color: '#3b82f6' },
                    { min: 500001,  max: 750000,  rate: '15%',  color: '#8b5cf6' },
                    { min: 750001,  max: 1000000, rate: '20%',  color: '#f59e0b' },
                    { min: 1000001, max: 2000000, rate: '25%',  color: '#f97316' },
                    { min: 2000001, max: Infinity, rate: '30%+', color: '#ef4444' },
                  ].map((b) => {
                    const isActive = dash.taxable >= b.min && (b.max === Infinity ? true : dash.taxable <= b.max);
                    const filled = b.max === Infinity
                      ? (dash.taxable > b.min ? 100 : 0)
                      : Math.min(100, Math.max(0, ((Math.min(dash.taxable, b.max) - b.min) / (b.max - b.min)) * 100));
                    const show = dash.taxable >= b.min;
                    return (
                      <div key={b.rate} className="flex items-center gap-2.5">
                        <span className={`text-xs w-8 font-semibold text-right ${isActive ? 'text-gray-800' : 'text-gray-300'}`}>{b.rate}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700"
                            style={{ width: `${show ? filled : 0}%`, backgroundColor: b.color, opacity: isActive ? 1 : 0.5 }} />
                        </div>
                        {isActive && <span className="text-xs font-bold whitespace-nowrap" style={{ color: b.color }}>◀ คุณอยู่นี่</span>}
                      </div>
                    );
                  })}
                </div>
                {dash.marginal > 0 && (
                  <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                    <p className="text-xs text-indigo-700">
                      ลดหย่อนเพิ่ม ฿10,000 → ประหยัด <span className="font-black text-indigo-900">฿{(dash.marginal * 100).toLocaleString()}</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-bold text-gray-800 text-sm mb-4">เมนูด่วน</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { href: '/financial-info', icon: Settings, bg: '#f0fdf4', color: '#16a34a', label: 'ข้อมูลการเงิน', desc: 'กรอก/แก้ไขข้อมูล' },
              { href: '/tax-deduction-calculator', icon: Calculator, bg: '#eff6ff', color: '#2563eb', label: 'คำนวณภาษี', desc: 'รับแผน AI 3 แผน' },
              { href: '/ai-optimizer', icon: TrendingUp, bg: '#faf5ff', color: '#7c3aed', label: 'AI Optimizer', desc: 'แนะนำกองทุน' },
              { href: '/document', icon: FileText, bg: '#f8fafc', color: '#475569', label: 'เอกสาร', desc: 'จัดการไฟล์ภาษี' },
            ].map(({ href, icon: Icon, bg, color, label, desc }) => (
              <Link key={href} href={href}>
                <div className="group p-4 rounded-xl border border-gray-100 hover:shadow-md transition-all cursor-pointer" style={{ backgroundColor: bg }}>
                  <div className="flex items-start justify-between mb-2.5">
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: color + '15' }}>
                      <Icon className="w-4 h-4" style={{ color }} />
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
                  </div>
                  <p className="font-semibold text-gray-800 text-sm">{label}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
