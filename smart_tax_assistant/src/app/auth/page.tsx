// src/app/auth/page.tsx
import AuthFormCard from '@/components/AuthFormCard/AuthFormCard';

export default function AuthPage() {
  return (
    // [FIX] เปลี่ยนจาก items-center เป็น items-start และเพิ่ม Padding ด้านบน (pt-24)
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-start justify-center p-4 pt-24 sm:pt-32">
      
      {/* Animated background elements (เหมือนเดิม) */}
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-2xl opacity-40 animate-pulse-slow"></div>
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-2xl opacity-40 animate-pulse-slow delay-1000"></div>
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-indigo-200 rounded-full mix-blend-multiply filter blur-2xl opacity-40 animate-pulse-slow delay-500"></div>
      
      {/* Content container (เหมือนเดิม) */}
      <div className="relative z-10 w-full max-w-md">
        <AuthFormCard />
      </div>

    </div>
  );
}