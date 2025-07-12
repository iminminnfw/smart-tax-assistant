import type { Metadata } from 'next';
import TermsContent from './TermsContent'; // Import Client Component ที่แยกออกมา

// คุณสามารถ export metadata ได้แล้ว เพราะไฟล์นี้เป็น Server Component
export const metadata: Metadata = {
  title: 'ข้อกำหนดการใช้งาน - SmartTax Assistant',
  description: 'ข้อกำหนดและเงื่อนไขการใช้งานบริการ SmartTax Assistant',
};

export default function TermsPage() {
  // เรียกใช้ Client Component ที่มี Logic การโต้ตอบกับผู้ใช้
  return <TermsContent />;
}