'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [userType, setUserType] = useState('');
  const [otherUserType, setOtherUserType] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    if (!name.trim() || !email.trim() || !password || !confirmPassword || !userType) {
      setError('กรุณากรอกข้อมูลให้ครบทุกช่อง');
      setIsLoading(false);
      return;
    }
    if (password !== confirmPassword) {
      setError('รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน');
      setIsLoading(false);
      return;
    }
    if (password.length < 6) {
       setError('รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร');
       setIsLoading(false);
       return;
    }

    console.log('Registering user:', { name, email, userType });
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log('Simulated registration complete');
    setError('ฟังก์ชันลงทะเบียนยังไม่ได้ Implement');
    setIsLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-screen py-16 px-4 sm:px-6 lg:px-8 pt-28 md:pt-36">
      <div className="max-w-lg w-full space-y-10 bg-white p-10 md:p-12 rounded-2xl shadow-2xl border border-gray-100">
        <div>
           <div className="flex justify-center mb-4">
             <svg className="h-10 w-auto text-blue-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"> <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="rgba(59, 130, 246, 0.1)"/> <path d="M17 9.5L12 12L7 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> <path d="M12 17.5V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> <path d="M7 14.5L12 17.5L17 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> </svg>
           </div>
          <h2 className="text-center text-3xl font-bold tracking-tight text-gray-900">
            สร้างบัญชี SmartTax
          </h2>
          <p className="mt-3 text-center text-sm text-gray-600">
            จัดการภาษีอย่างชาญฉลาด หรือ{' '}
            <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500 hover:underline">
              เข้าสู่ระบบ
            </Link>
          </p>
        </div>

        <form className="space-y-8" onSubmit={handleSubmit}>
          {error && (
            <div className="p-4 text-sm text-red-800 bg-red-100 rounded-lg border border-red-300" role="alert">
              <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label htmlFor="user-type" className="block text-sm font-medium text-gray-700 mb-2">
                ประเภทผู้ใช้งาน
              </label>
              <select
                id="user-type"
                name="user-type"
                required
                value={userType}
                onChange={(e) => setUserType(e.target.value)} 
                className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out bg-white"
              >
                <option value="" disabled>-- เลือกประเภท --</option>
                <option value="individual">บุคคลธรรมดา (ยื่น ภ.ง.ด. 90/91)</option>
                <option value="merchant">พ่อค้า/แม่ค้า/ฟรีแลนซ์ (ยื่น ภ.ง.ด. 94/90)</option>
                <option value="sme">เจ้าของกิจการ SME</option>
                <option value="other">อื่นๆ</option>
              </select>
            </div>
                   {/* เลือกอาชีพอื่น */}
            {userType === 'other' && (
              <div className="transition-all duration-300 ease-in-out"> 
                <label htmlFor="other-user-type" className="block text-sm font-medium text-gray-700 mb-2">
                  ระบุประเภทผู้ใช้งานอื่นๆ
                </label>
                <input
                  id="other-user-type"
                  name="other-user-type"
                  type="text"
                  required={userType === 'other'} 
                  value={otherUserType}
                  onChange={(e) => setOtherUserType(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
                  placeholder="เช่น นักศึกษา, ว่างงาน, เกษตรกร"
                />
              </div>
            )}

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                ชื่อ-นามสกุล (ตามบัตรประชาชน)
              </label>
              <input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)} 
                className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
                placeholder="กรอกชื่อและนามสกุลจริง"
              />
            </div>

            <div>
              <label htmlFor="email-address" className="block text-sm font-medium text-gray-700 mb-2">
                อีเมลสำหรับเข้าสู่ระบบ
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)} 
                className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
                placeholder="you@example.com"
              />
            </div>

             <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    ตั้งรหัสผ่าน
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)} 
                    className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
                    placeholder="อย่างน้อย 6 ตัวอักษร"
                  />
                </div>
                 <div>
                  <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 mb-2">
                    ยืนยันรหัสผ่าน
                  </label>
                  <input
                    id="confirm-password"
                    name="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)} 
                    className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
                    placeholder="กรอกรหัสผ่านอีกครั้ง"
                  />
                </div>
            </div>
          </div>

          <div className="flex items-start pt-4">
            <div className="flex-shrink-0">
              <input
                id="terms-agreement"
                name="terms-agreement"
                type="checkbox"
                required
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
              />
            </div>
            <div className="ml-3">
              <label htmlFor="terms-agreement" className="text-sm text-gray-700">
                ฉันได้อ่านและยอมรับ <Link href="/terms" target="_blank" className="font-medium text-blue-600 hover:text-blue-500 hover:underline">ข้อกำหนดการใช้งาน</Link> และ <Link href="/privacy" target="_blank" className="font-medium text-blue-600 hover:text-blue-500 hover:underline">นโยบายความเป็นส่วนตัว</Link> ของ SmartTax
              </label>
            </div>
          </div>

          <div className="pt-6">
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-full shadow-lg text-base font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out ${isLoading ? 'opacity-75 cursor-wait' : 'hover:scale-105 transform'}`}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  กำลังดำเนินการ...
                </>
              ) : (
                'สร้างบัญชีใช้งาน'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}