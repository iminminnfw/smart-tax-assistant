// src/lib/cron/tax-reminder.ts
// Core logic สำหรับส่งแจ้งเตือน deadline ภาษี
// ถูกเรียกจาก:
//   1. src/instrumentation.ts  — node-cron (local scheduler)
//   2. src/app/api/cron/tax-reminder/route.ts — HTTP endpoint (manual trigger / test)

import prisma from '@/lib/prisma';
import { sendEmailViaSES } from '@/lib/aws-ses';

// ============================================================
// Tax Deadlines (ปี 2568 / 2569) — ซิงค์กับ tax-calendar/page.tsx
// ============================================================
export const TAX_DEADLINES = [
  {
    id: 'pnd94-2025-paper',
    date: new Date('2025-09-30'),
    title: 'ภ.ง.ด. 94 กลางปี (เอกสาร)',
    form: 'ภ.ง.ด. 94',
    filingMethod: 'paper' as const,
  },
  {
    id: 'pnd94-2025-efiling',
    date: new Date('2025-10-08'),
    title: 'ภ.ง.ด. 94 กลางปี (ออนไลน์)',
    form: 'ภ.ง.ด. 94',
    filingMethod: 'efiling' as const,
  },
  {
    id: 'pnd90-2025-paper',
    date: new Date('2026-03-31'),
    title: 'ภ.ง.ด. 90 ประจำปี (เอกสาร)',
    form: 'ภ.ง.ด. 90',
    filingMethod: 'paper' as const,
  },
  {
    id: 'pnd90-2025-efiling',
    date: new Date('2026-04-08'),
    title: 'ภ.ง.ด. 90 ประจำปี (ออนไลน์)',
    form: 'ภ.ง.ด. 90',
    filingMethod: 'efiling' as const,
  },
];

// ============================================================
// Notification Levels
// ============================================================
const NOTIFY_DAYS = [30, 15, 7] as const;

type NotifyLevel = 'normal' | 'warning' | 'critical';

function getNotifyLevel(daysLeft: number): NotifyLevel {
  if (daysLeft === 30) return 'normal';
  if (daysLeft === 15) return 'warning';
  return 'critical';
}

function buildEmailText(deadlineTitle: string, daysLeft: number): string {
  const level = getNotifyLevel(daysLeft);
  if (level === 'normal') {
    return `[SmartTax] เหลือเวลาอีก 30 วันสำหรับ Deadline ${deadlineTitle} รีบเตรียมเอกสารและสรุปยอดลดหย่อน (RMF, ThaiESG) ให้พร้อมก่อนหมดเวลาได้เลยครับ`;
  }
  if (level === 'warning') {
    return `[SmartTax] ⚠️ เหลืออีกเพียง 15 วันสำหรับ Deadline ${deadlineTitle}! ยังไม่ได้ยื่นอยู่ใช่ไหม? เข้า Smart Tax Assistant ดูสรุปแผนภาษีแล้วรีบยื่นได้เลยครับ`;
  }
  return `[SmartTax] 🚨 ด่วนมาก! เหลืออีกแค่ 7 วันคือ Deadline สุดท้ายของ ${deadlineTitle} ถ้าไม่ยื่นจะเสียสิทธิ์ขอคืนภาษีและโดนค่าปรับทันที!`;
}

function buildEmailHTML(deadlineTitle: string, daysLeft: number, userName: string): string {
  const level = getNotifyLevel(daysLeft);
  const colorMap: Record<NotifyLevel, string> = {
    normal:   '#3b82f6',
    warning:  '#f59e0b',
    critical: '#dc2626',
  };
  const color = colorMap[level];
  const bodyText = buildEmailText(deadlineTitle, daysLeft).replace('[SmartTax] ', '');

  return `
<!DOCTYPE html>
<html lang="th">
<head><meta charset="UTF-8"/></head>
<body style="font-family:sans-serif;background:#f9fafb;padding:24px;">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:${color};padding:24px;text-align:center;">
      <h1 style="color:#fff;margin:0;font-size:20px;">Smart Tax Assistant</h1>
      <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;">แจ้งเตือนกำหนดยื่นภาษี</p>
    </div>
    <div style="padding:24px;">
      <p style="color:#374151;">สวัสดีคุณ <strong>${userName}</strong>,</p>
      <p style="color:#374151;line-height:1.6;">${bodyText}</p>
      <div style="background:#f3f4f6;border-radius:8px;padding:16px;margin:16px 0;">
        <p style="margin:0;color:#6b7280;font-size:14px;">📋 <strong>${deadlineTitle}</strong></p>
        <p style="margin:4px 0 0;color:#6b7280;font-size:14px;">⏰ เหลือเวลา <strong style="color:${color};">${daysLeft} วัน</strong></p>
      </div>
      <a href="${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/tax-calendar"
         style="display:inline-block;background:${color};color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
        ดูปฏิทินภาษี →
      </a>
      <div style="margin-top:16px;padding:12px 16px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;">
        <p style="margin:0;color:#166534;font-size:13px;">
          ✅ ยื่นภาษีเสร็จแล้ว?
          <a href="${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/tax-calendar"
             style="color:#166534;font-weight:bold;text-decoration:underline;">
            กดที่นี่เพื่อติ๊ก "ยื่นแล้ว"
          </a>
          เพื่อหยุดรับการแจ้งเตือน deadline นี้
        </p>
      </div>
    </div>
    <div style="padding:16px 24px;border-top:1px solid #e5e7eb;">
      <p style="color:#9ca3af;font-size:12px;margin:0;">
        คุณได้รับอีเมลนี้เพราะเปิดการแจ้งเตือนใน Smart Tax Assistant<br/>
        ปิดการแจ้งเตือนได้ที่ <a href="${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/profile-settings">ตั้งค่าบัญชี</a>
      </p>
    </div>
  </div>
</body>
</html>`;
}

// ============================================================
// Main function — เรียกได้จากทั้ง instrumentation.ts และ API route
// testMode=true → ข้าม daysLeft check, ส่งทุก deadline ให้ทุก user ทันที
// ============================================================
export async function runTaxReminder(options?: { testMode?: boolean }): Promise<{
  ok: boolean;
  date: string;
  deadlinesTriggered: string[];
  usersChecked: number;
  totalSent: number;
  testMode?: boolean;
  errors?: string[];
}> {
  const testMode = options?.testMode ?? false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // testMode: ส่งทุก deadline / ปกติ: เฉพาะที่ตรง 30/15/7 วัน
  const triggeredDeadlines = testMode
    ? TAX_DEADLINES
    : TAX_DEADLINES.filter((d) => {
        const daysLeft = Math.round(
          (d.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
        );
        return (NOTIFY_DAYS as readonly number[]).includes(daysLeft);
      });

  if (triggeredDeadlines.length === 0) {
    console.log('[tax-reminder] No notifications needed today');
    return {
      ok: true,
      date: today.toISOString().slice(0, 10),
      deadlinesTriggered: [],
      usersChecked: 0,
      totalSent: 0,
    };
  }

  // ดึง users ที่เปิดการแจ้งเตือน
  const users = await prisma.user.findMany({
    where: { notifyEnabled: true },
    select: {
      id: true,
      name: true,
      email: true,
      notifyEmail: true,
      filedDeadlines: true,
    },
  });

  let totalSent = 0;
  const errors: string[] = [];

  for (const deadline of triggeredDeadlines) {
    // testMode: แสดง daysLeft จริง (อาจติดลบ/เกิน) แต่ใช้ level = 'critical' เพื่อ demo
    const daysLeft = testMode
      ? 7
      : Math.round((deadline.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    const emailText = buildEmailText(deadline.title, daysLeft);

    for (const user of users) {
      // testMode: ส่งทุก user แม้จะติ๊กแล้ว / ปกติ: ข้ามถ้าติ๊กแล้ว
      if (!testMode && user.filedDeadlines.includes(deadline.id)) continue;

      if (user.notifyEmail && user.email) {
        const prefix = testMode ? '[TEST] ' : '';
        const subject = `${prefix}[SmartTax] ⏰ เหลือ ${daysLeft} วัน — ${deadline.title}`;
        const result = await sendEmailViaSES({
          to: user.email,
          subject,
          body: emailText,
          html: buildEmailHTML(deadline.title, daysLeft, user.name || 'คุณ'),
        });
        if (result.success) totalSent++;
        else errors.push(`Email to ${user.email}: ${result.error}`);
      }
    }
  }

  console.log(`[tax-reminder] testMode=${testMode} date=${today.toISOString().slice(0, 10)} sent=${totalSent} errors=${errors.length}`);

  return {
    ok: true,
    date: today.toISOString().slice(0, 10),
    deadlinesTriggered: triggeredDeadlines.map((d) => d.title),
    usersChecked: users.length,
    totalSent,
    ...(testMode && { testMode: true }),
    ...(errors.length > 0 && { errors }),
  };
}
