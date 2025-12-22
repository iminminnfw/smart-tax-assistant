// src/app/api/auth/register/route.ts
import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import bcrypt from 'bcryptjs';
import { createOTP, OTPPurpose } from '@/lib/otp';
import { sendOTPEmail } from '@/lib/email-service';

function splitFullName(full: string) {
  const parts = (full ?? '').trim().split(/\s+/).filter(Boolean);
  if (parts.length <= 1) return { firstName: parts[0] ?? '', lastName: '' };
  return { firstName: parts[0], lastName: parts.slice(1).join(' ') };
}

export async function POST(req: Request) {
  try {
    const { firstName, lastName, name, email, password } = await req.json();

    // 1) validate เบื้องต้น
    if (!email || !password || (!firstName && !lastName && !name)) {
      return NextResponse.json({ error: 'ข้อมูลไม่ครบ' }, { status: 400 });
    }

    // 2) normalize ชื่อ
    const fn = firstName ?? splitFullName(name).firstName;
    const ln = lastName  ?? splitFullName(name).lastName;
    const displayName = [fn, ln].filter(Boolean).join(' ').trim() || null;

    // 3) กันอีเมลซ้ำ
    const exists = await prisma.user.findUnique({ where: { email } });
    if (exists) {
      return NextResponse.json({ error: 'อีเมลนี้ถูกใช้แล้ว' }, { status: 409 });
    }

    // 4) แฮชรหัสผ่าน
    const passwordHashed = await bcrypt.hash(password, 12);

    // 5) สร้าง User (ยังไม่ยืนยันอีเมล - emailVerified = null)
    const user = await prisma.user.create({
      data: {
        password: passwordHashed,
        email,
        firstName: fn || null,
        lastName:  ln || null,
        name: [fn, ln].filter(Boolean).join(' ') || null,
        emailVerified: null, // ยังไม่ยืนยัน
      },
      select: { id: true, email: true, name: true, firstName: true, lastName: true },
    });

    // 6) สร้าง OTP สำหรับยืนยันอีเมล
    const otp = await createOTP({
      email: user.email,
      userId: user.id,
      purpose: OTPPurpose.EMAIL_VERIFICATION,
      expiresInMinutes: 10,
    });

    // 7) ส่งอีเมล OTP
    const emailResult = await sendOTPEmail({
      to: user.email,
      otpCode: otp.otpCode,
      purpose: OTPPurpose.EMAIL_VERIFICATION,
      expiresInMinutes: 10,
    });

    if (!emailResult.success) {
      console.error('Failed to send OTP email:', emailResult.error);
      // ไม่ return error เพราะ User ถูกสร้างแล้ว แค่ส่งอีเมลไม่สำเร็จ
      // สามารถให้ User ขอ OTP ใหม่ได้
    }

    return NextResponse.json(
      {
        ok: true,
        user,
        message: 'สมัครสมาชิกสำเร็จ กรุณายืนยันอีเมลด้วย OTP ที่ส่งไปยังอีเมลของคุณ',
        requiresEmailVerification: true,
      },
      { status: 201 }
    );
  } catch (e: any) {
    // กัน unique ซ้ำจากระดับ DB (สำรอง)
    if (e?.code === 'P2002') {
      return NextResponse.json({ error: 'ข้อมูลซ้ำ (unique)' }, { status: 409 });
    }
    console.error('REGISTER ERROR:', e);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
