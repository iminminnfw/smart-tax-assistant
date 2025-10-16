import { 
  User, Wallet, Home, Target, Calendar, FileText 
} from "lucide-react";

export const menuItems = [
  {
    href: '/profile-settings',
    icon: User,
    label: 'จัดการบัญชีผู้ใช้',
    color: 'text-blue-600 bg-blue-100',
    description: 'จัดการข้อมูลส่วนตัวและการตั้งค่า',
  },
  {
    href: '/financial-info',
    icon: Wallet,
    label: 'ข้อมูลทางการเงิน',
    color: 'text-green-600 bg-green-100',
    description: 'รายได้ รายจ่าย และข้อมูลการเงิน',
  },
  {
    href: '/WelcomeHome',
    icon: Home,
    label: 'Dashboard',
    color: 'text-purple-600 bg-purple-100',
    description: 'ภาพรวมและสถิติของคุณ',
  },
  {
    href: '/simulation',
    icon: Target,
    label: 'สร้างสถานการณ์จำลอง',
    color: 'text-orange-600 bg-orange-100',
    description: 'จำลองสถานการณ์ภาษีต่างๆ',
  },
  {
    href: '/calendar',
    icon: Calendar,
    label: 'ปฏิทิน',
    color: 'text-red-600 bg-red-100',
    description: 'กำหนดการและเตือนความจำ',
  },
  {
    href: '/document',   // 👈 เปลี่ยน path จาก /chat → /document
    icon: FileText,      // 👈 ใช้ FileText แทน MessageCircle
    label: 'ไฟล์',       // 👈 เปลี่ยนชื่อเมนู
    color: 'text-indigo-600 bg-indigo-100',
    description: 'จัดการไฟล์เอกสารภาษีต่างๆ', // 👈 อธิบายให้ตรงหมวด
  },
];