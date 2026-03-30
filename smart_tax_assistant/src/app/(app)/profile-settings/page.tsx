// src/app/(app)/profile-settings/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { AppNavigation } from '@/components/AppNavigation';
import {
  User,
  Loader2,
  Home,
  Camera,
  Edit3,
  Save,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Shield,
  CreditCard,
  FileText,
  Eye,
  EyeOff,
  Lock,
  Briefcase,
  Bell,
} from 'lucide-react';
import Link from 'next/link';

// Types
interface UserProfileData {
  personalInfo: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    dateOfBirth: string;
    address: string;
    district: string;
    province: string;
    postalCode: string;
  };
  taxInfo: {
    occupation: string;
    annualIncome: string;
    taxType: string;
    incomeType: string;
    expenseDeductionType: string;
    isVatRegistered: boolean;
  };
  preferences: {
    language: string;
    notifications: {
      enabled: boolean;
      email: boolean;
    };
  };
  meta?: {
    id: string;
    name: string;
    image: string;
    createdAt: string;
  };
}

export default function ProfileSettingsPage() {
  const router = useRouter();
  const { data: session, status } = useSession();

  // States
  const [userData, setUserData] = useState<UserProfileData>({
    personalInfo: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      dateOfBirth: '',
      address: '',
      district: '',
      province: '',
      postalCode: '',
    },
    taxInfo: {
      occupation: '',
      annualIncome: '',
      taxType: 'individual',
      incomeType: '40(8)',
      expenseDeductionType: 'standard',
      isVatRegistered: false,
    },
    preferences: {
      language: 'th',
      notifications: {
        enabled: false,
        email: false,
      },
    },
  });

  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loadingChangePass, setLoadingChangePass] = useState(false);
  const [message, setMessage] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [notiError, setNotiError] = useState('');

  // Fetch user profile
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (status === 'authenticated') {
        try {
          const response = await fetch('/api/user/profile');
          if (response.ok) {
            const data: UserProfileData = await response.json();
            // Merge notifications with defaults to prevent undefined → defined transition
            setUserData({
              ...data,
              preferences: {
                ...data.preferences,
                notifications: {
                  enabled: data.preferences?.notifications?.enabled ?? false,
                  email:   data.preferences?.notifications?.email   ?? false,
                },
              },
            });
          } else {
            console.error('Failed to fetch user profile');
          }
        } catch (error) {
          console.error('Error fetching user profile:', error);
        } finally {
          setIsLoadingProfile(false);
        }
      }
    };

    fetchUserProfile();
  }, [status]);

  // Update functions
  const updatePersonalInfo = (field: string, value: string) => {
    setUserData(prev => ({
      ...prev,
      personalInfo: {
        ...prev.personalInfo,
        [field]: value,
      },
    }));
  };

  const updateTaxInfo = (field: string, value: string) => {
    setUserData(prev => ({
      ...prev,
      taxInfo: {
        ...prev.taxInfo,
        [field]: value,
      },
    }));
  };

  const updateNotificationPreference = (field: string, value: boolean) => {
    setNotiError('');
    setUserData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        notifications: {
          ...prev.preferences.notifications,
          [field]: value,
        },
      },
    }));
  };

  // Save profile
  const handleSaveProfile = async () => {
    // Validate: ถ้าเปิด notification ต้องเลือกช่องทางอย่างน้อย 1 ช่อง
    const noti = userData.preferences.notifications;
    if (noti.enabled && !noti.email) {
      setNotiError('กรุณาเปิดรับการแจ้งเตือนทางอีเมลด้วย');
      return;
    }
    setNotiError('');

    setIsSaving(true);
    setSaveMessage('');

    try {
      const response = await fetch('/api/user/profile', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (response.ok) {
        setSaveMessage('✅ บันทึกข้อมูลสำเร็จ');
        setIsEditing(false);
      } else {
        const errorData = await response.json();
        setSaveMessage('❌ เกิดข้อผิดพลาด: ' + (errorData.error || 'ไม่สามารถบันทึกได้'));
      }
    } catch (error) {
      setSaveMessage('❌ เกิดข้อผิดพลาดในการเชื่อมต่อ');
      console.error('Error saving profile:', error);
    } finally {
      setIsSaving(false);
      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(''), 3000);
    }
  };

  // Change password
  const handleChangePassword = async () => {
    setLoadingChangePass(true);
    setMessage('');

    try {
      const res = await fetch('/api/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPassword,
          newPassword,
          confirmPassword,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.error || 'เกิดข้อผิดพลาด');
      } else {
        setMessage('✅ เปลี่ยนรหัสผ่านสำเร็จ');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      }
    } catch (err) {
      setMessage('เกิดข้อผิดพลาดในการเชื่อมต่อ');
    } finally {
      setLoadingChangePass(false);
      // Clear message after 3 seconds
      setTimeout(() => setMessage(''), 3000);
    }
  };

  // User object for display
  const user = {
    name: userData.meta?.name || `${userData.personalInfo.firstName} ${userData.personalInfo.lastName}`.trim() || session?.user?.name || 'ผู้ใช้',
    email: userData.personalInfo.email || session?.user?.email || '',
    image: userData.meta?.image || session?.user?.image || null,
  };

  // Loading state
  if (status === 'loading' || isLoadingProfile) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-slate-600">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  // Unauthorized
  if (status === 'unauthenticated') {
    router.push('/auth');
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation Component */}
      <AppNavigation />

      {/* Main Content */}
      <div>
        <div className="p-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <Link href="/WelcomeHome" className="text-slate-400 hover:text-slate-600">
                <Home className="w-5 h-5" />
              </Link>
              <span className="text-slate-400">/</span>
              <span className="font-medium text-slate-800">จัดการบัญชีผู้ใช้</span>
            </div>
            <h1 className="text-2xl font-semibold text-slate-800 mb-2">จัดการบัญชีผู้ใช้</h1>
            <p className="text-slate-600">จัดการข้อมูลส่วนตัว การตั้งค่าภาษี และความปลอดภัย</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Profile Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl p-6 border border-slate-200 sticky top-24">
                {/* Profile Image */}
                <div className="flex flex-col items-center mb-6">
                  <div className="relative">
                    {user.image ? (
                      <img
                        src={user.image}
                        alt={user.name}
                        className="w-24 h-24 rounded-full object-cover border-4 border-slate-100"
                      />
                    ) : (
                      <div className="w-24 h-24 bg-blue-600 rounded-full flex items-center justify-center">
                        <User className="w-12 h-12 text-white" />
                      </div>
                    )}
                    <button className="absolute -bottom-1 -right-1 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-700 transition-colors">
                      <Camera className="w-4 h-4 text-white" />
                    </button>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-800 mt-3">{user.name}</h3>
                  <p className="text-sm text-slate-500">{user.email}</p>
                  <div className="flex items-center space-x-2 mt-2 text-sm text-slate-500">
                    <Calendar className="w-4 h-4" />
                    <span>
                      สมาชิกตั้งแต่ {userData.meta?.createdAt
                        ? new Date(userData.meta.createdAt).toLocaleDateString('th-TH')
                        : 'เมษายน 2024'
                      }
                    </span>
                  </div>
                </div>


              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3 space-y-6">
              {/* Save Message */}
              {saveMessage && (
                <div className={`p-4 rounded-lg ${
                  saveMessage.includes('✅') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {saveMessage}
                </div>
              )}

              {/* Personal Information */}
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-800">ข้อมูลส่วนตัว</h2>
                    <p className="text-sm text-slate-500">จัดการข้อมูลส่วนตัวพื้นฐานของคุณ</p>
                  </div>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>{isEditing ? 'ยกเลิก' : 'แก้ไข'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      ชื่อจริง
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        value={userData.personalInfo.firstName}
                        onChange={(e) => updatePersonalInfo('firstName', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-slate-50'
                        }`}
                        placeholder="กรอกชื่อจริง"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      นามสกุล
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        value={userData.personalInfo.lastName}
                        onChange={(e) => updatePersonalInfo('lastName', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-slate-50'
                        }`}
                        placeholder="กรอกนามสกุล"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      อีเมล
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="email"
                        value={userData.personalInfo.email}
                        onChange={(e) => updatePersonalInfo('email', e.target.value)}
                        disabled={true} // Email shouldn't be editable here
                        className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg bg-slate-50"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">ไม่สามารถแก้ไขอีเมลได้</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      เบอร์โทรศัพท์
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="tel"
                        value={userData.personalInfo.phone}
                        onChange={(e) => updatePersonalInfo('phone', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-slate-50'
                        }`}
                        placeholder="กรอกเบอร์โทรศัพท์"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      วันเกิด
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="date"
                        value={userData.personalInfo.dateOfBirth}
                        onChange={(e) => updatePersonalInfo('dateOfBirth', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-slate-50'
                        }`}
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    ที่อยู่
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                    <textarea
                      value={userData.personalInfo.address}
                      onChange={(e) => updatePersonalInfo('address', e.target.value)}
                      disabled={!isEditing}
                      rows={3}
                      className={`w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-slate-50'
                      }`}
                      placeholder="กรอกที่อยู่ปัจจุบัน"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      อำเภอ/เขต
                    </label>
                    <input
                      type="text"
                      value={userData.personalInfo.district}
                      onChange={(e) => updatePersonalInfo('district', e.target.value)}
                      disabled={!isEditing}
                      className={`w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-slate-50'
                      }`}
                      placeholder="อำเภอ/เขต"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      จังหวัด
                    </label>
                    <input
                      type="text"
                      value={userData.personalInfo.province}
                      onChange={(e) => updatePersonalInfo('province', e.target.value)}
                      disabled={!isEditing}
                      className={`w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-slate-50'
                      }`}
                      placeholder="จังหวัด"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      รหัสไปรษณีย์
                    </label>
                    <input
                      type="text"
                      value={userData.personalInfo.postalCode}
                      onChange={(e) => updatePersonalInfo('postalCode', e.target.value)}
                      disabled={!isEditing}
                      className={`w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-slate-50'
                      }`}
                      placeholder="รหัสไปรษณีย์"
                      maxLength={5}
                    />
                  </div>
                </div>
              </div>

              {/* Tax Information — link to financial-info */}
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-800">ข้อมูลภาษีและการเงิน</h2>
                    <p className="text-sm text-slate-500">รายได้ ค่าลดหย่อน และข้อมูลภาษีทั้งหมด</p>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-100 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-slate-800">จัดการข้อมูลรายได้และค่าลดหย่อน</p>
                      <p className="text-xs text-slate-500">ประเภทรายได้ กองทุน ประกัน ครอบครัว และอื่นๆ</p>
                    </div>
                  </div>
                  <Link
                    href="/financial-info"
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
                  >
                    ไปหน้าการเงิน →
                  </Link>
                </div>
              </div>

              {/* Security Settings */}
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-800">ความปลอดภัย</h2>
                    <p className="text-sm text-slate-500">จัดการรหัสผ่านและการรักษาความปลอดภัย</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      รหัสผ่านปัจจุบัน
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="รหัสผ่านปัจจุบัน"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        รหัสผ่านใหม่
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="รหัสผ่านใหม่"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        ยืนยันรหัสผ่านใหม่
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="ยืนยันรหัสผ่านใหม่"
                        />
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={handleChangePassword}
                    disabled={loadingChangePass || !currentPassword || !newPassword || !confirmPassword}
                    className="w-full md:w-auto bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    {loadingChangePass ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Shield className="w-4 h-4" />
                    )}
                    <span>{loadingChangePass ? "กำลังบันทึก..." : "อัพเดตรหัสผ่าน"}</span>
                  </button>

                  {/* แสดงข้อความผลลัพธ์ */}
                  {message && (
                    <p className={`text-sm ${message.includes('✅') ? 'text-green-600' : 'text-red-600'}`}>
                      {message}
                    </p>
                  )}
                </div>

              </div>

              {/* Notification Preferences */}
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-800">การแจ้งเตือน</h2>
                    <p className="text-sm text-slate-500">จัดการประเภทการแจ้งเตือนที่ต้องการรับ</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* Master Toggle */}
                  <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Bell className="w-5 h-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-slate-800">รับการแจ้งเตือน</p>
                        <p className="text-sm text-slate-500">เปิด/ปิดการแจ้งเตือนกำหนดยื่นภาษีทั้งหมด</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={userData.preferences.notifications.enabled}
                        onChange={(e) => updateNotificationPreference('enabled', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Sub-options — แสดงเฉพาะเมื่อเปิด master toggle */}
                  {userData.preferences.notifications.enabled && (
                    <div className="ml-4 border-l-2 border-blue-200 pl-4">
                      {/* Email */}
                      <div className="flex items-center justify-between p-4 border border-slate-200 rounded-lg bg-white">
                        <div className="flex items-center space-x-3">
                          <Mail className="w-5 h-5 text-slate-600" />
                          <div>
                            <p className="font-medium text-slate-800">อีเมล</p>
                            <p className="text-sm text-slate-500">รับการแจ้งเตือนทางอีเมล</p>
                          </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={userData.preferences.notifications.email}
                            onChange={(e) => updateNotificationPreference('email', e.target.checked)}
                          />
                          <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                    </div>
                  )}

                  {/* Notification channel error */}
                  {notiError && (
                    <p className="text-sm text-red-500 font-medium pl-1">
                      ❌ {notiError}
                    </p>
                  )}
                </div>
              </div>

              {/* Save Button */}
              <div className="flex justify-end space-x-3 pt-6">
                <button
                  onClick={() => {
                    // Reset to original data if needed
                    setIsEditing(false);
                  }}
                  className="bg-white text-slate-700 px-5 py-2.5 rounded-lg border border-slate-300 hover:bg-slate-50 transition-colors text-sm font-medium"
                >
                  ยกเลิก
                </button>
                <button
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  <span>{isSaving ? 'กำลังบันทึก...' : 'บันทึกการเปลี่ยนแปลง'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}