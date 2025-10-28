/**
 * Trash Service
 *
 * Handles trash/recovery operations for documents and folders
 */

import { prisma } from '@/lib/prisma';
import type { TrashItem } from '../types/document.types';

export class TrashService {
  /**
   * Get all trash items for a user
   */
  async getTrashItems(userId: string): Promise<{
    folders: any[];
    files: any[];
  }> {
    const [folders, files] = await Promise.all([
      prisma.documentFolder.findMany({
        where: {
          userId,
          isDeleted: true,
        },
        orderBy: { deletedAt: 'desc' },
      }),
      prisma.documentFile.findMany({
        where: {
          userId,
          isDeleted: true,
        },
        orderBy: { deletedAt: 'desc' },
      }),
    ]);

    return { folders, files };
  }

  /**
   * Restore an item from trash
   */
  async restoreItem(
    id: string,
    type: 'file' | 'folder',
    userId: string
  ): Promise<void> {
    if (type === 'folder') {
      const folder = await prisma.documentFolder.findFirst({
        where: { id, userId, isDeleted: true },
      });

      if (!folder) {
        throw new Error('Folder not found in trash');
      }

      await prisma.documentFolder.update({
        where: { id },
        data: {
          isDeleted: false,
          deletedAt: null,
        },
      });
    } else {
      const file = await prisma.documentFile.findFirst({
        where: { id, userId, isDeleted: true },
      });

      if (!file) {
        throw new Error('File not found in trash');
      }

      await prisma.documentFile.update({
        where: { id },
        data: {
          isDeleted: false,
          deletedAt: null,
        },
      });
    }
  }

  /**
   * Permanently delete an item
   */
  async permanentlyDeleteItem(
    id: string,
    type: 'file' | 'folder',
    userId: string
  ): Promise<void> {
    if (type === 'folder') {
      const folder = await prisma.documentFolder.findFirst({
        where: { id, userId },
      });

      if (!folder) {
        throw new Error('Folder not found');
      }

      // Delete all files in folder first
      await prisma.documentFile.deleteMany({
        where: { folderId: id },
      });

      // Delete the folder
      await prisma.documentFolder.delete({
        where: { id },
      });
    } else {
      const file = await prisma.documentFile.findFirst({
        where: { id, userId },
      });

      if (!file) {
        throw new Error('File not found');
      }

      await prisma.documentFile.delete({
        where: { id },
      });
    }
  }

  /**
   * Empty entire trash for a user
   */
  async emptyTrash(userId: string): Promise<{
    deletedFiles: number;
    deletedFolders: number;
  }> {
    // Get items older than 7 days
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    // Delete old files
    const deletedFiles = await prisma.documentFile.deleteMany({
      where: {
        userId,
        isDeleted: true,
        deletedAt: {
          lt: sevenDaysAgo,
        },
      },
    });

    // Delete old folders
    const deletedFolders = await prisma.documentFolder.deleteMany({
      where: {
        userId,
        isDeleted: true,
        deletedAt: {
          lt: sevenDaysAgo,
        },
      },
    });

    return {
      deletedFiles: deletedFiles.count,
      deletedFolders: deletedFolders.count,
    };
  }

  /**
   * Clean up trash items older than specified days
   * Used by cron job
   */
  async cleanupOldTrash(days: number = 7): Promise<{
    deletedFiles: number;
    deletedFolders: number;
  }> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    const deletedFiles = await prisma.documentFile.deleteMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lt: cutoffDate,
        },
      },
    });

    const deletedFolders = await prisma.documentFolder.deleteMany({
      where: {
        isDeleted: true,
        deletedAt: {
          lt: cutoffDate,
        },
      },
    });

    return {
      deletedFiles: deletedFiles.count,
      deletedFolders: deletedFolders.count,
    };
  }

  /**
   * Get trash item count
   */
  async getTrashCount(userId: string): Promise<number> {
    const [folderCount, fileCount] = await Promise.all([
      prisma.documentFolder.count({
        where: { userId, isDeleted: true },
      }),
      prisma.documentFile.count({
        where: { userId, isDeleted: true },
      }),
    ]);

    return folderCount + fileCount;
  }

  /**
   * Check if trash is empty
   */
  async isTrashEmpty(userId: string): Promise<boolean> {
    const count = await this.getTrashCount(userId);
    return count === 0;
  }
}
