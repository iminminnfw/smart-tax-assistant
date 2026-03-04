// src/app/api/user/profile/route.ts
export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// ---------- GET: ดึงโปรไฟล์ ----------
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const u = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: {
      id: true, email: true, name: true, image: true,
      firstName: true, lastName: true, phone: true,
      dateOfBirth: true, address: true, district: true, province: true, postalCode: true,
      occupation: true, annualIncome: true, taxType: true,
      language: true,
      notifyEnabled: true, notifyEmail: true, notifySms: true, notifyTaxDeadlines: true, notifyReports: true,
      createdAt: true,
    },
  });

  if (!u) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  // แปลงเป็น shape ที่หน้า UI ใช้
  return NextResponse.json({
    personalInfo: {
      firstName: u.firstName ?? '',
      lastName : u.lastName  ?? '',
      email    : u.email,
      phone    : u.phone ?? '',
      dateOfBirth: u.dateOfBirth ? u.dateOfBirth.toISOString().slice(0, 10) : '',
      address  : u.address ?? '',
      district : u.district ?? '',
      province : u.province ?? '',
      postalCode: u.postalCode ?? '',
    },
    taxInfo: {
      occupation  : u.occupation ?? '',
      annualIncome: u.annualIncome ? String(u.annualIncome) : '',
      taxType     : (u.taxType ?? 'INDIVIDUAL').toLowerCase(), // 'individual'
    },
    preferences: {
      language: (u.language ?? 'TH').toLowerCase(),            // 'th' | 'en'
      notifications: {
        enabled: !!u.notifyEnabled,
        email  : !!u.notifyEmail,
        sms    : !!u.notifySms,
      },
    },
    meta: {
      id: u.id,
      name: u.name,
      image: u.image,
      createdAt: u.createdAt,
    }
  });
}

// ---------- PATCH: อัปเดตโปรไฟล์ ----------
export async function PATCH(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await req.json().catch(() => ({}));

  const pi = body?.personalInfo ?? {};
  const tx = body?.taxInfo ?? {};
  const pref = body?.preferences ?? {};
  const noti = pref?.notifications ?? {};

  // validate เบื้องต้นแบบเบาๆ
  const up: any = {};

  // personal info
  if (typeof pi.firstName === 'string') up.firstName = pi.firstName.trim() || null;
  if (typeof pi.lastName  === 'string') up.lastName  = pi.lastName.trim()  || null;
  if (typeof pi.phone     === 'string') up.phone     = pi.phone.trim()     || null;
  if (typeof pi.address   === 'string') up.address   = pi.address.trim()   || null;
  if (typeof pi.district  === 'string') up.district  = pi.district.trim()  || null;
  if (typeof pi.province  === 'string') up.province  = pi.province.trim()  || null;
  if (typeof pi.postalCode=== 'string') up.postalCode= pi.postalCode.trim()|| null;

  if (typeof pi.dateOfBirth === 'string' && pi.dateOfBirth) {
    const d = new Date(pi.dateOfBirth);
    if (!Number.isNaN(d.getTime())) up.dateOfBirth = d;
  } else if (pi.dateOfBirth === '') {
    up.dateOfBirth = null;
  }

  // ชื่อเต็ม name = first + last (ไม่เปิดเปลี่ยนอีเมลผ่าน endpoint นี้)
  if ('firstName' in pi || 'lastName' in pi) {
    const fn = (pi.firstName ?? '').toString().trim();
    const ln = (pi.lastName  ?? '').toString().trim();
    const name = `${fn} ${ln}`.trim();
    up.name = name || null;
  }

  // tax info
  if (typeof tx.occupation   === 'string') up.occupation   = tx.occupation.trim()   || null;
  if (tx.annualIncome !== undefined && tx.annualIncome !== '') {
    const v = Number(tx.annualIncome);
    if (!Number.isNaN(v) && v >= 0) up.annualIncome = v.toString(); // Prisma Decimal รับ string
  }
  if (typeof tx.taxType === 'string') {
    // Prisma enum: INDIVIDUAL
    up.taxType = 'INDIVIDUAL';
  }

  // preferences
  if (typeof pref.language === 'string') {
    up.language = (pref.language || 'th').toUpperCase(); // TH | EN
  }
  if (typeof noti.enabled === 'boolean') up.notifyEnabled = noti.enabled;
  if (typeof noti.email   === 'boolean') up.notifyEmail   = noti.email;
  if (typeof noti.sms     === 'boolean') up.notifySms     = noti.sms;

  // อัปเดต
  const saved = await prisma.user.update({
    where: { email: session.user.email },
    data: up,
    select: { id: true } // ตอบเบา ๆ พอ; FE จะ refetch อีกรอบก็ได้
  });

  return NextResponse.json({ ok: true, id: saved.id });
}
