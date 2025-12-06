// src/app/api/auth/verify-otp/route.ts
import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { verifyOTP, OTPPurpose } from '@/lib/otp';
import { sendWelcomeEmail } from '@/lib/email-service';

export async function POST(req: Request) {
  try {
    const { email, otpCode, purpose } = await req.json();

    // 1) Validate input
    if (!email || !otpCode || !purpose) {
      return NextResponse.json(
        { error: 'ข้อมูลไม่ครบ - ต้องการ email, otpCode และ purpose' },
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

    // 2) ยืนยัน OTP
    const verificationResult = await verifyOTP({
      email,
      otpCode,
      purpose,
    });

    if (!verificationResult.success) {
      return NextResponse.json(
        {
          success: false,
          error: verificationResult.error,
          attemptsLeft: verificationResult.attemptsLeft,
        },
        { status: 400 }
      );
    }

    // 3) ดำเนินการตาม purpose
    if (purpose === OTPPurpose.EMAIL_VERIFICATION) {
      // อัพเดท emailVerified
      const user = await prisma.user.update({
        where: { email },
        data: {
          emailVerified: new Date(),
        },
        select: {
          id: true,
          email: true,
          name: true,
          firstName: true,
          lastName: true,
          emailVerified: true,
        },
      });

      // ส่งอีเมลต้อนรับ (optional)
      try {
        await sendWelcomeEmail(user.email, user.name || user.firstName || 'ผู้ใช้');
      } catch (emailError) {
        console.error('Failed to send welcome email:', emailError);
        // ไม่ return error เพราะการยืนยันสำเร็จแล้ว
      }

      return NextResponse.json({
        success: true,
        message: 'ยืนยันอีเมลสำเร็จ!',
        user,
      });
    } else if (purpose === OTPPurpose.LOGIN_MFA) {
      // สำหรับ Login MFA - จะ return success และให้ client ทำการ login
      const user = await prisma.user.findUnique({
        where: { email },
        select: {
          id: true,
          email: true,
          name: true,
          firstName: true,
          lastName: true,
        },
      });

      return NextResponse.json({
        success: true,
        message: 'ยืนยัน OTP สำเร็จ!',
        user,
        requiresLogin: true, // บอก client ว่าต้อง complete login flow
      });
    } else if (purpose === OTPPurpose.PASSWORD_RESET) {
      // สำหรับ Password Reset - จะ return token สำหรับรีเซ็ตรหัสผ่าน
      return NextResponse.json({
        success: true,
        message: 'ยืนยัน OTP สำเร็จ!',
        allowPasswordReset: true,
        email,
      });
    }

    return NextResponse.json({
      success: true,
      message: 'ยืนยัน OTP สำเร็จ!',
    });
  } catch (error: any) {
    console.error('VERIFY OTP ERROR:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error.message },
      { status: 500 }
    );
  }
}
