// src/app/api/auth/login-mfa/route.ts
import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import bcrypt from 'bcryptjs';
import { createOTP, OTPPurpose } from '@/lib/otp';
import { sendOTPEmail } from '@/lib/email-service';

/**
 * Step 1 of Login MFA: ตรวจสอบ credentials และส่ง OTP
 */
export async function POST(req: Request) {
  try {
    const { email, password } = await req.json();

    // 1) Validate input
    if (!email || !password) {
      return NextResponse.json(
        { error: 'ข้อมูลไม่ครบ - ต้องการ email และ password' },
        { status: 400 }
      );
    }

    // 2) หา user จาก email
    const user = await prisma.user.findUnique({
      where: { email },
      select: {
        id: true,
        email: true,
        password: true,
        name: true,
        firstName: true,
        lastName: true,
        emailVerified: true,
      },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' },
        { status: 401 }
      );
    }

    // 3) ตรวจสอบรหัสผ่าน
    const isValidPassword = await bcrypt.compare(password, user.password);
    if (!isValidPassword) {
      return NextResponse.json(
        { error: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' },
        { status: 401 }
      );
    }

    // 4) ตรวจสอบว่ายืนยันอีเมลแล้วหรือยัง
    if (!user.emailVerified) {
      return NextResponse.json(
        {
          error: 'กรุณายืนยันอีเมลก่อนเข้าสู่ระบบ',
          requiresEmailVerification: true,
        },
        { status: 403 }
      );
    }

    // 5) สร้าง OTP สำหรับ Login MFA
    const otp = await createOTP({
      email: user.email,
      userId: user.id,
      purpose: OTPPurpose.LOGIN_MFA,
      expiresInMinutes: 10,
    });

    // 6) ส่งอีเมล OTP
    const emailResult = await sendOTPEmail({
      to: user.email,
      otpCode: otp.otpCode,
      purpose: OTPPurpose.LOGIN_MFA,
      expiresInMinutes: 10,
    });

    if (!emailResult.success) {
      console.error('Failed to send OTP email:', emailResult.error);
      return NextResponse.json(
        {
          success: false,
          error: 'ไม่สามารถส่งอีเมล OTP ได้ กรุณาลองใหม่อีกครั้ง',
        },
        { status: 500 }
      );
    }

    // 7) Return success พร้อมบอกว่าต้องกรอก OTP
    return NextResponse.json({
      success: true,
      message: 'ส่ง OTP สำเร็จ กรุณาตรวจสอบอีเมลของคุณ',
      requiresOTP: true,
      email: user.email,
      expiresAt: otp.expiresAt,
    });
  } catch (error: any) {
    console.error('LOGIN MFA ERROR:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error.message },
      { status: 500 }
    );
  }
}
