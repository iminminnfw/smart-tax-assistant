// src/app/api/auth/[...nextauth]/route.ts

import NextAuth, { AuthOptions } from "next-auth"; // <-- [1] Import AuthOptions
import { PrismaAdapter } from "@auth/prisma-adapter";
import prisma from "@/lib/prisma";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from 'bcrypt';


// [2] เพิ่ม Type 'AuthOptions' ตรงนี้ เพื่อให้ TypeScript ตรวจสอบความถูกต้องทั้งหมด
export const authOptions: AuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('กรุณากรอกข้อมูลให้ครบถ้วน');
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email }
        });

        if (!user || !user.password) {
          throw new Error('อีเมลหรือรหัสผ่านไม่ถูกต้อง');
        }

        const isPasswordCorrect = await bcrypt.compare(
          credentials.password,
          user.password
        );

        if (!isPasswordCorrect) {
          throw new Error('อีเมลหรือรหัสผ่านไม่ถูกต้อง');
        }
        
        return user;
      }
    })
  ],
  session: {
    // ตอนนี้ TypeScript จะรู้ว่า "jwt" เป็นค่าที่ถูกต้อง
    strategy: "jwt", 
  },
  secret: process.env.NEXTAUTH_SECRET,
  pages: {
    signIn: '/auth',
  },
};

const handler = NextAuth(authOptions); // <-- Error จะหายไปจากตรงนี้

export { handler as GET, handler as POST };