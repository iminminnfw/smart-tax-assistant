// src/app/api/trash/restore/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

// POST /api/trash/restore - Restore item from trash
export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const { id, type } = body; // type: 'folder' | 'file'

    if (!id || !type) {
      return NextResponse.json({ error: 'Missing id or type' }, { status: 400 });
    }

    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    if (type === 'folder') {
      // Restore folder
      const folder = await prisma.documentFolder.findFirst({
        where: { id, userId: user.id, isDeleted: true },
        include: { files: true },
      });

      if (!folder) {
        return NextResponse.json({ error: 'Folder not found in trash' }, { status: 404 });
      }

      // Restore folder and all its files
      await prisma.documentFolder.update({
        where: { id },
        data: { isDeleted: false, deletedAt: null },
      });

      if (folder.files.length > 0) {
        await prisma.documentFile.updateMany({
          where: { folderId: id, isDeleted: true },
          data: { isDeleted: false, deletedAt: null },
        });
      }

      return NextResponse.json({
        ok: true,
        message: 'Folder restored successfully',
        restoredFiles: folder.files.length,
      });

    } else if (type === 'file') {
      // Restore file
      const file = await prisma.documentFile.findFirst({
        where: { id, userId: user.id, isDeleted: true },
      });

      if (!file) {
        return NextResponse.json({ error: 'File not found in trash' }, { status: 404 });
      }

      await prisma.documentFile.update({
        where: { id },
        data: { isDeleted: false, deletedAt: null },
      });

      return NextResponse.json({
        ok: true,
        message: 'File restored successfully',
      });

    } else {
      return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
    }

  } catch (error) {
    console.error('Error restoring item:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
