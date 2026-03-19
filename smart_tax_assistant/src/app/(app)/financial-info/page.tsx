'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppNavigation from '@/components/AppNavigation';

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

export default function FinancialInfoPage() {
  const router = useRouter();
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/user/financial-profile')
      .then((r) => r.json())
      .then((data) => {
        if (data.tax_form_data) {
          setFormData({ ...DEFAULT_FORM, ...data.tax_form_data });
        } else {
          if (data.annual_income) {
            setFormData((prev) => ({ ...prev, gross_income: data.annual_income }));
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setSaved(false);
    if (type === 'checkbox') {
      setFormData((prev) => ({ ...prev, [name]: (e.target as HTMLInputElement).checked }));
    } else if (name === 'risk_tolerance' || name === 'income_type' || name === 'business_type' || name === 'expense_method') {
      setFormData((prev) => ({ ...prev, [name]: value }));
    } else {
      const num = value === '' ? 0 : parseInt(value) || 0;
      setFormData((prev) => ({ ...prev, [name]: num }));
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/user/financial-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          annual_income: formData.gross_income,
          risk_tolerance: formData.risk_tolerance,
          marital_status: formData.has_spouse ? 'married' : 'single',
          num_children: formData.number_of_children,
          num_parents: formData.number_of_parents,
          tax_form_data: formData,
          current_deductions: {
            rmf: formData.rmf,
            ssf: 0,
            thai_esg: formData.thai_esg,
            life_insurance: formData.life_insurance,
            health_insurance: formData.health_insurance,
            pension_fund: formData.pension_insurance,
            provident_fund: formData.provident_fund,
            social_security: formData.social_security,
          },
        }),
      });
      if (!res.ok) throw new Error('บันทึกไม่สำเร็จ');
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'เกิดข้อผิดพลาด');
    } finally {
      setSaving(false);
    }
  };

  const numField = (label: string, name: string, hint?: string) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {hint && <p className="text-xs text-gray-500 mb-1">{hint}</p>}
      <input
        type="number"
        name={name}
        value={(formData as any)[name] || ''}
        onChange={handleChange}
        min={0}
        placeholder="0"
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <AppNavigation />
        <div className="flex items-center justify-center h-64">
          <div className="text-center text-gray-500">กำลังโหลดข้อมูล...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <AppNavigation />

      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 text-white py-12 px-4 shadow-2xl">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-2">ข้อมูลการเงินและภาษี</h1>
          <p className="text-emerald-100 text-lg">กรอกข้อมูลเพื่อใช้คำนวณภาษีและรับคำแนะนำจาก AI</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">

        {/* 1. รายได้ */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded-lg text-sm">1</span>
            ข้อมูลรายได้
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('รายได้รวมทั้งปี (บาท)', 'gross_income', 'รายได้ทุกแหล่งก่อนหักค่าใช้จ่าย')}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ประเภทเงินได้</label>
              <select name="income_type" value={formData.income_type} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
                <option value="40(1)">40(1) - เงินเดือน/ค่าจ้าง</option>
                <option value="40(2)">40(2) - ค่าจ้างวิชาชีพอิสระ</option>
                <option value="40(6)">40(6) - วิชาชีพอิสระ (แพทย์/ทนาย ฯลฯ)</option>
                <option value="40(8)">40(8) - ธุรกิจ/พาณิชย์</option>
              </select>
            </div>
            {(formData.income_type === '40(8)' || formData.income_type === '40(6)') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ประเภทธุรกิจ</label>
                <select name="business_type" value={formData.business_type} onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="general_trade">การค้าทั่วไป (หัก 60%)</option>
                  <option value="service">บริการ (หัก 60%)</option>
                  <option value="agriculture">เกษตรกรรม (หัก 60%)</option>
                  <option value="industry">อุตสาหกรรม (หัก 60%)</option>
                  <option value="transport">ขนส่ง (หัก 60%)</option>
                  <option value="liberal_profession">วิชาชีพอิสระ (หัก 30%)</option>
                  <option value="rental">ให้เช่าทรัพย์สิน (หัก 10-30%)</option>
                  <option value="medical">วิชาชีพเวชกรรม (หัก 60%)</option>
                  <option value="contracting">รับเหมา (หัก 60%)</option>
                  <option value="other">อื่นๆ (หัก 60%)</option>
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">วิธีหักค่าใช้จ่าย</label>
              <select name="expense_method" value={formData.expense_method} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
                <option value="standard">หักแบบเหมา (ตามกฎหมาย)</option>
                <option value="actual">หักตามจริง</option>
              </select>
            </div>
            {formData.expense_method === 'actual' && numField('ค่าใช้จ่ายจริง (บาท)', 'actual_expenses')}
          </div>
        </section>

        {/* 2. ครอบครัว */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-purple-100 text-purple-600 px-2 py-1 rounded-lg text-sm">2</span>
            ข้อมูลครอบครัว
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 sm:col-span-2">
              <input
                type="checkbox"
                name="has_spouse"
                id="has_spouse"
                checked={formData.has_spouse}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label htmlFor="has_spouse" className="text-sm font-medium text-gray-700">
                มีคู่สมรสที่ไม่มีรายได้ (ลดหย่อนได้ 60,000 บาท)
              </label>
            </div>
            {numField('จำนวนบุตร', 'number_of_children', 'คนละ 30,000 บาท ไม่จำกัด')}
            {numField('จำนวนบิดามารดา', 'number_of_parents', 'สูงสุด 4 คน คนละ 30,000 บาท')}
            {numField('จำนวนคนพิการ/ทุพพลภาพในอุปการะ', 'number_of_disabled', 'คนละ 60,000 บาท')}
          </div>
        </section>

        {/* 3. ประกัน */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-green-100 text-green-600 px-2 py-1 rounded-lg text-sm">3</span>
            ประกันและสวัสดิการ
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('ประกันชีวิต (บาท)', 'life_insurance', 'สูงสุด 100,000 บาท')}
            {numField('ประกันชีวิตแบบบำนาญ (บาท)', 'life_insurance_pension', 'สูงสุด 10,000 บาท')}
            {numField('ประกันชีวิตพ่อแม่ (บาท)', 'life_insurance_parents', 'สูงสุด 15,000 บาทต่อคน')}
            {numField('ประกันสุขภาพตนเอง (บาท)', 'health_insurance', 'สูงสุด 25,000 บาท')}
            {numField('ประกันสุขภาพพ่อแม่ (บาท)', 'health_insurance_parents', 'สูงสุด 15,000/คน สูงสุด 4 คน')}
            {numField('ประกันบำนาญ (บาท)', 'pension_insurance', 'สูงสุด 15% ของรายได้ หรือ 200,000 บาท')}
            {numField('ประกันสังคม (บาท)', 'social_security', 'สูงสุด 9,000 บาท')}
          </div>
        </section>

        {/* 4. กองทุน */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-orange-100 text-orange-600 px-2 py-1 rounded-lg text-sm">4</span>
            กองทุนและการออม
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('กองทุนสำรองเลี้ยงชีพ PVD (บาท)', 'provident_fund', 'สูงสุด 15% ของรายได้ หรือ 500,000 บาท')}
            {numField('กบข. (บาท)', 'gpf', 'สูงสุด 30% ของรายได้ หรือ 500,000 บาท')}
            {numField('กองทุนสงเคราะห์ครูเอกชน (บาท)', 'pvd_teacher', 'สูงสุด 15% ของรายได้ หรือ 500,000 บาท')}
            {numField('RMF (บาท)', 'rmf', 'สูงสุด 30% ของรายได้ หรือ 500,000 บาท')}
            {numField('ThaiESG (บาท)', 'thai_esg', 'สูงสุด 300,000 บาท (ยกเว้น 30% ของรายได้)')}
            {numField('ThaiESGX เงินใหม่ (บาท)', 'thai_esgx_new', 'สูงสุด 300,000 บาท')}
            {numField('ThaiESGX จาก LTF (บาท)', 'thai_esgx_ltf', 'สูงสุด 300,000 บาท')}
            {numField('กอช. - กองทุนการออมแห่งชาติ (บาท)', 'nsf', 'สูงสุด 30,000 บาท')}
          </div>
        </section>

        {/* 5. อื่นๆ */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-red-100 text-red-600 px-2 py-1 rounded-lg text-sm">5</span>
            การลดหย่อนอื่นๆ (ปี 2568)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('ลงทุนหุ้นจดทะเบียนใหม่ (บาท)', 'stock_investment', 'สูงสุด 100,000 บาท (ถือ 2 ปี)')}
            {numField('Easy e-Receipt (บาท)', 'easy_e_receipt', 'สูงสุด 50,000 บาท')}
            {numField('ดอกเบี้ยเงินกู้บ้าน (บาท)', 'home_loan_interest', 'สูงสุด 100,000 บาท')}
          </div>
        </section>

        {/* 6. เงินบริจาค */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-pink-100 text-pink-600 px-2 py-1 rounded-lg text-sm">6</span>
            เงินบริจาค
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('บริจาคทั่วไป (บาท)', 'donation_general', 'ลดหย่อนได้ไม่เกิน 10% ของรายได้')}
            {numField('บริจาคเพื่อการศึกษา (บาท)', 'donation_education', 'นับได้ 2 เท่าของเงินบริจาค')}
            {numField('บริจาค Social Enterprise (บาท)', 'donation_social_enterprise', 'สูงสุด 100,000 บาท')}
            {numField('บริจาคพรรคการเมือง (บาท)', 'donation_political', 'สูงสุด 10,000 บาท')}
          </div>
        </section>

        {/* 7. ความเสี่ยง */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-indigo-100 text-indigo-600 px-2 py-1 rounded-lg text-sm">7</span>
            ระดับความเสี่ยงที่ยอมรับได้
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'low', label: 'ต่ำ', desc: 'ปลอดภัย เน้นประกัน', color: 'green' },
              { value: 'medium', label: 'ปานกลาง', desc: 'กระจายความเสี่ยง', color: 'yellow' },
              { value: 'high', label: 'สูง', desc: 'เน้นผลตอบแทน', color: 'red' },
            ].map(({ value, label, desc, color }) => (
              <button
                key={value}
                type="button"
                onClick={() => { setSaved(false); setFormData((prev) => ({ ...prev, risk_tolerance: value as 'low' | 'medium' | 'high' })); }}
                className={`p-3 rounded-xl border-2 text-center transition-all ${
                  formData.risk_tolerance === value
                    ? `border-${color}-500 bg-${color}-50`
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className={`font-bold text-sm ${formData.risk_tolerance === value ? `text-${color}-700` : 'text-gray-700'}`}>{label}</div>
                <div className="text-xs text-gray-500 mt-1">{desc}</div>
              </button>
            ))}
          </div>
        </section>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">{error}</div>
        )}

        {/* Sticky Save Bar */}
        <div className="sticky bottom-4 z-10">
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 p-4 flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={() => router.push('/tax-deduction-calculator')}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
            >
              ดูสรุปและคำนวณภาษี →
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className={`px-6 py-2.5 rounded-xl font-semibold text-white text-sm transition-all ${
                saved
                  ? 'bg-green-500'
                  : saving
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
              }`}
            >
              {saving ? 'กำลังบันทึก...' : saved ? '✓ บันทึกแล้ว' : '💾 บันทึกข้อมูล'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
