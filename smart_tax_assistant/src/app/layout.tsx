// src/app/layout.tsx
import type { Metadata } from "next";
import { Prompt } from "next/font/google"; 
import "../styles/globals.css"; 

import AuthProvider from "@/components/AuthProvider";

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
        <main className="flex-grow">
          <AuthProvider>
            {children} 
          </AuthProvider>
          
        </main>
      </body>
    </html>
  );
}