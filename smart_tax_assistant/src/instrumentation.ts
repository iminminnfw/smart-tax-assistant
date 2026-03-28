// src/instrumentation.ts
// รันทันทีเมื่อ Next.js server เริ่มต้น
// ตั้ง node-cron สำหรับส่งแจ้งเตือน deadline ภาษี
// ยิงเฉพาะ 3 รอบต่อ deadline: 30 วัน / 15 วัน / 7 วัน ก่อนครบกำหนด
// เวลาทั้งหมดเป็น ICT (Asia/Bangkok)

export async function register() {
  // รันเฉพาะฝั่ง server เท่านั้น
  if (process.env.NEXT_RUNTIME !== 'nodejs') return;

  const cron = (await import('node-cron')).default;
  const { runTaxReminder } = await import('@/lib/cron/tax-reminder');

  // ============================================================
  // ตารางเวลา: "นาที ชั่วโมง(UTC) วัน เดือน *"
  // ICT = UTC+7 → 08:00 ICT = 01:00 UTC
  //
  // ภ.ง.ด. 90 เอกสาร   deadline: 31 มี.ค.
  //   -30 วัน → 1  มี.ค.  0 1  1 3 *
  //   -15 วัน → 16 มี.ค.  0 1 16 3 *
  //   - 7 วัน → 24 มี.ค.  0 1 24 3 *
  //
  // ภ.ง.ด. 90 ออนไลน์  deadline: 8 เม.ย.
  //   -30 วัน → 9  มี.ค.  0 1  9 3 *
  //   -15 วัน → 24 มี.ค.  0 1 24 3 *  (ซ้ำกับบนได้ — ยิงครั้งเดียว API จัดการเอง)
  //   - 7 วัน → 1  เม.ย.  0 1  1 4 *
  //
  // ภ.ง.ด. 94 เอกสาร   deadline: 30 ก.ย.
  //   -30 วัน → 1  ก.ย.   0 1  1 9 *
  //   -15 วัน → 15 ก.ย.   0 1 15 9 *
  //   - 7 วัน → 23 ก.ย.   0 1 23 9 *
  //
  // ภ.ง.ด. 94 ออนไลน์  deadline: 8 ต.ค.
  //   -30 วัน → 8  ก.ย.   0 1  8 9 *
  //   -15 วัน → 23 ก.ย.   0 1 23 9 *  (ซ้ำกับบนได้)
  //   - 7 วัน → 1  ต.ค.   0 1  1 10 *
  // ============================================================

  const schedules: { label: string; expression: string }[] = [
    // ภ.ง.ด. 90 เอกสาร (31 มี.ค.)
    { label: 'ภ.ง.ด.90 เอกสาร -30วัน (1 มี.ค.)',  expression: '0 1 1 3 *'  },
    { label: 'ภ.ง.ด.90 ออนไลน์ -30วัน (9 มี.ค.)', expression: '0 1 9 3 *'  },
    { label: 'ภ.ง.ด.90 เอกสาร -15วัน (16 มี.ค.)', expression: '0 1 16 3 *' },
    { label: 'ภ.ง.ด.90 ทั้งคู่ (24 มี.ค.)',        expression: '0 1 24 3 *' },
    { label: 'ภ.ง.ด.90 ออนไลน์ -7วัน (1 เม.ย.)',  expression: '0 1 1 4 *'  },
    // ภ.ง.ด. 94 เอกสาร (30 ก.ย.)
    { label: 'ภ.ง.ด.94 เอกสาร -30วัน (1 ก.ย.)',   expression: '0 1 1 9 *'  },
    { label: 'ภ.ง.ด.94 ออนไลน์ -30วัน (8 ก.ย.)',  expression: '0 1 8 9 *'  },
    { label: 'ภ.ง.ด.94 เอกสาร -15วัน (15 ก.ย.)',  expression: '0 1 15 9 *' },
    { label: 'ภ.ง.ด.94 ทั้งคู่ (23 ก.ย.)',         expression: '0 1 23 9 *' },
    { label: 'ภ.ง.ด.94 ออนไลน์ -7วัน (1 ต.ค.)',   expression: '0 1 1 10 *' },
  ];

  for (const { label, expression } of schedules) {
    cron.schedule(expression, async () => {
      console.log(`[cron] ${label} — กำลังส่งแจ้งเตือน...`);
      try {
        const result = await runTaxReminder();
        console.log(`[cron] ${label} — เสร็จ: sent=${result.totalSent}`);
      } catch (err) {
        console.error(`[cron] ${label} — error:`, err);
      }
    }, {
      timezone: 'Asia/Bangkok',
    });
  }

  console.log(`[cron] ลงทะเบียน ${schedules.length} schedules เรียบร้อย`);
}
