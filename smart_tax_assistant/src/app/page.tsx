// src/app/page.tsx
'use client';

import Link from 'next/link';
import Image from 'next/image';
import React, { useState, useEffect } from 'react';
// [FIX] แก้ไขการ import ไอคอนจาก lucide-react ให้ถูกต้อง
import { ChevronRight, Shield, Upload, Target, Sparkles, CheckCircle, TrendingUp } from 'lucide-react';

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
  const [activeStep, setActiveStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // ใช้ isMounted เพื่อให้แน่ใจว่า component โหลดเสร็จก่อนเริ่ม animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    const interval = setInterval(() => {
      setActiveStep(prev => (prev + 1) % 3);
    }, 4000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
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
  const FloatingElement = ({ delay = 0, children, className = "", onClick = () => {} }: FloatingElementProps) => (
    <div 
      className={`transform transition-all duration-1000 ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
      } ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
      onClick={onClick}
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
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent animate-pulse">
                3 ขั้นตอน
              </span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              ประสบการณ์ใหม่ในการจัดการภาษีที่ไม่เคยมีมาก่อน พร้อมเทคโนโลยี AI ที่ล้ำสมัย 🚀
            </p>
          </div>
        </FloatingElement>
        <FloatingElement delay={200}>
          <div className="flex justify-center mb-16">
            <div className="flex items-center gap-8 p-4 bg-white/60 backdrop-blur-sm rounded-full shadow-lg border border-gray-200/50">
              {steps.map((_, index) => (
                <div key={index} className="flex items-center gap-4">
                  <PulsingDot active={activeStep === index} delay={index * 200} />
                  {index < steps.length - 1 && (
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </FloatingElement>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
          {steps.map((step, index) => {
            const IconComponent = step.icon;
            const isActive = activeStep === index;
            return (
              <FloatingElement 
                key={step.number} 
                delay={300 + index * 100}
                className="group cursor-pointer"
                onClick={() => setActiveStep(index)}
              >
                <div className={`relative transition-all duration-700 ${isActive ? 'scale-105 -translate-y-2' : 'hover:scale-102 hover:-translate-y-1'}`}>
                  <div className={`absolute inset-0 bg-gradient-to-r ${step.color} rounded-3xl opacity-0 group-hover:opacity-10 transition-opacity duration-500 blur-xl`}></div>
                  <div className={`relative bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border transition-all duration-500 overflow-hidden ${isActive ? 'border-transparent shadow-2xl bg-white/90' : 'border-gray-200/50 hover:border-gray-300/50 hover:shadow-2xl'}`}>
                    <div className={`h-2 bg-gradient-to-r ${step.color} ${isActive ? 'opacity-100' : 'opacity-60'} transition-opacity duration-500`}></div>
                    <div className="p-8">
                      <div className="flex items-center justify-center mb-8">
                        <div className={`relative inline-flex items-center justify-center h-24 w-24 rounded-2xl bg-gradient-to-r ${step.color} text-white shadow-2xl transition-all duration-500 ${isActive ? 'scale-110 shadow-3xl' : 'group-hover:scale-105'}`}>
                          <IconComponent className="h-10 w-10" />
                          <div className="absolute -top-2 -right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg"><span className="text-sm font-bold text-gray-700">{step.number}</span></div>
                          <div className={`absolute inset-0 rounded-2xl border-2 border-white/50 transition-all duration-500 ${isActive ? 'scale-125 opacity-0' : 'scale-100 opacity-100'}`}></div>
                        </div>
                      </div>
                      <div className="text-center space-y-6">
                        <h3 className={`text-2xl font-bold text-gray-900 transition-colors duration-300 ${isActive ? 'text-gray-900' : 'group-hover:text-gray-700'}`}>{step.title}</h3>
                        <p className="text-gray-600 leading-relaxed text-lg">{step.description}</p>
                        <div className={`transition-all duration-500 ${isActive ? 'opacity-100 max-h-96' : 'opacity-0 max-h-0 overflow-hidden'}`}>
                          <div className={`mt-6 p-4 bg-gradient-to-r ${step.bgColor} rounded-2xl`}>
                            <h4 className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4" /> คุณสมบัติเด่น</h4>
                            <ul className="space-y-2 text-sm text-gray-700">
                              {step.features.map((feature, idx) => (<li key={idx} className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" /><span>{feature}</span></li>))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className={`h-1 bg-gradient-to-r ${step.color} transition-opacity duration-500 ${isActive ? 'opacity-100' : 'opacity-0'}`}></div>
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
      {/* Enhanced Interactive Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.1),transparent_50%),radial-gradient(circle_at_80%_80%,rgba(16,185,129,0.08),transparent_50%),radial-gradient(circle_at_40%_40%,rgba(139,92,246,0.06),transparent_50%)]"></div>
        <div 
          className="absolute w-[600px] h-[600px] bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-full mix-blend-multiply filter blur-3xl animate-pulse opacity-70"
          style={{ left: `${mousePosition.x * 0.03}px`, top: `${mousePosition.y * 0.03}px`, transform: 'translate(-50%, -50%)' }}
        ></div>
        <div 
          className="absolute top-1/4 right-1/4 w-[400px] h-[400px] bg-gradient-to-r from-cyan-500/8 via-teal-500/8 to-blue-500/8 rounded-full mix-blend-multiply filter blur-3xl animate-pulse delay-1000"
          style={{ transform: `translateY(${scrollY * 0.1}px)` }}
        ></div>
        <div 
          className="absolute bottom-1/4 left-1/4 w-[350px] h-[350px] bg-gradient-to-r from-purple-500/8 via-pink-500/8 to-red-500/8 rounded-full mix-blend-multiply filter blur-3xl animate-pulse delay-2000"
          style={{ transform: `translateY(${scrollY * -0.05}px)` }}
        ></div>
        {[...Array(6)].map((_, i) => (
          <div key={i} className="absolute w-1 h-1 bg-blue-400/30 rounded-full animate-ping"
            style={{ left: `${20 + i * 15}%`, top: `${30 + i * 10}%`, animationDelay: `${i * 0.5}s`, animationDuration: `${3 + i * 0.5}s` }}
          ></div>
        ))}
      </div>

      {/* Enhanced Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute top-20 left-10 w-20 h-20 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-32 h-32 bg-gradient-to-br from-cyan-400/20 to-teal-400/20 rounded-full blur-xl animate-pulse delay-1000"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
          <div className="lg:grid lg:grid-cols-12 lg:gap-16 items-center">
            {/* Enhanced Text Content */}
            <div className={`text-center lg:text-left lg:col-span-6 z-10 transition-all duration-1000 transform ${ isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0' }`}>
              <span className="inline-flex items-center py-3 px-6 mb-8 text-sm font-semibold tracking-wider text-blue-800 bg-gradient-to-r from-blue-100 to-cyan-100 rounded-full shadow-lg backdrop-blur-sm border border-blue-200/50">
                <span className="w-2 h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full mr-2 animate-pulse shadow-sm"></span>
                 ยินดีต้อนรับสู่ SmartTax
              </span>
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-black tracking-tight text-gray-900 mb-8 leading-tight">
                <span className="block bg-gradient-to-r from-gray-900 via-blue-900 to-gray-900 bg-clip-text text-transparent">ระบบจัดการภาษี</span>
                <span className="block mt-2 bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent animate-pulse">อัจฉริยะด้วย AI</span>
              </h1>
              <p className="mt-6 text-xl md:text-2xl leading-relaxed text-gray-600 mb-12 max-w-2xl">
                ทำให้เรื่องภาษีเป็นเรื่องง่าย คำนวณแม่นยำ วางแผนลดหย่อนชาญฉลาด 
                <span className="block mt-2 text-blue-600 font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">🤖 พร้อม AI ปรึกษาได้ 24 ชั่วโมง</span>
              </p>
              <div className="flex flex-col sm:flex-row justify-center lg:justify-start space-y-4 sm:space-y-0 sm:space-x-6">
                <Link href="/auth" className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-semibold rounded-2xl text-white bg-gradient-to-r from-blue-600 via-purple-600 to-blue-700 shadow-2xl transition-all duration-300 ease-in-out hover:from-blue-700 hover:via-purple-700 hover:to-blue-800 hover:-translate-y-1 hover:shadow-[0_20px_40px_-10px_rgba(59,130,246,0.5)] active:scale-95 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-white/20 via-white/0 to-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <span className="relative flex items-center">
                    🚀 เริ่มต้นใช้งานฟรี
                    <svg className="ml-2 w-5 h-5 transition-transform duration-300 ease-in-out group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                  </span>
                </Link>
                <Link href="#howItWorks" className="group inline-flex items-center justify-center px-8 py-4 text-lg font-semibold rounded-2xl text-gray-700 bg-white/90 backdrop-blur-sm shadow-xl border border-gray-200/80 transition-all duration-300 ease-in-out hover:bg-white hover:border-blue-300 hover:-translate-y-1 hover:shadow-2xl hover:text-blue-600">
                  <span className="flex items-center">
                    <svg className="mr-2 w-5 h-5 text-blue-600 transition-transform duration-300 ease-in-out group-hover:scale-110" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                     ดูวิธีการทำงาน
                  </span>
                </Link>
              </div>
            </div>
            <div className={`mt-16 lg:mt-0 lg:col-span-6 relative transition-all duration-1000 delay-300 transform ${ isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0' }`}>
              <div className="relative mx-auto rounded-3xl shadow-2xl overflow-hidden bg-gradient-to-br from-white to-gray-50 p-4 border border-gray-200/50">
                <div className="relative rounded-2xl overflow-hidden shadow-2xl">
                  <Image src={heroImageUrl} alt="SmartTax Dashboard Preview" width={1740} height={1160} className="w-full h-auto object-cover" priority/>
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent"></div>
                </div>
              </div>
              <div className="absolute -bottom-8 -left-8 sm:bottom-auto sm:top-12 sm:-left-12 transform animate-float">
                <div className="bg-gradient-to-br from-white via-green-50 to-white backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-green-200/50 max-w-xs">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 text-white shadow-lg">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">✅ ยื่นภาษีสำเร็จ!</p>
                      <p className="text-xs text-gray-600">ยอดคืนภาษี: <span className="text-green-600 font-bold">฿12,500</span></p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="absolute -top-8 -right-8 sm:top-auto sm:bottom-12 sm:-right-12 transform animate-float-delay">
                <div className="bg-gradient-to-br from-white via-blue-50 to-white backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-blue-200/50 max-w-xs">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-gradient-to-r from-blue-400 to-purple-500 text-white shadow-lg">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-900">🤖 AI แนะนำ</p>
                      <p className="text-xs text-gray-600">ลดหย่อนเพิ่ม <span className="text-blue-600 font-bold">+฿5,000</span></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* [REPLACED] ส่วนนี้จะถูกแทนที่ */}
      <ModernHowItWorks />

      {/* Enhanced Features Section */}
      <section id="features" className="py-24 bg-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(16,185,129,0.05),transparent_50%),radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.05),transparent_50%)]"></div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center mb-20">
            <span className="inline-block py-3 px-6 text-sm font-semibold tracking-wider text-blue-800 uppercase bg-gradient-to-r from-blue-100 to-cyan-100 rounded-full mb-4 shadow-lg">
              ⭐ คุณสมบัติเด่น
            </span>
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-6">
              เครื่องมือที่ใช่สำหรับ
              <span className="text-blue-600"> ภาษีของคุณ</span>
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              ทุกสิ่งที่คุณต้องการในการจัดการภาษีอย่างมีประสิทธิภาพ 💪
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { 
                title: '🤖 AI Chatbot อัจฉริยะ', 
                description: 'ปรึกษาภาษี 24/7 กับ AI ที่เข้าใจกฎหมายไทย ให้คำตอบแม่นยำ และอัปเดตข้อมูลล่าสุดตลอดเวลา', 
                icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>,
                color: 'blue'
              },
              { 
                title: '⚡ คำนวณภาษีอัตโนมัติ', 
                description: 'เพียงอัปโหลดข้อมูล ระบบคำนวณภาษีให้ทันที ลดข้อผิดพลาด และประหยัดเวลา', 
                icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>,
                color: 'purple'
              },
              { 
                title: '🔔 แจ้งเตือนกำหนดการ', 
                description: 'ไม่พลาดทุกเดดไลน์ยื่นภาษี ด้วยการแจ้งเตือนผ่านช่องทางที่คุณเลือก Email, SMS', 
                icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>,
                color: 'green'
              },
              { 
                title: '💰 วางแผนลดหย่อนภาษี', 
                description: 'AI ช่วยวิเคราะห์และแนะนำแนวทางลดหย่อนภาษีที่เหมาะสมกับคุณ ประหยัดได้มากสุด', 
                icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
                color: 'teal'
              },
              { 
                title: '📊 สรุปรายงานภาษี', 
                description: 'ดูรายงานสรุปภาษีเข้าใจง่าย เปรียบเทียบข้อมูลย้อนหลังได้ในคลิกเดียว', 
                icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
                color: 'orange'
              },
              { 
                title: '🛡️ ปลอดภัยและเป็นส่วนตัว', 
                description: 'ปกป้องข้อมูลของคุณด้วยมาตรฐานความปลอดภัยระดับสากล เข้ารหัสข้อมูลครบวงจร', 
                icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>,
                color: 'gray'
              }
            ].map((feature) => (
              <div key={feature.title} className={`group relative p-8 bg-gradient-to-br from-white to-gray-50/50 rounded-3xl shadow-xl hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 border border-gray-200/50 overflow-hidden`}>
                <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${
                  feature.color === 'blue' ? 'from-blue-400 to-cyan-400' :
                  feature.color === 'purple' ? 'from-purple-400 to-pink-400' :
                  feature.color === 'green' ? 'from-green-400 to-teal-400' :
                  feature.color === 'teal' ? 'from-teal-400 to-cyan-400' :
                  feature.color === 'orange' ? 'from-orange-400 to-red-400' :
                  'from-gray-400 to-gray-500'
                } opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>
                <div className={`inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-r ${
                  feature.color === 'blue' ? 'from-blue-500 to-cyan-500' :
                  feature.color === 'purple' ? 'from-purple-500 to-pink-500' :
                  feature.color === 'green' ? 'from-green-500 to-teal-500' :
                  feature.color === 'teal' ? 'from-teal-500 to-cyan-500' :
                  feature.color === 'orange' ? 'from-orange-500 to-red-500' :
                  'from-gray-600 to-gray-800'
                } text-white mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      
       
    </>
  );
}