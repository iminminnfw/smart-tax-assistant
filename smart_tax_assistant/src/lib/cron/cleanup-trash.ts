// src/lib/cron/cleanup-trash.ts

import prisma from '@/lib/prisma';

export async function cleanupExpiredTrash() {
  try {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    console.log(`[Cleanup Cron] Starting cleanup for items deleted before ${sevenDaysAgo.toISOString()}`);

    // Permanently delete files older than 7 days
    const deletedFiles = await prisma.documentFile.deleteMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    // Permanently delete folders older than 7 days
    const deletedFolders = await prisma.documentFolder.deleteMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lte: sevenDaysAgo,
        },
      },
    });

    console.log(`[Cleanup Cron] Cleanup completed: ${deletedFiles.count} files and ${deletedFolders.count} folders permanently deleted`);

    return {
      success: true,
      deletedFiles: deletedFiles.count,
      deletedFolders: deletedFolders.count,
    };
  } catch (error) {
    console.error('[Cleanup Cron] Error during cleanup:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
