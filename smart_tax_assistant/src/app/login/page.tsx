'use client'; 

import React, { useState } from 'react';
import Link from 'next/link';


export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null); 
  const [isLoading, setIsLoading] = useState(false); 

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    if (!email.trim() || !password) {
      setError('กรุณากรอกอีเมลและรหัสผ่าน');
      setIsLoading(false);
      return;
    }
   
    console.log('Logging in user:', { email, rememberMe }); 
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log('Simulated login complete');
    
    setError('ฟังก์ชันเข้าสู่ระบบยังไม่ได้ Implement'); 
    setIsLoading(false);
  };

  return (
    
    <div className="flex items-center justify-center min-h-screen py-16 px-4 sm:px-6 lg:px-8 pt-28 md:pt-36">
      <div className="max-w-md w-full space-y-10 bg-white p-10 md:p-12 rounded-2xl shadow-2xl border border-gray-100">
        <div>
           <div className="flex justify-center mb-4">
             <svg className="h-10 w-auto text-blue-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"> <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="rgba(59, 130, 246, 0.1)"/> <path d="M17 9.5L12 12L7 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> <path d="M12 17.5V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> <path d="M7 14.5L12 17.5L17 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/> </svg>
           </div>
          <h2 className="text-center text-3xl font-bold tracking-tight text-gray-900">
            เข้าสู่ระบบ SmartTax
          </h2>
          <p className="mt-3 text-center text-sm text-gray-600">
            ยังไม่มีบัญชี?{' '}
            <Link href="/register" className="font-medium text-blue-600 hover:text-blue-500 hover:underline">
              สร้างบัญชีใหม่
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
              <label htmlFor="email-address" className="block text-sm font-medium text-gray-700 mb-2">
                อีเมล
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

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  รหัสผ่าน
                </label>
                <div className="text-sm">
                  <a href="#" className="font-medium text-blue-600 hover:text-blue-500 hover:underline">
                    ลืมรหัสผ่าน?
                  </a>
                </div>
              </div>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none block w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out"
                placeholder="กรอกรหัสผ่านของคุณ"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
              จดจำฉันไว้ในระบบ
            </label>
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
                  กำลังเข้าสู่ระบบ...
                </>
              ) : (
                'เข้าสู่ระบบ'
              )}
            </button>
          </div>
        </form>

       
      </div>
    </div>
  );
}