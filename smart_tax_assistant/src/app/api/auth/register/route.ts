// src/app/api/auth/register/route.ts
import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import bcrypt from 'bcryptjs';

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

    // ⬇️ ใช้อย่างใดอย่างหนึ่งให้ตรง schema ของคุณ
    // ถ้า schema มี field "passwordHash":
    const user = await prisma.user.create({
      data: {
        password: passwordHashed,
        email,// ✅ ใช้ฟิลด์ "password" ให้ตรง schema
        firstName: fn || null,
        lastName:  ln || null,
        name: [fn, ln].filter(Boolean).join(' ') || null,
  },
  select: { id: true, email: true, name: true, firstName: true, lastName: true },
});

    // // ถ้า schema ของคุณยังเป็น field "password":
    // const user = await prisma.user.create({
    //   data: {
    //     email,
    //     password: passwordHash,       // ← เก็บแฮชลงฟิลด์ password
    //     firstName: fn || null,
    //     lastName:  ln || null,
    //     name: displayName,
    //   },
    //   select: { id: true, email: true, name: true, firstName: true, lastName: true },
    // });

    return NextResponse.json({ ok: true, user }, { status: 201 });
  } catch (e: any) {
    // กัน unique ซ้ำจากระดับ DB (สำรอง)
    if (e?.code === 'P2002') {
      return NextResponse.json({ error: 'ข้อมูลซ้ำ (unique)' }, { status: 409 });
    }
    console.error('REGISTER ERROR:', e);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
