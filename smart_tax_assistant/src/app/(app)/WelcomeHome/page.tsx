// src/app/(app)/WelcomeHome/page.tsx
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import Logo from '@/components/Logo';
import { menuItems } from '@/config/menuItems';
import {
  LogOut,
  User,
  BarChart3,
  Settings,
  ArrowRight,
  Calculator,
  FileText,
  TrendingUp,
  TrendingDown,
  Calendar,
  PieChart,
  Bell,
  Search,
  Menu,
  MoreHorizontal,
  Loader2,
  X,
  Home,
  MessageCircle,
  Target,
  Wallet,
} from 'lucide-react';
import Link from 'next/link';

export default function WelcomeHomePage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Loading state
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-gray-600">กำลังโหลด...</p>
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

  const handleLogout = async () => {
    try {
      await signOut({
        callbackUrl: '/',
        redirect: true,
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Get user info from session
  const user = {
    name: session?.user?.name || 'ผู้ใช้',
    email: session?.user?.email || '',
    image: session?.user?.image || null,
  };

  // Updated menu items
 

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation และ Mobile Menu เหมือนเดิม */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="เปิดเมนู"
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6 text-gray-600" />
              ) : (
                <Menu className="w-6 h-6 text-gray-600" />
              )}
            </button>
            <Logo />
          </div>

          <div className="flex-1 max-w-md mx-8 hidden md:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="ค้นหาหรือพิมพ์คำสั่ง..."
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-gray-50/50 hover:bg-white focus:bg-white transition-colors"
              />
              <kbd className="absolute right-3 top-1/2 transform -translate-y-1/2 px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-300 rounded">
                ⌘K
              </kbd>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-400 hover:text-gray-600 relative transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
            </button>

            <div className="flex items-center space-x-3">
              {user.image ? (
                <img
                  src={user.image}
                  alt={user.name}
                  className="w-8 h-8 rounded-full object-cover border-2 border-gray-200"
                />
              ) : (
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}

              <div className="hidden md:block">
                <p className="text-sm font-medium text-gray-700">{user.name}</p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>

              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-500 transition-colors group"
                title="ออกจากระบบ"
              >
                <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-50"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <div className="fixed left-0 top-0 h-full w-80 bg-white shadow-xl z-50 transform transition-transform duration-300 ease-in-out overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  {user.image ? (
                    <img
                      src={user.image}
                      alt={user.name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div>
                    <p className="font-medium text-gray-800">{user.name}</p>
                    <p className="text-sm text-gray-500">{user.email}</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>

              <div className="space-y-2">
                {menuItems.map((item, index) => {
                  const IconComponent = item.icon;
                  return (
                    <Link
                      key={index}
                      href={item.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center space-x-4 p-4 rounded-xl hover:bg-gray-50 transition-colors group"
                    >
                      <div
                        className={`w-10 h-10 rounded-lg flex items-center justify-center ${item.color} group-hover:scale-110 transition-transform`}
                      >
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-800 group-hover:text-gray-900">
                          {item.label}
                        </p>
                        <p className="text-sm text-gray-500 group-hover:text-gray-600">
                          {item.description}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transform group-hover:translate-x-1 transition-all" />
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Main Content พร้อม Charts */}
      <div className={`transition-all duration-300 ease-in-out ${
        isMobileMenuOpen ? 'ml-80' : 'ml-0'
      }`}>
        <div className="p-6">
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              ยินดีต้อนรับ, คุณ{user.name}! 👋
            </h2>
            <p className="text-gray-600 text-lg">
              คุณได้ประหยัดภาษี{' '}
              <span className="font-semibold text-green-600">
                ฿{dashboardData.taxReduction.toLocaleString()}
              </span>{' '}
              ไปแล้ว และคำนวณภาษีได้{' '}
              <span className="font-semibold text-blue-600">
                ฿{dashboardData.totalTax.toLocaleString()}
              </span>{' '}
              ทำได้ดีมาก! 🎉
            </p>
          </div>

          {/* Stats Cards (คืนกลับมา) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Calculator className="w-6 h-6 text-blue-600" />
                </div>
                <span className="text-green-500 text-sm font-medium flex items-center bg-green-50 px-2 py-1 rounded-full">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  12.5%
                </span>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-1">
                ภาษีที่คำนวณได้
              </h3>
              <p className="text-2xl font-bold text-gray-800">
                ฿{dashboardData.totalTax.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-2">เพิ่มขึ้นจากเดือนที่แล้ว</p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <TrendingDown className="w-6 h-6 text-green-600" />
                </div>
                <span className="text-green-500 text-sm font-medium flex items-center bg-green-50 px-2 py-1 rounded-full">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  18.2%
                </span>
              </div>
              <h3 className="text-gray-600 text-sm font-medium mb-1">
                ลดหย่อนภาษีได้
              </h3>
              <p className="text-2xl font-bold text-gray-800">
                ฿{dashboardData.taxReduction.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-2">ประหยัดได้มากขึ้น!</p>
            </div>
          </div>

          {/* Charts Section (คืนกลับมา) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">
                    ภาษีรายเดือน
                  </h3>
                  <p className="text-sm text-gray-500">
                    เปรียบเทียบรายเดือนในปีนี้
                  </p>
                </div>
                <button className="hover:bg-gray-100 p-2 rounded-lg transition-colors">
                  <MoreHorizontal className="w-4 h-4 text-gray-400" />
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
                      <span className="text-sm font-medium text-gray-600 w-8">
                        {item.month}
                      </span>
                      <div className="flex-1">
                        <div className="w-full bg-gray-100 rounded-full h-8 relative overflow-hidden">
                          <div
                            className={`h-8 rounded-full flex items-center justify-end pr-3 transition-all duration-1000 ${
                              isCurrentMonth
                                ? 'bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg'
                                : 'bg-gradient-to-r from-gray-300 to-gray-400'
                            }`}
                            style={{ width: `${percentage}%` }}
                          >
                            <span className="text-white text-xs font-medium">
                              ฿{item.amount.toLocaleString()}
                            </span>
                          </div>
                          {isCurrentMonth && (
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-600/20 animate-pulse"></div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              

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
                      className="text-gray-200"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="url(#gradient)"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray={`${
                        dashboardData.totalProgress * 2.51
                      } 251`}
                      strokeLinecap="round"
                      className="transition-all duration-1000"
                    />
                    <defs>
                      <linearGradient
                        id="gradient"
                        x1="0%"
                        y1="0%"
                        x2="100%"
                        y2="0%"
                      >
                        <stop offset="0%" stopColor="#3B82F6" />
                        <stop offset="100%" stopColor="#8B5CF6" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-gray-800">
                      {dashboardData.totalProgress}%
                    </span>
                    <span className="text-green-500 text-sm font-medium bg-green-50 px-2 py-1 rounded-full">
                      +10%
                    </span>
                  </div>
                </div>

                <p className="text-center text-gray-600 text-sm mb-6 px-2">
                  คุณได้รับ{' '}
                  <span className="font-semibold text-blue-600">
                    ฿{dashboardData.totalTax.toLocaleString()}
                  </span>{' '}
                  วันนี้ สูงกว่าเดือนที่แล้ว ทำได้ดีมาก! 🚀
                </p>

                <div className="w-full space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600 text-sm font-medium">
                      เป้าหมาย
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-800">
                        ฿{dashboardData.monthlyTarget / 1000}K
                      </span>
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-gray-600 text-sm font-medium">
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
                    <span className="text-gray-600 text-sm font-medium">วันนี้</span>
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
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  การดำเนินการด่วน
                </h3>
                <p className="text-sm text-gray-500">
                  เลือกสิ่งที่คุณต้องการทำต่อไป
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link href="/tax-calculator">
                <div className="group p-6 rounded-xl border border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 cursor-pointer hover:shadow-md">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center group-hover:bg-blue-200 group-hover:scale-110 transition-all">
                      <Calculator className="w-6 h-6 text-blue-600" />
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transform group-hover:translate-x-1 transition-all" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">คำนวณภาษี</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    เริ่มคำนวณภาษีใหม่สำหรับปีนี้
                  </p>
                  <div className="flex items-center text-sm font-medium text-blue-600">
                    เริ่มคำนวณ
                  </div>
                </div>
              </Link>

              <Link href="/tax-forms">
                <div className="group p-6 rounded-xl border border-gray-200 hover:border-green-500 hover:bg-green-50 transition-all duration-200 cursor-pointer hover:shadow-md">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center group-hover:bg-green-200 group-hover:scale-110 transition-all">
                      <FileText className="w-6 h-6 text-green-600" />
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 transform group-hover:translate-x-1 transition-all" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">แบบฟอร์มภาษี</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    จัดการเอกสารและแบบฟอร์มภาษี
                  </p>
                  <div className="flex items-center text-sm font-medium text-green-600">
                    ดูแบบฟอร์ม
                  </div>
                </div>
              </Link>

              <Link href="/tax-reports">
                <div className="group p-6 rounded-xl border border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition-all duration-200 cursor-pointer hover:shadow-md">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center group-hover:bg-purple-200 group-hover:scale-110 transition-all">
                      <BarChart3 className="w-6 h-6 text-purple-600" />
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-purple-600 transform group-hover:translate-x-1 transition-all" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">รายงานภาษี</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    วิเคราะห์และดูรายงานภาษี
                  </p>
                  <div className="flex items-center text-sm font-medium text-purple-600">
                    ดูรายงาน
                  </div>
                </div>
              </Link>

              <Link href="/profile-settings">
                <div className="group p-6 rounded-xl border border-gray-200 hover:border-orange-500 hover:bg-orange-50 transition-all duration-200 cursor-pointer hover:shadow-md">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center group-hover:bg-orange-200 group-hover:scale-110 transition-all">
                      <Settings className="w-6 h-6 text-orange-600" />
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-orange-600 transform group-hover:translate-x-1 transition-all" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-2">ตั้งค่าบัญชี</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    จัดการข้อมูลส่วนตัวและการตั้งค่า
                  </p>
                  <div className="flex items-center text-sm font-medium text-orange-600">
                    ตั้งค่า
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}