// src/components/AuthFormCard/AuthFormCard.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Lock, Mail, User, Check, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-react';
import { signIn } from 'next-auth/react';

// --- OTP Verification Form Component ---
const OTPVerificationForm = ({
  email,
  purpose,
  onSuccess,
  onBack
}: {
  email: string;
  purpose: 'EMAIL_VERIFICATION' | 'LOGIN_MFA';
  onSuccess: () => void;
  onBack: () => void;
}) => {
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otpCode, purpose }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'การยืนยัน OTP ล้มเหลว');
      }

      if (data.success) {
        alert(`ยืนยัน OTP สำเร็จ! ${purpose === 'EMAIL_VERIFICATION' ? 'กรุณาเข้าสู่ระบบ' : ''}`);
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'ไม่สามารถส่ง OTP ใหม่ได้');
      }

      alert('ส่ง OTP ใหม่สำเร็จ! กรุณาตรวจสอบอีเมลของคุณ');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-full mb-3">
          <ShieldCheck className="h-6 w-6 text-white" />
        </div>
        <h2 className="text-2xl font-semibold text-slate-800">
          ยืนยัน OTP
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          กรุณากรอกรหัส OTP ที่ส่งไปยัง<br />
          <span className="font-medium text-slate-800">{email}</span>
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {error && (
          <div className="p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
            <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
          </div>
        )}

        <div>
          <label htmlFor="otp" className="block text-sm font-medium text-slate-700 mb-2">
            รหัส OTP (6 หลัก)
          </label>
          <input
            id="otp"
            type="text"
            required
            maxLength={6}
            pattern="[0-9]{6}"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
            className="w-full px-4 py-3 text-center text-2xl font-semibold tracking-widest border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white"
            placeholder="000000"
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={isLoading || otpCode.length !== 6}
            className={`w-full flex justify-center items-center py-2.5 px-6 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors text-sm ${
              isLoading || otpCode.length !== 6 ? 'opacity-60 cursor-not-allowed' : ''
            }`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                กำลังยืนยัน...
              </>
            ) : (
              <>
                ยืนยัน OTP
                <Check className="ml-2 h-4 w-4" />
              </>
            )}
          </button>
        </div>

        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={onBack}
            className="text-slate-600 hover:text-slate-800 transition-colors"
          >
            ← ย้อนกลับ
          </button>

          <button
            type="button"
            onClick={handleResend}
            disabled={isResending}
            className="flex items-center text-blue-600 hover:text-blue-700 transition-colors disabled:opacity-50"
          >
            {isResending ? (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-blue-600 border-t-transparent mr-1"></div>
                กำลังส่ง...
              </>
            ) : (
              <>
                <RefreshCw className="h-3 w-3 mr-1" />
                ส่ง OTP ใหม่
              </>
            )}
          </button>
        </div>
      </form>

      <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
        <p className="text-xs text-slate-600">
          <strong>หมายเหตุ:</strong> รหัส OTP จะหมดอายุใน 10 นาที
        </p>
      </div>
    </div>
  );
};

// --- Login Form Component ---
const LoginForm = ({
  onSwitchToRegister,
  onShowOTP
}: {
  onSwitchToRegister: () => void;
  onShowOTP: (email: string, password: string) => void;
}) => {
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

    try {
      const response = await fetch('/api/auth/login-mfa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (data.requiresEmailVerification && data.redirectUrl) {
        router.push(data.redirectUrl);
        return;
      }

      if (!response.ok) {
        throw new Error(data.error || 'เข้าสู่ระบบล้มเหลว');
      }

      if (data.requiresOTP) {
        onShowOTP(email, password);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-full mb-3">
          <Lock className="h-6 w-6 text-white" />
        </div>
        <h2 className="text-2xl font-semibold text-slate-800">
          เข้าสู่ระบบ
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          ยังไม่มีบัญชี?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            สร้างบัญชีใหม่
          </button>
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {error && (
          <div className="p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
            <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
          </div>
        )}

        <div className="space-y-3">
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              id="email-address"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
              placeholder="you@example.com"
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
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
              className="h-3.5 w-3.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
            />
            <label htmlFor="remember-me" className="ml-2 text-slate-600">
              จดจำฉันไว้
            </label>
          </div>
          <a href="#" className="font-medium text-blue-600 hover:text-blue-700 transition-colors">
            ลืมรหัสผ่าน?
          </a>
        </div>

        <div>
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full flex justify-center items-center py-2.5 px-6 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors text-sm ${isLoading ? 'opacity-60 cursor-wait' : ''}`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
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
const RegisterForm = ({
  onSwitchToLogin,
  onShowOTP
}: {
  onSwitchToLogin: () => void;
  onShowOTP: (email: string) => void;
}) => {
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

      if (data.ok && data.requiresEmailVerification) {
        onShowOTP(email);
      } else {
        alert('สร้างบัญชีสำเร็จแล้ว! กรุณาเข้าสู่ระบบ');
        onSwitchToLogin();
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-full mb-3">
          <User className="h-6 w-6 text-white" />
        </div>
        <h2 className="text-2xl font-semibold text-slate-800">
          สร้างบัญชีใหม่
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          มีบัญชีอยู่แล้ว?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            เข้าสู่ระบบ
          </button>
        </p>
      </div>

      <form className="space-y-3" onSubmit={handleSubmit}>
        {error && (
          <div className="p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
            <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              name="firstName"
              type="text"
              required
              className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
              placeholder="ชื่อ"
              autoComplete="given-name"
            />
          </div>

          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              name="lastName"
              type="text"
              required
              className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
              placeholder="นามสกุล"
              autoComplete="family-name"
            />
          </div>
        </div>

        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            name="email"
            type="email"
            required
            className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
            placeholder="อีเมล"
          />
        </div>

        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            name="password"
            type="password"
            required
            className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
            placeholder="ตั้งรหัสผ่าน"
          />
        </div>

        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            name="confirm-password"
            type="password"
            required
            className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
            placeholder="ยืนยันรหัสผ่าน"
          />
        </div>

        <div className="flex items-start pt-1">
          <input
            id="terms-agreement"
            name="terms-agreement"
            type="checkbox"
            required
            className="h-3.5 w-3.5 text-blue-600 rounded border-slate-300 mt-0.5 focus:ring-blue-500"
          />
          <label htmlFor="terms-agreement" className="ml-2 text-xs text-slate-600">
            ฉันยอมรับ{' '}
            <Link href="/terms" className="font-medium text-blue-600 hover:text-blue-700 transition-colors">
              ข้อกำหนด
            </Link>
            {' '}และ{' '}
            <Link href="/privacy" className="font-medium text-blue-600 hover:text-blue-700 transition-colors">
              นโยบายความเป็นส่วนตัว
            </Link>
          </label>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full flex justify-center items-center py-2.5 px-6 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors text-sm ${isLoading ? 'opacity-60 cursor-wait' : ''}`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
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
  const router = useRouter();
  const [view, setView] = useState<'login' | 'register' | 'otp-email' | 'otp-login'>('login');
  const [otpEmail, setOtpEmail] = useState('');
  const [loginCredentials, setLoginCredentials] = useState({ email: '', password: '' });

  const handleShowOTPForEmail = (email: string) => {
    setOtpEmail(email);
    setView('otp-email');
  };

  const handleShowOTPForLogin = (email: string, password: string) => {
    setOtpEmail(email);
    setLoginCredentials({ email, password });
    setView('otp-login');
  };

  const handleOTPEmailSuccess = () => {
    setView('login');
  };

  const handleOTPLoginSuccess = async () => {
    const result = await signIn('credentials', {
      redirect: false,
      email: loginCredentials.email,
      password: loginCredentials.password,
    });

    if (result?.error) {
      alert('เกิดข้อผิดพลาดในการเข้าสู่ระบบ: ' + result.error);
      setView('login');
    } else if (result?.ok) {
      console.log('Login successful with NextAuth!');
      router.push('/WelcomeHome');
    }
  };

  return (
    <div className="w-full">
      {view === 'login' && (
        <LoginForm
          onSwitchToRegister={() => setView('register')}
          onShowOTP={handleShowOTPForLogin}
        />
      )}

      {view === 'register' && (
        <RegisterForm
          onSwitchToLogin={() => setView('login')}
          onShowOTP={handleShowOTPForEmail}
        />
      )}

      {view === 'otp-email' && (
        <OTPVerificationForm
          email={otpEmail}
          purpose="EMAIL_VERIFICATION"
          onSuccess={handleOTPEmailSuccess}
          onBack={() => setView('login')}
        />
      )}

      {view === 'otp-login' && (
        <OTPVerificationForm
          email={otpEmail}
          purpose="LOGIN_MFA"
          onSuccess={handleOTPLoginSuccess}
          onBack={() => setView('login')}
        />
      )}
    </div>
  );
}
