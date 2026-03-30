'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import AppNavigation from '@/components/AppNavigation';
import MultiplePlansView from '@/components/TaxAdvisor/MultiplePlansView';
import { TaxCalculationResponse } from '@/lib/tax-advisor/types';

const DEFAULT_FORM = {
  gross_income: 0,
  income_type: '40(8)',
  profession_type: 'other',
  business_type: 'general_trade',
  expense_method: 'standard',
  actual_expenses: 0,
  has_spouse: false,
  number_of_children_30k: 0,
  number_of_children_60k: 0,
  number_of_parents: 0,
  number_of_disabled_family: 0,
  has_disabled_other: false,
  maternity_expense: 0,
  life_insurance: 0,
  health_insurance: 0,
  health_insurance_parents_own: 0,
  health_insurance_parents_spouse: 0,
  pension_insurance: 0,
  social_security_type: 'none' as 'none' | '33' | '39' | '40',
  social_security: 0,
  rmf: 0,
  thai_esg: 0,
  thai_esgx_new: 0,
  thai_esgx_ltf: 0,
  nsf: 0,
  social_enterprise_investment: 0,
  easy_e_receipt: 0,
  home_loan_interest: 0,
  new_house_construction: 0,
  donation_general: 0,
  donation_education: 0,
  donation_political: 0,
  risk_tolerance: 'medium' as 'low' | 'medium' | 'high',
};

type FormData = typeof DEFAULT_FORM;

function fmt(n: number) {
  return Math.round(n).toLocaleString('th-TH');
}

// ── คำนวณภาษี client-side (เหมือน dashboard) ──────────────────

function calcExpense(f: FormData) {
  if (f.expense_method === 'actual') return f.actual_expenses;
  const g = f.gross_income;
  if (f.income_type === '40(6)') {
    if (f.profession_type === 'medical' || f.profession_type === 'fine_arts') return g * 0.60;
    return g * 0.30;
  }
  if (f.income_type === '40(8)') {
    if (f.business_type === 'entertainment') {
      if (g <= 300000) return g * 0.60;
      return Math.min(300000 * 0.60 + (g - 300000) * 0.40, 600000);
    }
    return g * 0.60;
  }
  return 0;
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

function calcCurrentTax(f: FormData) {
  const g = f.gross_income;
  if (g <= 0) return null;
  const exp = calcExpense(f);

  // caps
  const lifeHealthUsed = Math.min(f.life_insurance + f.health_insurance, 100000);
  const maxPen = Math.min(g * 0.15, 200000 + Math.max(0, 100000 - Math.min(f.life_insurance, 100000)));
  const ssCap = f.social_security_type === '33' ? 9000 : f.social_security_type === '39' ? 5184 : f.social_security_type === '40' ? 3600 : 0;
  const maxEsg = Math.min(g * 0.30, 300000);
  const penUsed = Math.min(f.pension_insurance, maxPen);
  const rmfUsed = Math.min(f.rmf, Math.min(g * 0.30, 500000));
  const nsfUsed = Math.min(f.nsf, 30000);
  const retScale = (penUsed + rmfUsed + nsfUsed) > 500000 ? 500000 / (penUsed + rmfUsed + nsfUsed) : 1;

  const spouse   = f.has_spouse ? 60000 : 0;
  const children = (f.number_of_children_30k * 30000) + (f.number_of_children_60k * 60000);
  const parents  = Math.min(f.number_of_parents, 4) * 30000;
  const disabled = (f.number_of_disabled_family * 60000) + (f.has_disabled_other ? 60000 : 0);
  const maternity = Math.min(f.maternity_expense, 60000);
  const family   = spouse + children + parents + disabled + maternity;

  const deductSum =
    Math.round(rmfUsed * retScale) +
    Math.min(f.thai_esg, maxEsg) +
    Math.min(f.thai_esgx_new, maxEsg) +
    Math.min(f.thai_esgx_ltf, maxEsg) +
    lifeHealthUsed +
    Math.round(penUsed * retScale) +
    Math.min(f.health_insurance_parents_own + f.health_insurance_parents_spouse, 30000) +
    Math.min(f.social_security, ssCap) +
    Math.round(nsfUsed * retScale) +
    Math.min(f.easy_e_receipt, 50000) +
    Math.min(f.home_loan_interest, 100000) +
    Math.min(f.new_house_construction, 100000) +
    Math.min(f.social_enterprise_investment, 100000);

  const baseForDonation = Math.max(0, g - exp - 60000 - family - deductSum);
  const maxDonation     = Math.floor(baseForDonation * 0.10);
  const totalDonation   =
    Math.min(f.donation_general, maxDonation) +
    Math.min(f.donation_education * 2, maxDonation) +
    Math.min(f.donation_political, 10000);

  const totalDeduct  = exp + 60000 + family + deductSum + totalDonation;
  const taxableIncome = Math.max(0, g - totalDeduct);
  const taxProgressive = calcTax(taxableIncome);

  // มาตรา 48(2): เปรียบเทียบ 0.5% ของรายได้รวม
  const taxAmt05 = Math.round(g * 0.005);
  const taxAmount = (taxAmt05 > 5000 && taxAmt05 > taxProgressive) ? taxAmt05 : taxProgressive;

  const effectiveRate = g > 0 ? (taxAmount / g) * 100 : 0;

  return { taxableIncome, taxAmount, effectiveRate, totalDeduct, exp };
}

function SummaryRow({ label, value, unit = 'บาท' }: { label: string; value: number | boolean | string; unit?: string }) {
  if (typeof value === 'boolean') {
    return (
      <div className="flex justify-between py-1.5 border-b border-gray-100 last:border-0">
        <span className="text-sm text-gray-600">{label}</span>
        <span className={`text-sm font-medium ${value ? 'text-green-600' : 'text-gray-400'}`}>{value ? 'มี' : 'ไม่มี'}</span>
      </div>
    );
  }
  if (typeof value === 'number') {
    if (value === 0) return null;
    return (
      <div className="flex justify-between py-1.5 border-b border-gray-100 last:border-0">
        <span className="text-sm text-gray-600">{label}</span>
        <span className="text-sm font-semibold text-gray-800">{fmt(value)} {unit}</span>
      </div>
    );
  }
  return (
    <div className="flex justify-between py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-medium text-gray-800">{value}</span>
    </div>
  );
}

export default function TaxDeductionCalculator() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>(DEFAULT_FORM);
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);
  const [taxSummary, setTaxSummary] = useState<ReturnType<typeof calcCurrentTax>>(null);

  const [result, setResult] = useState<TaxCalculationResponse & { no_tax_required?: boolean } | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetch('/api/user/financial-profile')
      .then((r) => r.json())
      .then((data) => {
        if (data.tax_form_data) {
          const merged = { ...DEFAULT_FORM, ...data.tax_form_data };
          setFormData(merged);
          setTaxSummary(calcCurrentTax(merged));
          setHasData(true);
        } else if (data.annual_income) {
          setFormData((prev) => ({ ...prev, gross_income: data.annual_income }));
          setHasData(false);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (calculating) {
      setElapsedTime(0);
      interval = setInterval(() => setElapsedTime((p) => p + 1), 1000);
    }
    return () => { if (interval) clearInterval(interval); };
  }, [calculating]);

  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  const handleCancel = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setCalculating(false);
    setError('ยกเลิกการคำนวณแล้ว');
  };

  const handleCalculate = async () => {
    setCalculating(true);
    setError(null);
    setResult(null);

    const f = formData;

    // คำนวณค่าลดหย่อนครอบครัว
    const spouse_deduction = f.has_spouse ? 60000 : 0;
    const child_deduction = (f.number_of_children_30k * 30000) + (f.number_of_children_60k * 60000);
    const parent_support = Math.min(f.number_of_parents, 4) * 30000;
    const disabled_support = (f.number_of_disabled_family * 60000) + (f.has_disabled_other ? 60000 : 0);

    try {
      abortControllerRef.current = new AbortController();
      const apiPayload = {
        gross_income: f.gross_income,
        income_type: f.income_type,
        profession_type: f.profession_type,
        business_type: f.business_type,
        expense_method: f.expense_method,
        actual_expenses: f.actual_expenses,
        personal_deduction: 60000,
        spouse_deduction,
        child_deduction,
        parent_support,
        disabled_support,
        life_insurance: f.life_insurance,
        health_insurance: f.health_insurance,
        health_insurance_parents_own: f.health_insurance_parents_own,
        health_insurance_parents_spouse: f.health_insurance_parents_spouse,
        pension_insurance: f.pension_insurance,
        social_security_type: f.social_security_type,
        social_security: f.social_security,
        rmf: f.rmf,
        thai_esg: f.thai_esg,
        thai_esgx_new: f.thai_esgx_new,
        thai_esgx_ltf: f.thai_esgx_ltf,
        nsf: f.nsf,
        social_enterprise_investment: f.social_enterprise_investment,
        easy_e_receipt: f.easy_e_receipt,
        home_loan_interest: f.home_loan_interest,
        new_house_construction: f.new_house_construction,
        maternity_expense: f.maternity_expense,
        donation_general: f.donation_general,
        donation_education: f.donation_education,
        donation_political: f.donation_political,
        risk_tolerance: f.risk_tolerance,
      };

      const response = await fetch('/api/calculate-tax', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload),
        signal: abortControllerRef.current.signal,
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // ถ้าภาษีที่ต้องจ่าย = 0 ให้ set flag พิเศษ
      if (data.tax_result?.tax_amount === 0) {
        setResult({ ...data, no_tax_required: true });
      } else {
        setResult(data);
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      setError(err instanceof Error ? err.message : 'เกิดข้อผิดพลาด');
    } finally {
      setCalculating(false);
      abortControllerRef.current = null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <AppNavigation />
        <div className="flex items-center justify-center h-64 text-gray-500">กำลังโหลดข้อมูล...</div>
      </div>
    );
  }

  const f = formData;
  const incomeTypeLabel: Record<string, string> = {
    '40(6)': 'วิชาชีพอิสระ 40(6)',
    '40(8)': 'ธุรกิจ/พาณิชย์ 40(8)',
  };
  const professionLabel: Record<string, string> = {
    medical: 'แพทย์/ทันตแพทย์/เภสัช/พยาบาล',
    fine_arts: 'ศิลปินอาชีพ/ประณีตศิลปกรรม',
    other: 'วิชาชีพอิสระอื่นๆ',
  };
  const ssTypeLabel: Record<string, string> = { '33': 'มาตรา 33 (พนักงาน)', '39': 'มาตรา 39 (ผู้ประกันตนเอง)', '40': 'มาตรา 40 (บุคคลทั่วไป)', 'none': '' };
  const expenseLabel = f.expense_method === 'actual' ? `หักตามจริง ${fmt(f.actual_expenses)} บาท` : 'หักแบบเหมา';
  const riskLabel = { low: 'ต่ำ', medium: 'ปานกลาง', high: 'สูง' }[f.risk_tolerance] || 'ปานกลาง';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <AppNavigation />

      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white py-12 px-4 shadow-2xl">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-2">สรุปข้อมูลภาษี</h1>
          <p className="text-blue-100 text-lg">ตรวจสอบข้อมูล แล้วกด "คำนวณภาษีและรับแผน AI"</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">

        {/* ไม่มีข้อมูล */}
        {!hasData && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6 text-center">
            <div className="text-4xl mb-3">📋</div>
            <h3 className="text-lg font-bold text-yellow-800 mb-2">ยังไม่มีข้อมูลการเงิน</h3>
            <p className="text-yellow-700 text-sm mb-4">กรอกข้อมูลรายได้และการลดหย่อนภาษีก่อน เพื่อให้ AI คำนวณได้อย่างแม่นยำ</p>
            <button
              onClick={() => router.push('/financial-info')}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-6 py-2.5 rounded-xl font-semibold text-sm"
            >
              ไปกรอกข้อมูล →
            </button>
          </div>
        )}

        {/* Summary Sections */}
        {hasData && (
          <>
            {/* รายได้ */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-blue-100 text-blue-600 px-2 py-0.5 rounded text-xs">รายได้</span>
              </h3>
              <SummaryRow label="รายได้รวมทั้งปี" value={f.gross_income} />
              <SummaryRow label="ประเภทเงินได้" value={incomeTypeLabel[f.income_type] || f.income_type} />
              {f.income_type === '40(6)' && (
                <SummaryRow label="ประเภทวิชาชีพ" value={professionLabel[f.profession_type] || f.profession_type} />
              )}
              <SummaryRow label="วิธีหักค่าใช้จ่าย" value={expenseLabel} />
            </div>

            {/* ครอบครัว */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-purple-100 text-purple-600 px-2 py-0.5 rounded text-xs">ครอบครัว</span>
              </h3>
              <SummaryRow label="มีคู่สมรสไม่มีรายได้" value={f.has_spouse} />
              <SummaryRow label="จำนวนบุตร (คนละ 30,000)" value={f.number_of_children_30k} unit="คน" />
              <SummaryRow label="จำนวนบุตร (คนละ 60,000 — คนที่ 2 ขึ้นไปหลังปี 2561)" value={f.number_of_children_60k} unit="คน" />
              <SummaryRow label="จำนวนบิดามารดา" value={f.number_of_parents} unit="คน" />
              <SummaryRow label="คนพิการ/ทุพพลภาพในอุปการะ" value={f.number_of_disabled_family} unit="คน" />
              {f.has_disabled_other && (
                <SummaryRow label="ตัวเองเป็นคนพิการ/ทุพพลภาพ" value={true} />
              )}
              <SummaryRow label="ค่าฝากครรภ์และคลอดบุตร" value={f.maternity_expense} />
              {!f.has_spouse && f.number_of_children_30k === 0 && f.number_of_children_60k === 0 && f.number_of_parents === 0 && f.number_of_disabled_family === 0 && !f.has_disabled_other && f.maternity_expense === 0 && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนครอบครัว</p>
              )}
            </div>

            {/* ประกัน */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-green-100 text-green-600 px-2 py-0.5 rounded text-xs">ประกัน</span>
              </h3>
              <SummaryRow label="ประกันชีวิต/สุขภาพ (รวมกันสูงสุด 100,000)" value={f.life_insurance + f.health_insurance} />
              <SummaryRow label="ประกันสุขภาพพ่อแม่ตนเอง (สูงสุด 15,000)" value={f.health_insurance_parents_own} />
              <SummaryRow label="ประกันสุขภาพพ่อแม่คู่สมรส (สูงสุด 15,000)" value={f.health_insurance_parents_spouse} />
              <SummaryRow label="ประกันบำนาญ" value={f.pension_insurance} />
              {f.social_security_type !== 'none' && (
                <SummaryRow label={`ประกันสังคม (${ssTypeLabel[f.social_security_type]})`} value={f.social_security} />
              )}
              {[f.life_insurance + f.health_insurance, f.health_insurance_parents_own, f.health_insurance_parents_spouse, f.pension_insurance, f.social_security].every(v => v === 0) && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนประกัน</p>
              )}
            </div>

            {/* กองทุน */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-orange-100 text-orange-600 px-2 py-0.5 rounded text-xs">กองทุน</span>
              </h3>
              <SummaryRow label="RMF" value={f.rmf} />
              <SummaryRow label="ThaiESG" value={f.thai_esg} />
              <SummaryRow label="ThaiESGX (เงินใหม่)" value={f.thai_esgx_new} />
              <SummaryRow label="ThaiESGX (จาก LTF)" value={f.thai_esgx_ltf} />
              <SummaryRow label="กอช." value={f.nsf} />
              {[f.rmf, f.thai_esg, f.thai_esgx_new, f.thai_esgx_ltf, f.nsf].every(v => v === 0) && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนกองทุน</p>
              )}
            </div>

            {/* อื่นๆ + บริจาค */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-red-100 text-red-600 px-2 py-0.5 rounded text-xs">อื่นๆ และบริจาค</span>
              </h3>
              <SummaryRow label="ลงทุนวิสาหกิจเพื่อสังคม (SE)" value={f.social_enterprise_investment} />
              <SummaryRow label="Easy e-Receipt" value={f.easy_e_receipt} />
              <SummaryRow label="ดอกเบี้ยเงินกู้บ้าน" value={f.home_loan_interest} />
              <SummaryRow label="ค่าสร้างบ้านใหม่" value={f.new_house_construction} />
              <SummaryRow label="บริจาคทั่วไป" value={f.donation_general} />
              <SummaryRow label="บริจาคเพื่อการศึกษา (นับ 2 เท่า)" value={f.donation_education} />
              <SummaryRow label="บริจาคพรรคการเมือง" value={f.donation_political} />
              {[f.social_enterprise_investment, f.easy_e_receipt, f.home_loan_interest, f.new_house_construction, f.donation_general, f.donation_education, f.donation_political].every(v => v === 0) && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนอื่นๆ</p>
              )}
            </div>

            {/* ความเสี่ยง */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded text-xs">ความเสี่ยง</span>
              </h3>
              <SummaryRow label="ระดับความเสี่ยงที่ยอมรับได้" value={riskLabel} />
            </div>
          </>
        )}

        {/* สรุปภาษีปัจจุบัน */}
        {taxSummary && (
          <div className="bg-white rounded-2xl shadow-md p-5">
            <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-rose-100 text-rose-600 px-2 py-0.5 rounded text-xs">สรุปภาษีปัจจุบัน</span>
              <span className="text-xs text-gray-400 font-normal">คำนวณจากข้อมูลที่กรอก</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-50 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">รายได้รวม</p>
                <p className="text-lg font-bold text-gray-800">฿{fmt(formData.gross_income)}</p>
              </div>
              <div className="bg-gray-50 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">ลดหย่อนรวม</p>
                <p className="text-lg font-bold text-blue-600">฿{fmt(taxSummary.totalDeduct)}</p>
              </div>
              <div className="bg-gray-50 rounded-xl p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">เงินได้สุทธิ</p>
                <p className="text-lg font-bold text-gray-700">฿{fmt(taxSummary.taxableIncome)}</p>
              </div>
              <div className={`rounded-xl p-3 text-center ${taxSummary.taxAmount > 0 ? 'bg-rose-50' : 'bg-green-50'}`}>
                <p className="text-xs text-gray-500 mb-1">ภาษีที่ต้องจ่าย</p>
                <p className={`text-lg font-bold ${taxSummary.taxAmount > 0 ? 'text-rose-600' : 'text-green-600'}`}>
                  ฿{fmt(taxSummary.taxAmount)}
                </p>
                <p className="text-xs text-gray-400">{taxSummary.effectiveRate.toFixed(2)}% ของรายได้</p>
              </div>
            </div>
            {taxSummary.taxAmount === 0 && (
              <p className="text-center text-green-600 text-sm mt-3 font-medium">ไม่ต้องเสียภาษี (เงินได้สุทธิ ≤ 150,000 บาท)</p>
            )}
          </div>
        )}

        {/* Action Bar */}
        <div className="bg-white rounded-2xl shadow-md p-5 flex flex-col sm:flex-row items-center gap-4">
          <button
            onClick={() => router.push('/financial-info')}
            className="flex-1 sm:flex-none border-2 border-blue-500 text-blue-600 hover:bg-blue-50 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all"
          >
            แก้ไขข้อมูล →
          </button>
          <button
            onClick={handleCalculate}
            disabled={calculating || !hasData}
            className={`flex-1 px-6 py-3 rounded-xl font-bold text-white transition-all ${
              calculating || !hasData
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl'
            }`}
          >
            {calculating ? `AI กำลังวิเคราะห์... ${formatTime(elapsedTime)}` : 'คำนวณภาษีและรับแผน AI'}
          </button>
          {calculating && (
            <button onClick={handleCancel} className="text-sm text-red-500 hover:text-red-700 font-medium">
              ยกเลิก
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">{error}</div>
        )}

        {/* Result */}
        {result && (
          <>
            {result.no_tax_required ? (
              <div className="bg-green-50 border-2 border-green-200 rounded-2xl p-8 text-center">
                <div className="text-5xl mb-4">🎉</div>
                <h3 className="text-2xl font-bold text-green-800 mb-2">ไม่ต้องเสียภาษี!</h3>
                <p className="text-green-700">รายได้สุทธิ {fmt(result.tax_result?.taxable_income ?? 0)} บาท ≤ 150,000 บาท (เกณฑ์ยกเว้นภาษี)</p>
              </div>
            ) : (
              <MultiplePlansView plans={result.investment_plans?.plans ?? []} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
