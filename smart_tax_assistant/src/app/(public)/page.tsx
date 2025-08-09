// src/app/page.tsx
'use client';

import Link from 'next/link';
import Image from 'next/image';
import React, { useState, useEffect } from 'react';
// [FIX] แก้ไขการ import ไอคอนจาก lucide-react ให้ถูกต้อง
import { Bot, Zap, Bell, BarChart2, ChevronRight, Shield, Upload, Target, Sparkles, CheckCircle, TrendingUp } from 'lucide-react';

// --- [NEW] Type Definitions for Props ---
interface FloatingElementProps {
  delay?: number;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

interface PulsingDotProps {
  active: boolean;
  delay?: number;
}


// --- [NEW] คอมโพเนนต์ ModernHowItWorks ที่คุณสร้างขึ้น ---
const ModernHowItWorks = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // ใช้ isMounted เพื่อให้แน่ใจว่า component โหลดเสร็จก่อนเริ่ม animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => {
      clearTimeout(timer);
    };
  }, []);

  const steps = [
    {
      number: '1',
      title: '🔐 สร้างบัญชีของคุณ',
      description: 'ลงทะเบียนง่ายๆ เพียงไม่กี่คลิก และกรอกข้อมูลภาษีเบื้องต้น พร้อมระบบความปลอดภัยสูงสุด',
      icon: Shield,
      color: 'from-blue-500 via-blue-600 to-indigo-700',
      bgColor: 'from-blue-50 to-indigo-100',
      features: ['ระบบรักษาความปลอดภัยระดับธนาคาร', 'การยืนยันตัวตนแบบ 2FA', 'เข้ารหัสข้อมูลแบบ End-to-End']
    },
    {
      number: '2',
      title: '📄 อัปโหลดเอกสาร',
      description: 'รวบรวมเอกสารรายได้, ค่าใช้จ่าย, และข้อมูลลดหย่อนต่างๆ แล้วอัปโหลดเข้าระบบอัจฉริยะ',
      icon: Upload,
      color: 'from-purple-500 via-purple-600 to-pink-700',
      bgColor: 'from-purple-50 to-pink-100',
      features: ['รองรับไฟล์หลากหลายรูปแบบ', 'OCR อ่านเอกสารอัตโนมัติ', 'ระบบจัดหมวดหมู่อัจฉริยะ']
    },
    {
      number: '3',
      title: '🎯 รับผลและคำแนะนำ',
      description: 'รับผลการคำนวณภาษีอัตโนมัติ พร้อมคำแนะนำส่วนบุคคลจาก AI ที่ช่วยประหยัดภาษีได้มากที่สุด',
      icon: Target,
      color: 'from-green-500 via-emerald-600 to-teal-700',
      bgColor: 'from-green-50 to-emerald-100',
      features: ['คำนวณภาษีแม่นยำ 99.9%', 'คำแนะนำประหยัดภาษีส่วนบุคคล', 'รายงานวิเคราะห์เชิงลึก']
    }
  ];

  // [FIX] เพิ่ม Type ให้กับ Props
  const FloatingElement = ({ delay = 0, children, className = "" }: FloatingElementProps) => (
    <div 
      className={`transform transition-all duration-1000 ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
      } ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );

  // [FIX] เพิ่ม Type ให้กับ Props
  const PulsingDot = ({ active, delay = 0 }: PulsingDotProps) => (
    <div 
      className={`relative w-3 h-3 rounded-full transition-all duration-500 ${
        active ? 'bg-gradient-to-r from-blue-500 to-purple-500 scale-125' : 'bg-gray-300'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {active && (
        <div className="absolute inset-0 w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 animate-ping opacity-75"></div>
      )}
    </div>
  );

  return (
    <section id="howItWorks" className="py-32 bg-gradient-to-br from-slate-50 via-white to-blue-50 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.05),transparent_50%)]"></div>
        <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_80%_80%,rgba(147,51,234,0.05),transparent_50%)]"></div>
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-full h-full bg-[radial-gradient(ellipse_at_50%_100%,rgba(16,185,129,0.03),transparent_70%)]"></div>
      </div>
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-20 h-20 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute top-40 right-20 w-32 h-32 bg-gradient-to-br from-purple-400/20 to-pink-400/20 rounded-full blur-xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-40 left-20 w-24 h-24 bg-gradient-to-br from-green-400/20 to-blue-400/20 rounded-full blur-xl animate-pulse delay-2000"></div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <FloatingElement delay={0}>
          <div className="text-center mb-24">
            <div className="inline-flex items-center gap-2 py-3 px-6 text-sm font-semibold tracking-wider text-blue-800 uppercase bg-gradient-to-r from-blue-100 via-white to-cyan-100 rounded-full mb-6 shadow-lg border border-blue-200/50 backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>วิธีการทำงาน</span>
              <Sparkles className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-5xl md:text-6xl font-black text-gray-900 mb-6 leading-tight">
              จัดการภาษีง่ายๆ ใน{' '}
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
                3 ขั้นตอน
              </span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              ประสบการณ์ใหม่ในการจัดการภาษีที่ไม่เคยมีมาก่อน พร้อมเทคโนโลยี AI ที่ล้ำสมัย 🚀
            </p>
          </div>
        </FloatingElement>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
          {steps.map((step, index) => {
            const IconComponent = step.icon;
            return (
              <FloatingElement 
                key={step.number} 
                delay={300 + index * 100}
                className="group"
              >
                <div className="relative transition-all duration-700 hover:scale-105 hover:-translate-y-2">
                  <div className={`absolute inset-0 bg-gradient-to-r ${step.color} rounded-3xl opacity-0 group-hover:opacity-10 transition-opacity duration-500 blur-xl`}></div>
                  <div className="relative bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-gray-200/50 hover:border-gray-300/50 hover:shadow-2xl transition-all duration-500 overflow-hidden">
                    <div className={`h-2 bg-gradient-to-r ${step.color} opacity-100`}></div>
                    <div className="p-8">
                      <div className="flex items-center justify-center mb-8">
                        <div className={`relative inline-flex items-center justify-center h-24 w-24 rounded-2xl bg-gradient-to-r ${step.color} text-white shadow-2xl group-hover:scale-105 transition-all duration-500`}>
                          <IconComponent className="h-10 w-10" />
                          <div className="absolute -top-2 -right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg">
                            <span className="text-sm font-bold text-gray-700">{step.number}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-center space-y-6">
                        <h3 className="text-2xl font-bold text-gray-900 group-hover:text-gray-700 transition-colors duration-300">{step.title}</h3>
                        <p className="text-gray-600 leading-relaxed text-lg">{step.description}</p>
                        
                        {/* แสดงคุณสมบัติเด่นตลอดเวลา */}
                        <div className="opacity-100">
                          <div className={`mt-6 p-4 bg-gradient-to-r ${step.bgColor} rounded-2xl`}>
                            <h4 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                              <TrendingUp className="w-4 h-4" /> คุณสมบัติเด่น
                            </h4>
                            <ul className="space-y-2 text-sm text-gray-700">
                              {step.features.map((feature, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                  <span>{feature}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className={`h-1 bg-gradient-to-r ${step.color} opacity-100`}></div>
                  </div>
                </div>
              </FloatingElement>
            );
          })}
        </div>
       
      </div>
    </section>
  );
};


// --- คอมโพเนนต์หลักของหน้า Home ---
export default function Home() {
  const [isVisible, setIsVisible] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    setIsVisible(true);
    
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // [FIX] แก้ไข URL รูปภาพที่อาจมีปัญหา
  const heroImageUrl = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1740&q=80";

  return (
    <> 
    

{/* Diagonal Split Hero Section */}
<section className="relative min-h-screen bg-white overflow-hidden">
  
  {/* Background Image Overlay */}
  <div className="absolute inset-0">
    <div 
      className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-5"
      style={{
        backgroundImage: `url(${heroImageUrl})`,
        filter: 'grayscale(100%) brightness(1.2)'
      }}
    ></div>
  </div>
  
  {/* Animated Background Elements */}
  <div className="absolute inset-0 overflow-hidden pointer-events-none">
    <div className="absolute top-20 left-10 w-32 h-32 bg-gradient-to-br from-blue-100/30 to-purple-100/30 rounded-full blur-xl animate-pulse"></div>
    <div className="absolute top-40 right-20 w-48 h-48 bg-gradient-to-br from-purple-100/30 to-pink-100/30 rounded-full blur-xl animate-pulse delay-1000"></div>
    <div className="absolute bottom-40 left-20 w-40 h-40 bg-gradient-to-br from-green-100/30 to-blue-100/30 rounded-full blur-xl animate-pulse delay-2000"></div>
  </div>
  
  <div className="relative flex items-center min-h-[calc(100vh-80px)]">
    
    {/* Left Content */}
    <div className="relative z-20 w-full lg:w-1/2 px-8 lg:px-16">
      <div className="max-w-lg">
        <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
          ระบบจัดการภาษี<br />
          <span className="text-transparent bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text">
            อัจฉริยะด้วย AI
          </span>
        </h1>
        
        <p className="text-lg text-gray-600 leading-relaxed mb-8 max-w-md">
          ทำให้เรื่องภาษีเป็นเรื่องง่าย คำนวณภาษีแม่นยำ วางแผนลดหย่อนภาษี พร้อม AI ปรึกษาฟรี 24 ชั่วโมง
        </p>
        
        <div className="flex items-center space-x-4">
          <Link href="/#howItWorks" className="px-8 py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 text-white rounded-full font-semibold hover:from-pink-600 hover:via-purple-600 hover:to-blue-600 transition-all shadow-lg hover:shadow-xl transform hover:scale-105">
            วิธีใช้งาน
          </Link>
          <Link href="/#features" className="px-8 py-4 bg-gray-100 text-gray-900 border border-gray-200 rounded-full font-semibold hover:bg-gray-200 hover:border-gray-300 transition-all">
            คุณสมบัติ
          </Link>
        </div>
      </div>
    </div>
    
    {/* Right Visual - Diagonal Split with Image Integration */}
    <div className="absolute top-0 right-0 w-full lg:w-3/5 h-full">
      <div 
        className="relative w-full h-full"
        style={{
          background: `linear-gradient(135deg, transparent 0%, transparent 20%, rgba(249, 250, 251, 0.95) 20%, rgba(243, 244, 246, 1) 100%)`,
          clipPath: 'polygon(20% 0%, 100% 0%, 100% 100%, 0% 100%)'
        }}
      >
        
        {/* Background Image in Right Section */}
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-10"
          style={{
            backgroundImage: `url(${heroImageUrl})`,
            filter: 'grayscale(80%) brightness(1.1) contrast(0.9)',
            clipPath: 'polygon(20% 0%, 100% 0%, 100% 100%, 0% 100%)'
          }}
        ></div>
        
        {/* 3D Visual Elements */}
        <div className="relative w-full h-full flex items-center justify-center p-16">
          
          {/* Main Dashboard Mockup */}
          <div className="relative transform rotate-12 perspective-1000">
            <div className="w-80 h-56 bg-white shadow-2xl border border-gray-200 rounded-2xl overflow-hidden">
              
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                <div className="flex space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse delay-100"></div>
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse delay-200"></div>
                </div>
                <div className="text-gray-600 text-xs font-semibold">SmartTax AI</div>
              </div>
              
              {/* Content */}
              <div className="p-4 space-y-3 bg-white">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  </div>
                  <div>
                    <div className="text-gray-900 text-sm font-medium">คำนวณภาษี AI</div>
                    <div className="text-gray-500 text-xs">กำลังวิเคราะห์...</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-3 space-y-2 border border-gray-200">
                  <div className="text-green-600 text-sm font-semibold">✓ ตรวจพบค่าลดหย่อน</div>
                  <div className="text-xl text-gray-900 font-bold">฿15,750</div>
                  <div className="text-gray-500 text-xs">ประหยัดได้ +23%</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Floating AI Bots */}
          <div className="absolute top-20 right-20 transform -rotate-12">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 via-pink-500 to-purple-600 rounded-xl shadow-lg flex items-center justify-center border border-white/20">
              <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
              <div className="w-3 h-3 bg-white rounded-full animate-pulse ml-1 delay-200"></div>
            </div>
          </div>
          
          <div className="absolute bottom-24 left-16 transform rotate-6">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 rounded-xl shadow-lg flex items-center justify-center border border-white/20">
              <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
              <div className="w-3 h-3 bg-white rounded-full animate-pulse ml-1 delay-300"></div>
            </div>
          </div>
          
          {/* Connecting Lines/Beams */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-32 right-32 w-32 h-px bg-gradient-to-r from-purple-400 via-pink-400 to-transparent animate-pulse"></div>
            <div className="absolute bottom-32 left-24 w-24 h-px bg-gradient-to-r from-blue-400 via-cyan-400 to-transparent transform rotate-45 animate-pulse delay-500"></div>
          </div>
          
          {/* Enhanced Grid Pattern Overlay */}
          <div 
            className="absolute inset-0 opacity-5"
            style={{
              backgroundImage: `
                linear-gradient(rgba(59, 130, 246, 0.4) 1px, transparent 1px),
                linear-gradient(90deg, rgba(147, 51, 234, 0.4) 1px, transparent 1px)
              `,
              backgroundSize: '2rem 2rem',
              animation: 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite'
            }}
          ></div>
          
          {/* Additional Floating Elements */}
          <div className="absolute top-1/3 left-1/3 w-2 h-2 bg-blue-400 rounded-full animate-ping"></div>
          <div className="absolute bottom-1/3 right-1/3 w-3 h-3 bg-purple-400 rounded-full animate-ping delay-1000"></div>
          <div className="absolute top-2/3 left-1/4 w-1.5 h-1.5 bg-pink-400 rounded-full animate-ping delay-2000"></div>
          
        </div>
      </div>
    </div>
    
  </div>
</section>
      
      {/* [REPLACED] ส่วนนี้จะถูกแทนที่ */}
      <ModernHowItWorks />

   {/* Enhanced Features Section - Light Theme */}
<section id="features" className="py-32 bg-gradient-to-br from-gray-50 via-white to-blue-50 relative overflow-hidden">
  {/* Background elements for light theme */}
  <div className="absolute inset-0">
    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.05),transparent_50%)]"></div>
    <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_80%_80%,rgba(147,51,234,0.05),transparent_50%)]"></div>
    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-full h-full bg-[radial-gradient(ellipse_at_50%_100%,rgba(16,185,129,0.03),transparent_70%)]"></div>
  </div>
  
  <div className="absolute inset-0 w-full h-full bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:3rem_3rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]"></div>

  {/* Animated floating elements */}
  <div className="absolute inset-0 overflow-hidden pointer-events-none">
    <div className="absolute top-20 left-10 w-32 h-32 bg-gradient-to-br from-blue-100/40 to-purple-100/40 rounded-full blur-xl animate-pulse"></div>
    <div className="absolute top-40 right-20 w-48 h-48 bg-gradient-to-br from-purple-100/40 to-pink-100/40 rounded-full blur-xl animate-pulse delay-1000"></div>
    <div className="absolute bottom-40 left-20 w-40 h-40 bg-gradient-to-br from-green-100/40 to-blue-100/40 rounded-full blur-xl animate-pulse delay-2000"></div>
    <div className="absolute bottom-20 right-10 w-36 h-36 bg-gradient-to-br from-cyan-100/40 to-teal-100/40 rounded-full blur-xl animate-pulse delay-3000"></div>
  </div>

  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
    {/* Header section */}
    <div className="text-center mb-24">
      <div className="inline-flex items-center gap-2 py-3 px-6 text-sm font-semibold tracking-wider text-blue-800 uppercase bg-gradient-to-r from-blue-100 via-white to-cyan-100 rounded-full mb-6 shadow-lg border border-blue-200/50 backdrop-blur-sm">
        <span>⭐</span>
        <span>คุณสมบัติเด่น</span>
        <span>⭐</span>
      </div>
      <h2 className="text-5xl md:text-6xl font-black text-gray-900 mb-6 leading-tight">
        เครื่องมือที่ใช่สำหรับ
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600"> ภาษีของคุณ</span>
      </h2>
      <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
        ทุกสิ่งที่คุณต้องการในการจัดการภาษีอย่างมีประสิทธิภาพ พร้อมเทคโนโลยี AI ล้ำสมัย 💪
      </p>
    </div>
    
    {/* Alternating Feature Panels */}
    <div className="space-y-24">
      {(() => {
        const gradientMap = {
          blue: 'from-blue-500 to-cyan-500',
          purple: 'from-purple-500 to-pink-500',
          green: 'from-green-500 to-teal-500',
          teal: 'from-teal-500 to-cyan-500',
          orange: 'from-orange-500 to-red-500',
          gray: 'from-gray-500 to-slate-600',
        };

        const features = [
          { 
            title: '🤖 AI Chatbot อัจฉริยะ', 
            description: 'ปรึกษาภาษี 24/7 กับ AI ที่เข้าใจกฎหมายไทย ให้คำตอบแม่นยำ และอัปเดตข้อมูลล่าสุดตลอดเวลา ประหยัดค่าใช้จ่ายที่ปรึกษาภาษี', 
            icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>,
            color: 'blue',
            features: ['ตอบคำถามภาษี 24/7', 'อัปเดตกฎหมายล่าสุด', 'คำแนะนำเฉพาะบุคคล']
          },
          { 
            title: '⚡ คำนวณภาษีอัตโนมัติ', 
            description: 'เพียงอัปโหลดข้อมูล ระบบคำนวณภาษีให้ทันที ลดข้อผิดพลาด และประหยัดเวลา พร้อมตรวจสอบความถูกต้องแบบอัตโนมัติ', 
            icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>,
            color: 'purple',
            features: ['คำนวณแม่นยำ 99.9%', 'ประหยัดเวลา 80%', 'ตรวจสอบอัตโนมัติ']
          },
          { 
            title: '🔔 แจ้งเตือนกำหนดการ', 
            description: 'ไม่พลาดทุกเดดไลน์ยื่นภาษี ด้วยการแจ้งเตือนผ่านช่องทางที่คุณเลือก Email, SMS, Line รับประกันไม่เสียค่าปรับ', 
            icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>,
            color: 'green',
            features: ['แจ้งเตือนหลายช่องทาง', 'ปรับแต่งเวลาได้', 'ไม่พลาดกำหนดเวลา']
          },
          { 
            title: '💰 วางแผนลดหย่อนภาษี', 
            description: 'AI ช่วยวิเคราะห์และแนะนำแนวทางลดหย่อนภาษีที่เหมาะสมกับคุณ ประหยัดได้มากสุด พร้อมคำนวณผลตอบแทนจากการลงทุน', 
            icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
            color: 'teal',
            features: ['วิเคราะห์ส่วนบุคคล', 'แนะนำการลงทุน', 'ประหยัดสูงสุด']
          },
          { 
            title: '📊 สรุปรายงานภาษี', 
            description: 'ดูรายงานสรุปภาษีเข้าใจง่าย เปรียบเทียบข้อมูลย้อนหลังได้ในคลิกเดียว พร้อมกราฟแสดงแนวโน้มและการวิเคราะห์', 
            icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
            color: 'orange',
            features: ['รายงานภาพรวม', 'กราฟแนวโน้ม', 'เปรียบเทียบปีก่อน']
          },
          { 
            title: '🛡️ ปลอดภัยและเป็นส่วนตัว', 
            description: 'ปกป้องข้อมูลของคุณด้วยมาตรฐานความปลอดภัยระดับสากล เข้ารหัสข้อมูลครบวงจร พร้อมการสำรองข้อมูลอัตโนมัติ', 
            icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
            color: 'gray',
            features: ['เข้ารหัสระดับธนาคาร', 'สำรองข้อมูลอัตโนมัติ', 'มาตรฐานสากล']
          }
        ];

        return features.map((feature, index) => (
          <div key={feature.title} className={`transform transition-all duration-700 ${index % 2 === 0 ? 'translate-x-0' : 'translate-x-0'}`}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              
              {/* Visual Panel */}
              <div className={`relative flex items-center justify-center group ${index % 2 === 1 ? 'lg:order-first' : ''}`}>
                {/* Background glow effect */}
                <div className={`absolute w-80 h-80 bg-gradient-to-r ${gradientMap[feature.color as keyof typeof gradientMap]}/10 rounded-full blur-3xl animate-pulse group-hover:scale-110 transition-transform duration-1000`}></div>
                
                {/* Main visual container */}
                <div className={`relative flex items-center justify-center h-72 w-72 rounded-3xl bg-white/80 backdrop-blur-md border border-gray-200/50 shadow-2xl group-hover:shadow-3xl transition-all duration-500 group-hover:scale-105`}>
                  {/* Icon container */}
                  <div className={`flex items-center justify-center h-20 w-20 rounded-2xl bg-gradient-to-r ${gradientMap[feature.color as keyof typeof gradientMap]} text-white shadow-xl group-hover:scale-110 transition-transform duration-300`}>
                    {React.cloneElement(feature.icon, { className: "h-10 w-10" })}
                  </div>
                  
                  {/* Floating elements around the main icon */}
                  <div className="absolute top-6 right-6 w-4 h-4 bg-blue-400/60 rounded-full animate-ping"></div>
                  <div className="absolute bottom-8 left-8 w-3 h-3 bg-purple-400/60 rounded-full animate-ping delay-500"></div>
                  <div className="absolute top-1/2 left-6 w-2 h-2 bg-pink-400/60 rounded-full animate-ping delay-1000"></div>
                  
                  {/* Grid overlay */}
                  <div className="absolute inset-0 rounded-3xl opacity-5 bg-[linear-gradient(rgba(0,0,0,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.1)_1px,transparent_1px)] bg-[size:1rem_1rem]"></div>
                </div>
              </div>
              
              {/* Text Content */}
              <div className={`${index % 2 === 1 ? 'lg:order-last' : ''} space-y-6`}>
                {/* Icon badge */}
                <div className={`inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-gradient-to-r ${gradientMap[feature.color as keyof typeof gradientMap]} text-white mb-2 shadow-lg hover:scale-110 transition-transform duration-300`}>
                  {React.cloneElement(feature.icon, { className: "h-7 w-7" })}
                </div>
                
                {/* Title */}
                <h3 className="text-4xl font-bold text-gray-900 leading-tight">
                  {feature.title}
                </h3>
                
                {/* Description */}
                <p className="text-lg text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
                
                {/* Feature highlights */}
                <div className="space-y-3">
                  {feature.features.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className={`flex-shrink-0 w-5 h-5 rounded-full bg-gradient-to-r ${gradientMap[feature.color as keyof typeof gradientMap]} flex items-center justify-center`}>
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <span className="text-gray-700 font-medium">{item}</span>
                    </div>
                  ))}
                </div>
                
               
              </div>
            </div>
          </div>
        ));
      })()}
    </div>
    
    
  </div>
</section>

      
       
    </>
  );
}