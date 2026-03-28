// src/app/api/cron/tax-reminder/route.ts
// HTTP endpoint สำหรับ manual trigger และทดสอบ
// Core logic อยู่ที่ src/lib/cron/tax-reminder.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { runTaxReminder } from '@/lib/cron/tax-reminder';

function isAuthorized(req: NextRequest): boolean {
  const secret = process.env.CRON_SECRET;
  if (!secret) return true; // dev mode
  const headerSecret = req.headers.get('x-cron-secret');
  const querySecret  = req.nextUrl.searchParams.get('secret');
  return headerSecret === secret || querySecret === secret;
}

export async function POST(req: NextRequest) {
  if (!isAuthorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const testMode = req.nextUrl.searchParams.get('test') === 'true';
  const result = await runTaxReminder({ testMode });
  return NextResponse.json(result);
}

// GET — สำหรับ test ง่ายๆ ใน browser
export async function GET(req: NextRequest) {
  return POST(req);
}
