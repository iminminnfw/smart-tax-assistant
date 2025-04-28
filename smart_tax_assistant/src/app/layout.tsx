// src/app/layout.tsx
import type { Metadata } from "next";
import { Sarabun } from "next/font/google";
import "../styles/globals.css"; // Import Tailwind CSS และ custom styles

// Import Components ที่แยกออกมา
import Navbar from "@/components/Navbar/Navbar"; 
import Footer from "@/components/Footer/Footer"; 

// ตั้งค่า Font
const sarabun = Sarabun({
  weight: ["300", "400", "500", "700"],
  subsets: ["latin", "thai"],
  variable: '--font-sarabun',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "SmartTax Assistant", 
  description: "ระบบจัดการภาษีอัจฉริยะด้วย AI ทำให้เรื่องภาษีเป็นเรื่องง่าย",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      {/*
        เพิ่ม class flex flex-col min-h-screen ให้ body
        เพื่อให้ Footer ถูกดันลงไปอยู่ล่างสุดเสมอ
      */}
      <body className={`${sarabun.className} flex flex-col min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 text-gray-800`}>
        <Navbar /> {/* แสดง Navbar ทุกหน้า */}
        {/*
          เพิ่ม class flex-grow ให้ main
          เพื่อให้เนื้อหายืดเต็มพื้นที่ที่เหลือระหว่าง Navbar และ Footer
        */}
        <main className="flex-grow">
          {children} {/* แสดงเนื้อหาของ Page Component ที่นี่ */}
        </main>
        <Footer /> {/* แสดง Footer ทุกหน้า */}
      </body>
    </html>
  );
}