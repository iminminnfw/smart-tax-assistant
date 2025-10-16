// src/app/api/document/[id]/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

type ParamsType = { params: Promise<{ id: string }> };

export async function GET(req: Request, { params }: ParamsType) {
  const { id } = await params;
  
  const file = await prisma.documentFile.findUnique({
    where: { id },
    include: { folder: true },
  });

  if (!file) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(file);
}

export async function PATCH(req: Request, { params }: ParamsType) {
  const { id } = await params;
  const body = await req.json();

  const file = await prisma.documentFile.update({
    where: { id },
    data: {
      name: body.name,
      content: body.content,
      folderId: body.folderId,
      tags: body.tags,
    },
  });

  return NextResponse.json(file);
}

export async function DELETE(req: Request, { params }: ParamsType) {
  const { id } = await params;
  
  // ตรวจสอบสิทธิ์ของผู้ใช้
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  let userId = (session.user as any).id as string | undefined;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }
  
  if (!userId) {
    return NextResponse.json({ error: 'User not found' }, { status: 401 });
  }

  try {
    // ตรวจสอบว่าไฟล์เป็นของผู้ใช้
    const file = await prisma.documentFile.findFirst({
      where: { id, userId },
    });

    if (!file) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    // ลบไฟล์
    await prisma.documentFile.delete({ where: { id } });
    
    return NextResponse.json({ ok: true, message: 'File deleted successfully' });
  } catch (error) {
    console.error('Error deleting file:', error);
    return NextResponse.json({ error: 'Failed to delete file' }, { status: 500 });
  }
}