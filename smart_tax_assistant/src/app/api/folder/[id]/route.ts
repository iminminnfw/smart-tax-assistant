// src/app/api/folder/[id]/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

type ParamsP = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: ParamsP) {
  const { id } = await params;
  const folder = await prisma.documentFolder.findUnique({
    where: { id },
    include: { children: true, files: true },
  });
  if (!folder) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(folder);
}

export async function PATCH(req: Request, { params }: ParamsP) {
  const { id } = await params;
  
  // ⭐ เพิ่ม authentication check
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  const body = await req.json();
  const updated = await prisma.documentFolder.update({
    where: { 
      id,
      user: { email: session.user.email } // ⭐ ตรวจสอบว่าเป็นเจ้าของ
    },
    data: { name: body.name, color: body.color },
  });
  return NextResponse.json(updated);
}

// Soft delete folder (move to trash)
export async function DELETE(_req: Request, { params }: ParamsP) {
  const { id } = await params;

  // ตรวจสอบ authentication
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    // ตรวจสอบว่าโฟลเดอร์เป็นของผู้ใช้คนนี้หรือไม่
    const folder = await prisma.documentFolder.findFirst({
      where: {
        id,
        user: { email: session.user.email },
        isDeleted: false
      },
      include: { files: true },
    });

    if (!folder) {
      return NextResponse.json({ error: 'Folder not found' }, { status: 404 });
    }

    const now = new Date();

    // Soft delete ไฟล์ทั้งหมดในโฟลเดอร์
    if (folder.files.length > 0) {
      await prisma.documentFile.updateMany({
        where: { folderId: id, isDeleted: false },
        data: { isDeleted: true, deletedAt: now },
      });
    }

    // Soft delete โฟลเดอร์
    await prisma.documentFolder.update({
      where: { id },
      data: { isDeleted: true, deletedAt: now },
    });

    return NextResponse.json({
      ok: true,
      message: 'Folder moved to trash',
      deletedFiles: folder.files.length
    });

  } catch (error) {
    console.error('Error deleting folder:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}