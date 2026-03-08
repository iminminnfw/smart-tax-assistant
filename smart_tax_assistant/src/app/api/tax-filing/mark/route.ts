// src/app/api/tax-filing/mark/route.ts
// POST → ติ๊กว่ายื่นแล้ว
// DELETE → ยกเลิกการติ๊ก

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

const VALID_DEADLINE_IDS = [
  'pnd94-2025-paper',
  'pnd94-2025-efiling',
  'pnd90-2025-paper',
  'pnd90-2025-efiling',
];

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { deadlineId } = await req.json().catch(() => ({}));
  if (!VALID_DEADLINE_IDS.includes(deadlineId)) {
    return NextResponse.json({ error: 'Invalid deadlineId' }, { status: 400 });
  }

  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: { id: true, filedDeadlines: true },
  });
  if (!user) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  if (user.filedDeadlines.includes(deadlineId)) {
    return NextResponse.json({ ok: true, filedDeadlines: user.filedDeadlines });
  }

  const updated = await prisma.user.update({
    where: { id: user.id },
    data: { filedDeadlines: { push: deadlineId } },
    select: { filedDeadlines: true },
  });

  return NextResponse.json({ ok: true, filedDeadlines: updated.filedDeadlines });
}

export async function DELETE(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { deadlineId } = await req.json().catch(() => ({}));
  if (!VALID_DEADLINE_IDS.includes(deadlineId)) {
    return NextResponse.json({ error: 'Invalid deadlineId' }, { status: 400 });
  }

  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: { id: true, filedDeadlines: true },
  });
  if (!user) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  const updated = await prisma.user.update({
    where: { id: user.id },
    data: { filedDeadlines: user.filedDeadlines.filter((d) => d !== deadlineId) },
    select: { filedDeadlines: true },
  });

  return NextResponse.json({ ok: true, filedDeadlines: updated.filedDeadlines });
}

// GET → ดึง list deadline ที่ยื่นแล้ว
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { email: session.user.email },
    select: { filedDeadlines: true },
  });

  return NextResponse.json({ filedDeadlines: user?.filedDeadlines ?? [] });
}
