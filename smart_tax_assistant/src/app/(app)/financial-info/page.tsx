'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppNavigation from '@/components/AppNavigation';

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
  social_enterprise_investment: 0,
  easy_e_receipt: 0,
  home_loan_interest: 0,
  new_house_construction: 0,
  nsf: 0,
  donation_general: 0,
  donation_education: 0,
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
    } else if (name === 'risk_tolerance' || name === 'income_type' || name === 'profession_type' || name === 'business_type' || name === 'expense_method' || name === 'social_security_type') {
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
          num_children: formData.number_of_children_30k + formData.number_of_children_60k,
          num_parents: formData.number_of_parents,
          tax_form_data: formData,
          current_deductions: {
            rmf: formData.rmf,
            ssf: 0,
            thai_esg: formData.thai_esg,
            life_insurance: formData.life_insurance,
            health_insurance: formData.health_insurance,
            pension_fund: formData.pension_insurance,
            provident_fund: 0,
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
                <option value="40(6)">40(6) - วิชาชีพอิสระ (แพทย์/ทนาย/วิศวกร ฯลฯ)</option>
                <option value="40(8)">40(8) - ธุรกิจ/พาณิชย์/นักแสดง</option>
              </select>
            </div>
            {formData.income_type === '40(6)' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ประเภทวิชาชีพ</label>
                <select name="profession_type" value={(formData as any).profession_type} onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="medical">การประกอบโรคศิลปะ (หัก 60%)</option>
                  <option value="fine_arts">ประณีตศิลปกรรม (หัก 60%)</option>
                  <option value="law">กฎหมาย (หัก 30%)</option>
                  <option value="engineering">วิศวกรรม (หัก 30%)</option>
                  <option value="architecture">สถาปัตยกรรม (หัก 30%)</option>
                  <option value="accounting">การบัญชี (หัก 30%)</option>
                  <option value="other">วิชาชีพอื่นๆ (หัก 30%)</option>
                </select>
              </div>
            )}
            {formData.income_type === '40(8)' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ประเภทธุรกิจ</label>
                <select name="business_type" value={formData.business_type} onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="entertainment">นักแสดง/นักร้อง/นักดนตรี/นักกีฬาอาชีพ (60%+40%)</option>
                  <option value="general_trade">การค้าทั่วไป (หัก 60%)</option>
                  <option value="hotel_restaurant">โรงแรม/ภัตตาคาร/ปรุงอาหาร (หัก 60%)</option>
                  <option value="transportation">ขนส่ง/รับจ้างยานพาหนะ (หัก 60%)</option>
                  <option value="agriculture">เกษตรกรรม/ไม้ล้มลุก/ธัญชาติ (หัก 60%)</option>
                  <option value="livestock">เลี้ยงสัตว์ทุกชนิด (หัก 60%)</option>
                  <option value="hospital">สถานพยาบาล (มีเตียง) (หัก 60%)</option>
                  <option value="construction">รับเหมาก่อสร้าง (หัก 60%)</option>
                  <option value="manufacturing">อุตสาหกรรม/การผลิต (หัก 60%)</option>
                  <option value="photography">ถ่าย/ล้าง/อัดรูป (หัก 60%)</option>
                  <option value="tailoring">ตัด/เย็บ/ถัก/ปักเสื้อผ้า (หัก 60%)</option>
                  <option value="hair_salon">ดัด/ตัด/แต่งผม/ตกแต่งร่างกาย (หัก 60%)</option>
                  <option value="jewelry">เครื่องเงิน/ทอง/เพชร/พลอย (หัก 60%)</option>
                  <option value="mining">ทำเหมืองแร่ (หัก 60%)</option>
                  <option value="forestry">ป่าไม้/สวนยาง/ไม้ยืนต้น (หัก 60%)</option>
                  <option value="other_business">อื่นๆ (หัก 60%)</option>
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
            {numField('บุตรที่ได้ลดหย่อน 30,000/คน', 'number_of_children_30k', 'บุตรคนที่ 1 หรือบุตรคนที่ 2+ ที่เกิดก่อนปี 2561')}
            {numField('บุตรที่ได้ลดหย่อน 60,000/คน', 'number_of_children_60k', 'บุตรคนที่ 2 เป็นต้นไป ที่เกิดปี 2561 หรือหลัง')}
            {numField('จำนวนบิดามารดา', 'number_of_parents', 'สูงสุด 4 คน คนละ 30,000 บาท (อายุ >60 ปี รายได้ไม่เกิน 30,000/ปี)')}
            {numField('ค่าฝากครรภ์และคลอดบุตร (บาท)', 'maternity_expense', 'สูงสุด 60,000 บาทต่อครรภ์')}
            {numField('คนพิการที่เป็นคู่สมรส/ลูก/พ่อแม่', 'number_of_disabled_family', 'คนละ 60,000 บาท ไม่จำกัดจำนวน')}
            <div className="sm:col-span-2 flex items-center gap-3">
              <input
                type="checkbox"
                name="has_disabled_other"
                id="has_disabled_other"
                checked={(formData as any).has_disabled_other}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label htmlFor="has_disabled_other" className="text-sm font-medium text-gray-700">
                มีคนพิการ/ทุพพลภาพที่ไม่ใช่ครอบครัวในอุปการะ (ลดหย่อนได้ 60,000 บาท 1 คน)
              </label>
            </div>
          </div>
        </section>

        {/* 3. ประกัน */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-green-100 text-green-600 px-2 py-1 rounded-lg text-sm">3</span>
            ประกันและสวัสดิการ
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('ประกันชีวิต (บาท)', 'life_insurance', 'สูงสุด 100,000 บาท (รวมกับประกันสุขภาพไม่เกิน 100,000)')}
            {numField('ประกันสุขภาพตนเอง (บาท)', 'health_insurance', 'สูงสุด 25,000 บาท (รวมกับประกันชีวิตไม่เกิน 100,000)')}
            {numField('ประกันสุขภาพ/ชีวิตพ่อแม่ตนเอง (บาท)', 'health_insurance_parents_own', 'รวมทุกคนสูงสุด 15,000 บาท')}
            {formData.has_spouse && numField('ประกันสุขภาพ/ชีวิตพ่อแม่คู่สมรส (บาท)', 'health_insurance_parents_spouse', 'รวมทุกคนสูงสุด 15,000 บาท (คู่สมรสไม่มีรายได้)')}
            {numField('ประกันชีวิตแบบบำนาญ (บาท)', 'pension_insurance', 'สูงสุด 15% ของรายได้ / ถ้าไม่มีประกันชีวิตทั่วไปสูงสุด 300,000 บาท')}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ประเภทประกันสังคม</label>
              <select name="social_security_type" value={(formData as any).social_security_type} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
                <option value="none">ไม่ได้จ่ายประกันสังคม</option>
                <option value="33">มาตรา 33 — ลูกจ้าง (สูงสุด 9,000 บาท)</option>
                <option value="39">มาตรา 39 — สมัครใจต่อเนื่อง (สูงสุด 5,184 บาท)</option>
                <option value="40">มาตรา 40 — อาชีพอิสระ (สูงสุด 3,600 บาท)</option>
              </select>
            </div>
            {(formData as any).social_security_type !== 'none' && numField(
              'ประกันสังคม (บาท)',
              'social_security',
              (formData as any).social_security_type === '33' ? 'สูงสุด 9,000 บาท' :
              (formData as any).social_security_type === '39' ? 'สูงสุด 5,184 บาท' : 'สูงสุด 3,600 บาท'
            )}
          </div>
        </section>

        {/* 4. กองทุน */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-orange-100 text-orange-600 px-2 py-1 rounded-lg text-sm">4</span>
            กองทุนและการออม
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('RMF (บาท)', 'rmf', 'สูงสุด 30% ของรายได้ หรือ 500,000 บาท')}
            {numField('ThaiESG (บาท)', 'thai_esg', 'สูงสุด 30% ของรายได้ หรือ 300,000 บาท')}
            {numField('ThaiESGX เงินใหม่ (บาท)', 'thai_esgx_new', 'สูงสุด 30% ของรายได้ หรือ 300,000 บาท (วงเงินแยกจาก ThaiESG)')}
            {numField('ThaiESGX สับเปลี่ยนจาก LTF (บาท)', 'thai_esgx_ltf', 'สูงสุด 30% ของรายได้ หรือ 300,000 บาท (ปี 2568)')}
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
            {numField('ลงทุนวิสาหกิจเพื่อสังคม SE (บาท)', 'social_enterprise_investment', 'สูงสุด 100,000 บาท')}
            {numField('Easy e-Receipt (บาท)', 'easy_e_receipt', 'สูงสุด 50,000 บาท (16 ม.ค. – 28 ก.พ. 2568)')}
            {numField('ดอกเบี้ยเงินกู้บ้าน (บาท)', 'home_loan_interest', 'สูงสุด 100,000 บาท')}
            {numField('ค่าสร้างบ้านใหม่ — ยอดลดหย่อน (บาท)', 'new_house_construction', 'คำนวณเอง: ทุก 1 ล้านค่าก่อสร้าง = 10,000 สูงสุด 100,000')}

          </div>
        </section>

        {/* 6. เงินบริจาค */}
        <section className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="bg-pink-100 text-pink-600 px-2 py-1 rounded-lg text-sm">6</span>
            เงินบริจาค
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {numField('บริจาคทั่วไปหรือบริจาคเพื่อการศึกษา (บาท)', 'donation_general', 'สูงสุด 10% ของเงินได้หลังหักค่าลดหย่อน')}
            {numField('บริจาคเพื่อการกีฬา/สถานพยาบาลรัฐ (บาท)', 'donation_education', 'กรอกยอดที่บริจาคจริง — ระบบคำนวณ 2 เท่าให้ สูงสุด 10% ของเงินได้')}
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
