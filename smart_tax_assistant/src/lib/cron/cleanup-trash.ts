// src/lib/cron/cleanup-trash.ts

import prisma from '@/lib/prisma';
import { deleteFromS3, extractS3Key, isS3Url } from '@/lib/s3';

export async function cleanupExpiredTrash() {
  try {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    console.log(`[Cleanup Cron] Starting cleanup for items deleted before ${sevenDaysAgo.toISOString()}`);

    // ✅ STEP 1: Query expired files BEFORE deleting
    const expiredFiles = await prisma.documentFile.findMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[Cleanup Cron] Found ${expiredFiles.length} expired files to delete`);

    // ✅ STEP 2: Delete S3 files first
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

    // ✅ STEP 3: Delete files from database
    const deletedFiles = await prisma.documentFile.deleteMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[Cleanup Cron] Deleted ${deletedFiles.count} files from database. S3: ${s3DeletedCount} deleted, ${s3FailedCount} failed`);

    // ✅ STEP 4: Query expired folders (with their files)
    const expiredFolders = await prisma.documentFolder.findMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
      include: { files: true },
    });

    console.log(`[Cleanup Cron] Found ${expiredFolders.length} expired folders to delete`);

    // ✅ STEP 5: Delete S3 files from folders
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

    // ✅ STEP 6: Delete folders from database (will cascade delete files)
    const deletedFolders = await prisma.documentFolder.deleteMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[Cleanup Cron] Deleted ${deletedFolders.count} folders from database. S3: ${folderS3DeletedCount} deleted, ${folderS3FailedCount} failed`);

    const totalS3Deleted = s3DeletedCount + folderS3DeletedCount;
    const totalS3Failed = s3FailedCount + folderS3FailedCount;

    console.log(`[Cleanup Cron] Cleanup completed: ${deletedFiles.count} files + ${deletedFolders.count} folders. S3: ${totalS3Deleted} deleted, ${totalS3Failed} failed`);

    return {
      success: true,
      deletedFiles: deletedFiles.count,
      deletedFolders: deletedFolders.count,
      s3DeletedCount: totalS3Deleted,
      s3FailedCount: totalS3Failed,
    };
  } catch (error) {
    console.error('[Cleanup Cron] Error during cleanup:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
