/**
 * User Module Type Definitions
 */

export interface User {
  id: string;
  email: string;
  name: string | null;
  emailVerified: Date | null;
  image: string | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  image: string | null;
  documentCount?: number;
  folderCount?: number;
}

export interface UpdateProfileInput {
  name?: string;
  image?: string;
}

export interface ChangePasswordInput {
  currentPassword: string;
  newPassword: string;
}
