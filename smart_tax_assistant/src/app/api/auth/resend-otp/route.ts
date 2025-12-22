// src/app/api/auth/resend-otp/route.ts
import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { createOTP, OTPPurpose, hasValidOTP } from '@/lib/otp';
import { sendOTPEmail } from '@/lib/email-service';

export async function POST(req: Request) {
  try {
    const { email, purpose } = await req.json();

    // 1) Validate input
    if (!email || !purpose) {
      return NextResponse.json(
        { error: 'ข้อมูลไม่ครบ - ต้องการ email และ purpose' },
        { status: 400 }
      );
    }

    // ตรวจสอบว่า purpose ถูกต้อง
    if (!Object.values(OTPPurpose).includes(purpose)) {
      return NextResponse.json(
        { error: 'purpose ไม่ถูกต้อง' },
        { status: 400 }
      );
    }

    // 2) ตรวจสอบว่า user มีอยู่จริง
    const user = await prisma.user.findUnique({
      where: { email },
      select: { id: true, email: true, emailVerified: true },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'ไม่พบผู้ใช้ที่มีอีเมลนี้' },
        { status: 404 }
      );
    }

    // 3) ตรวจสอบว่ามี OTP ที่ยังใช้ได้อยู่หรือไม่ (rate limiting)
    const hasOTP = await hasValidOTP(email, purpose);
    if (hasOTP) {
      return NextResponse.json(
        {
          error: 'คุณมี OTP ที่ยังใช้ได้อยู่แล้ว กรุณารอให้หมดอายุก่อนขอใหม่',
        },
        { status: 429 } // Too Many Requests
      );
    }

    // 4) สร้าง OTP ใหม่
    const otp = await createOTP({
      email: user.email,
      userId: user.id,
      purpose,
      expiresInMinutes: 10,
    });

    // 5) ส่งอีเมล OTP
    const emailResult = await sendOTPEmail({
      to: user.email,
      otpCode: otp.otpCode,
      purpose,
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

    return NextResponse.json({
      success: true,
      message: 'ส่ง OTP ใหม่สำเร็จ กรุณาตรวจสอบอีเมลของคุณ',
      expiresAt: otp.expiresAt,
    });
  } catch (error: any) {
    console.error('RESEND OTP ERROR:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error.message },
      { status: 500 }
    );
  }
}
