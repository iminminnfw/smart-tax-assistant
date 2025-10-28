/**
 * Document Module Type Definitions
 */

export interface Document {
  id: string;
  userId: string;
  name: string;
  type: string;
  size: number;
  url: string;
  folderId: string | null;
  isDeleted: boolean;
  deletedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface DocumentFolder {
  id: string;
  userId: string;
  name: string;
  color: string;
  isDeleted: boolean;
  deletedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
  files?: Document[];
  children?: DocumentFolder[];
}

export interface CreateDocumentInput {
  userId: string;
  name: string;
  type: string;
  size: number;
  url: string;
  folderId?: string | null;
}

export interface UpdateDocumentInput {
  name?: string;
  folderId?: string | null;
}

export interface CreateFolderInput {
  userId: string;
  name: string;
  color?: string;
  parentId?: string | null;
}

export interface UpdateFolderInput {
  name?: string;
  color?: string;
}

export interface TrashItem {
  id: string;
  name: string;
  deletedAt: string;
  type: 'file' | 'folder';
  folderId?: string;
}

export interface ListDocumentsParams {
  userId: string;
  folderId?: string | null;
  includeDeleted?: boolean;
}

export interface ListFoldersParams {
  userId: string;
  includeFiles?: boolean;
  includeDeleted?: boolean;
}
