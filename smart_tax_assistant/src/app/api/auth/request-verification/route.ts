// src/app/api/auth/request-verification/route.ts
import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { createOTP, OTPPurpose } from '@/lib/otp';
import { sendOTPEmail } from '@/lib/email-service';

/**
 * Request Email Verification OTP
 * สำหรับ user เก่าที่ยังไม่ได้ยืนยันอีเมล
 */
export async function POST(req: Request) {
  try {
    const { email } = await req.json();

    // 1) Validate input
    if (!email) {
      return NextResponse.json(
        { error: 'กรุณาระบุอีเมล' },
        { status: 400 }
      );
    }

    // 2) หา user จาก email
    const user = await prisma.user.findUnique({
      where: { email },
      select: {
        id: true,
        email: true,
        emailVerified: true,
      },
    });

    if (!user) {
      return NextResponse.json(
        { error: 'ไม่พบอีเมลนี้ในระบบ' },
        { status: 404 }
      );
    }

    // 3) ตรวจสอบว่ายืนยันอีเมลแล้วหรือยัง
    if (user.emailVerified) {
      return NextResponse.json(
        {
          error: 'อีเมลนี้ได้รับการยืนยันแล้ว',
          alreadyVerified: true
        },
        { status: 400 }
      );
    }

    // 4) สร้าง OTP สำหรับ Email Verification
    const otp = await createOTP({
      email: user.email,
      userId: user.id,
      purpose: OTPPurpose.EMAIL_VERIFICATION,
      expiresInMinutes: 10,
    });

    // 5) ส่งอีเมล OTP
    const emailResult = await sendOTPEmail({
      to: user.email,
      otpCode: otp.otpCode,
      purpose: OTPPurpose.EMAIL_VERIFICATION,
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

    // 6) Return success
    return NextResponse.json({
      success: true,
      message: 'ส่งอีเมลยืนยันสำเร็จ กรุณาตรวจสอบอีเมลของคุณ',
      email: user.email,
      expiresAt: otp.expiresAt,
    });
  } catch (error: any) {
    console.error('REQUEST VERIFICATION ERROR:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error.message },
      { status: 500 }
    );
  }
}
