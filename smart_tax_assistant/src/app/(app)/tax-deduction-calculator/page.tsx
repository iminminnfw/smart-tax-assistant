'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import AppNavigation from '@/components/AppNavigation';
import MultiplePlansView from '@/components/TaxAdvisor/MultiplePlansView';
import { TaxCalculationResponse } from '@/lib/tax-advisor/types';
import { getApiUrl, API_CONFIG } from '@/config/api';

const DEFAULT_FORM = {
  gross_income: 0,
  income_type: '40(8)',
  business_type: 'general_trade',
  expense_method: 'standard',
  actual_expenses: 0,
  has_spouse: false,
  number_of_children: 0,
  number_of_parents: 0,
  number_of_disabled: 0,
  life_insurance: 0,
  life_insurance_pension: 0,
  life_insurance_parents: 0,
  health_insurance: 0,
  health_insurance_parents: 0,
  pension_insurance: 0,
  social_security: 0,
  provident_fund: 0,
  gpf: 0,
  pvd_teacher: 0,
  rmf: 0,
  thai_esg: 0,
  thai_esgx_new: 0,
  thai_esgx_ltf: 0,
  stock_investment: 0,
  easy_e_receipt: 0,
  home_loan_interest: 0,
  nsf: 0,
  donation_general: 0,
  donation_education: 0,
  donation_social_enterprise: 0,
  donation_political: 0,
  risk_tolerance: 'medium' as 'low' | 'medium' | 'high',
};

type FormData = typeof DEFAULT_FORM;

function fmt(n: number) {
  return n.toLocaleString('th-TH');
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
          setFormData({ ...DEFAULT_FORM, ...data.tax_form_data });
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
    const spouse_deduction = f.has_spouse ? 60000 : 0;
    const child_deduction = f.number_of_children * 30000;
    const parent_support = Math.min(f.number_of_parents, 4) * 30000;
    const disabled_support = f.number_of_disabled * 60000;

    const totalDeductions =
      60000 + spouse_deduction + child_deduction + parent_support + disabled_support +
      f.life_insurance + f.life_insurance_pension + f.life_insurance_parents +
      f.health_insurance + f.health_insurance_parents + f.pension_insurance +
      f.social_security + f.provident_fund + f.gpf + f.pvd_teacher +
      f.rmf + f.thai_esg + f.thai_esgx_new + f.thai_esgx_ltf +
      f.stock_investment + f.easy_e_receipt + f.home_loan_interest + f.nsf +
      f.donation_general + (f.donation_education * 2) + f.donation_social_enterprise + f.donation_political;

    const taxableIncome = Math.max(0, f.gross_income - totalDeductions);

    if (taxableIncome <= 150000) {
      setResult({
        tax_result: { gross_income: f.gross_income, taxable_income: taxableIncome, tax_amount: 0, effective_tax_rate: 0, total_deductions: totalDeductions, requires_optimization: false },
        investment_plans: { plans: [] },
        no_tax_required: true,
      });
      setCalculating(false);
      return;
    }

    try {
      abortControllerRef.current = new AbortController();
      const apiPayload = {
        gross_income: f.gross_income,
        income_type: f.income_type,
        business_type: f.business_type,
        expense_method: f.expense_method,
        actual_expenses: f.actual_expenses,
        personal_deduction: 60000,
        spouse_deduction,
        child_deduction,
        parent_support,
        disabled_support,
        life_insurance: f.life_insurance,
        life_insurance_pension: f.life_insurance_pension,
        life_insurance_parents: f.life_insurance_parents,
        health_insurance: f.health_insurance,
        health_insurance_parents: f.health_insurance_parents,
        pension_insurance: f.pension_insurance,
        social_security: f.social_security,
        provident_fund: f.provident_fund,
        gpf: f.gpf,
        pvd_teacher: f.pvd_teacher,
        rmf: f.rmf,
        thai_esg: f.thai_esg,
        thai_esgx_new: f.thai_esgx_new,
        thai_esgx_ltf: f.thai_esgx_ltf,
        stock_investment: f.stock_investment,
        easy_e_receipt: f.easy_e_receipt,
        home_loan_interest: f.home_loan_interest,
        nsf: f.nsf,
        donation_general: f.donation_general,
        donation_education: f.donation_education,
        donation_social_enterprise: f.donation_social_enterprise,
        donation_political: f.donation_political,
        risk_tolerance: f.risk_tolerance,
      };

      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.CALCULATE_TAX), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload),
        signal: abortControllerRef.current.signal,
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      setResult(await response.json());
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
    '40(1)': 'เงินเดือน/ค่าจ้าง 40(1)',
    '40(2)': 'ค่าจ้างวิชาชีพอิสระ 40(2)',
    '40(6)': 'วิชาชีพอิสระ 40(6)',
    '40(8)': 'ธุรกิจ/พาณิชย์ 40(8)',
  };
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
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-gray-800 flex items-center gap-2">
                  <span className="bg-blue-100 text-blue-600 px-2 py-0.5 rounded text-xs">รายได้</span>
                </h3>
              </div>
              <SummaryRow label="รายได้รวมทั้งปี" value={f.gross_income} />
              <SummaryRow label="ประเภทเงินได้" value={incomeTypeLabel[f.income_type] || f.income_type} />
              <SummaryRow label="วิธีหักค่าใช้จ่าย" value={expenseLabel} />
            </div>

            {/* ครอบครัว */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-purple-100 text-purple-600 px-2 py-0.5 rounded text-xs">ครอบครัว</span>
              </h3>
              <SummaryRow label="มีคู่สมรสไม่มีรายได้" value={f.has_spouse} />
              <SummaryRow label="จำนวนบุตร" value={f.number_of_children} unit="คน" />
              <SummaryRow label="จำนวนบิดามารดา" value={f.number_of_parents} unit="คน" />
              <SummaryRow label="คนพิการ/ทุพพลภาพในอุปการะ" value={f.number_of_disabled} unit="คน" />
              {!f.has_spouse && f.number_of_children === 0 && f.number_of_parents === 0 && f.number_of_disabled === 0 && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนครอบครัว</p>
              )}
            </div>

            {/* ประกัน */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-green-100 text-green-600 px-2 py-0.5 rounded text-xs">ประกัน</span>
              </h3>
              <SummaryRow label="ประกันชีวิต" value={f.life_insurance} />
              <SummaryRow label="ประกันชีวิตแบบบำนาญ" value={f.life_insurance_pension} />
              <SummaryRow label="ประกันชีวิตพ่อแม่" value={f.life_insurance_parents} />
              <SummaryRow label="ประกันสุขภาพ" value={f.health_insurance} />
              <SummaryRow label="ประกันสุขภาพพ่อแม่" value={f.health_insurance_parents} />
              <SummaryRow label="ประกันบำนาญ" value={f.pension_insurance} />
              <SummaryRow label="ประกันสังคม" value={f.social_security} />
              {[f.life_insurance, f.life_insurance_pension, f.life_insurance_parents, f.health_insurance, f.health_insurance_parents, f.pension_insurance, f.social_security].every(v => v === 0) && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนประกัน</p>
              )}
            </div>

            {/* กองทุน */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-orange-100 text-orange-600 px-2 py-0.5 rounded text-xs">กองทุน</span>
              </h3>
              <SummaryRow label="กองทุนสำรองเลี้ยงชีพ PVD" value={f.provident_fund} />
              <SummaryRow label="กบข." value={f.gpf} />
              <SummaryRow label="กองทุนสงเคราะห์ครูเอกชน" value={f.pvd_teacher} />
              <SummaryRow label="RMF" value={f.rmf} />
              <SummaryRow label="ThaiESG" value={f.thai_esg} />
              <SummaryRow label="ThaiESGX (เงินใหม่)" value={f.thai_esgx_new} />
              <SummaryRow label="ThaiESGX (จาก LTF)" value={f.thai_esgx_ltf} />
              <SummaryRow label="กอช." value={f.nsf} />
              {[f.provident_fund, f.gpf, f.pvd_teacher, f.rmf, f.thai_esg, f.thai_esgx_new, f.thai_esgx_ltf, f.nsf].every(v => v === 0) && (
                <p className="text-xs text-gray-400 text-center py-2">ไม่มีการลดหย่อนกองทุน</p>
              )}
            </div>

            {/* อื่นๆ + บริจาค */}
            <div className="bg-white rounded-2xl shadow-md p-5">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                <span className="bg-red-100 text-red-600 px-2 py-0.5 rounded text-xs">อื่นๆ และบริจาค</span>
              </h3>
              <SummaryRow label="ลงทุนหุ้นจดทะเบียนใหม่" value={f.stock_investment} />
              <SummaryRow label="Easy e-Receipt" value={f.easy_e_receipt} />
              <SummaryRow label="ดอกเบี้ยเงินกู้บ้าน" value={f.home_loan_interest} />
              <SummaryRow label="บริจาคทั่วไป" value={f.donation_general} />
              <SummaryRow label="บริจาคเพื่อการศึกษา" value={f.donation_education} />
              <SummaryRow label="บริจาค Social Enterprise" value={f.donation_social_enterprise} />
              <SummaryRow label="บริจาคพรรคการเมือง" value={f.donation_political} />
              {[f.stock_investment, f.easy_e_receipt, f.home_loan_interest, f.donation_general, f.donation_education, f.donation_social_enterprise, f.donation_political].every(v => v === 0) && (
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
              <MultiplePlansView result={result} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
