'use client';

import { useRouter } from 'next/navigation';



export default function TermsContent() {
  const router = useRouter();

  const handleBack = () => {
    router.push('/register'); // Navigate to register page
  };

  return (
    <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 pt-28 md:pt-36">
      <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-lg border border-gray-100">
        {/* Back Button */}
       <button
       onClick={handleBack}
       className="inline-flex items-center gap-2 mb-8 px-5 py-2.5 text-sm font-semibold text-blue-488 bg-white border-2 border-blue-200 hover:border-blue-500 hover:bg-blue-50 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 
       focus:ring-blue-500 focus:ring-offset-2 transform hover:-translate-y-0.5">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        กลับไปหน้าสมัครสมาชิก
        </button>

        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-gray-900">
            ข้อกำหนดการใช้งาน (Terms of Service)
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            อัปเดตล่าสุด: 10 มิถุนายน 2568
          </p>
        </div>

        <div className="prose prose-lg max-w-none">
          <h2><strong>1. การยอมรับข้อกำหนด</strong></h2>
          <p>
            โดยการเข้าถึงหรือใช้บริการ SmartTax Assistant ("บริการ") คุณตกลงที่จะผูกพันตามข้อกำหนดการใช้งานเหล่านี้ ("ข้อกำหนด")
            หากคุณไม่ยอมรับข้อกำหนดทั้งหมด คุณจะไม่สามารถเข้าถึงหรือใช้บริการได้
          </p>

          <h2><strong>2. คำอธิบายบริการ</strong></h2>
          <p>
            SmartTax Assistant เป็นแพลตฟอร์มที่ให้คำแนะนำเบื้องต้นด้านภาษีและเครื่องมือช่วยคำนวณภาษีโดยใช้เทคโนโลยีปัญญาประดิษฐ์
            ข้อมูลที่ได้รับจากบริการนี้ <strong className="text-red-600">**ไม่ใช่คำแนะนำทางกฎหมายหรือการเงินอย่างเป็นทางการ**</strong> และไม่สามารถใช้แทนที่คำปรึกษาจากผู้เชี่ยวชาญด้านภาษีหรือนักบัญชีที่มีใบอนุญาตได้
          </p>

          <h2><strong>3. การใช้งานที่ได้รับอนุญาต</strong></h2>
          <p>
            คุณตกลงที่จะใช้บริการเพื่อวัตถุประสงค์ที่ถูกต้องตามกฎหมายและเป็นไปตามข้อกำหนดเหล่านี้เท่านั้น คุณจะไม่ใช้บริการเพื่อ:
          </p>
          <ul>
            <li>กิจกรรมที่ผิดกฎหมายหรือฉ้อโกง</li>
            <li>การกระทำที่ละเมิดสิทธิ์ในทรัพย์สินทางปัญญาของผู้อื่น</li>
            <li>การส่งหรืออัปโหลดข้อมูลที่เป็นอันตราย เช่น ไวรัสหรือมัลแวร์</li>
          </ul>

          <h2><strong>4. ข้อจำกัดความรับผิดชอบ</strong></h2>
          <p>
            บริการนี้จัดทำขึ้น "ตามสภาพ" และ "ตามที่มี" เราไม่รับประกันความถูกต้อง ความสมบูรณ์ หรือความน่าเชื่อถือของข้อมูลใดๆ ที่ได้รับจากบริการ
            การตัดสินใจใดๆ ที่เกิดจากการใช้ข้อมูลจากบริการนี้ถือเป็นความรับผิดชอบของคุณแต่เพียงผู้เดียว เราขอแนะนำให้ปรึกษาผู้เชี่ยวชาญก่อนตัดสินใจทางการเงินหรือภาษีที่สำคัญ
          </p>

          <h2><strong>5. การติดต่อเรา</strong></h2>
          <p>
            หากคุณมีคำถามเกี่ยวกับข้อกำหนดเหล่านี้ โปรดติดต่อเราที่ <a href="mailto:contact@smarttax.com"><strong>contact@smarttax.com</strong></a>
          </p>
        </div>
      </div>
    </div>
  );
}