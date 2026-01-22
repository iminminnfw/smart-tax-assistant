// src/app/api/trash/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';
import { deleteFromS3, extractS3Key, isS3Url } from '@/lib/s3';

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

    console.log(`[7-Day Cleanup] Starting cleanup for items older than ${sevenDaysAgo.toISOString()}`);

    // Query expired files before deleting
    const expiredFiles = await prisma.documentFile.findMany({
      where: {
        userId: user.id,
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[7-Day Cleanup] Found ${expiredFiles.length} expired files to delete`);

    // Delete S3 files first
    let s3DeletedCount = 0;
    let s3FailedCount = 0;

    for (const file of expiredFiles) {
      if (file.fileUrl && isS3Url(file.fileUrl)) {
        try {
          const key = extractS3Key(file.fileUrl);
          if (key) {
            await deleteFromS3(key);
            console.log(`[S3 Delete] Deleted: ${key}`);
            s3DeletedCount++;
          }
        } catch (error: any) {
          console.error(`[S3 Delete] Failed to delete ${file.fileUrl}:`, error.message);
          s3FailedCount++;
          // Continue anyway - don't stop the operation
        }
      }
    }

    // Delete files from database
    const deletedFiles = await prisma.documentFile.deleteMany({
      where: {
        userId: user.id,
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[7-Day Cleanup] Deleted ${deletedFiles.count} files from database. S3: ${s3DeletedCount} deleted, ${s3FailedCount} failed`);

    // Query expired folders (with their files)
    const expiredFolders = await prisma.documentFolder.findMany({
      where: {
        userId: user.id,
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
      include: { files: true },
    });

    console.log(`[7-Day Cleanup] Found ${expiredFolders.length} expired folders to delete`);

    // Delete S3 files from folders
    let folderS3DeletedCount = 0;
    let folderS3FailedCount = 0;

    for (const folder of expiredFolders) {
      for (const file of folder.files) {
        if (file.fileUrl && isS3Url(file.fileUrl)) {
          try {
            const key = extractS3Key(file.fileUrl);
            if (key) {
              await deleteFromS3(key);
              console.log(`[S3 Delete] Deleted from folder ${folder.name}: ${key}`);
              folderS3DeletedCount++;
            }
          } catch (error: any) {
            console.error(`[S3 Delete] Failed to delete ${file.fileUrl}:`, error.message);
            folderS3FailedCount++;
            // Continue anyway
          }
        }
      }
    }

    // Delete folders from database (will cascade delete files)
    const deletedFolders = await prisma.documentFolder.deleteMany({
      where: {
        userId: user.id,
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[7-Day Cleanup] Deleted ${deletedFolders.count} folders from database. S3: ${folderS3DeletedCount} deleted, ${folderS3FailedCount} failed`);

    const totalS3Deleted = s3DeletedCount + folderS3DeletedCount;
    const totalS3Failed = s3FailedCount + folderS3FailedCount;

    console.log(`[7-Day Cleanup] Complete! Total DB: ${deletedFiles.count} files + ${deletedFolders.count} folders. Total S3: ${totalS3Deleted} deleted, ${totalS3Failed} failed`);

    return NextResponse.json({
      ok: true,
      message: 'Expired items permanently deleted',
      deletedFiles: deletedFiles.count,
      deletedFolders: deletedFolders.count,
      s3DeletedCount: totalS3Deleted,
      s3FailedCount: totalS3Failed,
    });
  } catch (error) {
    console.error('Error cleaning trash:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
