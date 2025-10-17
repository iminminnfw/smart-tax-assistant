/**
 * Folder Service
 *
 * Handles all folder-related business logic
 */

import { prisma } from '@/lib/prisma';
import type {
  DocumentFolder,
  CreateFolderInput,
  UpdateFolderInput,
  ListFoldersParams,
} from '../types/document.types';

export class FolderService {
  /**
   * List folders for a user
   */
  async listFolders(params: ListFoldersParams): Promise<DocumentFolder[]> {
    const where: any = {
      userId: params.userId,
      isDeleted: params.includeDeleted ? undefined : false,
    };

    const folders = await prisma.documentFolder.findMany({
      where,
      include: {
        files: params.includeFiles
          ? { where: { isDeleted: false } }
          : false,
        children: true,
      },
      orderBy: { createdAt: 'desc' },
    });

    return folders as DocumentFolder[];
  }

  /**
   * Get a single folder by ID
   */
  async getFolderById(
    id: string,
    userId: string,
    includeFiles = false
  ): Promise<DocumentFolder | null> {
    const folder = await prisma.documentFolder.findFirst({
      where: {
        id,
        userId,
        isDeleted: false,
      },
      include: {
        files: includeFiles ? { where: { isDeleted: false } } : false,
        children: true,
      },
    });

    return folder as DocumentFolder | null;
  }

  /**
   * Create a new folder
   */
  async createFolder(input: CreateFolderInput): Promise<DocumentFolder> {
    const folder = await prisma.documentFolder.create({
      data: {
        userId: input.userId,
        name: input.name,
        color: input.color || '#3B82F6', // Default blue
        parentId: input.parentId || null,
      },
    });

    return folder as DocumentFolder;
  }

  /**
   * Update a folder
   */
  async updateFolder(
    id: string,
    userId: string,
    input: UpdateFolderInput
  ): Promise<DocumentFolder> {
    // Verify ownership
    const existing = await this.getFolderById(id, userId);
    if (!existing) {
      throw new Error('Folder not found');
    }

    const updated = await prisma.documentFolder.update({
      where: { id },
      data: input,
    });

    return updated as DocumentFolder;
  }

  /**
   * Soft delete a folder and its contents
   */
  async deleteFolder(id: string, userId: string): Promise<void> {
    // Verify ownership
    const existing = await this.getFolderById(id, userId);
    if (!existing) {
      throw new Error('Folder not found');
    }

    const now = new Date();

    // Soft delete all files in folder
    await prisma.documentFile.updateMany({
      where: {
        folderId: id,
        isDeleted: false,
      },
      data: {
        isDeleted: true,
        deletedAt: now,
      },
    });

    // Soft delete the folder itself
    await prisma.documentFolder.update({
      where: { id },
      data: {
        isDeleted: true,
        deletedAt: now,
      },
    });
  }

  /**
   * Permanently delete a folder
   */
  async permanentlyDeleteFolder(id: string, userId: string): Promise<void> {
    const existing = await prisma.documentFolder.findFirst({
      where: { id, userId },
    });

    if (!existing) {
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
  }

  /**
   * Restore a deleted folder
   */
  async restoreFolder(id: string, userId: string): Promise<DocumentFolder> {
    const folder = await prisma.documentFolder.findFirst({
      where: { id, userId, isDeleted: true },
    });

    if (!folder) {
      throw new Error('Deleted folder not found');
    }

    const restored = await prisma.documentFolder.update({
      where: { id },
      data: {
        isDeleted: false,
        deletedAt: null,
      },
    });

    return restored as DocumentFolder;
  }

  /**
   * Get folder count for user
   */
  async getFolderCount(userId: string): Promise<number> {
    return prisma.documentFolder.count({
      where: {
        userId,
        isDeleted: false,
      },
    });
  }

  /**
   * Check if folder name exists for user
   */
  async folderNameExists(userId: string, name: string, excludeId?: string): Promise<boolean> {
    const where: any = {
      userId,
      name,
      isDeleted: false,
    };

    if (excludeId) {
      where.id = { not: excludeId };
    }

    const count = await prisma.documentFolder.count({ where });
    return count > 0;
  }
}
