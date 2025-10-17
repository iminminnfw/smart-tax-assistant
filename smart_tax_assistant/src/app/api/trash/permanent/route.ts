// src/app/api/trash/permanent/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

// DELETE /api/trash/permanent - Permanently delete specific item
export async function DELETE(req: Request) {
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
      // Verify folder is in trash and belongs to user
      const folder = await prisma.documentFolder.findFirst({
        where: { id, userId: user.id, isDeleted: true },
        include: { files: true },
      });

      if (!folder) {
        return NextResponse.json({ error: 'Folder not found in trash' }, { status: 404 });
      }

      // Delete all files in folder first
      if (folder.files.length > 0) {
        await prisma.documentFile.deleteMany({
          where: { folderId: id },
        });
      }

      // Permanently delete folder
      await prisma.documentFolder.delete({
        where: { id },
      });

      return NextResponse.json({
        ok: true,
        message: 'Folder permanently deleted',
        deletedFiles: folder.files.length,
      });

    } else if (type === 'file') {
      // Verify file is in trash and belongs to user
      const file = await prisma.documentFile.findFirst({
        where: { id, userId: user.id, isDeleted: true },
      });

      if (!file) {
        return NextResponse.json({ error: 'File not found in trash' }, { status: 404 });
      }

      // Permanently delete file
      await prisma.documentFile.delete({
        where: { id },
      });

      return NextResponse.json({
        ok: true,
        message: 'File permanently deleted',
      });

    } else {
      return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
    }

  } catch (error) {
    console.error('Error permanently deleting item:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
