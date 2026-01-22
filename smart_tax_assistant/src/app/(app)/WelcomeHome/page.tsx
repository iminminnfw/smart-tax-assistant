// src/app/(app)/WelcomeHome/page.tsx
'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { AppNavigation } from '@/components/AppNavigation';
import {
  BarChart3,
  Settings,
  ArrowRight,
  Calculator,
  FileText,
  TrendingUp,
  TrendingDown,
  MoreHorizontal,
  Loader2,
} from 'lucide-react';
import Link from 'next/link';

export default function WelcomeHomePage() {
  const router = useRouter();
  const { data: session, status } = useSession();

  // Loading state
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-slate-600">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  // Redirect if not authenticated
  if (status === 'unauthenticated') {
    router.push('/auth');
    return null;
  }

  // Mock dashboard data (คืนกลับมา)
  const dashboardData = {
    totalTax: 45680,
    monthlyTarget: 50000,
    taxReduction: 8540,
    completedForms: 3,
    totalProgress: 76.2,
    monthlyData: [
      { month: 'ม.ค.', amount: 35000 },
      { month: 'ก.พ.', amount: 42000 },
      { month: 'มี.ค.', amount: 38000 },
      { month: 'เม.ย.', amount: 45000 },
      { month: 'พ.ค.', amount: 41000 },
      { month: 'มิ.ย.', amount: 48000 },
      { month: 'ก.ค.', amount: 45680 },
    ],
  };

  const user = {
    name: session?.user?.name || 'ผู้ใช้',
    email: session?.user?.email || '',
    image: session?.user?.image || null,
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <AppNavigation />

      <div>
        <div className="p-6">
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-slate-800 mb-2">
              ยินดีต้อนรับ, คุณ{user.name}
            </h2>
            <p className="text-slate-600">
              คุณได้ประหยัดภาษี{' '}
              <span className="font-medium text-green-600">
                ฿{dashboardData.taxReduction.toLocaleString()}
              </span>{' '}
              ไปแล้ว และคำนวณภาษีได้{' '}
              <span className="font-medium text-blue-600">
                ฿{dashboardData.totalTax.toLocaleString()}
              </span>
            </p>
          </div>

          {/* Stats Cards (คืนกลับมา) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:border-slate-300 transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Calculator className="w-6 h-6 text-blue-600" />
                </div>
                <span className="text-green-500 text-sm font-medium flex items-center bg-green-50 px-2 py-1 rounded-full">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  12.5%
                </span>
              </div>
              <h3 className="text-slate-600 text-sm font-medium mb-1">
                ภาษีที่คำนวณได้
              </h3>
              <p className="text-2xl font-bold text-slate-800">
                ฿{dashboardData.totalTax.toLocaleString()}
              </p>
              <p className="text-xs text-slate-500 mt-2">เพิ่มขึ้นจากเดือนที่แล้ว</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:border-slate-300 transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <TrendingDown className="w-6 h-6 text-green-600" />
                </div>
                <span className="text-green-500 text-sm font-medium flex items-center bg-green-50 px-2 py-1 rounded-full">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  18.2%
                </span>
              </div>
              <h3 className="text-slate-600 text-sm font-medium mb-1">
                ลดหย่อนภาษีได้
              </h3>
              <p className="text-2xl font-bold text-slate-800">
                ฿{dashboardData.taxReduction.toLocaleString()}
              </p>
              <p className="text-xs text-slate-500 mt-2">ประหยัดได้มากขึ้น!</p>
            </div>
          </div>

          {/* Charts Section (คืนกลับมา) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">
                    ภาษีรายเดือน
                  </h3>
                  <p className="text-sm text-slate-500">
                    เปรียบเทียบรายเดือนในปีนี้
                  </p>
                </div>
                <button className="hover:bg-slate-100 p-2 rounded-lg transition-colors">
                  <MoreHorizontal className="w-4 h-4 text-slate-400" />
                </button>
              </div>

              <div className="space-y-3">
                {dashboardData.monthlyData.map((item, index) => {
                  const maxAmount = Math.max(
                    ...dashboardData.monthlyData.map((d) => d.amount)
                  );
                  const percentage = (item.amount / maxAmount) * 100;
                  const isCurrentMonth =
                    index === dashboardData.monthlyData.length - 1;

                  return (
                    <div key={index} className="flex items-center space-x-4 group">
                      <span className="text-sm font-medium text-slate-600 w-8">
                        {item.month}
                      </span>
                      <div className="flex-1">
                        <div className="w-full bg-slate-100 rounded-full h-8 relative overflow-hidden">
                          <div
                            className={`h-8 rounded-full flex items-center justify-end pr-3 transition-all duration-500 ${
                              isCurrentMonth
                                ? 'bg-blue-600'
                                : 'bg-slate-300'
                            }`}
                            style={{ width: `${percentage}%` }}
                          >
                            <span className="text-white text-xs font-medium">
                              ฿{item.amount.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
              

              <div className="flex flex-col items-center">
                <div className="relative w-32 h-32 mb-4">
                  <svg
                    className="w-32 h-32 transform -rotate-90"
                    viewBox="0 0 100 100"
                  >
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      className="text-slate-200"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="#2563EB"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray={`${
                        dashboardData.totalProgress * 2.51
                      } 251`}
                      strokeLinecap="round"
                      className="transition-all duration-500"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-semibold text-slate-800">
                      {dashboardData.totalProgress}%
                    </span>
                    <span className="text-green-600 text-sm font-medium bg-green-50 px-2 py-1 rounded-lg">
                      +10%
                    </span>
                  </div>
                </div>

                <p className="text-center text-slate-600 text-sm mb-6 px-2">
                  คุณได้รับ{' '}
                  <span className="font-medium text-blue-600">
                    ฿{dashboardData.totalTax.toLocaleString()}
                  </span>{' '}
                  วันนี้ สูงกว่าเดือนที่แล้ว
                </p>

                <div className="w-full space-y-4">
                  <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="text-slate-600 text-sm font-medium">
                      เป้าหมาย
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-800">
                        ฿{dashboardData.monthlyTarget / 1000}K
                      </span>
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-slate-600 text-sm font-medium">
                      ผลงาน
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-green-800">
                        ฿{dashboardData.totalTax / 1000}K
                      </span>
                      <TrendingUp className="w-4 h-4 text-green-500" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-slate-600 text-sm font-medium">วันนี้</span>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-blue-800">
                        ฿{dashboardData.totalTax / 1000}K
                      </span>
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions (คืนกลับมา) */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-800">
                  การดำเนินการด่วน
                </h3>
                <p className="text-sm text-slate-500">
                  เลือกสิ่งที่คุณต้องการทำต่อไป
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link href="/tax-calculator">
                <div className="group p-5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Calculator className="w-5 h-5 text-blue-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                  </div>
                  <h4 className="font-medium text-slate-800 mb-1">คำนวณภาษี</h4>
                  <p className="text-sm text-slate-500 mb-3">
                    เริ่มคำนวณภาษีใหม่สำหรับปีนี้
                  </p>
                  <span className="text-sm font-medium text-blue-600">
                    เริ่มคำนวณ
                  </span>
                </div>
              </Link>

              <Link href="/tax-forms">
                <div className="group p-5 rounded-lg border border-slate-200 hover:border-green-300 hover:bg-green-50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-green-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-green-600 transition-colors" />
                  </div>
                  <h4 className="font-medium text-slate-800 mb-1">แบบฟอร์มภาษี</h4>
                  <p className="text-sm text-slate-500 mb-3">
                    จัดการเอกสารและแบบฟอร์มภาษี
                  </p>
                  <span className="text-sm font-medium text-green-600">
                    ดูแบบฟอร์ม
                  </span>
                </div>
              </Link>

              <Link href="/tax-reports">
                <div className="group p-5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <BarChart3 className="w-5 h-5 text-blue-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                  </div>
                  <h4 className="font-medium text-slate-800 mb-1">รายงานภาษี</h4>
                  <p className="text-sm text-slate-500 mb-3">
                    วิเคราะห์และดูรายงานภาษี
                  </p>
                  <span className="text-sm font-medium text-blue-600">
                    ดูรายงาน
                  </span>
                </div>
              </Link>

              <Link href="/profile-settings">
                <div className="group p-5 rounded-lg border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                      <Settings className="w-5 h-5 text-slate-600" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
                  </div>
                  <h4 className="font-medium text-slate-800 mb-1">ตั้งค่าบัญชี</h4>
                  <p className="text-sm text-slate-500 mb-3">
                    จัดการข้อมูลส่วนตัวและการตั้งค่า
                  </p>
                  <span className="text-sm font-medium text-slate-600">
                    ตั้งค่า
                  </span>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}