/**
 * Migration Script: อัพเดท emailVerified สำหรับ user เก่าที่สมัครก่อนมี MFA
 *
 * วิธีใช้:
 * npx tsx scripts/migrate-existing-users.ts
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function migrateExistingUsers() {
  console.log('🔄 กำลังอัพเดท user เก่าที่ยังไม่มี emailVerified...\n');

  try {
    // 1. หา user ทั้งหมดที่ emailVerified = null
    const usersToUpdate = await prisma.user.findMany({
      where: {
        emailVerified: null,
      },
      select: {
        id: true,
        email: true,
        createdAt: true,
      },
    });

    console.log(`📊 พบ user ที่ต้องอัพเดท: ${usersToUpdate.length} คน\n`);

    if (usersToUpdate.length === 0) {
      console.log('✅ ไม่มี user ที่ต้องอัพเดท');
      return;
    }

    // 2. แสดงรายชื่อ user ที่จะอัพเดท
    console.log('📋 รายชื่อ user ที่จะอัพเดท:');
    usersToUpdate.forEach((user, index) => {
      console.log(`   ${index + 1}. ${user.email} (สมัครเมื่อ: ${user.createdAt.toLocaleDateString('th-TH')})`);
    });
    console.log('');

    // 3. ถามยืนยัน (comment out ถ้าต้องการ auto-run)
    console.log('⚠️  คุณต้องการอัพเดท user เหล่านี้หรือไม่?');
    console.log('   (แก้ไข script นี้แล้วรันใหม่ถ้าต้องการดำเนินการ)\n');

    // Uncomment บรรทัดด้านล่างเพื่อให้ script ทำงานจริง
    const CONFIRM_UPDATE = true; // เปลี่ยนเป็น true เพื่อยืนยัน

    if (!CONFIRM_UPDATE) {
      console.log('❌ ยกเลิกการอัพเดท (เปลี่ยน CONFIRM_UPDATE = true ถ้าต้องการดำเนินการ)');
      return;
    }

    // 4. อัพเดท emailVerified สำหรับ user เก่าทั้งหมด
    const result = await prisma.user.updateMany({
      where: {
        emailVerified: null,
      },
      data: {
        emailVerified: new Date(), // ใช้เวลาปัจจุบัน
      },
    });

    console.log(`✅ อัพเดทสำเร็จ: ${result.count} users\n`);

    // 5. แสดงผลลัพธ์
    const updatedUsers = await prisma.user.findMany({
      where: {
        id: { in: usersToUpdate.map((u) => u.id) },
      },
      select: {
        email: true,
        emailVerified: true,
      },
    });

    console.log('📋 ผลลัพธ์หลังอัพเดท:');
    updatedUsers.forEach((user, index) => {
      console.log(`   ${index + 1}. ${user.email}`);
      console.log(`      ✓ emailVerified: ${user.emailVerified?.toLocaleString('th-TH')}`);
    });

    console.log('\n🎉 Migration สำเร็จ!');
    console.log('💡 user เก่าทั้งหมดสามารถ login ได้แล้วโดยไม่ต้องยืนยันอีเมล\n');

  } catch (error) {
    console.error('❌ เกิดข้อผิดพลาด:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

// Run migration
migrateExistingUsers()
  .catch((error) => {
    console.error('Migration failed:', error);
    process.exit(1);
  });
