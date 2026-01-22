// src/components/Navbar/Navbar.tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Logo from '@/components/Logo';


export default function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <nav className={`fixed w-full top-0 z-50 transition-all duration-200 ${
      scrolled
        ? 'bg-white border-b border-slate-200'
        : 'bg-transparent'
    }`}>
       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Logo href="/" onClick={closeMobileMenu} />
          </div>

          {/* Desktop Menu */}
          <div className="hidden sm:flex sm:items-center sm:space-x-6">
            <Link href="/#features" className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              คุณสมบัติ
            </Link>
            <Link href="/#howItWorks" className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              วิธีใช้งาน
            </Link>
            <Link href="/auth" className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
              ลงทะเบียน
            </Link>
            <Link
              href="/auth"
              className="ml-4 inline-flex items-center px-5 py-2 text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              เข้าสู่ระบบ
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="sm:hidden flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
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

      {isMobileMenuOpen && (
         <div className="sm:hidden bg-white border-b border-slate-200">
           <div className="pt-2 pb-3 space-y-1 px-4">
              <Link href="/#features" className="block px-4 py-3 rounded-lg font-medium text-slate-700 hover:bg-slate-50 transition-colors" onClick={closeMobileMenu}>คุณสมบัติ</Link>
              <Link href="/#howItWorks" className="block px-4 py-3 rounded-lg font-medium text-slate-700 hover:bg-slate-50 transition-colors" onClick={closeMobileMenu}>วิธีใช้งาน</Link>
              <Link href="/auth" className="block px-4 py-3 rounded-lg font-medium text-slate-700 hover:bg-slate-50 transition-colors" onClick={closeMobileMenu}>เข้าสู่ระบบ</Link>
           </div>
           <div className="pt-2 pb-4 px-4 border-t border-slate-100">
             <Link href="/auth" className="block w-full px-5 py-2.5 rounded-lg text-center text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors" onClick={closeMobileMenu}>เริ่มใช้งานฟรี</Link>
           </div>
         </div>
      )}
    </nav>
  );
}
