// src/app/api/trash/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

// GET /api/trash - List all items in trash
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    // Get deleted folders and files
    const [folders, files] = await Promise.all([
      prisma.documentFolder.findMany({
        where: {
          userId: user.id,
          isDeleted: true,
        },
        orderBy: { deletedAt: 'desc' },
      }),
      prisma.documentFile.findMany({
        where: {
          userId: user.id,
          isDeleted: true,
        },
        include: { folder: true },
        orderBy: { deletedAt: 'desc' },
      }),
    ]);

    return NextResponse.json({ folders, files });
  } catch (error) {
    console.error('Error fetching trash:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

// DELETE /api/trash - Permanently delete items older than 7 days
export async function DELETE() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    // Permanently delete files older than 7 days
    const deletedFiles = await prisma.documentFile.deleteMany({
      where: {
        userId: user.id,
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    // Permanently delete folders older than 7 days
    const deletedFolders = await prisma.documentFolder.deleteMany({
      where: {
        userId: user.id,
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    return NextResponse.json({
      ok: true,
      message: 'Expired items permanently deleted',
      deletedFiles: deletedFiles.count,
      deletedFolders: deletedFolders.count,
    });
  } catch (error) {
    console.error('Error cleaning trash:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
