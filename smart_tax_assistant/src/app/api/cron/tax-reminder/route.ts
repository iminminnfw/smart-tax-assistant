// src/app/api/cron/tax-reminder/route.ts
// ถูกเรียกโดย AWS EventBridge ทุกวัน 08:00 ICT (01:00 UTC)
// ตรวจสอบ deadline ที่ใกล้ถึงและส่งแจ้งเตือนผ่าน SMS / Email

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { sendEmailViaSES } from '@/lib/aws-ses';

// ============================================================
// Tax Deadlines (ปี 2568 / 2569)
// ============================================================
const TAX_DEADLINES = [
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
// Notification Levels (ส่งทุกวันตาม range)
// ============================================================
// range 30-23 → normal  (สีน้ำเงิน)
// range 22-14 → warning (สีเหลือง)
// range 13-1  → critical (สีแดง)

type NotifyLevel = 'normal' | 'warning' | 'critical';

function getNotifyLevel(daysLeft: number): NotifyLevel {
  if (daysLeft >= 23) return 'normal';
  if (daysLeft >= 14) return 'warning';
  return 'critical';
}

function buildEmailText(deadlineTitle: string, daysLeft: number): string {
  const level = getNotifyLevel(daysLeft);

  if (level === 'normal') {
    return `[SmartTax] เหลือเวลาอีก ${daysLeft} วันสำหรับ Deadline ${deadlineTitle} รีบเตรียมเอกสารและสรุปยอดลดหย่อน (RMF, ThaiESG) ให้พร้อมก่อนหมดเวลาได้เลยครับ`;
  }
  if (level === 'warning') {
    return `[SmartTax] ⚠️ เหลืออีกเพียง ${daysLeft} วันสำหรับ Deadline ${deadlineTitle}! ยังไม่ได้ยื่นอยู่ใช่ไหม? เข้า Smart Tax Assistant ดูสรุปแผนภาษีแล้วรีบยื่นได้เลยครับ`;
  }
  // critical 1-13 วัน
  const dayWord = daysLeft === 1 ? 'พรุ่งนี้คือ' : `อีก ${daysLeft} วันคือ`;
  return `[SmartTax] 🚨 ด่วนมาก! ${dayWord} Deadline สุดท้ายของ ${deadlineTitle} ถ้าไม่ยื่นวันนี้จะเสียสิทธิ์ขอคืนภาษีและโดนค่าปรับทันที!`;
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
// Security: ตรวจ secret header จาก EventBridge
// ============================================================
function isAuthorized(req: NextRequest): boolean {
  const secret = process.env.CRON_SECRET;
  if (!secret) return true; // dev mode — ไม่บังคับ
  // รองรับทั้ง header และ query param (สำหรับทดสอบใน browser)
  const headerSecret = req.headers.get('x-cron-secret');
  const querySecret  = req.nextUrl.searchParams.get('secret');
  return headerSecret === secret || querySecret === secret;
}

// ============================================================
// POST /api/cron/tax-reminder
// ============================================================
export async function POST(req: NextRequest) {
  if (!isAuthorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // หา deadline ที่อยู่ใน range 1-30 วัน (ส่งทุกวัน)
  const triggeredDeadlines = TAX_DEADLINES.filter((d) => {
    const daysLeft = Math.round((d.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return daysLeft >= 1 && daysLeft <= 30;
  });

  if (triggeredDeadlines.length === 0) {
    return NextResponse.json({ ok: true, message: 'No notifications needed today', sent: 0 });
  }

  // ดึง users ที่เปิดการแจ้งเตือน
  const users = await prisma.user.findMany({
    where: { notifyEnabled: true },
    select: {
      id: true,
      name: true,
      email: true,
      notifyEmail: true,
    },
  });

  let totalSent = 0;
  const errors: string[] = [];

  for (const deadline of triggeredDeadlines) {
    const daysLeft = Math.round((deadline.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    const emailText = buildEmailText(deadline.title, daysLeft);

    for (const user of users) {
      const userName = user.name || 'คุณ';

      // ส่ง Email
      if (user.notifyEmail && user.email) {
        const subject = `[SmartTax] ⏰ เหลือ ${daysLeft} วัน — ${deadline.title}`;
        const result = await sendEmailViaSES({
          to: user.email,
          subject,
          body: emailText,
          html: buildEmailHTML(deadline.title, daysLeft, userName),
        });
        if (result.success) totalSent++;
        else errors.push(`Email to ${user.email}: ${result.error}`);
      }
    }
  }

  console.log(`[tax-reminder] sent=${totalSent}, errors=${errors.length}`);

  return NextResponse.json({
    ok: true,
    date: today.toISOString().slice(0, 10),
    deadlinesTriggered: triggeredDeadlines.map((d) => d.title),
    usersNotified: users.length,
    totalSent,
    errors: errors.length > 0 ? errors : undefined,
  });
}

// GET — สำหรับ test ง่ายๆ ใน browser
export async function GET(req: NextRequest) {
  return POST(req);
}
