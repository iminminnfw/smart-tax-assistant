// src/components/AuthFormCard/AuthFormCard.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation'; 
import { Lock, Mail, User, Building, ChevronDown, Check, ArrowRight, Sparkles } from 'lucide-react';
import { signIn } from 'next-auth/react';
// --- Login Form Component ---
const LoginForm = ({ onSwitchToRegister }: { onSwitchToRegister: () => void }) => {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    console.log('ข้อมูลที่จะส่งไปให้ signIn:', { email, password });
    
    const result = await signIn('credentials', {
      redirect: false, // สำคัญมาก: บอก NextAuth ว่าไม่ต้อง redirect เอง
      email: email,
      password: password,
    });

    setIsLoading(false);

    if (result?.error) {
      // ถ้าล็อกอินไม่ผ่าน, NextAuth จะคืนค่า error message ที่เรา throw ไว้ใน authorize()
      setError(result.error);
    } else if (result?.ok) {
      // ถ้าล็อกอินสำเร็จ (result.ok เป็น true)
      console.log('Login successful with NextAuth!');
      router.push('/WelcomeHome'); // สั่ง redirect ด้วยตัวเอง
    }
};

  return (
    <div className="w-full">
      {/* Header with gradient text */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-3 shadow-lg">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          เข้าสู่ระบบ SmartTax
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          ยังไม่มีบัญชี?{' '}
          <button 
            type="button" 
            onClick={onSwitchToRegister} 
            className="font-medium text-blue-600 hover:text-blue-500 hover:underline focus:outline-none transition-colors"
          >
            สร้างบัญชีใหม่
          </button>
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {error && (
          <div className="p-3 text-sm text-red-800 bg-red-50 rounded-lg border border-red-200">
            <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
          </div>
        )}
        
        <div className="space-y-3">
          <div className="relative group">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
            <input 
              id="email-address" 
              name="email" 
              type="email" 
              required 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm" 
              placeholder="you@example.com"
            />
          </div>
          
          <div className="relative group">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
            <input 
              id="password" 
              name="password" 
              type="password" 
              required 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm" 
              placeholder="กรอกรหัสผ่าน"
            />
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center">
            <input 
              id="remember-me" 
              name="remember-me" 
              type="checkbox" 
              checked={rememberMe} 
              onChange={(e) => setRememberMe(e.target.checked)} 
              className="h-3 w-3 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <label htmlFor="remember-me" className="ml-2 text-gray-700">
              จดจำฉันไว้
            </label>
          </div>
          <a href="#" className="font-medium text-blue-600 hover:underline hover:text-blue-500 transition-colors">
            ลืมรหัสผ่าน?
          </a>
        </div>

        <div>
          <button 
            type="submit" 
            disabled={isLoading} 
            className={`w-full flex justify-center items-center py-3 px-4 rounded-lg font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 hover:shadow-lg text-sm ${isLoading ? 'opacity-75 cursor-wait' : ''}`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                กำลังเข้าสู่ระบบ...
              </>
            ) : (
              <>
                เข้าสู่ระบบ
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

// --- Register Form Component ---
const RegisterForm = ({ onSwitchToLogin }: { onSwitchToLogin: () => void }) => {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    
    const formData = new FormData(event.currentTarget);
    const firstName = (formData.get('firstName') as string).trim();
    const lastName = (formData.get('lastName') as string).trim();
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    const confirmPassword = formData.get('confirm-password') as string;

    // ตรวจสอบรหัสผ่าน
    if (password !== confirmPassword) {
      setError('รหัสผ่านไม่ตรงกัน');
      setIsLoading(false);
      return;
    }

    try {

      const playload = {
        firstName,
        lastName,
        name: `${firstName} ${lastName}`.trim(),
        email,
        password,
      };

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(playload),
      });

      const data = await response.json();

      if (!response.ok) {
  
        throw new Error(data.error || 'มีบางอย่างผิดพลาด');
      }

      //console.log('Registration successful:', data);
      alert('สร้างบัญชีสำเร็จแล้ว! กรุณาเข้าสู่ระบบ');
      onSwitchToLogin();

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      {/* Header with gradient text */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full mb-3 shadow-lg">
          <User className="h-6 w-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          สร้างบัญชี SmartTax
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          มีบัญชีอยู่แล้ว?{' '}
          <button 
            type="button" 
            onClick={onSwitchToLogin} 
            className="font-medium text-purple-600 hover:text-purple-500 hover:underline focus:outline-none transition-colors"
          >
            เข้าสู่ระบบ
          </button>
        </p>
      </div>

      <form className="space-y-3" onSubmit={handleSubmit}>
        {error && (
          <div className="p-3 text-sm text-red-800 bg-red-50 rounded-lg border border-red-200">
            <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-3">
  <div className="relative group">
    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-purple-500 transition-colors" />
    <input
      name="firstName"
      type="text"
      required
      className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm"
      placeholder="ชื่อ"
      autoComplete="given-name"
    />
  </div>

  <div className="relative group">
    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-purple-500 transition-colors" />
    <input
      name="lastName"
      type="text"
      required
      className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm"
      placeholder="นามสกุล"
      autoComplete="family-name"
    />
  </div>
</div>

        <div className="relative group">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-purple-500 transition-colors" />
          <input 
            name="email" 
            type="email" 
            required 
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm" 
            placeholder="อีเมล"
          />
        </div>

        <div className="relative group">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-purple-500 transition-colors" />
          <input 
            name="password" 
            type="password" 
            required 
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm" 
            placeholder="ตั้งรหัสผ่าน"
          />
        </div>

        <div className="relative group">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-purple-500 transition-colors" />
          <input 
            name="confirm-password" 
            type="password" 
            required 
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 hover:bg-white focus:bg-white text-sm" 
            placeholder="ยืนยันรหัสผ่าน"
          />
        </div>

        <div className="flex items-start pt-1">
          <input 
            id="terms-agreement" 
            name="terms-agreement" 
            type="checkbox" 
            required 
            className="h-3 w-3 text-purple-600 rounded border-gray-300 mt-1 focus:ring-purple-500"
          />
          <label htmlFor="terms-agreement" className="ml-2 text-xs text-gray-700">
            ฉันยอมรับ{' '}
            <Link href="/terms" className="font-medium text-purple-600 hover:underline hover:text-purple-500 transition-colors">
              ข้อกำหนด
            </Link>
            {' '}และ{' '}
            <Link href="/privacy" className="font-medium text-purple-600 hover:underline hover:text-purple-500 transition-colors">
              นโยบายความเป็นส่วนตัว
            </Link>
          </label>
        </div>

        <div className="pt-2">
          <button 
            type="submit" 
            disabled={isLoading} 
            className={`w-full flex justify-center items-center py-3 px-4 rounded-lg font-semibold text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 transition-all duration-300 transform hover:scale-105 hover:shadow-lg text-sm ${isLoading ? 'opacity-75 cursor-wait' : ''}`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                กำลังสร้างบัญชี...
              </>
            ) : (
              <>
                สร้างบัญชีใช้งาน
                <Check className="ml-2 h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

// --- Main Flip Card Component ---
export default function AuthFormCard() {
  const [isFlipped, setIsFlipped] = useState(false);

  return (
    <div className="w-full [perspective:1000px]">
      {/* The actual flipping element */}
      <div 
        className="relative w-full h-full [transform-style:preserve-3d] transition-transform duration-700 ease-in-out"
        style={{ transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
      >
        {/* Front Side: Login Form */}
        <div className="absolute w-full h-full [backface-visibility:hidden]">
          <LoginForm onSwitchToRegister={() => setIsFlipped(true)} />
        </div>

        {/* Back Side: Register Form */}
        <div className="absolute w-full h-full [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <RegisterForm onSwitchToLogin={() => setIsFlipped(false)} />
        </div>
      </div>
    </div>
  );
}