// src/app/layout.tsx
import type { Metadata } from "next";
import { Prompt } from "next/font/google"; 
import "../styles/globals.css"; 

import Navbar from "@/components/Navbar/Navbar"; 
import Footer from "@/components/Footer/Footer"; 

const selectedFont = Prompt({
  weight: ["300", "400", "500", "700"],
  subsets: ["latin", "thai"],
  variable: '--font-selected',
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
     
      <body className={`${selectedFont.className} flex flex-col min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 text-gray-800`}>
        <Navbar /> 
        <main className="flex-grow">
          {children} 
        </main>
        <Footer /> 
      </body>
    </html>
  );
}