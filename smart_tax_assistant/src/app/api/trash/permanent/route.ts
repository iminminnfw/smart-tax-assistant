// src/app/api/trash/permanent/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';
import { deleteFromS3, extractS3Key, isS3Url } from '@/lib/s3';

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

      console.log(`[Permanent Delete] Deleting folder: ${folder.name} with ${folder.files.length} files`);

      // ✅ FIRST: Delete S3 files for each file in folder
      let s3DeletedCount = 0;
      let s3FailedCount = 0;

      for (const file of folder.files) {
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

      // ✅ THEN: Delete all files from database
      if (folder.files.length > 0) {
        await prisma.documentFile.deleteMany({
          where: { folderId: id },
        });
      }

      // ✅ FINALLY: Delete folder from database
      await prisma.documentFolder.delete({
        where: { id },
      });

      console.log(`[Permanent Delete] Folder deleted. S3: ${s3DeletedCount} deleted, ${s3FailedCount} failed. DB: ${folder.files.length} files deleted`);

      return NextResponse.json({
        ok: true,
        message: 'Folder permanently deleted',
        deletedFiles: folder.files.length,
        s3DeletedCount,
        s3FailedCount,
      });

    } else if (type === 'file') {
      // Verify file is in trash and belongs to user
      const file = await prisma.documentFile.findFirst({
        where: { id, userId: user.id, isDeleted: true },
      });

      if (!file) {
        return NextResponse.json({ error: 'File not found in trash' }, { status: 404 });
      }

      console.log(`[Permanent Delete] Deleting file: ${file.name}`);

      // ✅ FIRST: Delete from S3
      let s3Deleted = false;
      if (file.fileUrl && isS3Url(file.fileUrl)) {
        try {
          const key = extractS3Key(file.fileUrl);
          if (key) {
            await deleteFromS3(key);
            console.log(`[S3 Delete] Deleted: ${key}`);
            s3Deleted = true;
          }
        } catch (error: any) {
          console.error(`[S3 Delete] Failed to delete ${file.fileUrl}:`, error.message);
          // Continue anyway - still delete from database
        }
      }

      // ✅ THEN: Delete from database
      await prisma.documentFile.delete({
        where: { id },
      });

      console.log(`[Permanent Delete] File deleted. S3: ${s3Deleted ? 'deleted' : 'skipped/failed'}`);

      return NextResponse.json({
        ok: true,
        message: 'File permanently deleted',
        s3Deleted,
      });

    } else {
      return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
    }

  } catch (error) {
    console.error('Error permanently deleting item:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
