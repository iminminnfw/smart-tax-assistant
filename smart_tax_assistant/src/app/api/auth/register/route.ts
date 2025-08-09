import { NextResponse } from 'next/server';
// [แก้ไข] นำเข้า Prisma Client จากที่เดียวเพื่อประสิทธิภาพที่ดีกว่า
// หากยังไม่มีไฟล์นี้ ให้สร้าง src/lib/prisma.ts แล้วใส่ `export const prisma = new PrismaClient();`
// แต่เพื่อความง่าย จะใช้แบบเดิมไปก่อน
import { PrismaClient } from '@/generated/prisma/client';import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // --- [จุดแก้ไขที่สำคัญที่สุด] ---
    // ดึงค่าเฉพาะฟิลด์ที่ต้องการออกมาจาก body
    // เพื่อป้องกันไม่ให้มี field อื่นๆ ที่ไม่ต้องการ (เช่น id) ปะปนเข้าไป
    const { name, email, password } = body;

    // 1. ตรวจสอบว่ามีข้อมูลหลักครบถ้วนหรือไม่
    if (!name || !email || !password) {
      return NextResponse.json({ error: 'กรุณากรอกข้อมูลให้ครบถ้วน' }, { status: 400 });
    }
    
    // 2. ตรวจสอบว่ามีอีเมลนี้ในระบบแล้วหรือยัง
    const existingUser = await prisma.user.findUnique({ 
      where: { email: email } 
    });

    if (existingUser) {
      return NextResponse.json({ error: 'อีเมลนี้ถูกใช้งานแล้ว' }, { status: 409 }); // 409 Conflict
    }

    // 3. เข้ารหัสรหัสผ่าน (Hashing)
    const hashedPassword = await bcrypt.hash(password, 10);

    // 4. สร้างผู้ใช้ใหม่ในฐานข้อมูล โดยใช้ตัวแปรที่ดึงออกมา
    const user = await prisma.user.create({
      data: {
        name: name,
        email: email,
        password: hashedPassword,
        // ไม่ต้องระบุ id ที่นี่ ปล่อยให้ Prisma จัดการเอง!
      },
    });

    // ไม่ส่งข้อมูล user ทั้งหมดกลับไปเพื่อความปลอดภัย
    const userResult = {
      id: user.id,
      name: user.name,
      email: user.email
    };

    return NextResponse.json({ message: 'สร้างบัญชีสำเร็จ!', user: userResult }, { status: 201 });

  } catch (error) {
    console.error('[REGISTER_API_ERROR]', error);

    // เพิ่มการตรวจสอบประเภทของ error เพื่อให้ response ฉลาดขึ้น
    if (error instanceof Error && 'code' in error && (error as any).code === 'P2002') {
         return NextResponse.json({ error: 'อีเมลนี้ถูกใช้งานแล้ว' }, { status: 409 });
    }

    return NextResponse.json({ error: 'เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์' }, { status: 500 });
  }
}