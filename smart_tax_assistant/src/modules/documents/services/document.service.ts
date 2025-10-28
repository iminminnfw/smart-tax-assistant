/**
 * Document Service
 *
 * Handles all document-related business logic
 */

import { prisma } from '@/lib/prisma';
import type {
  Document,
  CreateDocumentInput,
  UpdateDocumentInput,
  ListDocumentsParams,
} from '../types/document.types';

export class DocumentService {
  /**
   * List documents for a user
   */
  async listDocuments(params: ListDocumentsParams): Promise<Document[]> {
    const where: any = {
      userId: params.userId,
      isDeleted: params.includeDeleted ? undefined : false,
    };

    if (params.folderId !== undefined) {
      where.folderId = params.folderId;
    }

    const documents = await prisma.documentFile.findMany({
      where,
      orderBy: { createdAt: 'desc' },
    });

    return documents as Document[];
  }

  /**
   * Get a single document by ID
   */
  async getDocumentById(id: string, userId: string): Promise<Document | null> {
    const document = await prisma.documentFile.findFirst({
      where: {
        id,
        userId,
        isDeleted: false,
      },
    });

    return document as Document | null;
  }

  /**
   * Create a new document
   */
  async createDocument(input: CreateDocumentInput): Promise<Document> {
    const document = await prisma.documentFile.create({
      data: {
        userId: input.userId,
        name: input.name,
        type: input.type,
        size: input.size,
        url: input.url,
        folderId: input.folderId || null,
      },
    });

    return document as Document;
  }

  /**
   * Update a document
   */
  async updateDocument(
    id: string,
    userId: string,
    input: UpdateDocumentInput
  ): Promise<Document> {
    // Verify ownership
    const existing = await this.getDocumentById(id, userId);
    if (!existing) {
      throw new Error('Document not found');
    }

    const updated = await prisma.documentFile.update({
      where: { id },
      data: input,
    });

    return updated as Document;
  }

  /**
   * Soft delete a document
   */
  async deleteDocument(id: string, userId: string): Promise<void> {
    // Verify ownership
    const existing = await this.getDocumentById(id, userId);
    if (!existing) {
      throw new Error('Document not found');
    }

    await prisma.documentFile.update({
      where: { id },
      data: {
        isDeleted: true,
        deletedAt: new Date(),
      },
    });
  }

  /**
   * Permanently delete a document
   */
  async permanentlyDeleteDocument(id: string, userId: string): Promise<void> {
    // Verify ownership
    const existing = await prisma.documentFile.findFirst({
      where: { id, userId },
    });

    if (!existing) {
      throw new Error('Document not found');
    }

    await prisma.documentFile.delete({
      where: { id },
    });
  }

  /**
   * Restore a deleted document
   */
  async restoreDocument(id: string, userId: string): Promise<Document> {
    const document = await prisma.documentFile.findFirst({
      where: { id, userId, isDeleted: true },
    });

    if (!document) {
      throw new Error('Deleted document not found');
    }

    const restored = await prisma.documentFile.update({
      where: { id },
      data: {
        isDeleted: false,
        deletedAt: null,
      },
    });

    return restored as Document;
  }

  /**
   * Get documents by folder
   */
  async getDocumentsByFolder(folderId: string, userId: string): Promise<Document[]> {
    return this.listDocuments({
      userId,
      folderId,
      includeDeleted: false,
    });
  }

  /**
   * Move document to different folder
   */
  async moveDocument(
    id: string,
    userId: string,
    targetFolderId: string | null
  ): Promise<Document> {
    return this.updateDocument(id, userId, { folderId: targetFolderId });
  }

  /**
   * Get document count for user
   */
  async getDocumentCount(userId: string): Promise<number> {
    return prisma.documentFile.count({
      where: {
        userId,
        isDeleted: false,
      },
    });
  }

  /**
   * Search documents by name
   */
  async searchDocuments(userId: string, query: string): Promise<Document[]> {
    const documents = await prisma.documentFile.findMany({
      where: {
        userId,
        isDeleted: false,
        name: {
          contains: query,
          mode: 'insensitive',
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    return documents as Document[];
  }
}
