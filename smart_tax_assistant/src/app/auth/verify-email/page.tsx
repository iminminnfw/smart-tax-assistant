// src/app/auth/verify-email/page.tsx
'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Mail, ShieldCheck, ArrowLeft, RefreshCw, Check } from 'lucide-react';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailFromUrl = searchParams.get('email') || '';

  const [step, setStep] = useState<'request' | 'verify'>('request');
  const [email, setEmail] = useState(emailFromUrl);
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    if (emailFromUrl) {
      setEmail(emailFromUrl);
    }
  }, [emailFromUrl]);

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/auth/request-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'ไม่สามารถส่ง OTP ได้');
      }

      if (data.success) {
        setSuccess('ส่ง OTP สำเร็จ! กรุณาตรวจสอบอีเมลของคุณ');
        setStep('verify');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          otpCode,
          purpose: 'EMAIL_VERIFICATION',
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'การยืนยัน OTP ล้มเหลว');
      }

      if (data.success) {
        setSuccess('ยืนยันอีเมลสำเร็จ! กำลัง redirect...');
        setTimeout(() => {
          router.push('/auth');
        }, 1500);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setIsResending(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose: 'EMAIL_VERIFICATION' }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'ไม่สามารถส่ง OTP ใหม่ได้');
      }

      setSuccess('ส่ง OTP ใหม่สำเร็จ!');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl border border-slate-200 p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-full mb-4">
              <ShieldCheck className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-semibold text-slate-800">
              ยืนยันอีเมล
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              {step === 'request'
                ? 'กรอกอีเมลของคุณเพื่อขอรหัส OTP'
                : 'กรอกรหัส OTP ที่ส่งไปยังอีเมลของคุณ'}
            </p>
          </div>

          {/* Alert Messages */}
          {error && (
            <div className="mb-4 p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
              <span className="font-medium">เกิดข้อผิดพลาด!</span> {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 text-sm text-green-700 bg-green-50 rounded-lg border border-green-200">
              <span className="font-medium">สำเร็จ!</span> {success}
            </div>
          )}

          {/* Step 1: Request OTP Form */}
          {step === 'request' && (
            <form onSubmit={handleRequestOTP} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                  อีเมล
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white text-sm"
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`w-full flex justify-center items-center py-2.5 px-6 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors text-sm ${
                  isLoading ? 'opacity-60 cursor-not-allowed' : ''
                }`}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    กำลังส่ง OTP...
                  </>
                ) : (
                  <>
                    ส่ง OTP
                    <Mail className="ml-2 h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Step 2: Verify OTP Form */}
          {step === 'verify' && (
            <form onSubmit={handleVerifyOTP} className="space-y-4">
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
                <p className="mt-2 text-xs text-slate-600">
                  ส่งไปยัง: <span className="font-medium">{email}</span>
                </p>
              </div>

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

              <div className="flex items-center justify-between text-sm">
                <button
                  type="button"
                  onClick={() => setStep('request')}
                  className="flex items-center text-slate-600 hover:text-slate-800 transition-colors"
                >
                  <ArrowLeft className="h-3 w-3 mr-1" />
                  เปลี่ยนอีเมล
                </button>

                <button
                  type="button"
                  onClick={handleResendOTP}
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
          )}

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-slate-200">
            <div className="text-center">
              <button
                type="button"
                onClick={() => router.push('/auth')}
                className="text-sm text-slate-600 hover:text-slate-800 transition-colors"
              >
                ← กลับไปหน้าเข้าสู่ระบบ
              </button>
            </div>
          </div>

          {/* Info Box */}
          <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <p className="text-xs text-slate-600">
              <strong>หมายเหตุ:</strong> รหัส OTP จะหมดอายุใน 10 นาที และกรอกผิดได้ไม่เกิน 5 ครั้ง
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
