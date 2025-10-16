// src/app/(app)/profile-settings/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
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
  Bell,
  Search,
  Menu,
  Loader2,
  X,
  Home,
  MessageCircle,
  Target,
  Wallet,
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
  Smartphone,
  IdCard,
  Briefcase,
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
  };
  preferences: {
    language: string;
    notifications: {
      email: boolean;
      sms: boolean;
      taxDeadlines: boolean;
      reports: boolean;
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
    },
    preferences: {
      language: 'th',
      notifications: {
        email: true,
        sms: false,
        taxDeadlines: true,
        reports: true,
      },
    },
  });

  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loadingChangePass, setLoadingChangePass] = useState(false);
  const [message, setMessage] = useState('');
  const [saveMessage, setSaveMessage] = useState('');

  // Fetch user profile
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (status === 'authenticated') {
        try {
          const response = await fetch('/api/user/profile');
          if (response.ok) {
            const data: UserProfileData = await response.json();
            setUserData(data);
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

  

  // User object for display
  const user = {
    name: userData.meta?.name || `${userData.personalInfo.firstName} ${userData.personalInfo.lastName}`.trim() || session?.user?.name || 'ผู้ใช้',
    email: userData.personalInfo.email || session?.user?.email || '',
    image: userData.meta?.image || session?.user?.image || null,
  };

  // Loading state
  if (status === 'loading' || isLoadingProfile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-gray-600">กำลังโหลด...</p>
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
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
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
                      className={`flex items-center space-x-4 p-4 rounded-xl transition-colors group ${
                        item.href === '/profile-settings' 
                          ? 'bg-blue-50 text-blue-600' 
                          : 'hover:bg-gray-50'
                      }`}
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

      {/* Main Content */}
      <div className={`transition-all duration-300 ease-in-out ${
        isMobileMenuOpen ? 'ml-80' : 'ml-0'
      }`}>
        <div className="p-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-4">
              <Link href="/WelcomeHome" className="text-gray-400 hover:text-gray-600">
                <Home className="w-5 h-5" />
              </Link>
              <span className="text-gray-400">/</span>
              <span className="font-medium text-gray-900">จัดการบัญชีผู้ใช้</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">จัดการบัญชีผู้ใช้</h1>
            <p className="text-gray-600">จัดการข้อมูลส่วนตัว การตั้งค่าภาษี และความปลอดภัย</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Profile Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 sticky top-24">
                {/* Profile Image */}
                <div className="flex flex-col items-center mb-6">
                  <div className="relative">
                    {user.image ? (
                      <img
                        src={user.image}
                        alt={user.name}
                        className="w-24 h-24 rounded-full object-cover border-4 border-gray-100"
                      />
                    ) : (
                      <div className="w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <User className="w-12 h-12 text-white" />
                      </div>
                    )}
                    <button className="absolute -bottom-1 -right-1 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-700 transition-colors shadow-lg">
                      <Camera className="w-4 h-4 text-white" />
                    </button>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900">{user.name}</h3>
                  <p className="text-sm text-gray-500">{user.email}</p>
                  <div className="flex items-center space-x-2 mt-2 text-sm text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>
                      สมาชิกตั้งแต่ {userData.meta?.createdAt 
                        ? new Date(userData.meta.createdAt).toLocaleDateString('th-TH') 
                        : 'เมษายน 2024'
                      }
                    </span>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-900">แบบฟอร์มที่สร้าง</span>
                    </div>
                    <span className="text-blue-600 font-semibold">3</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CreditCard className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-900">การคำนวณ</span>
                    </div>
                    <span className="text-green-600 font-semibold">12</span>
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
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">ข้อมูลส่วนตัว</h2>
                    <p className="text-gray-500">จัดการข้อมูลส่วนตัวพื้นฐานของคุณ</p>
                  </div>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>{isEditing ? 'ยกเลิก' : 'แก้ไข'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      ชื่อจริง
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={userData.personalInfo.firstName}
                        onChange={(e) => updatePersonalInfo('firstName', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-gray-50'
                        }`}
                        placeholder="กรอกชื่อจริง"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      นามสกุล
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={userData.personalInfo.lastName}
                        onChange={(e) => updatePersonalInfo('lastName', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-gray-50'
                        }`}
                        placeholder="กรอกนามสกุล"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      อีเมล
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="email"
                        value={userData.personalInfo.email}
                        onChange={(e) => updatePersonalInfo('email', e.target.value)}
                        disabled={true} // Email shouldn't be editable here
                        className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg bg-gray-50"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">ไม่สามารถแก้ไขอีเมลได้</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      เบอร์โทรศัพท์
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="tel"
                        value={userData.personalInfo.phone}
                        onChange={(e) => updatePersonalInfo('phone', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-gray-50'
                        }`}
                        placeholder="กรอกเบอร์โทรศัพท์"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      วันเกิด
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="date"
                        value={userData.personalInfo.dateOfBirth}
                        onChange={(e) => updatePersonalInfo('dateOfBirth', e.target.value)}
                        disabled={!isEditing}
                        className={`w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          isEditing ? 'bg-white' : 'bg-gray-50'
                        }`}
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ที่อยู่
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                    <textarea
                      value={userData.personalInfo.address}
                      onChange={(e) => updatePersonalInfo('address', e.target.value)}
                      disabled={!isEditing}
                      rows={3}
                      className={`w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-gray-50'
                      }`}
                      placeholder="กรอกที่อยู่ปัจจุบัน"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      อำเภอ/เขต
                    </label>
                    <input
                      type="text"
                      value={userData.personalInfo.district}
                      onChange={(e) => updatePersonalInfo('district', e.target.value)}
                      disabled={!isEditing}
                      className={`w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-gray-50'
                      }`}
                      placeholder="อำเภอ/เขต"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      จังหวัด
                    </label>
                    <input
                      type="text"
                      value={userData.personalInfo.province}
                      onChange={(e) => updatePersonalInfo('province', e.target.value)}
                      disabled={!isEditing}
                      className={`w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-gray-50'
                      }`}
                      placeholder="จังหวัด"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      รหัสไปรษณีย์
                    </label>
                    <input
                      type="text"
                      value={userData.personalInfo.postalCode}
                      onChange={(e) => updatePersonalInfo('postalCode', e.target.value)}
                      disabled={!isEditing}
                      className={`w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        isEditing ? 'bg-white' : 'bg-gray-50'
                      }`}
                      placeholder="รหัสไปรษณีย์"
                      maxLength={5}
                    />
                  </div>
                </div>
              </div>

              {/* Tax Information */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">ข้อมูลภาษี</h2>
                    <p className="text-gray-500">ข้อมูลพื้นฐานสำหรับการคำนวณภาษี</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      อาชีพ
                    </label>
                    <div className="relative">
                      <Briefcase className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={userData.taxInfo.occupation}
                        onChange={(e) => updateTaxInfo('occupation', e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="อาชีพปัจจุบัน"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      รายได้ต่อปี (บาท)
                    </label>
                    <input
                      type="number"
                      value={userData.taxInfo.annualIncome}
                      onChange={(e) => updateTaxInfo('annualIncome', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                      min="0"
                    />
                  </div>
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    ประเภทการยื่นภาษี
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex items-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="taxType"
                        value="individual"
                        checked={userData.taxInfo.taxType === 'individual'}
                        onChange={(e) => updateTaxInfo('taxType', e.target.value)}
                        className="text-blue-600"
                      />
                      <div className="ml-3">
                        <p className="font-medium text-gray-900">บุคคลธรรมดา</p>
                        <p className="text-sm text-gray-500">ยื่นภาษีเป็นรายบุคคล</p>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Security Settings */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">ความปลอดภัย</h2>
                    <p className="text-gray-500">จัดการรหัสผ่านและการรักษาความปลอดภัย</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      รหัสผ่านปัจจุบัน
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full pl-10 pr-12 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="รหัสผ่านปัจจุบัน"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        รหัสผ่านใหม่
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="รหัสผ่านใหม่"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        ยืนยันรหัสผ่านใหม่
                      </label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="ยืนยันรหัสผ่านใหม่"
                        />
                      </div>
                    </div>
                  </div>

                  <button 
                    onClick={handleChangePassword}
                    disabled={loadingChangePass || !currentPassword || !newPassword || !confirmPassword}
                    className="w-full md:w-auto bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
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

                {/* Two-Factor Authentication */}
                <div className="mt-8 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    การยืนยันตัวตน 2 ขั้นตอน
                  </h3>
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Smartphone className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="font-medium text-gray-900">SMS Authentication</p>
                        <p className="text-sm text-gray-500">
                          รับรหัสยืนยันทาง SMS เมื่อเข้าสู่ระบบ
                        </p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked={false} />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Notification Preferences */}
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">การแจ้งเตือน</h2>
                    <p className="text-gray-500">จัดการประเภทการแจ้งเตือนที่ต้องการรับ</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* Email Notifications */}
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Mail className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="font-medium text-gray-900">การแจ้งเตือนทางอีเมล</p>
                        <p className="text-sm text-gray-500">รับข่าวสารและการแจ้งเตือนทางอีเมล</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={userData.preferences.notifications.email}
                        onChange={(e) => updateNotificationPreference('email', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* SMS Notifications */}
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Smartphone className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="font-medium text-gray-900">การแจ้งเตือนทาง SMS</p>
                        <p className="text-sm text-gray-500">รับข้อความแจ้งเตือนทางโทรศัพท์</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={userData.preferences.notifications.sms}
                        onChange={(e) => updateNotificationPreference('sms', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Tax Deadline Reminders */}
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Calendar className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="font-medium text-gray-900">เตือนกำหนดยื่นภาษี</p>
                        <p className="text-sm text-gray-500">แจ้งเตือนก่อนครบกำหนดยื่นภาษี</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={userData.preferences.notifications.taxDeadlines}
                        onChange={(e) => updateNotificationPreference('taxDeadlines', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Report Notifications */}
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <BarChart3 className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="font-medium text-gray-900">รายงานผลการคำนวณ</p>
                        <p className="text-sm text-gray-500">แจ้งเตือนเมื่อมีรายงานใหม่</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer" 
                        checked={userData.preferences.notifications.reports}
                        onChange={(e) => updateNotificationPreference('reports', e.target.checked)}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Save Button */}
              <div className="flex justify-end space-x-4 pt-6">
                <button 
                  onClick={() => {
                    // Reset to original data if needed
                    setIsEditing(false);
                  }}
                  className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  ยกเลิก
                </button>
                <button 
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
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