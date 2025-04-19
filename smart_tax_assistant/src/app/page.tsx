'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';

export default function Home() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll effect for navbar
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 text-gray-800">
      {/* Navbar */}
      <nav className={`fixed w-full top-0 z-50 transition-all duration-300 ease-in-out ${
        scrolled
          ? 'bg-white/90 backdrop-blur-lg shadow-lg border-b border-gray-200/50'
          : 'bg-transparent'
      }`}>
         <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20 items-center">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="flex items-center">
                <svg className="h-9 w-auto text-blue-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                   <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="rgba(59, 130, 246, 0.1)"/>
                   <path d="M17 9.5L12 12L7 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                   <path d="M12 17.5V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                   <path d="M7 14.5L12 17.5L17 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span className="ml-2 text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                  SmartTax
                </span>
              </Link>
            </div>

            {/* Desktop Menu */}
            <div className="hidden sm:flex sm:items-center sm:space-x-8">
              <Link href="#features" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200">
                คุณสมบัติ
              </Link>
              <Link href="#howItWorks" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200">
                วิธีใช้งาน
              </Link>
              <Link href="#pricing" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200">
                แพ็คเกจ
              </Link>
              <Link href="/login" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200">
                เข้าสู่ระบบ
              </Link>
              <Link
                href="/register"
                className="ml-4 inline-flex items-center px-5 py-2.5 border border-transparent text-sm font-medium rounded-full shadow-lg text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300 transform hover:scale-105"
              >
                เริ่มใช้งานฟรี
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <div className="sm:hidden flex items-center">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-blue-600 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors"
                aria-controls="mobile-menu"
                aria-expanded={isMobileMenuOpen}
              >
                <span className="sr-only">Open main menu</span>
                <svg className={`h-6 w-6 ${isMobileMenuOpen ? 'hidden' : 'block'}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                <svg className={`h-6 w-6 ${isMobileMenuOpen ? 'block' : 'hidden'}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
           <div className="sm:hidden bg-white shadow-lg rounded-b-2xl absolute w-full">
             <div className="pt-2 pb-3 space-y-1 px-4">
                <Link href="#features" className="block px-4 py-3 rounded-lg font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors" onClick={() => setIsMobileMenuOpen(false)}>คุณสมบัติ</Link>
                <Link href="#howItWorks" className="block px-4 py-3 rounded-lg font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors" onClick={() => setIsMobileMenuOpen(false)}>วิธีใช้งาน</Link>
                <Link href="#pricing" className="block px-4 py-3 rounded-lg font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors" onClick={() => setIsMobileMenuOpen(false)}>แพ็คเกจ</Link>
                <Link href="/login" className="block px-4 py-3 rounded-lg font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors" onClick={() => setIsMobileMenuOpen(false)}>เข้าสู่ระบบ</Link>
            </div>
            <div className="pt-2 pb-4 px-4 border-t border-gray-100">
              <Link href="/register" className="block w-full px-5 py-3 rounded-full text-center font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-md" onClick={() => setIsMobileMenuOpen(false)}>เริ่มใช้งานฟรี</Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <main>
        <section className="relative pt-28 md:pt-36 pb-20 overflow-hidden">
          {/* Background elements */}
          <div className="absolute inset-0 z-0 pointer-events-none">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.1),transparent_60%)]"></div>
            <div className="absolute top-1/3 right-0 w-96 h-96 bg-indigo-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow"></div>
            <div className="absolute bottom-0 left-1/4 w-80 h-80 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-pulse-slow delay-1000"></div>
          </div>

          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="lg:grid lg:grid-cols-12 lg:gap-16 items-center">
              {/* Text Content */}
              <div className="text-center lg:text-left lg:col-span-6 z-10">
                <span className="inline-block py-1.5 px-4 mb-5 text-xs font-semibold tracking-wider text-blue-700 uppercase bg-blue-100 rounded-full shadow-sm">
                  ยินดีต้อนรับสู่ SmartTax
                </span>
                <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
                  <span className="block">ระบบจัดการภาษี</span>
                  <span className="block mt-1 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                    อัจฉริยะด้วย AI
                  </span>
                </h1>
                <p className="mt-6 text-xl leading-relaxed text-gray-600">
                  ทำให้เรื่องภาษีเป็นเรื่องง่าย คำนวณแม่นยำ วางแผนลดหย่อนชาญฉลาด พร้อม AI ปรึกษาได้ 24 ชั่วโมง
                </p>
                {/* Buttons */}
                <div className="mt-10 flex flex-col sm:flex-row justify-center lg:justify-start space-y-4 sm:space-y-0 sm:space-x-4">
                  <Link href="/register" className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-medium rounded-full shadow-lg text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 transform hover:scale-105 hover:-translate-y-0.5">
                    เริ่มต้นใช้งานฟรี <svg className="ml-2 w-5 h-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                  </Link>
                  <Link href="#howItWorks" className="inline-flex items-center justify-center px-8 py-4 border border-gray-300 text-base font-medium rounded-full text-blue-700 bg-white hover:bg-blue-50 shadow-md transition-all duration-300 transform hover:scale-105 hover:-translate-y-0.5">
                    ดูวิธีการทำงาน <svg className="ml-2 w-5 h-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                  </Link>
                </div>
                {/* Corrected Social Proof Section */}
                <div className="mt-10 flex items-center justify-center lg:justify-start space-x-6">
                  <div className="flex -space-x-2 overflow-hidden">
                    <Image src="https://via.placeholder.com/40/DBEAFE/1E40AF?text=U1" alt="User 1" width={32} height={32} className="inline-block h-8 w-8 rounded-full ring-2 ring-white object-cover" />
                    <Image src="https://via.placeholder.com/40/C7D2FE/1D4ED8?text=U2" alt="User 2" width={32} height={32} className="inline-block h-8 w-8 rounded-full ring-2 ring-white object-cover" />
                    <Image src="https://via.placeholder.com/40/A5B4FC/3B82F6?text=U3" alt="User 3" width={32} height={32} className="inline-block h-8 w-8 rounded-full ring-2 ring-white object-cover" />
                    <div className="flex items-center justify-center h-8 w-8 rounded-full ring-2 ring-white bg-gray-200 text-gray-500 text-xs font-medium">
                       +99
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    <span className="font-medium text-gray-900">เข้าร่วมกับ 1,200+ ผู้ใช้งาน</span> ที่วางใจเรา
                  </div>
                </div>
                {/* End of Corrected Social Proof */}
              </div>

              {/* Image Content */}
              <div className="mt-12 lg:mt-0 lg:col-span-6 relative">
                 <div className="relative mx-auto rounded-2xl shadow-xl overflow-hidden bg-white p-2">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl transform -rotate-1 scale-105 opacity-5 -z-10"></div>
                  <div className="relative rounded-xl overflow-hidden">
                     <Image
                        src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1740&q=80"
                        alt="SmartTax Dashboard Preview"
                        width={1740}
                        height={1160}
                        className="w-full h-auto object-cover"
                        priority
                      />
                  </div>
                 </div>
                 {/* Floating Elements ... (keep as before) ... */}
                  <div className="absolute -bottom-6 -left-6 sm:bottom-auto sm:top-10 sm:-left-10 transform animate-float">
                   <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg p-4 flex items-center space-x-3">
                      <div className="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-green-100 text-green-600">
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      </div>
                      <div><p className="text-sm font-semibold text-gray-900">ยื่นภาษีสำเร็จ!</p><p className="text-xs text-gray-500">ยอดคืนภาษี: ฿1,250</p></div>
                   </div>
                 </div>
                 <div className="absolute -top-6 -right-6 sm:top-auto sm:bottom-10 sm:-right-10 transform animate-float-delay">
                    <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg p-4 flex items-center space-x-3">
                       <div className="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-blue-100 text-blue-600">
                          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                       </div>
                      <div><p className="text-sm font-semibold text-gray-900">AI แนะนำ</p><p className="text-xs text-gray-500">ลดหย่อนเพิ่มด้วย RMF...</p></div>
                   </div>
                 </div>
              </div>
            </div>
          </div>

          {/* Brand Logos */}
          <div className="relative max-w-7xl mx-auto mt-24 px-4 sm:px-6 lg:px-8">
              <div className="py-8 px-6 bg-white/60 backdrop-blur-md rounded-2xl shadow-lg border border-gray-100">
                <p className="text-center text-sm font-medium text-gray-600 mb-6">ได้รับความไว้วางใจจากแบรนด์ชั้นนำ</p>
                <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-5 items-center">
                  {[
                    { name: "TechCorp", url: "https://via.placeholder.com/150x50/E0E7FF/3730A3?text=TechCorp" },
                    { name: "FinanceInc", url: "https://via.placeholder.com/150x50/D1FAE5/065F46?text=FinanceInc" },
                    { name: "RetailHub", url: "https://via.placeholder.com/150x50/FEF3C7/92400E?text=RetailHub" },
                    { name: "ServicePro", url: "https://via.placeholder.com/150x50/FEE2E2/991B1B?text=ServicePro" },
                    { name: "GlobalEnt", url: "https://via.placeholder.com/150x50/E5E7EB/1F2937?text=GlobalEnt" },
                  ].map((brand) => (
                    <div key={brand.name} className="col-span-1 flex justify-center grayscale opacity-60 hover:grayscale-0 hover:opacity-100 transition duration-300 ease-in-out transform hover:scale-105">
                      <Image
                        src={brand.url}
                        alt={brand.name}
                        width={150}
                        height={50}
                        className="h-10 w-auto object-contain"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
        </section>

         {/* How It Works Section */}
        <section id="howItWorks" className="py-20 bg-gradient-to-b from-blue-50 to-indigo-100/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-base font-semibold tracking-wide uppercase text-blue-600">วิธีการทำงาน</h2>
              <p className="mt-1 text-3xl font-extrabold text-gray-900 sm:text-4xl lg:text-5xl">
                จัดการภาษีง่ายๆ ใน 3 ขั้นตอน
              </p>
            </div>
            <div className="mt-16">
              <div className="flex flex-col lg:flex-row lg:items-start lg:space-x-8 relative">
                 <div className="hidden lg:block absolute top-16 left-1/3 w-1/3 h-1 border-t-2 border-dashed border-blue-300 -translate-y-1/2 z-0"></div>
                {/* Step 1 */}
                <div className="flex-1 flex flex-col items-center text-center p-8 relative mb-10 lg:mb-0">
                   <div className="relative z-10 flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-bold text-2xl shadow-lg mb-6 ring-4 ring-white">1</div>
                   <h3 className="text-xl font-semibold text-gray-900 mb-3">สร้างบัญชีของคุณ</h3>
                   <p className="text-base text-gray-600">ลงทะเบียนง่ายๆ เพียงไม่กี่คลิก และกรอกข้อมูลภาษีเบื้องต้น</p>
                   <div className="mt-6 p-4 bg-white rounded-xl shadow-md border border-gray-100"><svg className="h-10 w-10 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg></div>
                   <div className="lg:hidden absolute bottom-0 left-1/2 w-1 h-10 border-l-2 border-dashed border-blue-300 transform -translate-x-1/2 translate-y-full"></div>
                </div>
                {/* Step 2 */}
                <div className="flex-1 flex flex-col items-center text-center p-8 relative mb-10 lg:mb-0">
                   <div className="relative z-10 flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-bold text-2xl shadow-lg mb-6 ring-4 ring-white">2</div>
                   <h3 className="text-xl font-semibold text-gray-900 mb-3">เชื่อมต่อ/อัปโหลดข้อมูล</h3>
                   <p className="text-base text-gray-600">เชื่อมต่อกับบัญชีธนาคาร หรืออัปโหลดเอกสารรายได้และค่าใช้จ่าย</p>
                   <div className="mt-6 p-4 bg-white rounded-xl shadow-md border border-gray-100"><svg className="h-10 w-10 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg></div>
                   <div className="lg:hidden absolute bottom-0 left-1/2 w-1 h-10 border-l-2 border-dashed border-blue-300 transform -translate-x-1/2 translate-y-full"></div>
                </div>
                {/* Step 3 */}
                <div className="flex-1 flex flex-col items-center text-center p-8 relative">
                   <div className="relative z-10 flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-bold text-2xl shadow-lg mb-6 ring-4 ring-white">3</div>
                   <h3 className="text-xl font-semibold text-gray-900 mb-3">รับผลและคำแนะนำ</h3>
                   <p className="text-base text-gray-600">รับผลการคำนวณภาษีอัตโนมัติ พร้อมคำแนะนำส่วนบุคคลจาก AI</p>
                   <div className="mt-6 p-4 bg-white rounded-xl shadow-md border border-gray-100"><svg className="h-10 w-10 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg></div>
                </div>
              </div>
            </div>
          </div>
        </section>
        {/* Features Section */}
        <section id="features" className="py-20 bg-white overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <span className="inline-block py-1 px-3 text-xs font-semibold tracking-wider text-blue-600 uppercase bg-blue-50 rounded-full">คุณสมบัติเด่น</span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">เครื่องมือที่ใช่สำหรับภาษีของคุณ</h2>
              <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">ทุกสิ่งที่คุณต้องการในการจัดการภาษีอย่างมีประสิทธิภาพ</p>
            </div>
            <div className="mt-16">
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  { title: 'AI Chatbot อัจฉริยะ', description: 'ปรึกษาภาษี 24/7 กับ AI ที่เข้าใจกฎหมายไทย ให้คำตอบแม่นยำ', icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg> },
                  { title: 'คำนวณภาษีอัตโนมัติ', description: 'เพียงอัปโหลดข้อมูล ระบบคำนวณภาษีให้ทันที ลดข้อผิดพลาด', icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg> },
                  { title: 'แจ้งเตือนกำหนดการ', description: 'ไม่พลาดทุกเดดไลน์ยื่นภาษี ด้วยการแจ้งเตือนผ่านช่องทางที่คุณเลือก', icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg> },
                  { title: 'วางแผนลดหย่อนภาษี', description: 'AI ช่วยวิเคราะห์และแนะนำแนวทางลดหย่อนภาษีที่เหมาะสมกับคุณ', icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> },
                  { title: 'สรุปรายงานภาษี', description: 'ดูรายงานสรุปภาษีเข้าใจง่าย เปรียบเทียบข้อมูลย้อนหลังได้', icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg> },
                  { title: 'ปลอดภัยและเป็นส่วนตัว', description: 'ปกป้องข้อมูลของคุณด้วยมาตรฐานความปลอดภัยระดับสากล', icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg> },
                ].map((feature) => (
                  <div key={feature.title} className="p-6 bg-gray-50 rounded-xl shadow-sm border border-gray-100 hover:shadow-lg transition-shadow duration-300">
                    <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white mb-5 shadow-md">{feature.icon}</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                    <p className="text-base text-gray-600">{feature.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
        {/* Pricing Section Placeholder */}
        <section id="pricing" className="py-20 bg-gradient-to-b from-indigo-50/50 to-white">
           <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-base font-semibold tracking-wide uppercase text-indigo-600">ราคาและแพ็คเกจ</h2>
              <p className="mt-1 text-3xl font-extrabold text-gray-900 sm:text-4xl lg:text-5xl">เลือกแพ็คเกจที่เหมาะกับคุณ</p>
              <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">เริ่มต้นใช้งานฟรี หรืออัปเกรดเพื่อเข้าถึงฟีเจอร์ขั้นสูง</p>
            </div>
             <div className="mt-16 text-center text-gray-500">
                <p>(ส่วนแสดงราคาและแพ็คเกจจะถูกเพิ่มเข้ามาในภายหลัง)</p>
                <div className="mt-8">
                   <Link href="/register" className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-full shadow-md text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all">ดูแพ็คเกจทั้งหมด</Link>
                </div>
            </div>
           </div>
        </section>
        {/* Call to Action Section */}
        <section className="bg-gradient-to-r from-blue-700 to-indigo-700">
          <div className="max-w-4xl mx-auto py-16 px-4 sm:px-6 sm:py-24 lg:max-w-7xl lg:px-8 lg:flex lg:items-center lg:justify-between">
            <h2 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
              <span className="block">พร้อมเปลี่ยนเรื่องภาษี</span>
              <span className="block bg-clip-text text-transparent bg-gradient-to-r from-blue-100 to-indigo-200">ให้เป็นเรื่องง่ายหรือยัง?</span>
            </h2>
            <div className="mt-6 space-y-4 sm:space-y-0 sm:flex sm:space-x-5 lg:mt-0 lg:flex-shrink-0">
              <Link href="/register" className="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-full shadow-md text-blue-700 bg-white hover:bg-blue-50 transition duration-300 transform hover:scale-105">ลงทะเบียนใช้งานฟรี</Link>
              <Link href="/contact" className="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-full text-white bg-blue-500 hover:bg-blue-400 transition duration-300 transform hover:scale-105">ติดต่อฝ่ายขาย</Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900" aria-labelledby="footer-heading">
        <h2 id="footer-heading" className="sr-only">Footer</h2>
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8">
          <div className="pb-8 xl:grid xl:grid-cols-5 xl:gap-8">
            <div className="grid grid-cols-2 gap-8 xl:col-span-4 md:grid-cols-4">
              <div> <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">เกี่ยวกับเรา</h3> <ul role="list" className="mt-4 space-y-4"> <li><Link href="/about" className="text-base text-gray-300 hover:text-white transition-colors">เกี่ยวกับบริษัท</Link></li> <li><Link href="/careers" className="text-base text-gray-300 hover:text-white transition-colors">ร่วมงานกับเรา</Link></li> <li><Link href="/blog" className="text-base text-gray-300 hover:text-white transition-colors">บล็อก</Link></li> </ul> </div>
              <div className="mt-12 md:mt-0"> <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">บริการ</h3> <ul role="list" className="mt-4 space-y-4"> <li><Link href="#features" className="text-base text-gray-300 hover:text-white transition-colors">คุณสมบัติ</Link></li> <li><Link href="#pricing" className="text-base text-gray-300 hover:text-white transition-colors">ราคา</Link></li> <li><Link href="/integrations" className="text-base text-gray-300 hover:text-white transition-colors">การเชื่อมต่อ</Link></li> </ul> </div>
              <div className="mt-12 md:mt-0"> <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">ความช่วยเหลือ</h3> <ul role="list" className="mt-4 space-y-4"> <li><Link href="/faq" className="text-base text-gray-300 hover:text-white transition-colors">คำถามที่พบบ่อย</Link></li> <li><Link href="/docs" className="text-base text-gray-300 hover:text-white transition-colors">คู่มือการใช้งาน</Link></li> <li><Link href="/contact" className="text-base text-gray-300 hover:text-white transition-colors">ติดต่อเรา</Link></li> </ul> </div>
              <div className="mt-12 md:mt-0"> <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">กฎหมาย</h3> <ul role="list" className="mt-4 space-y-4"> <li><Link href="/privacy" className="text-base text-gray-300 hover:text-white transition-colors">นโยบายความเป็นส่วนตัว</Link></li> <li><Link href="/terms" className="text-base text-gray-300 hover:text-white transition-colors">ข้อกำหนดการใช้งาน</Link></li> </ul> </div>
            </div>
            <div className="mt-12 xl:mt-0 xl:col-span-1"> <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">ติดตามข่าวสาร</h3> <p className="mt-4 text-base text-gray-300">รับข่าวสารและเคล็ดลับภาษีส่งตรงถึงอีเมลคุณ</p> <form className="mt-4 sm:flex sm:max-w-md"> <label htmlFor="email-address" className="sr-only">Email address</label> <input type="email" name="email-address" id="email-address" autoComplete="email" required className="appearance-none min-w-0 w-full bg-white border border-transparent rounded-md py-2 px-4 text-base text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white focus:border-white focus:placeholder-gray-400" placeholder="กรอกอีเมลของคุณ" /> <div className="mt-3 rounded-md sm:mt-0 sm:ml-3 sm:flex-shrink-0"> <button type="submit" className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 border border-transparent rounded-md py-2 px-4 flex items-center justify-center text-base font-medium text-white hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-blue-500 transition-all"> ติดตาม </button> </div> </form> </div>
          </div>
          <div className="mt-8 border-t border-gray-700 pt-8 md:flex md:items-center md:justify-between">
            <div className="flex space-x-6 md:order-2">
               <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors"><span className="sr-only">Facebook</span><svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" /></svg></a>
               <a href="#" className="text-gray-400 hover:text-gray-300 transition-colors"><span className="sr-only">Twitter</span><svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg></a>
            </div>
            <p className="mt-8 text-base text-gray-400 md:mt-0 md:order-1">
              © {new Date().getFullYear()} Smart Tax Assistant. สงวนลิขสิทธิ์.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}