/**
 * OTP Service - สำหรับสร้าง ยืนยัน และจัดการ OTP
 */

import { prisma } from '@/lib/prisma';
import crypto from 'crypto';

export enum OTPPurpose {
  EMAIL_VERIFICATION = 'EMAIL_VERIFICATION',
  LOGIN_MFA = 'LOGIN_MFA',
  PASSWORD_RESET = 'PASSWORD_RESET',
}

export interface CreateOTPOptions {
  email: string;
  userId?: string;
  purpose: OTPPurpose;
  expiresInMinutes?: number;
}

export interface VerifyOTPOptions {
  email: string;
  otpCode: string;
  purpose: OTPPurpose;
}

/**
 * สร้าง OTP 6 หลักแบบสุ่ม
 */
function generateOTPCode(): string {
  return crypto.randomInt(100000, 999999).toString();
}

/**
 * สร้าง OTP ใหม่และเก็บลงฐานข้อมูล
 */
export async function createOTP(options: CreateOTPOptions) {
  const {
    email,
    userId,
    purpose,
    expiresInMinutes = 10, // default 10 นาที
  } = options;

  // ลบ OTP เก่าที่ยังไม่ verified สำหรับ email และ purpose นี้
  await prisma.oTP.deleteMany({
    where: {
      email,
      purpose,
      verified: false,
    },
  });

  // สร้าง OTP code
  const otpCode = generateOTPCode();

  // คำนวณเวลาหมดอายุ
  const expiresAt = new Date();
  expiresAt.setMinutes(expiresAt.getMinutes() + expiresInMinutes);

  // บันทึกลงฐานข้อมูล
  const otp = await prisma.oTP.create({
    data: {
      email,
      userId: userId || null,
      otpCode,
      purpose,
      expiresAt,
      verified: false,
      attempts: 0,
      maxAttempts: 5,
    },
  });

  return {
    id: otp.id,
    otpCode,
    expiresAt,
  };
}

/**
 * ยืนยัน OTP
 */
export async function verifyOTP(options: VerifyOTPOptions) {
  const { email, otpCode, purpose } = options;

  // หา OTP ที่ตรงกับเงื่อนไข
  const otp = await prisma.oTP.findFirst({
    where: {
      email,
      purpose,
      verified: false,
    },
    orderBy: {
      createdAt: 'desc',
    },
  });

  // ไม่พบ OTP
  if (!otp) {
    return {
      success: false,
      error: 'OTP not found or already used',
    };
  }

  // ตรวจสอบว่าหมดอายุแล้วหรือไม่
  if (new Date() > otp.expiresAt) {
    return {
      success: false,
      error: 'OTP has expired',
    };
  }

  // ตรวจสอบจำนวนครั้งที่พยายามกรอก
  if (otp.attempts >= otp.maxAttempts) {
    return {
      success: false,
      error: 'Maximum verification attempts exceeded',
    };
  }

  // ตรวจสอบ OTP code
  if (otp.otpCode !== otpCode) {
    // เพิ่มจำนวนครั้งที่พยายามกรอกผิด
    await prisma.oTP.update({
      where: { id: otp.id },
      data: {
        attempts: otp.attempts + 1,
      },
    });

    return {
      success: false,
      error: 'Invalid OTP code',
      attemptsLeft: otp.maxAttempts - (otp.attempts + 1),
    };
  }

  // OTP ถูกต้อง - mark as verified
  await prisma.oTP.update({
    where: { id: otp.id },
    data: {
      verified: true,
      verifiedAt: new Date(),
    },
  });

  return {
    success: true,
    userId: otp.userId,
  };
}

/**
 * ลบ OTP ที่หมดอายุแล้ว (cleanup)
 */
export async function cleanupExpiredOTPs() {
  const result = await prisma.oTP.deleteMany({
    where: {
      expiresAt: {
        lt: new Date(),
      },
    },
  });

  return {
    deletedCount: result.count,
  };
}

/**
 * ตรวจสอบว่ามี OTP ที่ยังใช้ได้อยู่หรือไม่
 */
export async function hasValidOTP(
  email: string,
  purpose: OTPPurpose
): Promise<boolean> {
  const otp = await prisma.oTP.findFirst({
    where: {
      email,
      purpose,
      verified: false,
      expiresAt: {
        gt: new Date(),
      },
    },
  });

  return otp !== null;
}
