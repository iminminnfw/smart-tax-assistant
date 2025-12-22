// src/lib/auth.ts
import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import prisma from "@/lib/prisma";
import bcrypt from "bcryptjs";
import { verifyOTP, OTPPurpose } from "@/lib/otp";

export const authOptions: NextAuthOptions = {

  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
        otpCode: { label: "OTP Code", type: "text" },
        skipOtp: { label: "Skip OTP", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const user = await prisma.user.findUnique({
          where: { email: credentials.email },
        });

        if (!user) return null;

        const isValid = await bcrypt.compare(credentials.password, user.password);
        if (!isValid) return null;

        // ตรวจสอบว่ายืนยันอีเมลแล้วหรือยัง
        if (!user.emailVerified) {
          throw new Error("EMAIL_NOT_VERIFIED");
        }

        // ตรวจสอบ OTP (optional - เฉพาะเมื่อมี otpCode ส่งมา)
        if (credentials.otpCode) {
          // ถ้ามี OTP code ส่งมา ให้ยืนยัน OTP
          const otpResult = await verifyOTP({
            email: credentials.email,
            otpCode: credentials.otpCode,
            purpose: OTPPurpose.LOGIN_MFA,
          });

          if (!otpResult.success) {
            throw new Error(`OTP_INVALID: ${otpResult.error}`);
          }
        }
        // ถ้าไม่มี otpCode ส่งมา ก็ให้ผ่านได้เลย (ไม่บังคับ MFA)

        // ส่งข้อมูล user กลับไปใน session
        return {
          id: user.id,
          name: user.name,
          email: user.email,
        };
      },
    }),
  ],
  session: { strategy: "jwt" },
  pages: {
    signIn: "/auth", // หน้า login ของคุณ
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) token.id = (user as any).id;
      return token;
    },
    async session({ session, token }) {
      if (session.user && token?.id) {
        (session.user as any).id = token.id as string; 
      }
      return session;
    },
  },
};